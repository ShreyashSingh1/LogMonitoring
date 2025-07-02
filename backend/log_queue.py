import queue
import threading
from datetime import datetime
from log_parser import LogParser
from json_accumulator import JSONAccumulator

class LogQueue:
    def __init__(self, socketio):
        self.queue = queue.Queue()
        self.socketio = socketio
        self.json_accumulator = JSONAccumulator()
        self.log_parser = LogParser()
        self.processing_thread = None
        self.is_running = False
        
    def start(self):
        """Start the log processing thread"""
        if not self.is_running:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._process_logs, daemon=True)
            self.processing_thread.start()
    
    def stop(self):
        """Stop the log processing thread"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join()
    
    def add_log(self, log_entry):
        """Add a log entry to the queue"""
        self.queue.put(log_entry)
    
    def _process_logs(self):
        """Process logs from the queue"""
        while self.is_running:
            try:
                log_entry = self.queue.get(timeout=1)
                parsed_log = self.log_parser.parse_log(log_entry)
                
                if parsed_log:
                    # Add to unified JSON files
                    self.json_accumulator.add_log(parsed_log)
                    
                    # Emit to WebSocket
                    self._emit_log(parsed_log)
                
                self.queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing log: {e}")
    
    def _emit_log(self, log):
        """Emit log to appropriate WebSocket channels"""
        try:
            # Emit to type-specific channel
            self.socketio.emit(f'new_{log["log_type"]}_log', log)
            
            # Emit to all logs channel
            self.socketio.emit('new_log', log)
            
            # Emit to error channel if error/warning
            if log["level"] in ["error", "warning"]:
                self.socketio.emit('error_detected', log)
                
        except Exception as e:
            print(f"Error emitting log: {e}") 