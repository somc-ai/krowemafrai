"""
Entry point for the Multi-Agent Custom Automation Engine Solution Accelerator.
This file imports the main application from the backend module.
"""

import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'backend')
sys.path.insert(0, backend_path)

# Import the main application from the backend
from app_kernel import app

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (Azure Web Apps sets this)
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(app, host="0.0.0.0", port=port)