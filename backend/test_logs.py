#!/usr/bin/env python3
import json
import time
from datetime import datetime
import os
import glob

def find_latest_log_files():
    """Find the most recent log files to append to"""
    
    # Find latest Python log files (go up one directory from backend)
    python_logs = {}
    for log_type in ['info', 'error', 'access', 'warning']:
        pattern = f"../python_logs/{log_type}-*.log"
        files = glob.glob(pattern)
        if files:
            # Get the most recent file (by modification time)
            latest_file = max(files, key=os.path.getmtime)
            python_logs[log_type] = latest_file
    
    # Find latest Node.js log files (go up one directory from backend)
    node_logs = {}
    for log_type, subdir in [('requests', 'requestsLogs'), ('error', 'errorLogs'), ('access', 'accessLogs')]:
        pattern = f"../node_logs/{subdir}/{log_type}-*.log"
        files = glob.glob(pattern)
        if files:
            # Get the most recent file (by modification time)
            latest_file = max(files, key=os.path.getmtime)
            node_logs[log_type] = latest_file
    
    return python_logs, node_logs

def ensure_directory_exists(filepath):
    """Ensure the directory for the file exists"""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def add_test_python_logs(file_paths):
    """Add test entries to Python log files"""
    
    # Test entries for different Python log files
    python_logs = {
        'info': {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "name": "test.application",
            "message": "TEST: User login successful - testing log monitoring system",
            "path": "/app/test1.py:123",
            "function": "test_login",
            "filename": "test1.py",
            "stack_info": None,
            "request_id": "req-test-12345",
            "client_ip": "192.168.1.100",
            "user_id": "test_user_999"
        },
        'error': {
            "timestamp": datetime.now().isoformat(),
            "level": "ERROR", 
            "name": "test.application",
            "message": "TEST: Database connection failed - this is a test error",
            "path": "/app/test2.py:456",
            "function": "test_db_connect",
            "filename": "test2.py",
            "stack_info": None,
            "request_id": "req-test-67890",
            "client_ip": "192.168.1.100",
            "user_id": "test_user_999"
        },
        'access': {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "name": "test.access",
            "message": "GET /test/endpoint - 200 - 45.2ms - req-test-access-123",
            "path": "/test/endpoint",
            "function": "logging_middleware",
            "filename": "test3.py",
            "stack_info": None,
            "status_code": 200,
            "duration_ms": 45.2,
            "user_id": "test_user_999",
            "request_id": "req-test-access-123",
            "client_ip": "192.168.1.100"
        }
    }
    
    for log_type, log_entry in python_logs.items():
        if log_type in file_paths:
            filename = file_paths[log_type]
            print(f"Adding test entry to {filename}")
            
            ensure_directory_exists(filename)
            
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')

def add_test_node_logs(file_paths):
    """Add test entries to Node.js log files"""
    
    # Test Node.js request log
    node_request_log = {
        "level": "info",
        "message": {
            "endpoint": "/test1/api/users",
            "ip": "::ffff:192.168.1.100",
            "level": "INFO",
            "method": "POST",
            "req_id": "req-test-node-123",
            "response_time": "25.5ms",
            "status_code": 201,
            "user_agent": "TestAgent/1.0",
            "user_id": "test_user_999"
        },
        "timestamp": datetime.now().isoformat() + "Z"
    }
    
    # Test Node.js error log
    node_error_log = {
        "timestamp": datetime.now().isoformat() + "Z",
        "level": "error",
        "message": "TEST1: Authentication failed for user test_user_999 - invalid token",
        "req_id": "req-test-node-error-456",
        "ip": "::ffff:192.168.1.100"
    }
    
    # Test Node.js access log
    node_access_log = {
        "level": "info",
        "message": {
            "endpoint": "/test3/health",
            "ip": "::ffff:192.168.1.100",
            "level": "INFO", 
            "method": "GET",
            "req_id": "req-test-node-access-789",
            "response_time": "2.1ms",
            "status_code": 200,
            "user_agent": "TestAgent/1.0",
            "user_id": "test_user_999"
        },
        "timestamp": datetime.now().isoformat() + "Z"
    }
    
    # Map logs to their corresponding files
    logs_to_add = [
        ("requests", node_request_log),
        ("error", node_error_log),
        ("access", node_access_log)
    ]
    
    for log_type, log_entry in logs_to_add:
        if log_type in file_paths:
            filename = file_paths[log_type]
            print(f"Adding test entry to {filename}")
            
            ensure_directory_exists(filename)
            
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')

def main():
    print("🧪 TESTING LOG MONITORING SYSTEM")
    print("=" * 50)
    
    print("🔍 Finding existing log files...")
    python_files, node_files = find_latest_log_files()
    
    print("\n📝 Python log files found:")
    if python_files:
        for log_type, filepath in python_files.items():
            print(f"  ✅ {log_type}: {filepath}")
    else:
        print("  ❌ No Python log files found!")
    
    print("\n📝 Node.js log files found:")
    if node_files:
        for log_type, filepath in node_files.items():
            print(f"  ✅ {log_type}: {filepath}")
    else:
        print("  ❌ No Node.js log files found!")
    
    if not python_files and not node_files:
        print("\n❌ No log files found to append to!")
        print("   Make sure your log files exist with the pattern:")
        print("   - python_logs/[info|error|access|warning]-YYYY-MM-DD.log")
        print("   - node_logs/[requestsLogs|errorLogs|accessLogs]/[requests|error|access]-YYYY-MM-DD.log")
        return
    
    print("\n📝 Adding test log entries...")
    
    # Add test logs
    if python_files:
        add_test_python_logs(python_files)
    
    if node_files:
        add_test_node_logs(node_files)
    
    print("\n✅ Test log entries added!")
    print("\n📊 Expected results:")
    print("  • New entries should appear in backend/unified_logs/ JSONL files")
    print("  • Real-time updates should appear on dashboard")
    print("  • Check the following unified files:")
    print("    - unified_request_logs_2025_W27.jsonl (Python access + Node requests)")
    print("    - unified_error_logs_2025_W27.jsonl (Python error + Node error)")
    print("    - unified_info_logs_2025_W27.jsonl (Python info + Node access)")
    
    print("\n🚀 How to run the complete test:")
    print("1. Start backend: cd backend && python app.py")
    print("2. Start frontend: cd frontend && npm run dev")
    print("3. Open dashboard: http://localhost:3000")
    print("4. Run this test: python test_logs.py")
    print("5. Watch logs appear in real-time!")

if __name__ == "__main__":
    main() 