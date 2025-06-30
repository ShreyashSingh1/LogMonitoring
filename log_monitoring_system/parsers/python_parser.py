import re
import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import pandas as pd
from urllib.parse import urlparse

@dataclass 
class PythonLogEntry:
    timestamp: str
    level: str
    message: str
    log_type: str  # access or error
    source_file: str = ""
    
    # Access log specific fields
    ip_address: Optional[str] = None
    user_id: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    http_version: Optional[str] = None
    status_code: Optional[str] = None
    response_size: Optional[str] = None
    referer: Optional[str] = None
    user_agent: Optional[str] = None
    response_time: Optional[str] = None
    
    # Error log specific fields (JSON)
    logger_name: Optional[str] = None
    function_name: Optional[str] = None
    filename: Optional[str] = None
    file_path: Optional[str] = None
    stack_info: Optional[str] = None
    error_category: Optional[str] = None

class PythonLogParser:
    def __init__(self):
        # Apache-style access log pattern
        # Format: IP - user_id [timestamp] "METHOD URL HTTP/version" status_code response_size "referer" "user_agent" response_time
        self.access_pattern = re.compile(
            r'^(\S+) - (\S+) \[([^\]]+)\] "(\w+) ([^"]+) HTTP/([^"]+)" (\d+) (\d+) "([^"]*)" "([^"]*)" ([\d.]+) ms$'
        )
        
        # Error categories for classification
        self.error_categories = {
            'wikipedia': 'API_ERROR',
            'rate_limit': 'RATE_LIMIT', 
            'validation': 'VALIDATION_ERROR',
            'streaming': 'STREAMING_ERROR',
            'authentication': 'AUTH_ERROR',
            'database': 'DB_ERROR',
            'network': 'NETWORK_ERROR'
        }
    
    def parse_access_log_line(self, line: str, source_file: str = "") -> Optional[PythonLogEntry]:
        """Parse Apache-style access log line"""
        line = line.strip()
        if not line:
            return None
            
        match = self.access_pattern.match(line)
        if not match:
            return None
            
        groups = match.groups()
        
        # Parse timestamp to standard format
        timestamp_str = groups[2]  # 30/Jun/2025:14:28:25
        try:
            # Convert from Apache format to ISO format
            dt = datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S")
            formatted_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            formatted_timestamp = timestamp_str
        
        # Determine user - could be user_id, 'anonymous', or 'testclient'
        user_identifier = groups[1]
        user_id = user_identifier if user_identifier.isdigit() else None
        
        entry = PythonLogEntry(
            timestamp=formatted_timestamp,
            level="INFO",  # Access logs are typically INFO level
            message=f"{groups[3]} {groups[4]} - {groups[6]}",
            log_type="access",
            source_file=source_file,
            ip_address=groups[0],
            user_id=user_id,
            method=groups[3],
            url=groups[4],
            http_version=groups[5],
            status_code=groups[6],
            response_size=groups[7],
            referer=groups[8] if groups[8] != '-' else None,
            user_agent=groups[9],
            response_time=groups[10]
        )
        
        return entry
    
    def parse_error_log_line(self, line: str, source_file: str = "") -> Optional[PythonLogEntry]:
        """Parse JSON-formatted error log line"""
        line = line.strip()
        if not line:
            return None
            
        try:
            log_data = json.loads(line)
        except json.JSONDecodeError:
            # If not JSON, treat as plain text error
            return PythonLogEntry(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                level="ERROR",
                message=line,
                log_type="error", 
                source_file=source_file
            )
        
        # Extract timestamp
        timestamp = log_data.get('timestamp', '')
        if timestamp:
            try:
                # Convert ISO format to our standard format
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                formatted_timestamp = timestamp
        else:
            formatted_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Categorize error
        message = log_data.get('message', '')
        error_category = self._categorize_error(message)
        
        # Extract user_id if present in the log data
        user_id = None
        if 'user_id' in log_data:
            user_id = str(log_data['user_id'])
        
        entry = PythonLogEntry(
            timestamp=formatted_timestamp,
            level=log_data.get('level', 'ERROR'),
            message=message,
            log_type="error",
            source_file=source_file,
            logger_name=log_data.get('name'),
            function_name=log_data.get('function'),
            filename=log_data.get('filename'),
            file_path=log_data.get('path'),
            stack_info=log_data.get('stack_info'),
            error_category=error_category,
            user_id=user_id
        )
        
        return entry
    
    def _categorize_error(self, message: str) -> str:
        """Categorize error based on message content"""
        message_lower = message.lower()
        
        for keyword, category in self.error_categories.items():
            if keyword in message_lower:
                return category
                
        return 'GENERAL_ERROR'
    
    def parse_line(self, line: str, log_type: str, source_file: str = "") -> Optional[PythonLogEntry]:
        """Parse a single log line based on the log type"""
        if log_type == "access":
            return self.parse_access_log_line(line, source_file)
        elif log_type == "error":
            return self.parse_error_log_line(line, source_file)
        else:
            return None
    
    def parse_file(self, file_path: str, log_type: str) -> List[PythonLogEntry]:
        """Parse an entire log file"""
        entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        entry = self.parse_line(line, log_type, os.path.basename(file_path))
                        if entry:
                            entries.append(entry)
                    except Exception as e:
                        print(f"Error parsing line {line_num} in {file_path}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            
        return entries
    
    def to_csv_format(self, entries: List[PythonLogEntry]) -> List[Dict]:
        """Convert log entries to CSV-ready format"""
        csv_data = []
        
        for entry in entries:
            csv_row = {
                'timestamp': entry.timestamp,
                'level': entry.level,
                'log_type': entry.log_type,
                'source_file': entry.source_file,
                'message': entry.message,
                'ip_address': entry.ip_address or '',
                'user_id': entry.user_id or '',
                'method': entry.method or '',
                'url': entry.url or '',
                'status_code': entry.status_code or '',
                'response_time': entry.response_time or '',
                'user_agent': entry.user_agent or '',
                'logger_name': entry.logger_name or '',
                'function_name': entry.function_name or '',
                'filename': entry.filename or '',
                'error_category': entry.error_category or '',
                'parsed_at': datetime.now().isoformat()
            }
            csv_data.append(csv_row)
            
        return csv_data
    
    def save_to_csv(self, entries: List[PythonLogEntry], output_file: str):
        """Save parsed entries to CSV file"""
        csv_data = self.to_csv_format(entries)
        
        if not csv_data:
            print("No data to save")
            return
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        fieldnames = [
            'timestamp', 'level', 'log_type', 'source_file', 'message',
            'ip_address', 'user_id', 'method', 'url', 'status_code', 
            'response_time', 'user_agent', 'logger_name', 'function_name',
            'filename', 'error_category', 'parsed_at'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
            
        print(f"Saved {len(csv_data)} entries to {output_file}")
    
    def get_summary_stats(self, entries: List[PythonLogEntry]) -> Dict:
        """Generate summary statistics"""
        if not entries:
            return {}
            
        df = pd.DataFrame([asdict(entry) for entry in entries])
        
        stats = {
            'total_entries': len(entries),
            'log_types': df['log_type'].value_counts().to_dict(),
            'levels': df['level'].value_counts().to_dict(),
            'status_codes': df['status_code'].value_counts().to_dict(),
            'error_categories': df['error_category'].value_counts().to_dict(),
            'unique_users': df['user_id'].nunique(),
            'unique_ips': df['ip_address'].nunique(),
            'time_range': {
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max()
            }
        }
        
        return stats

# Example usage
if __name__ == "__main__":
    parser = PythonLogParser()
    
    # Parse access logs
    access_entries = parser.parse_file("../Logs/python_backend_logs/velocity_access.log", "access")
    print(f"Parsed {len(access_entries)} access log entries")
    
    # Parse error logs
    error_entries = parser.parse_file("../Logs/python_backend_logs/velocity_error.log", "error")
    print(f"Parsed {len(error_entries)} error log entries")
    
    # Combine and save to CSV
    all_entries = access_entries + error_entries
    parser.save_to_csv(all_entries, "../parsed_logs/python_logs.csv")
    
    # Print summary statistics
    stats = parser.get_summary_stats(all_entries)
    print("\nSummary Statistics:")
    print(json.dumps(stats, indent=2, default=str)) 