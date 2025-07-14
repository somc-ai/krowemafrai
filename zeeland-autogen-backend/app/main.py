from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="SoMC.AI Zeeland API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"service": "SoMC.AI Zeeland API", "status": "active"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/agents")
async def agents():
    return {"agents": [{"name": "Test Agent", "status": "active"}]}
