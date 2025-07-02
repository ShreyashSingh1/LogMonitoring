import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.file_positions = {}
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if event.src_path.endswith('.log'):
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
            # Monitor node_logs directory and subdirectories
            if os.path.exists(self.node_logs_path):
                self.observer.schedule(self.handler, self.node_logs_path, recursive=True)
                print(f"Monitoring node logs: {self.node_logs_path}")
            
            # Monitor python_logs directory
            if os.path.exists(self.python_logs_path):
                self.observer.schedule(self.handler, self.python_logs_path, recursive=True)
                print(f"Monitoring python logs: {self.python_logs_path}")
            
            # Start observer
            self.observer.start()
            print("Log monitoring started successfully")
            
            # Read existing files on startup
            self.read_existing_files()
            
        except Exception as e:
            print(f"Error starting log monitor: {e}")
    
    def read_existing_files(self):
        """Read existing log files on startup"""
        def read_all_files():
            time.sleep(2)  # Give some time for system to initialize
            
            for root, dirs, files in os.walk(self.node_logs_path):
                for file in files:
                    if file.endswith('.log'):
                        file_path = os.path.join(root, file)
                        self.read_file_content(file_path, max_lines=50)  # Read last 50 lines
            
            for root, dirs, files in os.walk(self.python_logs_path):
                for file in files:
                    if file.endswith('.log'):
                        file_path = os.path.join(root, file)
                        self.read_file_content(file_path, max_lines=50)  # Read last 50 lines
        
        # Start in background thread
        thread = threading.Thread(target=read_all_files, daemon=True)
        thread.start()
    
    def read_file_content(self, file_path, max_lines=None):
        """Read content from a log file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # If max_lines specified, take only the last N lines
                if max_lines and len(lines) > max_lines:
                    lines = lines[-max_lines:]
                
                for line in lines:
                    line = line.strip()
                    if line:
                        log_entry = {
                            'file_path': file_path,
                            'content': line,
                            'timestamp': time.time()
                        }
                        self.log_queue.add_log(log_entry)
                
                # Update file position
                self.handler.file_positions[file_path] = f.tell()
                
        except Exception as e:
            print(f"Error reading existing file {file_path}: {e}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.observer.stop()
        self.observer.join() 