"""
Minimal web application for Azure Web App deployment.
This serves as a fallback when full dependencies are not available.
"""

import os
import json
import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class ZeelandHandler(SimpleHTTPRequestHandler):
    """Custom handler for the Zeeland Multi-Agent Team application."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            self.serve_html()
        elif self.path == '/health':
            self.serve_json({"status": "healthy", "service": "SoMC AI - Zeeland Multi-Agent Team"})
        elif self.path == '/api/status':
            self.serve_json({
                "system_status": "active",
                "agents_available": True,
                "database_connected": bool(os.getenv("COSMOSDB_ENDPOINT")),
                "ai_configured": bool(os.getenv("AZURE_OPENAI_ENDPOINT")),
                "environment": os.getenv("ENVIRONMENT", "development"),
                "deployment_time": datetime.datetime.now().isoformat()
            })
        elif self.path == '/api/agents':
            self.serve_agents()
        else:
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/api/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(post_data)
                message = data.get('message', '')
                
                response = {
                    "response": f"Bedankt voor uw vraag: '{message}'. Ons multi-agent team voor Zeeland analyseert dit vanuit demografisch, economisch en beleidsperspectief. De volledige AI-functionaliteit wordt momenteel geconfigureerd.",
                    "agents_consulted": ["Beleid Adviseur", "Demografische Analist", "Economische Analist"],
                    "session_id": data.get("session_id", "demo-session"),
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                self.serve_json(response)
            except json.JSONDecodeError:
                self.serve_json({"error": "Invalid JSON"}, status=400)
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_html(self):
        """Serve the main HTML page."""
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'HTML file not found')
    
    def serve_json(self, data, status=200):
        """Serve JSON response."""
        content = json.dumps(data, indent=2)
        
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', len(content.encode('utf-8')))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def serve_agents(self):
        """Serve agents information."""
        agents = [
            {
                "name": "Beleid Adviseur",
                "description": "Adviseert over beleidsvorming en implementatie voor de provincie Zeeland",
                "status": "active",
                "expertise": ["beleid", "governance", "implementatie"]
            },
            {
                "name": "Demografische Analist",
                "description": "Analyseert demografische trends en bevolkingsontwikkelingen",
                "status": "active",
                "expertise": ["demografie", "bevolkingsanalyse", "trends"]
            },
            {
                "name": "Economische Analist",
                "description": "Analyseert economische impact en identificeert kansen",
                "status": "active",
                "expertise": ["economie", "impact-analyse", "kansen"]
            },
            {
                "name": "Communicatie Specialist",
                "description": "Helpt bij communicatie en stakeholder management",
                "status": "active",
                "expertise": ["communicatie", "stakeholders", "burgerparticipatie"]
            }
        ]
        
        self.serve_json({"agents": agents, "total_count": len(agents)})

def run_server():
    """Run the HTTP server."""
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting SoMC AI - Zeeland Multi-Agent Team on port {port}")
    print(f"📂 Serving from: {os.getcwd()}")
    print(f"🌐 Available at: http://localhost:{port}")
    
    server = HTTPServer(('', port), ZeelandHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.server_close()

if __name__ == "__main__":
    run_server()