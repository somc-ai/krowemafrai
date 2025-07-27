import sys
import os
import asyncio
import logging
import uuid
from typing import Dict, List, Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Create minimal fallback classes
class InputTask(BaseModel):
    session_id: str
    description: str

class HumanFeedback(BaseModel):
    session_id: str
    step_id: str = ""
    approved: bool = True
    human_feedback: str = ""

class HumanClarification(BaseModel):
    session_id: str
    step_id: str = ""
    human_clarification: str = ""

# Try imports with fallbacks
try:
    from middleware.health_check import HealthCheckMiddleware
    HEALTH_CHECK_AVAILABLE = True
except ImportError:
    HEALTH_CHECK_AVAILABLE = False
    print("Warning: HealthCheckMiddleware not available, skipping")

# Azure monitoring - optional import
try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    AZURE_MONITOR_AVAILABLE = True
except ImportError:
    AZURE_MONITOR_AVAILABLE = False

# Import core agent and model dependencies - these should work now
try:
    from kernel_agents.agent_factory import AgentFactory
    from models.messages_kernel import AgentType, PlanWithSteps, Step, AgentMessage
    from app_config import config
    from context.cosmos_memory_kernel import initialize_runtime_and_context
    DEPENDENCIES_AVAILABLE = True
    print("INFO: All dependencies loaded successfully")
except ImportError as e:
    print(f"Warning: Core dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False
    
    # Keep the fallback classes
    class AgentFactory:
        @staticmethod
        async def create_agent(**kwargs):
            return None
            
        @staticmethod
        async def create_all_agents(**kwargs):
            return {}
            
        @staticmethod
        def clear_cache():
            pass

    class AgentType:
        HUMAN = "Human_Agent"
        HR = "Hr_Agent"
        MARKETING = "Marketing_Agent"
        GROUP_CHAT_MANAGER = "Group_Chat_Manager"
        
    class Step:
        def __init__(self, **kwargs):
            self.id = kwargs.get('id', '')
            self.plan_id = kwargs.get('plan_id', '')
            self.step_number = kwargs.get('step_number', 0)
            self.description = kwargs.get('description', '')
            self.status = kwargs.get('status', 'pending')
            for key, value in kwargs.items():
                setattr(self, key, value)
                
        def model_dump(self):
            return {
                'id': getattr(self, 'id', ''),
                'plan_id': getattr(self, 'plan_id', ''),
                'step_number': getattr(self, 'step_number', 0),
                'description': getattr(self, 'description', ''),
                'status': getattr(self, 'status', 'pending')
            }
        
    class AgentMessage:
        pass
        
    class PlanWithSteps:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def update_step_counts(self):
            pass

    class config:
        @staticmethod
        def get_ai_project_client():
            return None
            
    async def initialize_runtime_and_context(session_id, user_id):
        # Return minimal fallback objects
        class FallbackMemoryStore:
            async def get_plan_by_session(self, session_id):
                return None
            async def get_plan_by_plan_id(self, plan_id):
                return None
            async def get_steps_by_plan(self, plan_id):
                return []
            async def get_data_by_type_and_session_id(self, data_type, session_id):
                return []
            async def get_all_plans(self):
                return []
            async def get_steps_for_plan(self, plan_id):
                return []
            async def get_data_by_type(self, data_type):
                return []
            async def get_data_by_type_and_plan_id(self, data_type):
                return []
            async def delete_all_items(self, item_type):
                pass
            async def get_all_items(self):
                return []
                
        return None, FallbackMemoryStore()
except Exception as e:
    print(f"Error during imports: {e}")
    DEPENDENCIES_AVAILABLE = False

# Try to import optional dependencies - these might fail in Azure
def get_authenticated_user_details(request_headers):
    return {"user_principal_id": "anonymous_user"}

def track_event_if_configured(event_name, properties=None):
    pass

class Config:
    FRONTEND_SITE_NAME = ""

# Set up logger
logger = logging.getLogger(__name__)

# Check if the Application Insights Instrumentation Key is set in the environment variables
connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if connection_string and AZURE_MONITOR_AVAILABLE:
    # Configure Application Insights if the Instrumentation Key is found
    configure_azure_monitor(connection_string=connection_string)
    logging.info(
        "Application Insights configured with the provided Instrumentation Key"
    )
elif connection_string:
    logging.warning(
        "Application Insights connection string found but azure-monitor-opentelemetry not installed"
    )
else:
    # Log a warning if the Instrumentation Key is not found
    logging.warning(
        "No Application Insights Instrumentation Key found. Skipping configuration"
    )

# Configure logging
logging.basicConfig(level=logging.INFO)

# Suppress INFO logs from 'azure.core.pipeline.policies.http_logging_policy'
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
    logging.WARNING
)
logging.getLogger("azure.identity.aio._internal").setLevel(logging.WARNING)

# # Suppress info logs from OpenTelemetry exporter
logging.getLogger("azure.monitor.opentelemetry.exporter.export._base").setLevel(
    logging.WARNING
)

# Initialize the FastAPI app with proper configuration
app = FastAPI(
    title="SoMC Agents",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

frontend_url = Config.FRONTEND_SITE_NAME

# Add this near the top of your app.py, after initializing the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure health check - only if available
if HEALTH_CHECK_AVAILABLE:
    app.add_middleware(HealthCheckMiddleware, password="", checks={})
    logging.info("Added health check middleware")
else:
    logging.info("Skipped health check middleware - not available")


@app.get("/")
async def root():
    """Root endpoint to confirm the API is running."""
    return {"message": "AI Agent GOV API is running", "status": "healthy", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Container Apps."""
    return {"status": "healthy", "service": "ai-agent-gov-backend"}


@app.post("/api/input_task")
async def input_task_endpoint(input_task: InputTask, request: Request):
    """
    Receive the initial input task from the user.
    Returns a proper response structure that the frontend expects.
    """
    
    # Simplified version to avoid hanging in Azure
    try:
        # Create minimal agent responses
        available_agents = [
            {
                "agent_name": "HR Specialist",
                "agent_expertise": "hr",
                "response": f"HR analyse voor: {input_task.description}"
            },
            {
                "agent_name": "Marketing Expert", 
                "agent_expertise": "marketing",
                "response": f"Marketing perspectief: {input_task.description}"
            }
        ]
        
        # Return minimal response structure
        return {
            "status": "success",
            "session_id": input_task.session_id,
            "agent_responses": available_agents,
            "message": "Analyse voltooid"
        }
        
    except Exception as e:
        # Return basic error response
        return {
            "status": "error", 
            "session_id": input_task.session_id,
            "message": f"Error: {str(e)}"
        }


@app.post("/api/human_feedback")
async def human_feedback_endpoint(human_feedback: HumanFeedback, request: Request):
    """
    Receive human feedback on a step.
    """
    return {
        "status": "Feedback received - simplified",
        "session_id": human_feedback.session_id,
        "step_id": human_feedback.step_id,
    }


@app.post("/api/human_clarification_on_plan")
async def human_clarification_endpoint(
    human_clarification: HumanClarification, request: Request
):
    """
    Receive human clarification on a plan.

    ---
    tags:
      - Clarification
    parameters:
      - name: user_principal_id
        in: header
        type: string
        required: true
        description: User ID extracted from the authentication header
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            plan_id:
              type: string
              description: The plan ID requiring clarification
            session_id:
              type: string
              description: The session ID
            human_clarification:
              type: string
              description: Clarification details provided by the user
            user_id:
              type: string
              description: The user ID providing the clarification
    responses:
      200:
        description: Clarification received successfully
        schema:
          type: object
          properties:
            status:
              type: string
            session_id:
              type: string
      400:
        description: Missing or invalid user information
    """
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    user_id = authenticated_user["user_principal_id"]
    if not user_id:
        track_event_if_configured(
            "UserIdNotFound", {"status_code": 400, "detail": "no user"}
        )
        raise HTTPException(status_code=400, detail="no user")

    kernel, memory_store = await initialize_runtime_and_context(
        human_clarification.session_id, user_id
    )
    client = None
    try:
        client = config.get_ai_project_client()
    except Exception as client_exc:
        logging.error(f"Error creating AIProjectClient: {client_exc}")

    human_agent = await AgentFactory.create_agent(
        agent_type=AgentType.HUMAN,
        session_id=human_clarification.session_id,
        user_id=user_id,
        memory_store=memory_store,
        client=client,
    )

    if human_agent is None:
        track_event_if_configured(
            "AgentNotFound",
            {
                "status": "Agent not found",
                "session_id": human_clarification.session_id,
                "step_id": human_clarification.step_id,
            },
        )
        raise HTTPException(status_code=404, detail="Agent not found")

    # Use the human agent to handle the feedback
    await human_agent.handle_human_clarification(
        human_clarification=human_clarification
    )

    track_event_if_configured(
        "Completed Human clarification on the plan",
        {
            "status": "Clarification received",
            "session_id": human_clarification.session_id,
        },
    )
    if client:
        try:
            client.close()
        except Exception as e:
            logging.error(f"Error sending to AIProjectClient: {e}")
    return {
        "status": "Clarification received",
        "session_id": human_clarification.session_id,
    }


@app.post("/api/approve_step_or_steps")
async def approve_step_endpoint(
    human_feedback: HumanFeedback, request: Request
) -> Dict[str, str]:
    """
    Approve a step or multiple steps in a plan.

    ---
    tags:
      - Approval
    parameters:
      - name: user_principal_id
        in: header
        type: string
        required: true
        description: User ID extracted from the authentication header
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            step_id:
              type: string
              description: Optional step ID to approve
            plan_id:
              type: string
              description: The plan ID
            session_id:
              type: string
              description: The session ID
            approved:
              type: boolean
              description: Whether the step(s) are approved
            human_feedback:
              type: string
              description: Optional feedback details
            updated_action:
              type: string
              description: Optional updated action
            user_id:
              type: string
              description: The user ID providing the approval
    responses:
      200:
        description: Approval status returned
        schema:
          type: object
          properties:
            status:
              type: string
      400:
        description: Missing or invalid user information
    """
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    user_id = authenticated_user["user_principal_id"]
    if not user_id:
        track_event_if_configured(
            "UserIdNotFound", {"status_code": 400, "detail": "no user"}
        )
        raise HTTPException(status_code=400, detail="no user")

    # Get the agents for this session
    kernel, memory_store = await initialize_runtime_and_context(
        human_feedback.session_id, user_id
    )
    client = None
    try:
        client = config.get_ai_project_client()
    except Exception as client_exc:
        logging.error(f"Error creating AIProjectClient: {client_exc}")
    agents = await AgentFactory.create_all_agents(
        session_id=human_feedback.session_id,
        user_id=user_id,
        memory_store=memory_store,
        client=client,
    )

    # Send the approval to the group chat manager
    group_chat_manager = agents[AgentType.GROUP_CHAT_MANAGER.value]

    await group_chat_manager.handle_human_feedback(human_feedback)

    if client:
        try:
            client.close()
        except Exception as e:
            logging.error(f"Error sending to AIProjectClient: {e}")
    # Return a status message
    if human_feedback.step_id:
        track_event_if_configured(
            "Completed Human clarification with step_id",
            {
                "status": f"Step {human_feedback.step_id} - Approval:{human_feedback.approved}."
            },
        )

        return {
            "status": f"Step {human_feedback.step_id} - Approval:{human_feedback.approved}."
        }
    else:
        track_event_if_configured(
            "Completed Human clarification without step_id",
            {"status": "All steps approved"},
        )

        return {"status": "All steps approved"}


@app.get("/api/plans")
async def get_plans(
    request: Request,
    session_id: Optional[str] = Query(None),
    plan_id: Optional[str] = Query(None),
):
    """
    Retrieve plans for the current user.

    ---
    tags:
      - Plans
    parameters:
      - name: session_id
        in: query
        type: string
        required: false
        description: Optional session ID to retrieve plans for a specific session
    responses:
      200:
        description: List of plans with steps for the user
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                description: Unique ID of the plan
              session_id:
                type: string
                description: Session ID associated with the plan
              initial_goal:
                type: string
                description: The initial goal derived from the user's input
              overall_status:
                type: string
                description: Status of the plan (e.g., in_progress, completed)
              steps:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: string
                      description: Unique ID of the step
                    plan_id:
                      type: string
                      description: ID of the plan the step belongs to
                    action:
                      type: string
                      description: The action to be performed
                    agent:
                      type: string
                      description: The agent responsible for the step
                    status:
                      type: string
                      description: Status of the step (e.g., planned, approved, completed)
      400:
        description: Missing or invalid user information
      404:
        description: Plan not found
    """
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    user_id = authenticated_user["user_principal_id"]
    if not user_id:
        track_event_if_configured(
            "UserIdNotFound", {"status_code": 400, "detail": "no user"}
        )
        raise HTTPException(status_code=400, detail="no user")

    # Initialize memory context
    kernel, memory_store = await initialize_runtime_and_context(
        session_id or "", user_id
    )

    if session_id:
        plan = await memory_store.get_plan_by_session(session_id=session_id)
        if not plan:
            track_event_if_configured(
                "GetPlanBySessionNotFound",
                {"status_code": 400, "detail": "Plan not found"},
            )
            raise HTTPException(status_code=404, detail="Plan not found")

        # Use get_steps_by_plan to match the original implementation
        steps = await memory_store.get_steps_by_plan(plan_id=plan.id)
        plan_with_steps = PlanWithSteps(**plan.model_dump(), steps=steps)
        plan_with_steps.update_step_counts()
        return [plan_with_steps]
    if plan_id:
        plan = await memory_store.get_plan_by_plan_id(plan_id=plan_id)
        if not plan:
            track_event_if_configured(
                "GetPlanBySessionNotFound",
                {"status_code": 400, "detail": "Plan not found"},
            )
            raise HTTPException(status_code=404, detail="Plan not found")

        # Use get_steps_by_plan to match the original implementation
        steps = await memory_store.get_steps_by_plan(plan_id=plan.id)
        messages = await memory_store.get_data_by_type_and_session_id(
            "agent_message", session_id=plan.session_id
        )

        plan_with_steps = PlanWithSteps(**plan.model_dump(), steps=steps)
        plan_with_steps.update_step_counts()
        return [plan_with_steps, messages]

    all_plans = await memory_store.get_all_plans()
    # Fetch steps for all plans concurrently
    steps_for_all_plans = await asyncio.gather(
        *[memory_store.get_steps_by_plan(plan_id=plan.id) for plan in all_plans]
    )
    # Create list of PlanWithSteps and update step counts
    list_of_plans_with_steps = []
    for plan, steps in zip(all_plans, steps_for_all_plans):
        plan_with_steps = PlanWithSteps(**plan.model_dump(), steps=steps)
        plan_with_steps.update_step_counts()
        list_of_plans_with_steps.append(plan_with_steps)

    return list_of_plans_with_steps


@app.get("/api/steps/{plan_id}")
async def get_steps_by_plan(plan_id: str, request: Request):
    """
    Retrieve steps for a specific plan.

    ---
    tags:
      - Steps
    parameters:
      - name: plan_id
        in: path
        type: string
        required: true
        description: The ID of the plan to retrieve steps for
    responses:
      200:
        description: List of steps associated with the specified plan
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                description: Unique ID of the step
              plan_id:
                type: string
                description: ID of the plan the step belongs to
              action:
                type: string
                description: The action to be performed
              agent:
                type: string
                description: The agent responsible for the step
              status:
                type: string
                description: Status of the step (e.g., planned, approved, completed)
              agent_reply:
                type: string
                description: Optional response from the agent after execution
              human_feedback:
                type: string
                description: Optional feedback provided by a human
              updated_action:
                type: string
                description: Optional modified action based on feedback
       400:
        description: Missing or invalid user information
      404:
        description: Plan or steps not found
    """
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    user_id = authenticated_user["user_principal_id"]
    if not user_id:
        track_event_if_configured(
            "UserIdNotFound", {"status_code": 400, "detail": "no user"}
        )
        raise HTTPException(status_code=400, detail="no user")

    # Initialize memory context
    kernel, memory_store = await initialize_runtime_and_context("", user_id)
    steps = await memory_store.get_steps_for_plan(plan_id=plan_id)
    return steps


@app.get("/api/agent_messages/{session_id}")
async def get_agent_messages(session_id: str, request: Request):
    """
    Retrieve agent messages for a specific session.

    ---
    tags:
      - Agent Messages
    parameters:
      - name: session_id
        in: path
        type: string
        required: true
        in: path
        type: string
        required: true
        description: The ID of the session to retrieve agent messages for
    responses:
      200:
        description: List of agent messages associated with the specified session
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                description: Unique ID of the agent message
              session_id:
                type: string
                description: Session ID associated with the message
              plan_id:
                type: string
                description: Plan ID related to the agent message
              content:
                type: string
                description: Content of the message
              source:
                type: string
                description: Source of the message (e.g., agent type)
              timestamp:
                type: string
                format: date-time
                description: Timestamp of the message
              step_id:
                type: string
                description: Optional step ID associated with the message
      400:
        description: Missing or invalid user information
      404:
        description: Agent messages not found
    """
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    user_id = authenticated_user["user_principal_id"]
    if not user_id:
        track_event_if_configured(
            "UserIdNotFound", {"status_code": 400, "detail": "no user"}
        )
        raise HTTPException(status_code=400, detail="no user")

    # Initialize memory context
    kernel, memory_store = await initialize_runtime_and_context(
        session_id or "", user_id
    )
    agent_messages = await memory_store.get_data_by_type("agent_message")
    return agent_messages


@app.get("/api/agent_messages_by_plan/{plan_id}")
async def get_agent_messages_by_plan(
    plan_id: str, request: Request
):
    """
    Retrieve agent messages for a specific session.

    ---
    tags:
      - Agent Messages
    parameters:
      - name: session_id
        in: path
        type: string
        required: true
        in: path
        type: string
        required: true
        description: The ID of the session to retrieve agent messages for
    responses:
      200:
        description: List of agent messages associated with the specified session
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                description: Unique ID of the agent message
              session_id:
                type: string
                description: Session ID associated with the message
              plan_id:
                type: string
                description: Plan ID related to the agent message
              content:
                type: string
                description: Content of the message
              source:
                type: string
                description: Source of the message (e.g., agent type)
              timestamp:
                type: string
                format: date-time
                description: Timestamp of the message
              step_id:
                type: string
                description: Optional step ID associated with the message
      400:
        description: Missing or invalid user information
      404:
        description: Agent messages not found
    """
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    user_id = authenticated_user["user_principal_id"]
    if not user_id:
        track_event_if_configured(
            "UserIdNotFound", {"status_code": 400, "detail": "no user"}
        )
        raise HTTPException(status_code=400, detail="no user")

    # Initialize memory context
    kernel, memory_store = await initialize_runtime_and_context("", user_id)
    agent_messages = await memory_store.get_data_by_type_and_plan_id("agent_message")
    return agent_messages


@app.delete("/api/messages")
async def delete_all_messages(request: Request) -> Dict[str, str]:
    """
    Delete all messages across sessions.

    ---
    tags:
      - Messages
    responses:
      200:
        description: Confirmation of deletion
        schema:
          type: object
          properties:
            status:
              type: string
              description: Status message indicating all messages were deleted
      400:
        description: Missing or invalid user information
    """
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    user_id = authenticated_user["user_principal_id"]
    if not user_id:
        track_event_if_configured(
            "UserIdNotFound", {"status_code": 400, "detail": "no user"}
        )
        raise HTTPException(status_code=400, detail="no user")

    # Initialize memory context
    kernel, memory_store = await initialize_runtime_and_context("", user_id)

    await memory_store.delete_all_items("plan")
    await memory_store.delete_all_items("session")
    await memory_store.delete_all_items("step")
    await memory_store.delete_all_items("agent_message")

    # Clear the agent factory cache
    AgentFactory.clear_cache()

    return {"status": "All messages deleted"}


@app.get("/api/messages")
async def get_all_messages(request: Request):
    """
    Retrieve all messages across sessions.

    ---
    tags:
      - Messages
    responses:
      200:
        description: List of all messages across sessions
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                description: Unique ID of the message
              data_type:
                type: string
                description: Type of the message (e.g., session, step, plan, agent_message)
              session_id:
                type: string
                description: Session ID associated with the message
              user_id:
                type: string
                description: User ID associated with the message
              content:
                type: string
                description: Content of the message
              timestamp:
                type: string
                format: date-time
                description: Timestamp of the message
      400:
        description: Missing or invalid user information
    """
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    user_id = authenticated_user["user_principal_id"]
    if not user_id:
        track_event_if_configured(
            "UserIdNotFound", {"status_code": 400, "detail": "no user"}
        )
        raise HTTPException(status_code=400, detail="no user")

    # Initialize memory context
    kernel, memory_store = await initialize_runtime_and_context("", user_id)
    message_list = await memory_store.get_all_items()
    return message_list


@app.get("/api/agent-tools")
async def get_agent_tools():
    """
    Retrieve all available agent tools.

    ---
    tags:
      - Agent Tools
    responses:
      200:
        description: List of all available agent tools and their descriptions
        schema:
          type: array
          items:
            type: object
            properties:
              agent:
                type: string
                description: Name of the agent associated with the tool
              function:
                type: string
                description: Name of the tool function
              description:
                type: string
                description: Detailed description of what the tool does
              arguments:
                type: string
                description: Arguments required by the tool function
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
            },
            {
                "agent": "procurement",
                "function": "create_procurement_agent",
                "description": "Creates a procurement agent for purchasing and vendor tasks",
                "arguments": "session_id, user_id, temperature (optional)"
            },
            {
                "agent": "tech_support", 
                "function": "create_tech_support_agent",
                "description": "Creates a technical support agent for IT support tasks",
                "arguments": "session_id, user_id, temperature (optional)"
            },
            {
                "agent": "generic",
                "function": "create_generic_agent",
                "description": "Creates a generic agent for general purpose tasks",
                "arguments": "session_id, user_id, temperature (optional)"
            },
            {
                "agent": "planner",
                "function": "create_planner_agent", 
                "description": "Creates a planner agent for task planning and coordination",
                "arguments": "session_id, user_id, temperature (optional)"
            }
        ]
        
        return available_agents
    except Exception as e:
        logger.error(f"Error getting agent tools: {e}")
        return []


# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_kernel:app", host="0.0.0.0", port=8000)
