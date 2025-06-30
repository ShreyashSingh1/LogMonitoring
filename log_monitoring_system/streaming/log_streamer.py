import time
import os
import threading
import csv
from datetime import datetime
from typing import Dict, List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import queue
import json
from pathlib import Path

# Import our parsers
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ..parsers.node_parser import NodeLogParser
from ..parsers.python_parser import PythonLogParser

class LogFileHandler(FileSystemEventHandler):
    """Handles file system events for log files"""
    
    def __init__(self, streamer):
        self.streamer = streamer
        self.file_positions = {}  # Track file positions for tail functionality
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = event.src_path
        if self.streamer.should_monitor_file(file_path):
            self.streamer.process_file_changes(file_path)

class LogStreamer:
    """Real-time log streaming and processing system"""
    
    def __init__(self, config_file: str = "streaming_config.json"):
        self.config = self.load_config(config_file)
        self.node_parser = NodeLogParser()
        self.python_parser = PythonLogParser()
        
        # Threading components
        self.observer = Observer()
        self.event_queue = queue.Queue()
        self.is_running = False
        
        # File tracking
        self.file_positions = {}
        self.csv_files = {}
        
        # Initialize CSV files
        self.setup_csv_files()
    
    def load_config(self, config_file: str) -> Dict:
        """Load streaming configuration"""
        default_config = {
            "monitor_directories": [
                "Logs/node_backend_logs/accessLogs",
                "Logs/node_backend_logs/errorLogs", 
                "Logs/python_backend_logs"
            ],
            "output_directory": "parsed_logs/streaming",
            "csv_files": {
                "node_access": "node_access_stream.csv",
                "node_error": "node_error_stream.csv",
                "python_access": "python_access_stream.csv",
                "python_error": "python_error_stream.csv",
                "combined": "all_logs_stream.csv"
            },
            "file_patterns": {
                "node_access": ["access-*.log"],
                "node_error": ["error-*.log"],
                "python_access": ["velocity_access.log"],
                "python_error": ["velocity_error.log", "velocity_warning.log", "velocity_info.log"]
            },
            "poll_interval": 1.0,
            "max_batch_size": 100
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Error loading config file: {e}, using defaults")
        
        return default_config
    
    def setup_csv_files(self):
        """Initialize CSV output files with headers"""
        output_dir = self.config["output_directory"]
        os.makedirs(output_dir, exist_ok=True)
        
        # Define CSV headers for different log types
        headers = {
            "node": [
                'timestamp', 'level', 'log_type', 'source_file', 'message',
                'user_id', 'action', 'email', 'token_count', 'error_type', 'parsed_at'
            ],
            "python": [
                'timestamp', 'level', 'log_type', 'source_file', 'message',
                'ip_address', 'user_id', 'method', 'url', 'status_code', 
                'response_time', 'user_agent', 'logger_name', 'function_name',
                'filename', 'error_category', 'parsed_at'
            ]
        }
        
        # Combined headers (union of both)
        combined_headers = list(set(headers["node"] + headers["python"]))
        
        for csv_name, filename in self.config["csv_files"].items():
            file_path = os.path.join(output_dir, filename)
            
            # Determine headers based on file type
            if "node" in csv_name:
                file_headers = headers["node"]
            elif "python" in csv_name:
                file_headers = headers["python"]
            else:  # combined
                file_headers = combined_headers
            
            # Create file with headers if it doesn't exist
            if not os.path.exists(file_path):
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=file_headers)
                    writer.writeheader()
            
            self.csv_files[csv_name] = {
                'path': file_path,
                'headers': file_headers
            }
    
    def should_monitor_file(self, file_path: str) -> bool:
        """Check if a file should be monitored based on patterns"""
        filename = os.path.basename(file_path)
        
        for log_type, patterns in self.config["file_patterns"].items():
            for pattern in patterns:
                if self.match_pattern(filename, pattern):
                    return True
        return False
    
    def match_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcard)"""
        if '*' in pattern:
            prefix, suffix = pattern.split('*', 1)
            return filename.startswith(prefix) and filename.endswith(suffix)
        return filename == pattern
    
    def get_log_type(self, file_path: str) -> Optional[str]:
        """Determine log type based on file path and name"""
        filename = os.path.basename(file_path)
        file_path_lower = file_path.lower()
        
        # Node.js logs
        if 'node_backend_logs' in file_path_lower:
            if 'access' in file_path_lower:
                return 'node_access'
            elif 'error' in file_path_lower:
                return 'node_error'
        
        # Python logs
        elif 'python_backend_logs' in file_path_lower:
            if 'access' in filename:
                return 'python_access'
            else:  # error, warning, info logs
                return 'python_error'
        
        return None
    
    def process_file_changes(self, file_path: str):
        """Process changes in a monitored file"""
        log_type = self.get_log_type(file_path)
        if not log_type:
            return
        
        # Get file position for tailing
        current_position = self.file_positions.get(file_path, 0)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Seek to last known position
                f.seek(current_position)
                
                new_lines = []
                for line in f:
                    line = line.strip()
                    if line:
                        new_lines.append(line)
                
                # Update file position
                self.file_positions[file_path] = f.tell()
                
                if new_lines:
                    self.process_new_lines(new_lines, log_type, file_path)
                    
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    def process_new_lines(self, lines: List[str], log_type: str, file_path: str):
        """Process new log lines and append to CSV"""
        entries = []
        
        # Parse lines based on log type
        for line in lines:
            try:
                if log_type.startswith('node'):
                    entry = self.node_parser.parse_line(line, os.path.basename(file_path))
                    if entry:
                        csv_data = self.node_parser.to_csv_format([entry])[0]
                        entries.append(csv_data)
                        
                elif log_type.startswith('python'):
                    parser_log_type = 'access' if 'access' in log_type else 'error'
                    entry = self.python_parser.parse_line(line, parser_log_type, os.path.basename(file_path))
                    if entry:
                        csv_data = self.python_parser.to_csv_format([entry])[0]
                        entries.append(csv_data)
                        
            except Exception as e:
                print(f"Error parsing line from {file_path}: {e}")
                continue
        
        if entries:
            self.append_to_csv(entries, log_type)
            print(f"Processed {len(entries)} new entries from {file_path}")
    
    def append_to_csv(self, entries: List[Dict], log_type: str):
        """Append entries to appropriate CSV files"""
        # Append to specific log type CSV
        if log_type in self.csv_files:
            self._append_to_file(entries, log_type)
        
        # Also append to combined CSV
        if 'combined' in self.csv_files:
            self._append_to_file(entries, 'combined')
    
    def _append_to_file(self, entries: List[Dict], csv_name: str):
        """Append entries to a specific CSV file"""
        csv_info = self.csv_files[csv_name]
        file_path = csv_info['path']
        headers = csv_info['headers']
        
        try:
            with open(file_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                
                for entry in entries:
                    # Ensure all required fields are present
                    row = {}
                    for header in headers:
                        row[header] = entry.get(header, '')
                    writer.writerow(row)
                    
        except Exception as e:
            print(f"Error appending to {file_path}: {e}")
    
    def start_monitoring(self):
        """Start the real-time monitoring system"""
        if self.is_running:
            print("Streamer is already running")
            return
        
        self.is_running = True
        
        # Set up file system monitoring
        handler = LogFileHandler(self)
        
        for directory in self.config["monitor_directories"]:
            if os.path.exists(directory):
                self.observer.schedule(handler, directory, recursive=True)
                print(f"Monitoring directory: {directory}")
            else:
                print(f"Warning: Directory not found: {directory}")
        
        # Initialize file positions for existing files
        self.initialize_file_positions()
        
        # Start observer
        self.observer.start()
        print("Log streaming started. Press Ctrl+C to stop.")
        
        try:
            while self.is_running:
                time.sleep(self.config["poll_interval"])
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def initialize_file_positions(self):
        """Initialize file positions to end of existing files"""
        for directory in self.config["monitor_directories"]:
            if not os.path.exists(directory):
                continue
                
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self.should_monitor_file(file_path):
                        try:
                            # Set position to end of file for real-time monitoring
                            with open(file_path, 'r', encoding='utf-8') as f:
                                f.seek(0, 2)  # Seek to end
                                self.file_positions[file_path] = f.tell()
                                print(f"Initialized monitoring for: {file_path}")
                        except Exception as e:
                            print(f"Error initializing {file_path}: {e}")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.observer.stop()
        self.observer.join()
        print("Log streaming stopped")
    
    def process_existing_files(self):
        """Process all existing log files (for initial setup)"""
        print("Processing existing log files...")
        
        for directory in self.config["monitor_directories"]:
            if not os.path.exists(directory):
                continue
                
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self.should_monitor_file(file_path):
                        log_type = self.get_log_type(file_path)
                        if log_type:
                            print(f"Processing existing file: {file_path}")
                            
                            # Parse entire file
                            if log_type.startswith('node'):
                                entries = self.node_parser.parse_file(file_path)
                                csv_data = self.node_parser.to_csv_format(entries)
                            elif log_type.startswith('python'):
                                parser_log_type = 'access' if 'access' in log_type else 'error'
                                entries = self.python_parser.parse_file(file_path, parser_log_type)
                                csv_data = self.python_parser.to_csv_format(entries)
                            
                            if csv_data:
                                self.append_to_csv(csv_data, log_type)
                                print(f"Processed {len(csv_data)} entries from {file_path}")

# Example usage and configuration
def create_sample_config():
    """Create a sample configuration file"""
    config = {
        "monitor_directories": [
            "Logs/node_backend_logs/accessLogs",
            "Logs/node_backend_logs/errorLogs",
            "Logs/python_backend_logs"
        ],
        "output_directory": "parsed_logs/streaming",
        "csv_files": {
            "node_access": "node_access_stream.csv",
            "node_error": "node_error_stream.csv",
            "python_access": "python_access_stream.csv",
            "python_error": "python_error_stream.csv",
            "combined": "all_logs_stream.csv"
        },
        "file_patterns": {
            "node_access": ["access-*.log"],
            "node_error": ["error-*.log"],
            "python_access": ["velocity_access.log"],
            "python_error": ["velocity_error.log", "velocity_warning.log", "velocity_info.log"]
        },
        "poll_interval": 1.0,
        "max_batch_size": 100
    }
    
    with open("streaming_config.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Created streaming_config.json")

if __name__ == "__main__":
    # Create sample config if needed
    if not os.path.exists("streaming_config.json"):
        create_sample_config()
    
    # Start streaming
    streamer = LogStreamer()
    
    # Process existing files first (optional)
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--process-existing":
        streamer.process_existing_files()
    
    # Start real-time monitoring
    streamer.start_monitoring() 