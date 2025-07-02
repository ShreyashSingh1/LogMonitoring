import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.file_positions = {}
        self.initial_read_complete = {}  # Track which files have been read initially
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if event.src_path.endswith('.log'):
            # Only process if initial read is complete
            if self.initial_read_complete.get(event.src_path, False):
                self.read_new_lines(event.src_path)
    
    def read_new_lines(self, file_path):
        """Read only new lines from the modified file"""
        try:
            # Get current file size
            current_size = os.path.getsize(file_path)
            
            # Get last known position
            last_position = self.file_positions.get(file_path, 0)
            
            # If file is smaller, it might have been rotated
            if current_size < last_position:
                last_position = 0
            
            # Read new content
            with open(file_path, 'r', encoding='utf-8') as f:
                f.seek(last_position)
                new_lines = f.readlines()
                
                for line in new_lines:
                    line = line.strip()
                    if line:
                        log_entry = {
                            'file_path': file_path,
                            'content': line,
                            'timestamp': time.time()
                        }
                        self.log_queue.add_log(log_entry)
                
                # Update position
                self.file_positions[file_path] = f.tell()
                
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

class LogMonitor:
    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.observer = Observer()
        self.handler = LogFileHandler(log_queue)
        
        # Paths to monitor
        self.node_logs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'node_logs')
        self.python_logs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'python_logs')
        
    def start_monitoring(self):
        """Start monitoring log directories"""
        try:
            # First read existing files
            self.read_existing_files()
            
            # Then start monitoring for changes
            if os.path.exists(self.node_logs_path):
                self.observer.schedule(self.handler, self.node_logs_path, recursive=True)
                print(f"Monitoring node logs: {self.node_logs_path}")
            
            if os.path.exists(self.python_logs_path):
                self.observer.schedule(self.handler, self.python_logs_path, recursive=True)
                print(f"Monitoring python logs: {self.python_logs_path}")
            
            # Start observer
            self.observer.start()
            print("Log monitoring started successfully")
            
        except Exception as e:
            print(f"Error starting log monitor: {e}")
    
    def read_existing_files(self):
        """Read existing log files on startup"""
        def process_file(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    for line in lines:
                        line = line.strip()
                        if line:
                            log_entry = {
                                'file_path': file_path,
                                'content': line,
                                'timestamp': time.time()
                            }
                            self.log_queue.add_log(log_entry)
                    
                    # Set file position and mark as read
                    self.handler.file_positions[file_path] = os.path.getsize(file_path)
                    self.handler.initial_read_complete[file_path] = True
                    print(f"Initial read complete for {file_path}")
                    
            except Exception as e:
                print(f"Error reading existing file {file_path}: {e}")
        
        # Process node logs
        if os.path.exists(self.node_logs_path):
            for root, dirs, files in os.walk(self.node_logs_path):
                for file in files:
                    if file.endswith('.log'):
                        process_file(os.path.join(root, file))
        
        # Process python logs
        if os.path.exists(self.python_logs_path):
            for root, dirs, files in os.walk(self.python_logs_path):
                for file in files:
                    if file.endswith('.log'):
                        process_file(os.path.join(root, file))
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.observer.stop()
        self.observer.join() 