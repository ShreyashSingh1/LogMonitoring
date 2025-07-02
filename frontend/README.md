# Log Monitoring System

A comprehensive real-time log monitoring system with dashboard, built with Python Flask backend and React frontend.

## 🚀 Features

- **Real-time Log Monitoring**: Continuously watches log files for new entries using watchdog
- **WebSocket Communication**: Real-time updates to dashboard via Socket.IO
- **CSV Export**: Automatically converts logs to CSV format with queue-based processing
- **Interactive Dashboard**: Beautiful React-based dashboard with Material-UI components
- **Advanced Filtering**: Search, filter by level, source, and time range
- **Error Detection**: Automatic error highlighting and notifications
- **Analytics**: Charts, statistics, and trends visualization
- **Multiple Log Sources**: Supports both Node.js and Python log formats

## 📁 Project Structure

```
LogSystem/
├── backend/                    # Python Flask backend
│   ├── app.py                 # Main Flask application
│   ├── log_monitor.py         # File monitoring with watchdog
│   ├── log_parser.py          # Log parsing for different formats
│   ├── csv_manager.py         # CSV conversion and database management
│   └── requirements.txt       # Python dependencies
├── template/                   # React dashboard template
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── Dashboard.jsx  # Main dashboard
│   │   │   ├── LogViewer.jsx  # Detailed log viewer
│   │   │   ├── Analytics.jsx  # Analytics and charts
│   │   │   ├── Settings.jsx   # Configuration settings
│   │   │   └── Navbar.jsx     # Navigation sidebar
│   │   ├── contexts/          # React contexts
│   │   │   └── SocketContext.jsx # Socket.IO integration
│   │   ├── services/          # API services
│   │   │   └── api.js         # HTTP API client
│   │   ├── App.jsx            # Main App component
│   │   └── main.jsx           # React entry point
│   ├── package.json           # Frontend dependencies
│   └── vite.config.js         # Vite configuration
├── node_logs/                  # Node.js log files
│   ├── accessLogs/            # Access logs
│   ├── errorLogs/             # Error logs
│   └── requestsLogs/          # Request logs
├── python_logs/               # Python log files
│   ├── access-YYYY-MM-DD.log  # Python access logs
│   ├── error-YYYY-MM-DD.log   # Python error logs
│   ├── info-YYYY-MM-DD.log    # Python info logs
│   └── warning-YYYY-MM-DD.log # Python warning logs
└── README.md                  # This file
```

## 🛠️ Installation & Setup

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend server:**
   ```bash
   python app.py
   ```
   The backend will start on `http://localhost:5000`

### Frontend Setup

1. **Navigate to template directory:**
   ```bash
   cd template
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   The frontend will start on `http://localhost:3000`

## 🔧 Configuration

### Log File Monitoring

The system automatically monitors:
- `node_logs/` directory (recursive)
- `python_logs/` directory (recursive)

### Supported Log Formats

#### Node.js Logs (JSON format):
```json
{
  "level": "info",
  "message": "User authenticated successfully: userId=933",
  "timestamp": "2025-07-01T11:42:18.563Z"
}
```

#### Python Logs (JSON format):
```json
{
  "timestamp": "2025-07-01T15:48:33.703460",
  "level": "ACCESS",
  "name": "http.access",
  "message": "HTTP GET http://0.0.0.0:8000/remix-suggestion/853 - 200",
  "method": "GET",
  "status_code": 200,
  "client_ip": "127.0.0.1"
}
```

## 📊 Dashboard Features

### Main Dashboard
- Real-time log statistics
- Log volume charts (24-hour view)
- Log level distribution (pie chart)
- Recent log entries table
- Connection status indicator

### Log Viewer
- Advanced search and filtering
- Pagination for large datasets
- Expandable row details
- JSON log viewer dialog
- Real-time log streaming

### Analytics
- Time-based log volume charts
- Error trend analysis
- Source-based statistics
- Most frequent errors table
- Customizable time ranges

### Settings
- System status monitoring
- Display configuration
- Notification preferences
- Data management tools
- CSV file downloads

## 🔄 Real-time Features

### WebSocket Events

#### Client → Server
- `connect`: Establish connection
- `disconnect`: Close connection

#### Server → Client
- `status`: Connection status updates
- `new_log`: New log entry detected
- `error_detected`: Error-level log detected

### Queue-based Processing

The system uses a queue-based architecture:
1. **File Watcher** → Detects file changes
2. **Log Queue** → Queues new log entries
3. **Parser** → Processes and formats logs
4. **CSV Manager** → Saves to CSV and database
5. **WebSocket** → Broadcasts to connected clients

## 🗄️ Data Storage

### SQLite Database
- Fast querying with indexed fields
- Stores parsed log data
- Supports filtering and statistics

### CSV Files
Generated automatically:
- `all_logs.csv` - All logs
- `{source}_logs.csv` - Source-specific logs
- `error_logs.csv` - Error-level logs only
- `logs_{date}.csv` - Daily log files

## 🔍 API Endpoints

### Backend API
- `GET /` - System status
- `GET /api/logs` - Get logs with filtering
- `GET /api/logs/errors` - Get error logs only
- `GET /api/stats` - Get system statistics

### Query Parameters
- `type`: Filter by log type (node, python, all)
- `level`: Filter by log level (info, warn, error, all)
- `limit`: Number of logs to return

## 🎨 UI Components

### Material-UI Integration
- Consistent design system
- Responsive layout
- Dark/light theme support
- Professional component library

### Charts & Visualizations
- Recharts for data visualization
- Line charts for trends
- Pie charts for distribution
- Bar charts for comparisons

## 🚀 Usage Examples

### Starting the System
```bash
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend
cd template
npm run dev
```

### Adding New Log Sources
1. Add log files to `node_logs/` or `python_logs/`
2. System automatically detects and monitors new files
3. Logs appear in dashboard in real-time

### Exporting Data
1. Go to Settings page
2. Click "Export Logs"
3. Select date range and filters
4. Download generated CSV file

## 🛡️ Error Handling

### Backend Error Handling
- Graceful file read errors
- Queue processing error recovery
- Database connection management
- WebSocket connection stability

### Frontend Error Handling
- API request error handling
- WebSocket reconnection logic
- Component error boundaries
- User-friendly error messages

## 🔧 Development

### Adding New Log Parsers
1. Extend `LogParser` class in `log_parser.py`
2. Add new parsing methods
3. Update file detection logic

### Adding New Dashboard Components
1. Create component in `template/src/components/`
2. Add routing in `App.jsx`
3. Update navigation in `Navbar.jsx`

## 📝 Logging Configuration

### Log Levels Supported
- **ERROR**: Critical errors requiring attention
- **WARN/WARNING**: Warning conditions
- **INFO**: General information
- **DEBUG**: Debug-level messages

### File Naming Conventions
- Node.js: `{type}-{date}.log` in subdirectories
- Python: `{level}-{date}.log` in root directory

## 🔮 Future Enhancements

- [ ] Email/Slack notifications for critical errors
- [ ] Log retention policies
- [ ] User authentication and roles
- [ ] Multi-tenant support
- [ ] Performance metrics monitoring
- [ ] Integration with external logging services

## 🐛 Troubleshooting

### Common Issues

1. **Backend not starting:**
   - Check Python dependencies: `pip install -r requirements.txt`
   - Verify port 5000 is available

2. **Frontend not connecting:**
   - Ensure backend is running on port 5000
   - Check browser console for WebSocket errors

3. **Logs not appearing:**
   - Verify log file permissions
   - Check log file format (must be JSON)
   - Monitor backend console for parsing errors

### Debug Mode
Start backend with debug mode:
```bash
python app.py
# Debug mode is enabled by default in development
```

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Note**: This system is designed for development and monitoring environments. For production use, consider adding authentication, rate limiting, and additional security measures. 