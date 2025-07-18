"""
Entry point for the Multi-Agent Custom Automation Engine Solution Accelerator.
This file serves as the main entry point for Azure Web App deployment.
"""

import os
import sys

print("🚀 Starting SoMC AI - Zeeland Multi-Agent Team")
print(f"📂 Working directory: {os.getcwd()}")
print(f"🐍 Python version: {sys.version}")

# Check if we have all required dependencies and environment variables for the full system
has_full_system = False

try:
    # Try to import the full backend system
    backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'backend')
    sys.path.insert(0, backend_path)
    
    # Check if we have the required environment variables
    required_vars = [
        'AZURE_OPENAI_ENDPOINT', 
        'AZURE_AI_SUBSCRIPTION_ID', 
        'AZURE_AI_RESOURCE_GROUP', 
        'AZURE_AI_PROJECT_NAME', 
        'AZURE_AI_AGENT_ENDPOINT'
    ]
    
    has_all_vars = all(os.getenv(var) for var in required_vars)
    
    if has_all_vars:
        # Try to import the full backend system
        import importlib.util
        spec = importlib.util.spec_from_file_location("app_kernel", os.path.join(backend_path, "app_kernel.py"))
        app_kernel = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_kernel)
        
        # Try to import required dependencies
        import fastapi
        import uvicorn
        
        app = app_kernel.app
        has_full_system = True
        print("✅ Full multi-agent system loaded successfully")
    else:
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        print(f"⚠️  Missing environment variables: {missing_vars}")
        print("🔄 Falling back to minimal app")
        
except Exception as e:
    print(f"⚠️  Full backend not available ({e})")
    print("🔄 Using minimal app")

if not has_full_system:
    # Fall back to minimal app
    try:
        from app import run_server
        print("✅ Minimal app loaded successfully")
        
        if __name__ == "__main__":
            run_server()
            
    except Exception as e:
        print(f"❌ Error loading minimal app: {e}")
        # Final fallback - create a very basic server
        import http.server
        import socketserver
        
        port = int(os.getenv("PORT", 8000))
        
        class BasicHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "healthy", "message": "SoMC AI - Zeeland Multi-Agent Team is running"}')
                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'<html><body><h1>SoMC AI - Zeeland Multi-Agent Team</h1><p>System is running but requires configuration.</p></body></html>')
        
        with socketserver.TCPServer(("", port), BasicHandler) as httpd:
            print(f"🚀 Basic server running on port {port}")
            httpd.serve_forever()

else:
    # Use the full system
    if __name__ == "__main__":
        import uvicorn
        port = int(os.getenv("PORT", 8000))
        print(f"🚀 Starting full system on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)