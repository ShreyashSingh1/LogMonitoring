from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import os
from datetime import datetime
from log_monitor import LogMonitor
from log_queue import LogQueue
from json_accumulator import JSONAccumulator

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'log_monitoring_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize components
json_accumulator = JSONAccumulator()
log_queue = LogQueue(socketio)
log_monitor = LogMonitor(log_queue)

@app.route('/')
def index():
    return jsonify({
        "status": "Log Monitoring System Running",
        "endpoints": [
            "/api/logs",
            "/api/logs/errors",
            "/api/logs/requests",
            "/api/stats"
        ]
    })

@app.route('/api/logs')
def get_logs():
    """Get all logs with optional filtering"""
    log_type = request.args.get('type', 'all')  # all, info, error, request
    level = request.args.get('level')  # info, error, warning
    week = request.args.get('week')  # YYYY_WXX format
    
    logs = json_accumulator.get_logs(log_type, level, week)
    return jsonify(logs)

@app.route('/api/logs/errors')
def get_errors():
    """Get only error and warning logs"""
    week = request.args.get('week')
    logs = json_accumulator.get_logs('error', None, week)
    return jsonify(logs)

@app.route('/api/logs/requests')
def get_requests():
    """Get only request logs"""
    week = request.args.get('week')
    logs = json_accumulator.get_logs('request', None, week)
    return jsonify(logs)

@app.route('/api/stats')
def get_stats():
    """Get log statistics"""
    week = request.args.get('week')
    all_logs = json_accumulator.get_logs('all', None, week)
    
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
            'info': len([l for l in all_logs if l.get('level') == 'info']),
            'error': len([l for l in all_logs if l.get('level') == 'error']),
            'warning': len([l for l in all_logs if l.get('level') in ['warn', 'warning']]),
            'access': len([l for l in all_logs if l.get('original_level', '').upper() == 'ACCESS'])
        }
    }
    
    return jsonify(stats)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'msg': 'Connected to log monitoring system'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    # Start log monitoring
    log_queue.start()
    log_monitor.start_monitoring()
    
    # Start the Flask-SocketIO server
    print("Starting Log Monitoring System...")
    print("Access dashboard at: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
