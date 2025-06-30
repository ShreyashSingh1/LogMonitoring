import re
import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd

@dataclass
class NodeLogEntry:
    timestamp: str
    level: str
    message: str
    user_id: Optional[str] = None
    action: Optional[str] = None
    email: Optional[str] = None
    token_count: Optional[str] = None
    error_type: Optional[str] = None
    log_type: str = "access"  # access or error
    source_file: str = ""

class NodeLogParser:
    def __init__(self):
        self.patterns = {
            # Basic log pattern: timestamp level: message
            'basic': re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+): (.+)$'),
            
            # User authentication patterns
            'user_auth': re.compile(r'User authenticated successfully: userId=(\d+)'),
            'login': re.compile(r'Login successful for user: ([^,]+), user_id: (\d+)'),
            'tokens': re.compile(r'Fetched tokens for user_id=(\d+): (\d+)'),
            'token_update': re.compile(r'Tokens (?:updated|deducted) for user_id=(\d+)\. New total: (\d+)'),
            
            # Error patterns  
            'jwt_error': re.compile(r'JWT specific error: (\w+) - (.+)'),
            'login_failed': re.compile(r'Login failed: (.+) for email: ([^,\s]+)'),
            'payment_error': re.compile(r'Error sending payment failure email: (.+)'),
            
            # Extension and other patterns
            'extension': re.compile(r'Extension install status updated: user_id=(\d+), installed=(\w+)'),
            'registration': re.compile(r'New user registered: ([^,]+), user_id: (\d+)')
        }
    
    def parse_line(self, line: str, source_file: str = "") -> Optional[NodeLogEntry]:
        """Parse a single log line into a structured NodeLogEntry"""
        line = line.strip()
        if not line:
            return None
            
        # Extract basic timestamp, level, message
        basic_match = self.patterns['basic'].match(line)
        if not basic_match:
            return None
            
        timestamp, level, message = basic_match.groups()
        
        # Determine log type based on level
        log_type = "error" if level.lower() in ['error', 'warn'] else "access"
        
        # Create base entry
        entry = NodeLogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            log_type=log_type,
            source_file=source_file
        )
        
        # Extract specific information based on message content
        self._extract_specific_info(entry, message)
        
        return entry
    
    def _extract_specific_info(self, entry: NodeLogEntry, message: str):
        """Extract specific information from the message"""
        
        # User authentication
        user_auth_match = self.patterns['user_auth'].search(message)
        if user_auth_match:
            entry.user_id = user_auth_match.group(1)
            entry.action = "user_authentication"
            return
            
        # Login successful
        login_match = self.patterns['login'].search(message)
        if login_match:
            entry.email = login_match.group(1)
            entry.user_id = login_match.group(2)
            entry.action = "login_success"
            return
            
        # Token operations
        tokens_match = self.patterns['tokens'].search(message)
        if tokens_match:
            entry.user_id = tokens_match.group(1)
            entry.token_count = tokens_match.group(2)
            entry.action = "token_fetch"
            return
            
        token_update_match = self.patterns['token_update'].search(message)
        if token_update_match:
            entry.user_id = token_update_match.group(1)
            entry.token_count = token_update_match.group(2)
            entry.action = "token_update"
            return
            
        # JWT Errors
        jwt_error_match = self.patterns['jwt_error'].search(message)
        if jwt_error_match:
            entry.error_type = jwt_error_match.group(1)
            entry.action = "jwt_error"
            return
            
        # Login failed
        login_failed_match = self.patterns['login_failed'].search(message)
        if login_failed_match:
            entry.action = "login_failed"
            entry.email = login_failed_match.group(2)
            return
            
        # Extension status
        extension_match = self.patterns['extension'].search(message)
        if extension_match:
            entry.user_id = extension_match.group(1)
            entry.action = "extension_status"
            return
            
        # New registration
        registration_match = self.patterns['registration'].search(message)
        if registration_match:
            entry.email = registration_match.group(1)
            entry.user_id = registration_match.group(2)
            entry.action = "user_registration"
            return
    
    def parse_file(self, file_path: str) -> List[NodeLogEntry]:
        """Parse an entire log file"""
        entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        entry = self.parse_line(line, os.path.basename(file_path))
                        if entry:
                            entries.append(entry)
                    except Exception as e:
                        print(f"Error parsing line {line_num} in {file_path}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            
        return entries
    
    def to_csv_format(self, entries: List[NodeLogEntry]) -> List[Dict]:
        """Convert log entries to CSV-ready format"""
        csv_data = []
        
        for entry in entries:
            csv_row = {
                'timestamp': entry.timestamp,
                'level': entry.level,
                'log_type': entry.log_type,
                'source_file': entry.source_file,
                'message': entry.message,
                'user_id': entry.user_id or '',
                'action': entry.action or '',
                'email': entry.email or '',
                'token_count': entry.token_count or '',
                'error_type': entry.error_type or '',
                'parsed_at': datetime.now().isoformat()
            }
            csv_data.append(csv_row)
            
        return csv_data
    
    def save_to_csv(self, entries: List[NodeLogEntry], output_file: str):
        """Save parsed entries to CSV file"""
        csv_data = self.to_csv_format(entries)
        
        if not csv_data:
            print("No data to save")
            return
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        fieldnames = [
            'timestamp', 'level', 'log_type', 'source_file', 'message',
            'user_id', 'action', 'email', 'token_count', 'error_type', 'parsed_at'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
            
        print(f"Saved {len(csv_data)} entries to {output_file}")
    
    def get_summary_stats(self, entries: List[NodeLogEntry]) -> Dict:
        """Generate summary statistics"""
        if not entries:
            return {}
            
        df = pd.DataFrame([asdict(entry) for entry in entries])
        
        stats = {
            'total_entries': len(entries),
            'log_types': df['log_type'].value_counts().to_dict(),
            'levels': df['level'].value_counts().to_dict(),
            'actions': df['action'].value_counts().to_dict(),
            'unique_users': df['user_id'].nunique(),
            'time_range': {
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max()
            }
        }
        
        return stats

# Example usage
if __name__ == "__main__":
    parser = NodeLogParser()
    
    # Parse access logs
    access_entries = parser.parse_file("../Logs/node_backend_logs/accessLogs/access-2025-27.log")
    print(f"Parsed {len(access_entries)} access log entries")
    
    # Parse error logs  
    error_entries = parser.parse_file("../Logs/node_backend_logs/errorLogs/error-2025-27.log")
    print(f"Parsed {len(error_entries)} error log entries")
    
    # Combine and save to CSV
    all_entries = access_entries + error_entries
    parser.save_to_csv(all_entries, "../parsed_logs/node_logs.csv")
    
    # Print summary statistics
    stats = parser.get_summary_stats(all_entries)
    print("\nSummary Statistics:")
    print(json.dumps(stats, indent=2, default=str)) 