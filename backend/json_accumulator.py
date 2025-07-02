import os
import json
from datetime import datetime
import threading

class JSONAccumulator:
    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(__file__), "unified_logs")
        os.makedirs(self.base_dir, exist_ok=True)
        self.lock = threading.Lock()
        self.current_week = self._get_current_week()
        self.cleanup_old_logs()
        
    def _get_current_week(self):
        """Returns current year and week number (e.g., '2025_W27')"""
        return datetime.now().strftime("%Y_W%V")
        
    def _get_file_path(self, log_type, week=None):
        """Get the file path for a specific log type and week"""
        if week is None:
            week = self.current_week
        return os.path.join(self.base_dir, f"unified_{log_type}_logs_{week}.json")
        
    def cleanup_old_logs(self):
        """Clean up existing log files in the unified_logs directory"""
        try:
            for filename in os.listdir(self.base_dir):
                file_path = os.path.join(self.base_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print("Cleaned up old unified logs")
        except Exception as e:
            print(f"Error cleaning up old logs: {e}")

    def _append_to_file(self, file_path, log_entry):
        """Append a log entry to a JSON file"""
        with self.lock:
            try:
                # Initialize logs list
                logs = []
                
                # Read existing logs if file exists
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                try:
                                    logs = json.loads(content)
                                except json.JSONDecodeError:
                                    print(f"Error parsing JSON in {file_path}, starting fresh")
                                    logs = []
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
                        logs = []
                
                # Append the new log entry
                logs.append(log_entry)
                
                # Write the entire logs list back to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2)
                    f.write('\n')  # Add single newline at end of file
                    
            except Exception as e:
                print(f"Error appending to {file_path}: {e}")
    
    def add_log(self, parsed_log):
        """Add a parsed log entry to appropriate unified files"""
        try:
            week = self._get_current_week()
            
            print(f"Adding log: source={parsed_log.get('source')}, log_type={parsed_log.get('log_type')}")
            
            # Add to type-specific file
            log_type = parsed_log.get("log_type", "")
            
            if log_type == "request":
                self._append_to_file(self._get_file_path("request", week), parsed_log)
                print(f"Added to request file")
            elif parsed_log.get("level") in ["error", "warn", "warning"]:
                self._append_to_file(self._get_file_path("error", week), parsed_log)
                print(f"Added to error file")
            elif parsed_log.get("level") == "info":
                self._append_to_file(self._get_file_path("info", week), parsed_log)
                print(f"Added to info file")
            
            # Add to all logs file
            self._append_to_file(self._get_file_path("all", week), parsed_log)
            print(f"Added to all logs file")
            
        except Exception as e:
            print(f"Error adding log: {e}")
    
    def get_logs(self, log_type="all", level=None, week=None):
        """Get logs with optional filtering"""
        try:
            if week is None:
                week = self.current_week
                
            file_path = self._get_file_path(log_type, week)
            
            if not os.path.exists(file_path):
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            if level:
                logs = [log for log in logs if log.get("level") == level]
                
            return logs
            
        except Exception as e:
            print(f"Error getting logs: {e}")
            return [] 