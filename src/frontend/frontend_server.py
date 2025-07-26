import html
import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Set to False when using wildcard origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Build paths
BUILD_DIR = os.path.join(os.path.dirname(__file__), "build")
INDEX_HTML = os.path.join(BUILD_DIR, "index.html")

# Serve static files from build directory
app.mount(
    "/assets", StaticFiles(directory=os.path.join(BUILD_DIR, "assets")), name="assets"
)

# Mount additional static files that might be needed
app.mount(
    "/static", StaticFiles(directory=BUILD_DIR), name="static"
)


@app.get("/")
async def serve_index():
    return FileResponse(INDEX_HTML)


@app.get("/health")
async def health_check():
    """Health check endpoint for Container Apps."""
    return {"status": "healthy", "service": "ai-agent-gov-frontend"}


@app.get("/favicon.ico")
async def serve_favicon():
    return FileResponse(os.path.join(BUILD_DIR, "favicon.ico"))


@app.get("/favicon-96x96.png")
async def serve_favicon_96():
    return FileResponse(os.path.join(BUILD_DIR, "favicon-96x96.png"))


@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(os.path.join(BUILD_DIR, "manifest.json"))


@app.get("/logo192.png")
async def serve_logo192():
    return FileResponse(os.path.join(BUILD_DIR, "logo192.png"))


@app.get("/logo512.png")
async def serve_logo512():
    return FileResponse(os.path.join(BUILD_DIR, "logo512.png"))


@app.get("/robots.txt")
async def serve_robots():
    return FileResponse(os.path.join(BUILD_DIR, "robots.txt"))


@app.get("/web.config")
async def serve_web_config():
    return FileResponse(os.path.join(BUILD_DIR, "web.config"))


@app.get("/debug/build-contents")
async def debug_build_contents():
    """Debug endpoint to list build directory contents"""
    try:
        contents = []
        for root, dirs, files in os.walk(BUILD_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, BUILD_DIR)
                contents.append(rel_path)
        return {"build_dir": BUILD_DIR, "contents": sorted(contents)}
    except Exception as e:
        return {"error": str(e), "build_dir": BUILD_DIR}


@app.get("/config")
async def get_config():
    # Use the working backend URL as fallback
    default_backend_url = "https://backend-aiagents-gov.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io"
    backend_url = html.escape(os.getenv("BACKEND_API_URL", default_backend_url))
    auth_enabled = html.escape(os.getenv("AUTH_ENABLED", "false"))
    backend_url = backend_url + "/api"

    config = {
        "API_URL": backend_url,
        "ENABLE_AUTH": auth_enabled,
    }
    return config


@app.get("/{full_path:path}")
async def serve_app(full_path: str):
    """Serve static files or fall back to index.html for client-side routing"""
    # First check if file exists in build directory
    file_path = os.path.join(BUILD_DIR, full_path)
    
    # If it's a file that exists, serve it
    if os.path.exists(file_path) and os.path.isfile(file_path):
        # Determine media type based on file extension
        media_type = None
        if full_path.endswith('.js'):
            media_type = 'application/javascript'
        elif full_path.endswith('.css'):
            media_type = 'text/css'
        elif full_path.endswith('.png'):
            media_type = 'image/png'
        elif full_path.endswith('.ico'):
            media_type = 'image/x-icon'
        elif full_path.endswith('.json'):
            media_type = 'application/json'
        elif full_path.endswith('.html'):
            media_type = 'text/html'
        
        return FileResponse(file_path, media_type=media_type)
    
    # For any other routes (React Router paths), serve index.html
    return FileResponse(INDEX_HTML, media_type='text/html')


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
