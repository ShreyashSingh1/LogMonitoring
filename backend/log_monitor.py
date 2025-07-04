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
            print(f"🔄 File modified: {event.src_path}")  # Debug line
            # Only process if initial read is complete
            if self.initial_read_complete.get(event.src_path, False):
                print(f"📖 Reading new lines from: {event.src_path}")  # Debug line
                self.read_new_lines(event.src_path)
            else:
                print(f"⏳ Initial read not complete for: {event.src_path}")  # Debug line
    
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
                print(f"Log file rotated: {os.path.basename(file_path)}")
            
            # If no new content, return early
            if current_size == last_position:
                return
            
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
                
                # Update position using f.tell() for consistency
                new_position = f.tell()
                self.file_positions[file_path] = new_position
                
        except Exception as e:
            print(f"Error reading file {os.path.basename(file_path)}: {e}")
            import traceback
            traceback.print_exc()

class LogMonitor:
    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.observer = Observer()
        self.handler = LogFileHandler(log_queue)
        self.is_running = False
        
        # Paths to monitor
        self.node_logs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'node_logs')
        self.python_logs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'python_logs')
        
        # Create log directories if they don't exist
        os.makedirs(self.node_logs_path, exist_ok=True)
        os.makedirs(self.python_logs_path, exist_ok=True)
        print("Log directories initialized")
    
    def start(self):
        """Start monitoring log directories"""
        if self.is_running:
            print("Log monitor is already running")
            return
            
        try:
            print("Starting log monitor...")
            
            # First read existing files
            self.read_existing_files()
            
            # Then start monitoring for changes
            self.observer.schedule(self.handler, self.node_logs_path, recursive=True)
            self.observer.schedule(self.handler, self.python_logs_path, recursive=True)
            
            # Start observer
            self.observer.start()
            self.is_running = True
            print("Log monitoring started successfully")
            
        except Exception as e:
            print(f"Error starting log monitor: {e}")
            self.is_running = False
            raise
    
    def stop(self):
        """Stop monitoring"""
        if not self.is_running:
            return
            
        try:
            print("Stopping log monitor...")
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            print("Log monitor stopped successfully")
        except Exception as e:
            print(f"Error stopping log monitor: {e}")
            raise
    
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
                    
                    # Set file position using f.tell() for consistency with read_new_lines
                    file_position = f.tell()
                    self.handler.file_positions[file_path] = file_position
                    self.handler.initial_read_complete[file_path] = True
                    
            except Exception as e:
                print(f"Error reading existing file {os.path.basename(file_path)}: {e}")
                import traceback
                traceback.print_exc()
        
        print("Reading existing log files...")
        
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
        
        print("Finished reading existing log files") 