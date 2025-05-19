#!/usr/bin/env python3
"""
AI Meeting Assistant - Startup Script
"""

import os
import sys
import webbrowser
import subprocess
import time
import signal
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

def check_env_file():
    """Check if .env file exists in the backend directory"""
    env_file = BACKEND_DIR / ".env"
    if not env_file.exists():
        logger.warning("No .env file found in backend directory")
        create_default = input("Would you like to create a default .env file? (y/n): ")
        if create_default.lower() == 'y':
            api_key = input("Enter your OpenAI API Key (leave blank to skip): ")
            with open(env_file, 'w') as f:
                f.write(f"OPENAI_API_KEY={api_key}\n")
            logger.info("Created .env file")
        else:
            logger.warning("No .env file created. Some features may not work correctly.")

def start_backend():
    """Start the backend FastAPI server"""
    logger.info("Starting backend server...")
    
    # Check if we're in the correct environment
    if not (BACKEND_DIR / "main.py").exists():
        logger.error("Backend main.py not found. Make sure you're in the correct directory.")
        sys.exit(1)
    
    # Build the command to run the backend
    cmd = [sys.executable, str(BACKEND_DIR / "main.py")]
    
    # Start backend process
    try:
        backend_process = subprocess.Popen(
            cmd,
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        logger.info("Backend server started")
        return backend_process
    except Exception as e:
        logger.error(f"Failed to start backend server: {str(e)}")
        sys.exit(1)

def start_frontend():
    """Open the frontend in the default web browser"""
    logger.info("Opening frontend in web browser...")
    
    frontend_index = FRONTEND_DIR / "index.html"
    if not frontend_index.exists():
        logger.error("Frontend index.html not found. Make sure you're in the correct directory.")
        sys.exit(1)
    
    # Convert to file URL
    file_url = f"file://{frontend_index.absolute()}"
    
    # Open in web browser
    try:
        webbrowser.open(file_url)
        logger.info("Frontend opened in web browser")
    except Exception as e:
        logger.error(f"Failed to open frontend in web browser: {str(e)}")
        logger.info(f"You can manually open the frontend at: {file_url}")

def main():
    """Main entry point"""
    logger.info("Starting AI Meeting Assistant")
    
    # Check for environment file
    check_env_file()
    
    # Start backend server
    backend_process = start_backend()
    
    # Give the backend a moment to start
    time.sleep(2)
    
    # Check if backend started successfully
    if backend_process.poll() is not None:
        logger.error("Backend server failed to start")
        if backend_process.stdout:
            for line in backend_process.stdout:
                print(line, end='')
        sys.exit(1)
    
    # Start frontend
    start_frontend()
    
    # Print some helpful information
    print("\n" + "="*60)
    print("AI Meeting Assistant is now running")
    print("="*60)
    print("Backend server is running at: http://localhost:8000")
    print("Frontend is open in your web browser")
    print("\nPress Ctrl+C to stop the application\n")
    
    # Keep the script running until interrupted
    try:
        # Stream backend logs
        while backend_process.poll() is None:
            if backend_process.stdout:
                line = backend_process.stdout.readline()
                if line:
                    print(line, end='')
    except KeyboardInterrupt:
        logger.info("Stopping application...")
    finally:
        # Clean up
        if backend_process.poll() is None:
            backend_process.send_signal(signal.SIGINT)
            backend_process.wait(timeout=5)
        logger.info("Application stopped")

if __name__ == "__main__":
    main()
