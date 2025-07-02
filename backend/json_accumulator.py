import os
import json
from datetime import datetime
import threading
import glob
import hashlib

class JSONAccumulator:
    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(__file__), "unified_logs")
        os.makedirs(self.base_dir, exist_ok=True)
        self.lock = threading.Lock()
        self.current_week = self._get_current_week()
        self.processed_logs = set()  # Store hashes of processed logs
        
    def _get_current_week(self):
        """Returns current year and week number (e.g., '2025_W27')"""
        return datetime.now().strftime("%Y_W%V")
        
    def _get_file_path(self, log_type, week=None):
        """Get the file path for a specific log type and week"""
        if week is None:
            week = self.current_week
        if log_type == "all":
            return os.path.join(self.base_dir, f"unified_*_logs_{week}.jsonl")
        return os.path.join(self.base_dir, f"unified_{log_type}_logs_{week}.jsonl")
    
    def _generate_log_hash(self, log_entry):
        """Generate a unique hash for a log entry"""
        # Create a string with key fields that make a log unique
        unique_fields = [
            str(log_entry.get('timestamp', '')),
            str(log_entry.get('source', '')),
            str(log_entry.get('message', '')),
            str(log_entry.get('level', '')),
            str(log_entry.get('file_path', ''))
        ]
        unique_string = '|'.join(unique_fields)
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def _append_to_file(self, file_path, log_entry):
        """Append a log entry to a JSONL file if not already processed"""
        with self.lock:
            try:
                # Generate hash for the log entry
                log_hash = self._generate_log_hash(log_entry)
                
                # Skip if already processed
                if log_hash in self.processed_logs:
                    print(f"Skipping duplicate log: {log_entry.get('message', '')[:50]}...")
                    return
                
                # Ensure the directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Append the log and store its hash
                with open(file_path, 'a', encoding='utf-8') as f:
                    json.dump(log_entry, f, separators=(',', ':'))
                    f.write('\n')
                
                # Mark as processed
                self.processed_logs.add(log_hash)
                    
            except Exception as e:
                print(f"Error appending to {file_path}: {e}")
    
    def add_log(self, parsed_log):
        """Add a parsed log entry to appropriate unified files based on the new categorization"""
        try:
            if not parsed_log:
                return
                
            week = self._get_current_week()
            source = parsed_log.get('source')
            level = parsed_log.get('level', '').lower()
            file_path = parsed_log.get('file_path', '')
            
            print(f"Adding log: source={source}, level={level}, file_path={file_path}")
            
            # Add timestamp if not present
            if 'timestamp' not in parsed_log:
                parsed_log['timestamp'] = datetime.now().isoformat()
            
            # UNIFIED REQUEST LOGS: Python access + Node.js requests
            if ((source == "python" and "access-" in file_path) or 
                (source == "node" and "requestsLogs" in file_path)):
                self._append_to_file(self._get_file_path("request", week), parsed_log)
                print(f"Added to unified REQUEST file")
            
            # UNIFIED ERROR LOGS: Python error + Python warning + Node.js error  
            elif ((source == "python" and ("error-" in file_path or "warning-" in file_path)) or
                  (source == "node" and "errorLogs" in file_path)):
                self._append_to_file(self._get_file_path("error", week), parsed_log)
                print(f"Added to unified ERROR file")
            
            # UNIFIED INFO LOGS: Python info + Node.js access
            elif ((source == "python" and "info-" in file_path) or
                  (source == "node" and "accessLogs" in file_path)):
                self._append_to_file(self._get_file_path("info", week), parsed_log)
                print(f"Added to unified INFO file")
            
            else:
                print(f"Log not categorized: source={source}, file_path={file_path}")
            
        except Exception as e:
            print(f"Error adding log: {e}")
    
    def _load_existing_log_hashes(self):
        """Load hashes of existing logs to prevent duplicates"""
        try:
            # Get all log files
            all_files = glob.glob(os.path.join(self.base_dir, "unified_*_logs_*.jsonl"))
            
            for file_path in all_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    log_entry = json.loads(line)
                                    log_hash = self._generate_log_hash(log_entry)
                                    self.processed_logs.add(log_hash)
                                except json.JSONDecodeError:
                                    continue
            
            print(f"Loaded {len(self.processed_logs)} existing log hashes")
            
        except Exception as e:
            print(f"Error loading existing log hashes: {e}")
    
    def get_logs(self, log_type="all", level=None, week=None):
        """Get logs with optional filtering"""
        try:
            if week is None:
                week = self.current_week
            
            all_logs = []
            
            # Get file pattern based on log type
            file_pattern = self._get_file_path(log_type, week)
            
            # Get all matching files
            matching_files = glob.glob(file_pattern)
            
            # Read logs from all matching files
            for file_path in matching_files:
                if not os.path.exists(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    log_entry = json.loads(line)
                                    # Apply level filter if specified
                                    if level and log_entry.get("level", "").lower() != level.lower():
                                        continue
                                    all_logs.append(log_entry)
                                except json.JSONDecodeError:
                                    print(f"Skipping invalid JSON line in {file_path}: {line}")
                                    continue
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
                    continue
            
            return all_logs
            
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []
            
    def get_available_weeks(self):
        """Get list of available log weeks"""
        try:
            weeks = set()
            for file_path in glob.glob(os.path.join(self.base_dir, "unified_*_logs_*.jsonl")):
                filename = os.path.basename(file_path)
                week = filename.split("_")[-1].replace(".jsonl", "")
                weeks.add(week)
            return sorted(list(weeks))
        except Exception as e:
            print(f"Error getting available weeks: {e}")
            return [] 