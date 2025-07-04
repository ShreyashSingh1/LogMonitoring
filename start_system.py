#!/usr/bin/env python3
"""
Log Monitoring System Startup Script
This script helps start both the backend and frontend services.
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Python packages
    try:
        import flask
        import flask_socketio
        import watchdog
        import pandas
        print("✅ Python dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("📦 Install with: pip install -r backend/requirements.txt")
        return False
    
    # Check Node.js
    try:
        subprocess.run(['node', '--version'], check=True, capture_output=True)
        print("✅ Node.js is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js is not installed")
        print("📦 Install Node.js from: https://nodejs.org/")
        return False
    
    # Check npm packages (if node_modules exists)
    template_dir = Path("template")
    if (template_dir / "node_modules").exists():
        print("✅ Node.js dependencies are installed")
    else:
        print("⚠️  Node.js dependencies not installed")
        print("📦 Installing npm packages...")
        try:
            subprocess.run(['npm', 'install'], cwd=template_dir, check=True)
            print("✅ Node.js dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install Node.js dependencies")
            return False
    
    return True

def start_backend():
    """Start the Flask backend server"""
    print("🚀 Starting backend server...")
    backend_dir = Path("backend")
    
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return None
    
    try:
        process = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        print("✅ Backend server started (PID: {})".format(process.pid))
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the React frontend development server"""
    print("🎨 Starting frontend development server...")
    template_dir = Path("template")
    
    if not template_dir.exists():
        print("❌ Template directory not found")
        return None
    
    try:
        process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=template_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        print("✅ Frontend server started (PID: {})".format(process.pid))
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def print_status():
    """Print system status and URLs"""
    print("\n" + "="*50)
    print("🎯 LOG MONITORING SYSTEM RUNNING")
    print("="*50)
    print("📊 Dashboard: http://localhost:3000")
    print("🔧 Backend API: http://localhost:5000")
    print("📡 WebSocket: ws://localhost:5000")
    print("="*50)
    print("📝 Monitoring directories:")
    print("   • node_logs/ (Node.js logs)")
    print("   • python_logs/ (Python logs)")
    print("="*50)
    print("⚡ Press Ctrl+C to stop all services")
    print("="*50)

def cleanup_processes(processes):
    """Clean up spawned processes"""
    print("\n🛑 Shutting down services...")
    
    for name, process in processes.items():
        if process and process.poll() is None:
            print(f"   Stopping {name}...")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            except Exception as e:
                print(f"   Warning: Error stopping {name}: {e}")
    
    print("✅ All services stopped")

def main():
    """Main startup function"""
    print("🚀 Starting Log Monitoring System...")
    print("="*50)
    
    # Check if we're in the right directory
    if not Path("backend").exists() or not Path("template").exists():
        print("❌ Please run this script from the LogSystem root directory")
        print("   Expected structure:")
        print("   LogSystem/")
        print("   ├── backend/")
        print("   ├── template/")
        print("   └── start_system.py")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing dependencies.")
        sys.exit(1)
    
    print("\n📦 All dependencies are satisfied!")
    
    # Start services
    processes = {}
    
    try:
        # Start backend
        backend_process = start_backend()
        if not backend_process:
            print("❌ Failed to start backend server")
            sys.exit(1)
        processes['backend'] = backend_process
        
        # Wait a moment for backend to initialize
        print("⏳ Waiting for backend to initialize...")
        time.sleep(3)
        
        # Start frontend
        frontend_process = start_frontend()
        if not frontend_process:
            print("❌ Failed to start frontend server")
            cleanup_processes(processes)
            sys.exit(1)
        processes['frontend'] = frontend_process
        
        # Wait for frontend to initialize
        print("⏳ Waiting for frontend to initialize...")
        time.sleep(5)
        
        # Print status
        print_status()
        
        # Monitor processes
        while True:
            time.sleep(1)
            
            # Check if any process died
            for name, process in processes.items():
                if process and process.poll() is not None:
                    print(f"\n❌ {name} process died unexpectedly")
                    cleanup_processes(processes)
                    sys.exit(1)
    
    except KeyboardInterrupt:
        cleanup_processes(processes)
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        cleanup_processes(processes)
        sys.exit(1)

if __name__ == "__main__":
    main() 