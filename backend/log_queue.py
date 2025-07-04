import queue
import threading
import os
from datetime import datetime, timedelta
from log_parser import LogParser
from json_accumulator import JSONAccumulator

class LogQueue:
    def __init__(self, socketio, json_accumulator=None):
        self.queue = queue.Queue()
        self.socketio = socketio
        self.json_accumulator = json_accumulator or JSONAccumulator()
        self.log_parser = LogParser()
        self.processing_thread = None
        self.is_running = False
        self.batch_size = 10  # Process logs in small batches for efficiency
        self.batch_timeout = 0.1  # Seconds to wait for batch completion
        
    def start(self):
        """Start the log processing thread"""
        if not self.is_running:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._process_logs, daemon=True)
            self.processing_thread.start()
            print("📋 Log Queue: Processing thread started")
    
    def stop(self):
        """Stop the log processing thread"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join()
            print("📋 Log Queue: Processing thread stopped")
    
    def add_log(self, log_entry):
        """Add a log entry to the queue"""
        try:
            self.queue.put(log_entry)
            print(f"📥 Log Queue: Added new log entry from {os.path.basename(log_entry.get('file_path', 'unknown'))} (queue size: {self.queue.qsize()})")
        except Exception as e:
            print(f"❌ Log Queue: Error adding log entry: {e}")
    
    def _process_logs(self):
        """Process logs from the queue in batches"""
        while self.is_running:
            try:
                # Get a batch of logs
                batch = []
                start_time = datetime.now()
                
                # Try to fill the batch
                while len(batch) < self.batch_size:
                    try:
                        # Get a log entry with timeout
                        log_entry = self.queue.get(timeout=self.batch_timeout)
                        batch.append(log_entry)
                        self.queue.task_done()
                    except queue.Empty:
                        break  # No more logs available
                    
                    # Check if we've exceeded the batch timeout
                    if (datetime.now() - start_time).total_seconds() > self.batch_timeout:
                        break
                
                if not batch:
                    continue  # No logs to process
                
                # Process the batch
                processed_count = 0
                for log_entry in batch:
                    try:
                        parsed_log = self.log_parser.parse_log(log_entry)
                        if parsed_log:
                            # Add to unified JSON files
                            self.json_accumulator.add_log(parsed_log)
                            # Emit to WebSocket
                            self._emit_log(parsed_log)
                            processed_count += 1
                        else:
                            print(f"⚠️ Log Queue: Failed to parse log from {os.path.basename(log_entry.get('file_path', 'unknown'))}")
                    except Exception as e:
                        print(f"❌ Log Queue: Error processing log: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                print(f"📤 Log Queue: Processed batch of {processed_count}/{len(batch)} logs successfully")
                
            except Exception as e:
                print(f"❌ Log Queue: Error in processing thread: {e}")
                import traceback
                traceback.print_exc()
    
    def _emit_log(self, log):
        """Emit log to appropriate WebSocket channels with error handling"""
        try:
            log_type = log.get("log_type", "info")
            level = log.get("level", "info")
            source = log.get("source", "unknown")
            
            print(f"📡 Socket.IO: Emitting log (type={log_type}, level={level}, source={source})")
            
            # Emit to general channel
            self.socketio.emit('new_log', log)
            print(f"✅ Socket.IO: Emitted to new_log channel")
            
            # Emit to type-specific channel
            event_name = f'new_{log_type}_log'
            self.socketio.emit(event_name, log)
            print(f"✅ Socket.IO: Emitted to {event_name} channel")
            
            # Special handling for errors and warnings
            if level.lower() in ["error", "warning", "warn"]:
                self.socketio.emit('error_detected', log)
                print(f"⚠️ Socket.IO: Emitted error_detected for {level} log")
            
            # Calculate and emit stats update
            week = self.json_accumulator.current_week
            all_logs = []
            for log_type in ['info', 'error', 'request']:
                logs = self.json_accumulator.get_logs(log_type, None, week)
                all_logs.extend(logs)
            
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
                }
            }
            
            self.socketio.emit('stats_update', stats)
            print(f"📊 Socket.IO: Emitted stats update")
            
            print(f"✅ Socket.IO: Successfully emitted log events for {log_type}")
            
        except Exception as e:
            print(f"❌ Socket.IO: Error emitting log: {e}")
            import traceback
            traceback.print_exc() 