#!/usr/bin/env python3
"""
Real-time WebSocket test script to verify the log monitoring system is working properly.
Run this after starting the backend to test real-time updates.
"""

import socketio
import json
import time
import threading
from datetime import datetime
import os
import glob

class LogTestClient:
    def __init__(self):
        self.sio = socketio.Client()
        self.stats_received = 0
        self.logs_received = 0
        self.connected = False
        
        # Setup event handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.sio.event
        def connect():
            print("🟢 Connected to WebSocket server")
            self.connected = True
        
        @self.sio.event
        def disconnect():
            print("🔴 Disconnected from WebSocket server")
            self.connected = False
        
        @self.sio.event
        def connection_established(data):
            print(f"✅ Connection established. Client ID: {data.get('client_id')}")
            print(f"📊 Initial stats: {data.get('stats', {}).get('total_logs', 0)} total logs")
        
        @self.sio.event
        def new_log(data):
            self.logs_received += 1
            log_type = data.get('log_type', 'unknown')
            source = data.get('source', 'unknown')
            message = data.get('message', '')[:50]
            print(f"📋 New {log_type} log from {source}: {message}...")
        
        @self.sio.event
        def stats_update(data):
            self.stats_received += 1
            total = data.get('total_logs', 0)
            print(f"📊 Stats update #{self.stats_received}: {total} total logs")
        
        @self.sio.event
        def error_detected(data):
            source = data.get('source', 'unknown')
            message = data.get('message', '')[:50]
            print(f"🚨 Error detected from {source}: {message}...")
    
    def connect_to_server(self):
        try:
            print("🔗 Connecting to WebSocket server...")
            self.sio.connect('http://127.0.0.1:5000')
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def disconnect_from_server(self):
        if self.connected:
            self.sio.disconnect()
    
    def get_status(self):
        return {
            'connected': self.connected,
            'logs_received': self.logs_received,
            'stats_received': self.stats_received
        }

def add_single_test_log():
    """Add a single test log to verify real-time processing"""
    # Find the most recent Python info log file
    pattern = "../python_logs/info-*.log"
    files = glob.glob(pattern)
    
    if not files:
        print("❌ No Python info log files found!")
        return False
    
    latest_file = max(files, key=os.path.getmtime)
    
    test_log = {
        "timestamp": datetime.now().isoformat(),
        "level": "INFO",
        "name": "test.realtime",
        "message": f"REALTIME TEST: WebSocket verification at {datetime.now().strftime('%H:%M:%S')}",
        "path": "/app/test_realtime.py:123",
        "function": "test_realtime_updates",
        "filename": "test_realtime.py",
        "stack_info": None,
        "request_id": f"req-realtime-{int(time.time())}",
        "client_ip": "127.0.0.1",
        "user_id": "test_realtime_user"
    }
    
    try:
        with open(latest_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(test_log) + '\n')
        
        print(f"✅ Added test log to {os.path.basename(latest_file)}")
        return True
    except Exception as e:
        print(f"❌ Error adding test log: {e}")
        return False

def main():
    print("🧪 REAL-TIME WEBSOCKET TEST")
    print("=" * 50)
    
    # Create test client
    client = LogTestClient()
    
    # Connect to server
    if not client.connect_to_server():
        return
    
    try:
        # Wait for connection to establish
        time.sleep(2)
        
        print("\n🔍 Testing real-time log updates...")
        print("   Adding a test log entry...")
        
        # Add a test log
        if add_single_test_log():
            print("   Waiting for real-time updates...")
            
            # Wait for processing
            time.sleep(3)
            
            # Check results
            status = client.get_status()
            print(f"\n📊 Test Results:")
            print(f"   Connected: {status['connected']}")
            print(f"   Logs received: {status['logs_received']}")
            print(f"   Stats updates: {status['stats_received']}")
            
            if status['logs_received'] > 0 and status['stats_received'] > 0:
                print("✅ Real-time updates are working!")
            elif status['logs_received'] > 0:
                print("⚠️ Logs received but no stats updates")
            elif status['stats_received'] > 0:
                print("⚠️ Stats received but no new logs")
            else:
                print("❌ No real-time updates received - check backend logs")
        
        print("\n🔄 Adding another test log to double-check...")
        time.sleep(1)
        
        if add_single_test_log():
            time.sleep(2)
            final_status = client.get_status()
            print(f"   Final count - Logs: {final_status['logs_received']}, Stats: {final_status['stats_received']}")
        
    except KeyboardInterrupt:
        print("\n⛔ Test interrupted by user")
    finally:
        client.disconnect_from_server()
        print("👋 Test completed")

if __name__ == "__main__":
    main() 