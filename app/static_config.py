import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

def setup_static_files(app: FastAPI):
    """Setup static files for production deployment"""
    
    # Get the directory where this file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Static files path
    static_dir = os.path.join(current_dir, "static")
    
    # Check if static directory exists
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        print(f"Static files mounted from: {static_dir}")
    else:
        print(f"Warning: Static directory not found at {static_dir}")
        
    return static_dir