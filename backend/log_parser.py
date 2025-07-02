import json
import os
from datetime import datetime
import re

class LogParser:
    def __init__(self):
        pass
    
    def parse_log(self, log_entry):
        """Parse a log entry based on its source and format"""
        try:
            file_path = log_entry['file_path']
            content = json.loads(log_entry['content'])
            source = "node" if "node_logs" in file_path else "python"
            
            # Determine log type and parse accordingly
            if self._is_request_log(file_path, content):
                return self._parse_request_log(source, content, file_path)
            elif self._is_error_log(content):
                return self._parse_error_log(source, content, file_path)
            else:
                return self._parse_info_log(source, content, file_path)
                
        except Exception as e:
            print(f"Error parsing log entry: {e}")
            return None
    
    def _is_request_log(self, file_path, content):
        """Determine if this is a request log"""
        if "requestsLogs" in file_path:
            return True
        if "python_logs" in file_path and "access-" in file_path:
            return True
        return False
    
    def _is_error_log(self, content):
        """Determine if this is an error/warning log"""
        level = content.get("level", "").lower()
        return level in ["error", "warn", "warning"]
    
    def _parse_request_log(self, source, content, file_path):
        """Parse request logs from both Node and Python"""
        if source == "node":
            msg = content["message"]
            return {
                "source": source,
                "log_type": "request",
                "original_level": content["level"],
                "timestamp": content["timestamp"],
                "endpoint": msg["endpoint"],
                "ip": msg["ip"],
                "method": msg["method"],
                "status_code": msg["status_code"],
                "response_time": float(msg["response_time"].replace("ms", "")),
                "user_agent": msg.get("user_agent", "-"),
                "user_id": msg.get("user_id", "-"),
                "req_id": msg.get("req_id", "-"),
                "file_path": file_path
            }
        else:
            return {
                "source": source,
                "log_type": "request",
                "original_level": content["level"],
                "timestamp": content["timestamp"],
                "endpoint": content["path"],
                "ip": content.get("client_ip", "-"),
                "method": content["method"],
                "status_code": content["status_code"],
                "response_time": content.get("duration_ms", 0),
                "user_agent": content.get("user_agent", "-").strip('"'),
                "user_id": content.get("user_id", "-"),
                "req_id": content.get("request_id", "-"),
                "url": content.get("url", "-"),
                "file_path": file_path
            }
    
    def _parse_error_log(self, source, content, file_path):
        """Parse error and warning logs"""
        if source == "node":
            return {
                "source": source,
                "log_type": "error",
                "level": content["level"].lower(),
                "timestamp": content["timestamp"],
                "message": content["message"],
                "req_id": content.get("req_id", "-"),
                "ip": content.get("ip", "-"),
                "user_id": self._extract_user_id(content["message"]),
                "file_path": file_path,
                "function": "-",
                "filename": "-",
                "error_details": None
            }
        else:
            return {
                "source": source,
                "log_type": "error",
                "level": content["level"].lower(),
                "timestamp": content["timestamp"],
                "message": content["message"],
                "path": content.get("path", "-"),
                "function": content.get("function", "-"),
                "filename": content.get("filename", "-"),
                "req_id": content.get("request_id", "-"),
                "user_id": content.get("user_id", "-"),
                "ip": content.get("client_ip", "-"),
                "file_path": file_path,
                "error_details": self._extract_error_details(content["message"])
            }
    
    def _parse_info_log(self, source, content, file_path):
        """Parse info logs"""
        if source == "node":
            return {
                "source": source,
                "log_type": "info",
                "level": content["level"].lower(),
                "timestamp": content["timestamp"],
                "message": content["message"],
                "req_id": content.get("req_id", "-"),
                "ip": content.get("ip", "-"),
                "user_id": self._extract_user_id(content["message"]),
                "file_path": file_path,
                "function": "-",
                "filename": "-",
                "duration_ms": None
            }
        else:
            return {
                "source": source,
                "log_type": "info",
                "level": content["level"].lower(),
                "timestamp": content["timestamp"],
                "message": content["message"],
                "path": content.get("path", "-"),
                "function": content.get("function", "-"),
                "filename": content.get("filename", "-"),
                "status_code": content.get("status_code"),
                "duration_ms": content.get("duration_ms"),
                "user_id": content.get("user_id", "-"),
                "req_id": content.get("request_id", "-"),
                "ip": content.get("client_ip", "-"),
                "file_path": file_path
            }
    
    def _extract_user_id(self, message):
        """Extract user_id from message if present"""
        user_id_match = re.search(r'user_id[=:](\d+)', message)
        if user_id_match:
            return user_id_match.group(1)
        return "-"
    
    def _extract_error_details(self, message):
        """Extract structured error details from message if possible"""
        if "validation error" in message.lower():
            return {
                "type": "validation_error",
                "details": message
            }
        return None
    
    def parse_node_log(self, file_path, content, timestamp):
        """Parse Node.js log entries"""
        try:
            # Try to parse as JSON
            log_data = json.loads(content)
            
            # Determine log type from file path
            log_type = self.get_node_log_type(file_path)
            
            parsed = {
                'source': 'node',
                'log_type': log_type,
                'level': log_data.get('level', 'info'),
                'message': log_data.get('message', ''),
                'timestamp': log_data.get('timestamp', datetime.now().isoformat()),
                'file_path': file_path,
                'parsed_at': datetime.fromtimestamp(timestamp).isoformat(),
                'raw_content': content
            }
            
            # Add additional fields if present
            if 'userId' in log_data.get('message', ''):
                user_id_match = re.search(r'userId[=:](\d+)', log_data['message'])
                if user_id_match:
                    parsed['user_id'] = user_id_match.group(1)
            
            return parsed
            
        except json.JSONDecodeError:
            # If not JSON, treat as plain text
            return self.parse_generic_log(file_path, content, timestamp)
    
    def parse_python_log(self, file_path, content, timestamp):
        """Parse Python log entries"""
        try:
            # Try to parse as JSON
            log_data = json.loads(content)
            
            # Determine log type from file name
            log_type = self.get_python_log_type(file_path)
            
            parsed = {
                'source': 'python',
                'log_type': log_type,
                'level': log_data.get('level', 'info'),
                'message': log_data.get('message', ''),
                'timestamp': log_data.get('timestamp', datetime.now().isoformat()),
                'file_path': file_path,
                'parsed_at': datetime.fromtimestamp(timestamp).isoformat(),
                'raw_content': content,
                'name': log_data.get('name', ''),
                'function': log_data.get('function', ''),
                'filename': log_data.get('filename', '')
            }
            
            # Add HTTP-specific fields if present
            if 'method' in log_data:
                parsed.update({
                    'method': log_data.get('method'),
                    'url': log_data.get('url'),
                    'status_code': log_data.get('status_code'),
                    'client_ip': log_data.get('client_ip'),
                    'user_agent': log_data.get('user_agent'),
                    'duration_ms': log_data.get('duration_ms'),
                    'request_id': log_data.get('request_id')
                })
            
            # Add error-specific fields if present
            if 'exception' in log_data:
                exception = log_data['exception']
                parsed.update({
                    'exception_type': exception.get('type'),
                    'exception_message': exception.get('message'),
                    'traceback': exception.get('traceback')
                })
            
            return parsed
            
        except json.JSONDecodeError:
            # If not JSON, treat as plain text
            return self.parse_generic_log(file_path, content, timestamp)
    
    def parse_generic_log(self, file_path, content, timestamp):
        """Parse generic log entries that aren't JSON"""
        # Try to extract timestamp from content
        timestamp_pattern = r'(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})'
        timestamp_match = re.search(timestamp_pattern, content)
        
        # Try to extract log level
        level_pattern = r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE)\b'
        level_match = re.search(level_pattern, content, re.IGNORECASE)
        
        return {
            'source': 'generic',
            'log_type': 'unknown',
            'level': level_match.group(1).lower() if level_match else 'info',
            'message': content,
            'timestamp': timestamp_match.group(1) if timestamp_match else datetime.now().isoformat(),
            'file_path': file_path,
            'parsed_at': datetime.fromtimestamp(timestamp).isoformat(),
            'raw_content': content
        }
    
    def get_node_log_type(self, file_path):
        """Determine Node.js log type from file path"""
        if 'accessLogs' in file_path:
            return 'access'
        elif 'errorLogs' in file_path:
            return 'error'
        elif 'requestsLogs' in file_path:
            return 'requests'
        else:
            return 'general'
    
    def get_python_log_type(self, file_path):
        """Determine Python log type from file name"""
        filename = os.path.basename(file_path)
        if 'access' in filename:
            return 'access'
        elif 'error' in filename:
            return 'error'
        elif 'info' in filename:
            return 'info'
        elif 'warning' in filename:
            return 'warning'
        else:
            return 'general'
    
    def is_error_log(self, parsed_log):
        """Check if a parsed log is an error"""
        level = parsed_log.get('level', '').lower()
        return level in ['error', 'warn', 'warning', 'fatal'] 