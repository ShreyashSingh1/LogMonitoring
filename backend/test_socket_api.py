#!/usr/bin/env python3
"""
Test script to verify Socket.IO API endpoints are working correctly
"""
import socketio
import json
import time
import asyncio

class SocketAPITester:
    def __init__(self, url='http://127.0.0.1:5000'):
        self.sio = socketio.Client()
        self.url = url
        self.responses = {}
        self.setup_listeners()
    
    def setup_listeners(self):
        """Setup Socket.IO event listeners"""
        
        @self.sio.event
        def connect():
            print("✅ Connected to Socket.IO server")
        
        @self.sio.event
        def disconnect():
            print("❌ Disconnected from Socket.IO server")
        
        @self.sio.event
        def connection_established(data):
            print(f"🤝 Connection established: {data.get('client_id')}")
            print(f"📊 Initial stats: {data.get('stats', {}).get('total_logs', 0)} total logs")
        
        # Response handlers
        response_events = [
            'logs_response', 'error_logs_response', 'request_logs_response',
            'stats_response', 'request_stats_response', 'sources_response',
            'levels_response', 'search_logs_response', 'health_response'
        ]
        
        for event in response_events:
            self.sio.on(event, lambda data, evt=event: self.handle_response(evt, data))
        
        @self.sio.event
        def error(data):
            print(f"❌ Socket error: {data}")
    
    def handle_response(self, event, data):
        """Handle API responses"""
        self.responses[event] = data
        print(f"📡 Received {event}: {len(str(data))} bytes")
    
    def connect_and_wait(self):
        """Connect to server and wait for connection"""
        try:
            self.sio.connect(self.url)
            time.sleep(2)  # Wait for connection_established
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def test_endpoint(self, event_name, request_data, response_event, timeout=5):
        """Test a specific Socket.IO endpoint"""
        print(f"\n🧪 Testing {event_name}...")
        
        # Clear previous response
        if response_event in self.responses:
            del self.responses[response_event]
        
        # Send request
        self.sio.emit(event_name, request_data)
        
        # Wait for response
        start_time = time.time()
        while response_event not in self.responses and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if response_event in self.responses:
            response = self.responses[response_event]
            print(f"✅ {event_name} - Success")
            
            # Print relevant info based on response type
            if 'logs' in response:
                print(f"   📝 Returned {len(response['logs'])} logs")
                if 'total' in response:
                    print(f"   📊 Total available: {response['total']}")
            elif 'sources' in response:
                print(f"   🔗 Found {len(response['sources'])} sources")
            elif 'levels' in response:
                print(f"   📋 Found {len(response['levels'])} levels")
            elif 'status' in response:
                print(f"   💚 Health status: {response['status']}")
            elif 'total_logs' in response:
                print(f"   📊 Total logs: {response['total_logs']}")
            
            return True
        else:
            print(f"❌ {event_name} - Timeout (no response)")
            return False
    
    def run_all_tests(self):
        """Run all API endpoint tests"""
        if not self.connect_and_wait():
            return False
        
        print("\n🚀 Starting Socket.IO API Tests...")
        
        tests = [
            ('get_health', {}, 'health_response'),
            ('get_stats', {}, 'stats_response'),
            ('get_sources', {}, 'sources_response'),
            ('get_levels', {}, 'levels_response'),
            ('get_logs', {'page': 1, 'per_page': 10}, 'logs_response'),
            ('get_error_logs', {'page': 1, 'per_page': 5}, 'error_logs_response'),
            ('get_request_logs', {'page': 1, 'per_page': 5}, 'request_logs_response'),
            ('get_request_stats', {}, 'request_stats_response'),
            ('search_logs', {'q': 'test', 'field': 'message', 'per_page': 5}, 'search_logs_response'),
        ]
        
        passed = 0
        failed = 0
        
        for event_name, request_data, response_event in tests:
            success = self.test_endpoint(event_name, request_data, response_event)
            if success:
                passed += 1
            else:
                failed += 1
        
        print(f"\n📋 Test Results:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        # Disconnect
        self.sio.disconnect()
        
        return failed == 0

def main():
    """Main test function"""
    print("🧪 Socket.IO API Test Suite")
    print("=" * 50)
    
    tester = SocketAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Socket.IO API is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the server logs.")
        return 1

if __name__ == "__main__":
    exit(main()) 