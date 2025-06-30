import os
import json
import pandas as pd
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import plotly.graph_objs as go
import plotly.utils
from collections import defaultdict
import threading
import time

app = Flask(__name__)

class LogDashboard:
    def __init__(self, csv_directory="parsed_logs/streaming"):
        self.csv_directory = csv_directory
        self.data_cache = {}
        self.last_update = {}
        self.cache_duration = 5  # Cache data for 5 seconds
        
    def get_csv_files(self):
        """Get list of available CSV files"""
        csv_files = {}
        if os.path.exists(self.csv_directory):
            for filename in os.listdir(self.csv_directory):
                if filename.endswith('.csv'):
                    file_path = os.path.join(self.csv_directory, filename)
                    csv_files[filename] = file_path
        return csv_files
    
    def load_csv_data(self, csv_file, force_reload=False):
        """Load and cache CSV data"""
        file_path = os.path.join(self.csv_directory, csv_file)
        
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        # Check cache
        cache_key = csv_file
        now = datetime.now()
        
        if not force_reload and cache_key in self.data_cache:
            if cache_key in self.last_update:
                if (now - self.last_update[cache_key]).seconds < self.cache_duration:
                    return self.data_cache[cache_key]
        
        # Load fresh data
        try:
            df = pd.read_csv(file_path)
            self.data_cache[cache_key] = df
            self.last_update[cache_key] = now
            return df
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return pd.DataFrame()
    
    def get_summary_stats(self, df):
        """Generate summary statistics"""
        if df.empty:
            return {}
        
        stats = {
            'total_entries': len(df),
            'time_range': {
                'start': df['timestamp'].min() if 'timestamp' in df.columns else 'N/A',
                'end': df['timestamp'].max() if 'timestamp' in df.columns else 'N/A'
            }
        }
        
        # Add column-specific stats
        for col in ['level', 'log_type', 'action', 'error_category', 'status_code']:
            if col in df.columns:
                stats[col] = df[col].value_counts().to_dict()
        
        # User stats
        if 'user_id' in df.columns:
            stats['unique_users'] = df['user_id'].nunique()
            stats['top_users'] = df['user_id'].value_counts().head(10).to_dict()
        
        return stats
    
    def create_time_series_chart(self, df, time_col='timestamp', group_col='level'):
        """Create time series chart"""
        if df.empty or time_col not in df.columns:
            return {}
        
        # Convert timestamp to datetime
        df[time_col] = pd.to_datetime(df[time_col])
        
        # Group by time intervals (hourly)
        df['hour'] = df[time_col].dt.floor('H')
        
        if group_col in df.columns:
            time_series = df.groupby(['hour', group_col]).size().unstack(fill_value=0)
        else:
            time_series = df.groupby('hour').size()
        
        # Create plotly chart
        fig = go.Figure()
        
        if isinstance(time_series, pd.DataFrame):
            for col in time_series.columns:
                fig.add_trace(go.Scatter(
                    x=time_series.index,
                    y=time_series[col],
                    mode='lines+markers',
                    name=str(col)
                ))
        else:
            fig.add_trace(go.Scatter(
                x=time_series.index,
                y=time_series.values,
                mode='lines+markers',
                name='Count'
            ))
        
        fig.update_layout(
            title=f'Log Entries Over Time (Grouped by {group_col})',
            xaxis_title='Time',
            yaxis_title='Count',
            height=400
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def create_pie_chart(self, df, column):
        """Create pie chart for categorical data"""
        if df.empty or column not in df.columns:
            return {}
        
        value_counts = df[column].value_counts().head(10)
        
        fig = go.Figure(data=[go.Pie(
            labels=value_counts.index,
            values=value_counts.values,
            hole=0.3
        )])
        
        fig.update_layout(
            title=f'Distribution of {column.title()}',
            height=400
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

# Initialize dashboard
dashboard = LogDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    csv_files = dashboard.get_csv_files()
    return render_template('dashboard.html', csv_files=list(csv_files.keys()))

@app.route('/api/files')
def get_files():
    """API endpoint to get available CSV files"""
    csv_files = dashboard.get_csv_files()
    return jsonify(list(csv_files.keys()))

@app.route('/api/data/<filename>')
def get_data(filename):
    """API endpoint to get data from specific CSV file"""
    df = dashboard.load_csv_data(filename)
    
    # Apply filters if provided
    filters = request.args.to_dict()
    
    if 'level' in filters and 'level' in df.columns:
        df = df[df['level'] == filters['level']]
    
    if 'log_type' in filters and 'log_type' in df.columns:
        df = df[df['log_type'] == filters['log_type']]
    
    if 'user_id' in filters and 'user_id' in df.columns:
        df = df[df['user_id'] == filters['user_id']]
    
    if 'search' in filters and 'message' in df.columns:
        search_term = filters['search'].lower()
        df = df[df['message'].str.lower().str.contains(search_term, na=False)]
    
    # Limit results
    limit = int(filters.get('limit', 100))
    df_limited = df.tail(limit)
    
    return jsonify({
        'data': df_limited.to_dict('records'),
        'total': len(df),
        'filtered': len(df_limited)
    })

@app.route('/api/stats/<filename>')
def get_stats(filename):
    """API endpoint to get statistics for specific CSV file"""
    df = dashboard.load_csv_data(filename)
    stats = dashboard.get_summary_stats(df)
    return jsonify(stats)

@app.route('/api/charts/<filename>')
def get_charts(filename):
    """API endpoint to get charts for specific CSV file"""
    df = dashboard.load_csv_data(filename)
    
    charts = {}
    
    # Time series chart
    if 'timestamp' in df.columns:
        charts['time_series'] = dashboard.create_time_series_chart(df)
    
    # Pie charts for categorical columns
    for col in ['level', 'log_type', 'action', 'error_category']:
        if col in df.columns:
            charts[f'{col}_pie'] = dashboard.create_pie_chart(df, col)
    
    return jsonify(charts)

@app.route('/api/live_data')
def get_live_data():
    """API endpoint to get live data from all sources"""
    csv_files = dashboard.get_csv_files()
    live_data = {}
    
    for filename in csv_files.keys():
        df = dashboard.load_csv_data(filename, force_reload=True)
        if not df.empty:
            # Get recent entries (last 10)
            recent = df.tail(10)
            live_data[filename] = {
                'recent_entries': recent.to_dict('records'),
                'total_count': len(df),
                'last_entry_time': df['timestamp'].max() if 'timestamp' in df.columns else 'N/A'
            }
    
    return jsonify(live_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 