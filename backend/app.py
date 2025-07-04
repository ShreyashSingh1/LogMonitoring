from flask import Flask, jsonify, request, make_response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
from log_monitor import LogMonitor
from log_queue import LogQueue
from json_accumulator import JSONAccumulator
import eventlet
from functools import wraps
import signal
import sys

# Patch eventlet for better async performance
eventlet.monkey_patch(socket=True, select=True)

# Define allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Add Vite's default dev server port
    "http://127.0.0.1:5173",
    "ws://localhost:3000",
    "ws://127.0.0.1:3000",
    "ws://localhost:5173",
    "ws://127.0.0.1:5173"
]

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}})
app.config['SECRET_KEY'] = 'log_monitoring_secret_key'

# Configure SocketIO with better performance settings
socketio = SocketIO(
    app,
    cors_allowed_origins=ALLOWED_ORIGINS,
    async_mode='eventlet',
    ping_timeout=5000,
    ping_interval=25000,
    max_http_buffer_size=100 * 1024 * 1024,  # 100MB
    async_handlers=True,
    logger=True,  # Enable logging temporarily to debug connection issues
    engineio_logger=True,
    always_connect=True,
    path='/socket.io/',
    transports=['websocket', 'polling']
)

# Initialize components
json_accumulator = JSONAccumulator()
log_queue = LogQueue(socketio, json_accumulator)
log_monitor = LogMonitor(log_queue)

# Track connected clients
connected_clients = set()

def paginate_logs(logs, page=1, per_page=50):
    """Helper function to paginate logs"""
    start = (page - 1) * per_page
    end = start + per_page
    return logs[start:end]

def filter_logs(logs, filters):
    """Helper function to filter logs based on multiple criteria"""
    filtered_logs = logs
    
    if filters.get('source'):
        filtered_logs = [log for log in filtered_logs if log.get('source') == filters['source']]
    
    if filters.get('level'):
        filtered_logs = [log for log in filtered_logs if log.get('level', '').lower() == filters['level'].lower()]
    
    if filters.get('search_term'):
        search_term = filters['search_term'].lower()
        search_type = filters.get('search_type', 'message')
        
        if search_type == 'req_id':
            filtered_logs = [
                log for log in filtered_logs 
                if (search_term in str(log.get('req_id', '')).lower() or 
                    search_term in str(log.get('request_id', '')).lower())
            ]
        else:  # default to message search
            filtered_logs = [log for log in filtered_logs if search_term in str(log.get('message', '')).lower()]
    
    if filters.get('start_time'):
        try:
            start_time = datetime.fromisoformat(filters['start_time'])
            filtered_logs = [log for log in filtered_logs if datetime.fromisoformat(log.get('timestamp', '')).replace(tzinfo=None) >= start_time]
        except (ValueError, TypeError):
            pass
    
    if filters.get('end_time'):
        try:
            end_time = datetime.fromisoformat(filters['end_time'])
            filtered_logs = [log for log in filtered_logs if datetime.fromisoformat(log.get('timestamp', '')).replace(tzinfo=None) <= end_time]
        except (ValueError, TypeError):
            pass
    
    return filtered_logs

@socketio.on('connect')
def handle_connect():
    """Handle new client connections"""
    client_id = request.sid
    connected_clients.add(client_id)
    # Only log total connections count
    print(f"Active socket connections: {len(connected_clients)}")
    
    # Send initial stats to the new client
    week = json_accumulator.current_week
    all_logs = []
    for log_type in ['info', 'error', 'request']:
        logs = json_accumulator.get_logs(log_type, None, week)
        all_logs.extend(logs)
    
    emit('connection_established', {
        'client_id': client_id,
        'stats': get_current_stats(),
        'recent_logs': all_logs[-100:]
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnections"""
    client_id = request.sid
    if client_id in connected_clients:
        connected_clients.remove(client_id)
    # Only log total connections count
    print(f"Active socket connections: {len(connected_clients)}")

def get_current_stats():
    """Get current system stats"""
    week = json_accumulator.current_week
    all_logs = []
    for log_type in ['info', 'error', 'request']:
        logs = json_accumulator.get_logs(log_type, None, week)
        all_logs.extend(logs)
    
    now = datetime.now()
    last_hour = now - timedelta(hours=1)
    last_24h = now - timedelta(days=1)
    
    return {
        'total_logs': len(all_logs),
        'by_type': {
            'info': len([l for l in all_logs if l.get('log_type') == 'info']),
            'error': len([l for l in all_logs if l.get('log_type') == 'error']),
            'request': len([l for l in all_logs if l.get('log_type') == 'request'])
        },
        'by_source': {
            'node': len([l for l in all_logs if l.get('source') == 'node']),
            'python': len([l for l in all_logs if l.get('source') == 'python'])
        },
        'by_level': {
            'info': len([l for l in all_logs if l.get('level', '').lower() == 'info']),
            'error': len([l for l in all_logs if l.get('level', '').lower() == 'error']),
            'warning': len([l for l in all_logs if l.get('level', '').lower() in ['warn', 'warning']]),
            'access': len([l for l in all_logs if l.get('level', '').lower() == 'access'])
        },
        'time_based': {
            'last_hour': len([l for l in all_logs if datetime.fromisoformat(l.get('timestamp', '')).replace(tzinfo=None) >= last_hour]),
            'last_24h': len([l for l in all_logs if datetime.fromisoformat(l.get('timestamp', '')).replace(tzinfo=None) >= last_24h])
        }
    }

def error_response(message, status_code=400):
    """Helper function to create error responses"""
    return make_response(
        jsonify({
            'error': True,
            'message': message,
            'status_code': status_code
        }),
        status_code
    )

def validate_date_param(date_str):
    """Validate and parse date string"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None

def api_response(func):
    """Decorator for API endpoints with error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            print(f"❌ API Error in {func.__name__}: {str(e)}")
            return error_response("Internal server error", 500)
    return wrapper

@app.route('/')
@api_response
def index():
    """Get system status and Socket.IO API documentation"""
    available_weeks = json_accumulator.get_available_weeks()
    return jsonify({
        "status": "Log Monitoring System Running (Socket.IO Based)",
        "version": "2.0.0",
        "available_weeks": available_weeks,
        "current_week": json_accumulator.current_week,
        "stats": get_current_stats(),
        "api_type": "Socket.IO Events (Real-time)",
        "connection_url": "ws://127.0.0.1:5000/socket.io/",
        "rest_endpoints": {
            "GET /": "System status and Socket.IO API documentation",
            "GET /api/health": "System health check for external monitoring"
        },
        "socket_events": {
            "client_events": {
                "get_logs": "Request logs with filtering and pagination → logs_response",
                "get_error_logs": "Request error logs → error_logs_response", 
                "get_request_logs": "Request HTTP logs → request_logs_response",
                "get_stats": "Request system statistics → stats_response",
                "get_request_stats": "Request HTTP statistics → request_stats_response",
                "get_sources": "Request available log sources → sources_response",
                "get_levels": "Request available log levels → levels_response",
                "search_logs": "Search logs with advanced filters → search_logs_response",
                "get_health": "Request health status → health_response"
            },
            "server_events": {
                "connect": "Client connection established",
                "disconnect": "Client disconnection",
                "connection_established": "Initial connection data with stats and recent logs",
                "new_log": "Real-time log broadcast (any type)",
                "new_info_log": "Real-time info log broadcast",
                "new_error_log": "Real-time error log broadcast", 
                "new_request_log": "Real-time request log broadcast",
                "error_detected": "Error/warning log detected",
                "stats_update": "Real-time statistics update",
                "logs_response": "Response to get_logs request",
                "error_logs_response": "Response to get_error_logs request",
                "request_logs_response": "Response to get_request_logs request", 
                "stats_response": "Response to get_stats request",
                "request_stats_response": "Response to get_request_stats request",
                "sources_response": "Response to get_sources request",
                "levels_response": "Response to get_levels request",
                "search_logs_response": "Response to search_logs request",
                "health_response": "Response to get_health request",
                "error": "Error message for failed requests"
            }
        },
        "migration_note": "All REST API endpoints have been converted to Socket.IO events for better real-time performance. Use the socket events above instead of HTTP requests."
    })

# Keep health endpoint for external monitoring
@app.route('/api/health')
@api_response
def health_check():
    """System health check endpoint for external monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'log_queue': {
                'status': 'running' if log_queue.is_running else 'stopped',
                'queue_size': log_queue.queue.qsize()
            },
            'log_monitor': {
                'status': 'running' if log_monitor.is_running else 'stopped'
            },
            'websocket': {
                'connected_clients': len(connected_clients)
            }
        },
        'message': 'All API endpoints have been converted to Socket.IO events for better performance'
    })

# Socket.IO Event Handlers
@socketio.on('get_logs')
def handle_get_logs(data):
    """Handle get logs request via socket"""
    try:
        # Get filter parameters from data
        log_type = data.get('type', 'all')
        source = data.get('source')
        level = data.get('level')
        week = data.get('week', json_accumulator.current_week)
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        search_term = data.get('search_term')
        search_type = data.get('search_type', 'message')
        
        # Get pagination parameters
        page = data.get('page', 1)
        per_page = min(data.get('per_page', 50), 100)
        
        # Get logs
        logs = json_accumulator.get_logs(log_type, None, week)
        
        # Apply filters
        filters = {
            'source': source,
            'level': level,
            'start_time': start_time,
            'end_time': end_time,
            'search_term': search_term,
            'search_type': search_type,
        }
        filtered_logs = filter_logs(logs, filters)
        
        # Sort logs by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Paginate results
        paginated_logs = paginate_logs(filtered_logs, page, per_page)
        
        emit('logs_response', {
            'logs': paginated_logs,
            'total': len(filtered_logs),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(filtered_logs) + per_page - 1) // per_page,
            'week': week,
            'available_weeks': json_accumulator.get_available_weeks()
        })
    except Exception as e:
        emit('error', {'message': f'Error fetching logs: {str(e)}'})

@socketio.on('get_error_logs')
def handle_get_error_logs(data):
    """Handle get error logs request via socket"""
    try:
        week = data.get('week', json_accumulator.current_week)
        page = data.get('page', 1)
        per_page = min(data.get('per_page', 50), 100)
        
        # Get all error logs
        logs = json_accumulator.get_logs('error', None, week)
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Paginate results
        paginated_logs = paginate_logs(logs, page, per_page)
        
        emit('error_logs_response', {
            'logs': paginated_logs,
            'total': len(logs),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(logs) + per_page - 1) // per_page,
            'week': week,
            'available_weeks': json_accumulator.get_available_weeks()
        })
    except Exception as e:
        emit('error', {'message': f'Error fetching error logs: {str(e)}'})

@socketio.on('get_request_logs')
def handle_get_request_logs(data):
    """Handle get request logs request via socket"""
    try:
        week = data.get('week', json_accumulator.current_week)
        source = data.get('source')
        status_code = data.get('status_code')
        page = data.get('page', 1)
        per_page = min(data.get('per_page', 50), 100)
        
        # Get all request logs
        logs = json_accumulator.get_logs('request', None, week)
        
        # Apply filters
        if source:
            logs = [log for log in logs if log.get('source') == source]
        if status_code:
            logs = [log for log in logs if str(log.get('status_code')) == status_code]
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Paginate results
        paginated_logs = paginate_logs(logs, page, per_page)
        
        emit('request_logs_response', {
            'logs': paginated_logs,
            'total': len(logs),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(logs) + per_page - 1) // per_page,
            'week': week,
            'available_weeks': json_accumulator.get_available_weeks()
        })
    except Exception as e:
        emit('error', {'message': f'Error fetching request logs: {str(e)}'})

@socketio.on('get_stats')
def handle_get_stats(data):
    """Handle get stats request via socket"""
    try:
        week = data.get('week', json_accumulator.current_week)
        
        # Get all logs for the week
        all_logs = []
        for log_type in ['info', 'error', 'request']:
            logs = json_accumulator.get_logs(log_type, None, week)
            all_logs.extend(logs)
        
        # Calculate time ranges
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(days=1)
        
        stats = {
            'total_logs': len(all_logs),
            'by_type': {
                'info': len([l for l in all_logs if l.get('log_type') == 'info']),
                'error': len([l for l in all_logs if l.get('log_type') == 'error']),
                'request': len([l for l in all_logs if l.get('log_type') == 'request'])
            },
            'by_source': {
                'node': len([l for l in all_logs if l.get('source') == 'node']),
                'python': len([l for l in all_logs if l.get('source') == 'python'])
            },
            'by_level': {
                'info': len([l for l in all_logs if l.get('level', '').lower() == 'info']),
                'error': len([l for l in all_logs if l.get('level', '').lower() == 'error']),
                'warning': len([l for l in all_logs if l.get('level', '').lower() in ['warn', 'warning']]),
                'access': len([l for l in all_logs if l.get('level', '').lower() == 'access'])
            },
            'time_based': {
                'last_hour': len([l for l in all_logs if datetime.fromisoformat(l.get('timestamp', '')).replace(tzinfo=None) >= last_hour]),
                'last_24h': len([l for l in all_logs if datetime.fromisoformat(l.get('timestamp', '')).replace(tzinfo=None) >= last_24h])
            },
            'week': week,
            'available_weeks': json_accumulator.get_available_weeks()
        }
        
        emit('stats_response', stats)
    except Exception as e:
        emit('error', {'message': f'Error fetching stats: {str(e)}'})

@socketio.on('get_request_stats')
def handle_get_request_stats(data):
    """Handle get request stats request via socket"""
    try:
        week = data.get('week', json_accumulator.current_week)
        request_logs = json_accumulator.get_logs('request', None, week)
        
        # Initialize stats
        stats = {
            'total_requests': len(request_logs),
            'by_source': {
                'node': len([l for l in request_logs if l.get('source') == 'node']),
                'python': len([l for l in request_logs if l.get('source') == 'python'])
            },
            'by_method': {},
            'by_status': {
                '2xx': 0,
                '3xx': 0,
                '4xx': 0,
                '5xx': 0
            },
            'response_times': {
                'avg': 0,
                'min': float('inf'),
                'max': 0
            },
            'week': week,
            'available_weeks': json_accumulator.get_available_weeks()
        }
        
        # Calculate detailed stats
        total_response_time = 0
        for log in request_logs:
            # Method stats
            method = log.get('method', 'UNKNOWN')
            stats['by_method'][method] = stats['by_method'].get(method, 0) + 1
            
            # Status code stats
            status_code = str(log.get('status_code', ''))
            if status_code.startswith('2'):
                stats['by_status']['2xx'] += 1
            elif status_code.startswith('3'):
                stats['by_status']['3xx'] += 1
            elif status_code.startswith('4'):
                stats['by_status']['4xx'] += 1
            elif status_code.startswith('5'):
                stats['by_status']['5xx'] += 1
            
            # Response time stats
            try:
                response_time = float(log.get('response_time', 0))
                total_response_time += response_time
                stats['response_times']['min'] = min(stats['response_times']['min'], response_time)
                stats['response_times']['max'] = max(stats['response_times']['max'], response_time)
            except (ValueError, TypeError):
                pass
        
        # Calculate average response time
        if request_logs:
            stats['response_times']['avg'] = total_response_time / len(request_logs)
        if stats['response_times']['min'] == float('inf'):
            stats['response_times']['min'] = 0
        
        emit('request_stats_response', stats)
    except Exception as e:
        emit('error', {'message': f'Error fetching request stats: {str(e)}'})

@socketio.on('get_sources')
def handle_get_sources(data):
    """Handle get sources request via socket"""
    try:
        week = data.get('week', json_accumulator.current_week)
        all_logs = []
        for log_type in ['info', 'error', 'request']:
            logs = json_accumulator.get_logs(log_type, None, week)
            all_logs.extend(logs)
        
        sources = {}
        for log in all_logs:
            source = log.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        emit('sources_response', {
            'sources': [
                {'name': source, 'count': count}
                for source, count in sorted(sources.items())
            ]
        })
    except Exception as e:
        emit('error', {'message': f'Error fetching sources: {str(e)}'})

@socketio.on('get_levels')
def handle_get_levels(data):
    """Handle get levels request via socket"""
    try:
        week = data.get('week', json_accumulator.current_week)
        all_logs = []
        for log_type in ['info', 'error', 'request']:
            logs = json_accumulator.get_logs(log_type, None, week)
            all_logs.extend(logs)
        
        levels = {}
        for log in all_logs:
            level = log.get('level', 'unknown').lower()
            levels[level] = levels.get(level, 0) + 1
        
        emit('levels_response', {
            'levels': [
                {'name': level, 'count': count}
                for level, count in sorted(levels.items())
            ]
        })
    except Exception as e:
        emit('error', {'message': f'Error fetching levels: {str(e)}'})

@socketio.on('search_logs')
def handle_search_logs(data):
    """Handle advanced log search request via socket"""
    try:
        # Get search parameters
        query = data.get('q', '').lower()
        log_type = data.get('type')
        source = data.get('source')
        level = data.get('level')
        start_time = validate_date_param(data.get('start_time'))
        end_time = validate_date_param(data.get('end_time'))
        field = data.get('field', 'message')  # Field to search in
        page = data.get('page', 1)
        per_page = min(data.get('per_page', 50), 100)
        
        # Get all logs
        all_logs = []
        types_to_search = [log_type] if log_type else ['info', 'error', 'request']
        for t in types_to_search:
            logs = json_accumulator.get_logs(t, None, json_accumulator.current_week)
            all_logs.extend(logs)
        
        # Apply filters
        filtered_logs = all_logs
        
        if query:
            filtered_logs = [
                log for log in filtered_logs
                if query in str(log.get(field, '')).lower()
            ]
        
        if source:
            filtered_logs = [
                log for log in filtered_logs
                if log.get('source') == source
            ]
        
        if level:
            filtered_logs = [
                log for log in filtered_logs
                if log.get('level', '').lower() == level.lower()
            ]
        
        if start_time:
            filtered_logs = [
                log for log in filtered_logs
                if datetime.fromisoformat(log.get('timestamp', '')).replace(tzinfo=None) >= start_time
            ]
        
        if end_time:
            filtered_logs = [
                log for log in filtered_logs
                if datetime.fromisoformat(log.get('timestamp', '')).replace(tzinfo=None) <= end_time
            ]
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Paginate results
        paginated_logs = paginate_logs(filtered_logs, page, per_page)
        
        emit('search_logs_response', {
            'logs': paginated_logs,
            'total': len(filtered_logs),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(filtered_logs) + per_page - 1) // per_page,
            'query_params': {
                'q': query,
                'type': log_type,
                'source': source,
                'level': level,
                'field': field,
                'start_time': start_time.isoformat() if start_time else None,
                'end_time': end_time.isoformat() if end_time else None
            }
        })
    except Exception as e:
        emit('error', {'message': f'Error searching logs: {str(e)}'})

@socketio.on('get_health')
def handle_get_health(data):
    """Handle health check request via socket"""
    try:
        emit('health_response', {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'log_queue': {
                    'status': 'running' if log_queue.is_running else 'stopped',
                    'queue_size': log_queue.queue.qsize()
                },
                'log_monitor': {
                    'status': 'running' if log_monitor.is_running else 'stopped'
                },
                'websocket': {
                    'connected_clients': len(connected_clients)
                }
            }
        })
    except Exception as e:
        emit('error', {'message': f'Error fetching health status: {str(e)}'})

if __name__ == '__main__':
    try:
        # Start components
        log_queue.start()
        log_monitor.start()
        
        print("🚀 Starting Log Monitoring System...")
        socketio.run(
            app,
            host='127.0.0.1',
            port=5000,
            debug=True,  # Enable debug mode temporarily
            use_reloader=False,
            log_output=True,
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        log_monitor.stop()
        log_queue.stop()
        raise
