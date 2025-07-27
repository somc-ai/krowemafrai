from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import uuid

# Create minimal fallback classes
class InputTask(BaseModel):
    session_id: str = None
    description: str

app = FastAPI(title="AI Agent GOV API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AI Agent GOV API is running", "status": "healthy", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ai-agent-gov-backend"}

@app.post("/api/input_task")
async def input_task_endpoint(input_task: InputTask, request: Request):
    """
    Receive the initial input task from the user.
    Returns a proper response structure that the frontend expects.
    """
    
    # Generate session_id if not provided
    session_id = input_task.session_id or str(uuid.uuid4())
    
    # Simplified version to avoid hanging in Azure
    try:
        # Return response structure matching frontend expectations
        return {
            "status": "success",
            "session_id": session_id,
            "plan_id": str(uuid.uuid4()),  # Generate a plan ID
            "description": input_task.description
        }
        
    except Exception as e:
        # Return basic error response
        return {
            "status": "error", 
            "session_id": session_id,
            "plan_id": "",
            "description": input_task.description
        }

@app.get("/api/agent-tools")
async def get_agent_tools():
    """
    Retrieve all available agent tools.
    """
    try:
        # Return hard-coded agent list for now to test the frontend
        available_agents = [
            {
                "agent": "hr",
                "function": "create_hr_agent",
                "description": "Creates an HR agent for human resources tasks",
                "arguments": "session_id, user_id, temperature (optional)"
            },
            {
                "agent": "marketing",
                "function": "create_marketing_agent", 
                "description": "Creates a marketing agent for marketing campaign tasks",
                "arguments": "session_id, user_id, temperature (optional)"
            },
            {
                "agent": "product",
                "function": "create_product_agent",
                "description": "Creates a product agent for product development tasks", 
                "arguments": "session_id, user_id, temperature (optional)"
            }
        ]
        
        return available_agents
    except Exception as e:
        return []

@app.get("/api/agents")
async def agents():
    return {"agents": [{"name": "Test Agent", "status": "active"}]}
