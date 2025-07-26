import html
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/favicon.ico")
async def serve_favicon():
    return FileResponse(os.path.join(BUILD_DIR, "favicon.ico"))


@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(os.path.join(BUILD_DIR, "manifest.json"))


@app.get("/logo192.png")
async def serve_logo192():
    return FileResponse(os.path.join(BUILD_DIR, "logo192.png"))


@app.get("/logo512.png")
async def serve_logo512():
    return FileResponse(os.path.join(BUILD_DIR, "logo512.png"))


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
    # First check if file exists in build directory
    file_path = os.path.join(BUILD_DIR, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    # Otherwise serve index.html for client-side routing
    return FileResponse(INDEX_HTML)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
