from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
from log_monitor import LogMonitor
from log_queue import LogQueue
from json_accumulator import JSONAccumulator

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'log_monitoring_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize components
json_accumulator = JSONAccumulator()
log_queue = LogQueue(socketio, json_accumulator)
log_monitor = LogMonitor(log_queue)

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

@app.route('/')
def index():
    available_weeks = json_accumulator.get_available_weeks()
    return jsonify({
        "status": "Log Monitoring System Running",
        "available_weeks": available_weeks,
        "current_week": json_accumulator.current_week,
        "endpoints": [
            "/api/logs",
            "/api/logs/errors",
            "/api/logs/requests",
            "/api/stats",
            "/api/stats/requests"
        ]
    })

@app.route('/api/logs')
def get_logs():
    """Get all logs with filtering and pagination"""
    # Get filter parameters
    log_type = request.args.get('type', 'all')
    source = request.args.get('source')
    level = request.args.get('level')
    week = request.args.get('week', json_accumulator.current_week)
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    search_term = request.args.get('search_term')
    search_type = request.args.get('search_type', 'message')
    
    # Debug log
    print("Search parameters:", {
        'type': log_type,
        'source': source,
        'level': level,
        'week': week,
        'start_time': start_time,
        'end_time': end_time,
        'search_term': search_term,
        'search_type': search_type
    })
    
    # Get pagination parameters
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
    except ValueError:
        page = 1
        per_page = 50
    
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
    
    return jsonify({
        'logs': paginated_logs,
        'total': len(filtered_logs),
        'page': page,
        'per_page': per_page,
        'total_pages': (len(filtered_logs) + per_page - 1) // per_page,
        'week': week,
        'available_weeks': json_accumulator.get_available_weeks()
    })

@app.route('/api/logs/errors')
def get_errors():
    """Get error and warning logs with filtering and pagination"""
    week = request.args.get('week', json_accumulator.current_week)
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
    except ValueError:
        page = 1
        per_page = 50
    
    # Get all error logs
    logs = json_accumulator.get_logs('error', None, week)
    
    # Sort by timestamp (newest first)
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Paginate results
    paginated_logs = paginate_logs(logs, page, per_page)
    
    return jsonify({
        'logs': paginated_logs,
        'total': len(logs),
        'page': page,
        'per_page': per_page,
        'total_pages': (len(logs) + per_page - 1) // per_page,
        'week': week,
        'available_weeks': json_accumulator.get_available_weeks()
    })

@app.route('/api/logs/requests')
def get_requests():
    """Get request logs with filtering and pagination"""
    week = request.args.get('week', json_accumulator.current_week)
    source = request.args.get('source')  # node, python
    status_code = request.args.get('status_code')
    
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
    except ValueError:
        page = 1
        per_page = 50
    
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
    
    return jsonify({
        'logs': paginated_logs,
        'total': len(logs),
        'page': page,
        'per_page': per_page,
        'total_pages': (len(logs) + per_page - 1) // per_page,
        'week': week,
        'available_weeks': json_accumulator.get_available_weeks()
    })

@app.route('/api/stats')
def get_stats():
    """Get comprehensive log statistics"""
    week = request.args.get('week', json_accumulator.current_week)
    
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
    
    return jsonify(stats)

@app.route('/api/stats/requests')
def get_request_stats():
    """Get detailed request log statistics"""
    week = request.args.get('week', json_accumulator.current_week)
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
    
    return jsonify(stats)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'msg': 'Connected to log monitoring system'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    # Load existing log hashes to prevent duplicates
    json_accumulator._load_existing_log_hashes()
    
    # Start log monitoring
    log_queue.start()
    log_monitor.start_monitoring()
    
    # Start the Flask-SocketIO server
    print("Starting Log Monitoring System...")
    print("Access dashboard at: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
