import sys
import os
import asyncio
import logging
import uuid
from datetime import datetime
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
    selected_agents: Optional[List[str]] = None  # List of selected agent expertise types

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

# Try Azure OpenAI import
try:
    from openai import AzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False

# Try Directus integration import
try:
    from directus_integration import directus_manager
    DIRECTUS_AVAILABLE = True
except ImportError:
    DIRECTUS_AVAILABLE = False
    print("Warning: Directus integration not available")

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

async def generate_ai_response(agent_type: str, user_query: str) -> str:
    """Generate AI response for specific agent type"""
    
    # Force enable debug logging for OpenAI
    logger.info(f"=== AI Response Generation Start ===")
    logger.info(f"Agent Type: {agent_type}")
    logger.info(f"User Query: {user_query}")
    logger.info(f"AZURE_OPENAI_AVAILABLE: {AZURE_OPENAI_AVAILABLE}")
    
    # Check environment variables
    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai_api_key = os.getenv("AZURE_OPENAI_API_KEY") 
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    
    logger.info(f"Environment Check:")
    logger.info(f"- Endpoint: {openai_endpoint}")
    logger.info(f"- API Key: {'***' + openai_api_key[-10:] if openai_api_key else 'MISSING'}")
    logger.info(f"- Deployment: {deployment_name}")
    
    # Force try Azure OpenAI even if flag is False
    try:
        if not openai_endpoint or not openai_api_key:
            logger.error("Missing OpenAI credentials - using fallback")
            raise Exception("Missing OpenAI credentials")
            
        logger.info("Creating Azure OpenAI client...")
        client = AzureOpenAI(
            azure_endpoint=openai_endpoint,
            api_key=openai_api_key,
            api_version="2024-08-01-preview"
        )
        logger.info("Azure OpenAI client created successfully")
        
        # Use configurable agent prompts
        agent_prompt = format_agent_prompt(agent_type, user_query)
        
        # Get agent configuration for advanced settings
        agent_config = get_agent_config(agent_type)
        
        # Use model override if specified
        model_name = agent_config.get("model_override") or deployment_name
        temperature = agent_config.get("temperature", 0.7)
        max_tokens = agent_config.get("max_tokens", 800)
        
        logger.info(f"Using model: {model_name}, temp: {temperature}, max_tokens: {max_tokens}")
        
        logger.info("Calling Azure OpenAI API...")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": agent_prompt},
                {"role": "user", "content": f"Scenario: {user_query}"}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        ai_result = response.choices[0].message.content.strip()
        logger.info(f"Azure OpenAI SUCCESS! Response length: {len(ai_result)}")
        logger.info(f"Response preview: {ai_result[:100]}...")
        return ai_result
        
    except Exception as e:
        logger.error(f"Azure OpenAI FAILED: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Full error: {str(e)}")
        
        # Return a clear fallback that shows we're using fallback
        return f"""🤖 **{agent_type.upper()} AI Analyse**

**Scenario:** {user_query}

⚠️ **AI Service Tijdelijk Niet Beschikbaar**

Voor dit scenario '{user_query}' zou normaal een gedetailleerde {agent_type} analyse verschijnen met:
- Specifieke aanbevelingen voor jouw situatie
- Concrete implementatie stappen  
- Meetbare KPIs en success criteria

**Tijdelijke fallback actief** - herstart de analyse voor volledige AI-powered inzichten.

**Debug info:** {str(e)[:100]}"""

class Config:
    FRONTEND_SITE_NAME = ""

# Set up logger
logger = logging.getLogger(__name__)

# Agent configuration system - can be extended with Directus CMS
AGENT_CONFIGS = {
    "hr": {
        "name": "HR Specialist",
        "prompt": "Je bent een ervaren HR strategist. Voor scenario '{query}' geef concrete HR adviezen over talent management, organisatie design, en implementatie. Geen templates - specifieke acties.",
        "focus": ["talent management", "organisatie design", "change management", "performance KPIs"],
        "instructions": "Focus op praktische implementatie en menselijke aspecten",
        "system_prompt": "Je bent een expert HR adviseur met 15+ jaar ervaring",
        "capabilities": ["talent_analysis", "org_design", "change_management"],
        "response_format": "markdown",
        "language": "nl",
        "temperature": 0.7,
        "max_tokens": 1500
    },
    "marketing": {
        "name": "Marketing Expert", 
        "prompt": "Je bent een senior marketing strategist. Voor scenario '{query}' geef concrete marketing adviezen over doelgroep, kanalen, en campagnes. Geen templates - specifieke tactieken.",
        "focus": ["doelgroep segmentatie", "channel strategy", "campagne development", "ROI metrics"],
        "instructions": "Richt je op meetbare resultaten en data-driven aanpak",
        "system_prompt": "Je bent een ervaren marketing strategist met focus op ROI",
        "capabilities": ["market_analysis", "campaign_planning", "roi_optimization"],
        "response_format": "markdown",
        "language": "nl",
        "temperature": 0.7,
        "max_tokens": 1500
    },
    "product": {
        "name": "Product Specialist",
        "prompt": "Je bent een product strategy expert. Voor scenario '{query}' geef concrete product adviezen over features, UX, en roadmap. Geen templates - specifieke product beslissingen.",
        "focus": ["product features", "user experience", "technical feasibility", "product metrics"],
        "instructions": "Balanceer gebruikersbehoeften met technische realiteit",
        "system_prompt": "Je bent een product manager met sterke UX en tech achtergrond",
        "capabilities": ["user_research", "feature_planning", "roadmap_development"],
        "response_format": "markdown",
        "language": "nl",
        "temperature": 0.6,
        "max_tokens": 1500
    },
    "procurement": {
        "name": "Procurement Agent",
        "prompt": "Je bent een procurement strategist. Voor scenario '{query}' geef concrete sourcing adviezen over leveranciers, kosten, en risico's. Geen templates - specifieke sourcing acties.",
        "focus": ["vendor management", "cost optimization", "risk mitigation", "contract strategy"],
        "instructions": "Focus op kostenbesparingen en risicominimalisatie",
        "system_prompt": "Je bent een senior inkoop specialist met sterke onderhandelingsvaardigheden",
        "capabilities": ["vendor_analysis", "cost_optimization", "risk_assessment"],
        "response_format": "markdown",
        "language": "nl",
        "temperature": 0.5,
        "max_tokens": 1500
    },
    "tech_support": {
        "name": "Tech Support Agent",
        "prompt": "Je bent een IT/tech strategist. Voor scenario '{query}' geef concrete technische adviezen over infrastructure, security, en implementatie. Geen templates - specifieke tech oplossingen.",
        "focus": ["infrastructure", "security", "scalability", "implementation"],
        "instructions": "Prioriteer security en schaalbaarheid in alle oplossingen",
        "system_prompt": "Je bent een senior IT architect met security expertise",
        "capabilities": ["infrastructure_design", "security_analysis", "scalability_planning"],
        "response_format": "markdown",
        "language": "nl",
        "temperature": 0.4,
        "max_tokens": 1500
    },
    "generic": {
        "name": "Business Strategist",
        "prompt": "Je bent een senior business strategist. Voor scenario '{query}' geef concrete business adviezen over strategie, resources, en ROI. Geen templates - specifieke business acties.",
        "focus": ["strategic alignment", "resource planning", "business value", "implementation roadmap"],
        "instructions": "Koppel alle adviezen aan concrete business outcomes",
        "system_prompt": "Je bent een ervaren business consultant met brede expertise",
        "capabilities": ["strategy_development", "business_analysis", "implementation_planning"],
        "response_format": "markdown",
        "language": "nl",
        "temperature": 0.7,
        "max_tokens": 1500
    },
    "planner": {
        "name": "Strategic Planner",
        "prompt": "Je bent een strategische planner. Voor scenario '{query}' geef concrete planning adviezen over tijdlijnen, mijlpalen, en resources. Geen templates - specifieke planning acties.",
        "focus": ["timeline planning", "milestone definition", "resource allocation", "risk planning"],
        "instructions": "Maak realistische planningen met buffer voor onverwachte zaken",
        "system_prompt": "Je bent een ervaren project manager met strategische focus",
        "capabilities": ["project_planning", "resource_management", "risk_planning"],
        "response_format": "markdown", 
        "language": "nl",
        "temperature": 0.6,
        "max_tokens": 1500
    }
}

def get_agent_config(agent_type: str) -> dict:
    """Get agent configuration - loads from Directus CMS if available, falls back to local configs"""
    if DIRECTUS_AVAILABLE and directus_manager.is_enabled():
        try:
            directus_configs = directus_manager.get_agent_configs_sync()
            if directus_configs and agent_type in directus_configs:
                return directus_configs[agent_type]
        except Exception as e:
            logger.warning(f"Failed to load from Directus: {e}")
    
    return AGENT_CONFIGS.get(agent_type, AGENT_CONFIGS["generic"])

def format_agent_prompt(agent_type: str, user_query: str) -> str:
    """Format agent prompt with query - customizable per agent with enhanced features"""
    config = get_agent_config(agent_type)
    
    # Start with system prompt if available
    system_part = config.get("system_prompt", "")
    if system_part:
        system_part += "\n\n"
    
    # Add main prompt
    main_prompt = config["prompt"].format(query=user_query)
    
    # Add instructions if available
    instructions = config.get("instructions", "")
    if instructions:
        main_prompt += f"\n\nSpecifieke instructies: {instructions}"
    
    # Add capabilities context
    capabilities = config.get("capabilities", [])
    if capabilities:
        main_prompt += f"\n\nJe hebt toegang tot deze capabilities: {', '.join(capabilities)}"
    
    # Add response format guidance
    response_format = config.get("response_format", "markdown")
    if response_format == "markdown":
        main_prompt += "\n\nFormatteer je antwoord in duidelijke Markdown met headers en bullet points."
    elif response_format == "json":
        main_prompt += "\n\nGeef je antwoord terug als gestructureerd JSON object."
    
    # Add language preference
    language = config.get("language", "nl")
    if language != "nl":
        lang_names = {"en": "English", "fr": "French", "de": "German"}
        main_prompt += f"\n\nAntwoord in het {lang_names.get(language, language)}."
    
    return system_part + main_prompt

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
    """Root endpoint with comprehensive API information."""
    return {
        "message": "AI Agent GOV API is running", 
        "status": "healthy", 
        "version": "2.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health", 
            "specialists": "/api/agent-tools",
            "input_task": "/api/input_task",
            "plans": "/api/plans",
            "messages": "/api/messages"
        },
        "docs": "/docs"
    }


@app.get("/api/agent-configs")
async def get_agent_configs():
    """Get all agent configurations - integrates with Directus CMS when available"""
    if DIRECTUS_AVAILABLE and directus_manager.is_enabled():
        try:
            directus_configs = directus_manager.get_agent_configs_sync()  # Use sync version
            if directus_configs:
                return {
                    "agents": directus_configs,
                    "source": "directus_cms", 
                    "count": len(directus_configs)
                }
        except Exception as e:
            logger.warning(f"Failed to load from Directus, using local configs: {e}")
    
    return {
        "agents": AGENT_CONFIGS,
        "source": "local_config",
        "count": len(AGENT_CONFIGS)
    }

@app.put("/api/agent-configs/{agent_type}")
async def update_agent_config(agent_type: str, config: dict):
    """Update agent configuration - syncs with Directus CMS when available"""
    # Validate required fields
    if "name" not in config or "prompt" not in config:
        raise HTTPException(status_code=400, detail="Missing required fields: name, prompt")
    
    # Update local config first
    if agent_type in AGENT_CONFIGS:
        AGENT_CONFIGS[agent_type].update(config)
        
        # Try to sync with Directus
        if DIRECTUS_AVAILABLE and directus_manager.is_enabled():
            try:
                success = await directus_manager.update_agent_config(agent_type, config)
                if success:
                    return {
                        "message": f"Agent {agent_type} configuration updated in both local and Directus",
                        "agent": AGENT_CONFIGS[agent_type],
                        "synced_to_directus": True
                    }
                else:
                    return {
                        "message": f"Agent {agent_type} configuration updated locally (Directus sync failed)",
                        "agent": AGENT_CONFIGS[agent_type],
                        "synced_to_directus": False
                    }
            except Exception as e:
                logger.warning(f"Failed to sync to Directus: {e}")
                return {
                    "message": f"Agent {agent_type} configuration updated locally only",
                    "agent": AGENT_CONFIGS[agent_type],
                    "synced_to_directus": False
                }
        
        return {
            "message": f"Agent {agent_type} configuration updated",
            "agent": AGENT_CONFIGS[agent_type],
            "directus_available": DIRECTUS_AVAILABLE
        }
    else:
        raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found")

@app.get("/api/directus/status")
async def get_directus_status():
    """Get Directus CMS integration status"""
    if DIRECTUS_AVAILABLE:
        return {
            "directus_available": True,
            "directus_enabled": directus_manager.is_enabled(),
            "directus_url": directus_manager.base_url if directus_manager.is_enabled() else None,
            "collection": directus_manager.collection
        }
    else:
        return {
            "directus_available": False,
            "message": "Directus integration module not available"
        }

@app.get("/api/directus/schema")
async def get_directus_schema():
    """Get recommended Directus collection schema for AI agents"""
    if DIRECTUS_AVAILABLE:
        return directus_manager.get_collection_schema()
    else:
        raise HTTPException(status_code=503, detail="Directus integration not available")

# Add endpoint to test agent prompts
@app.post("/api/test-agent-prompt")
async def test_agent_prompt(request: dict):
    """Test how an agent prompt would look with a specific query"""
    agent_type = request.get("agent_type", "generic")
    query = request.get("query", "Test scenario")
    
    # Get config from Directus or fallback to local
    config = get_agent_config(agent_type)
    if not config or config == AGENT_CONFIGS.get("generic"):
        # Check if this is a valid Directus agent type
        if DIRECTUS_AVAILABLE and directus_manager.is_enabled():
            directus_configs = directus_manager.get_agent_configs_sync()
            if directus_configs and agent_type not in directus_configs:
                available_agents = list(directus_configs.keys())
                raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found. Available: {available_agents}")
        else:
            if agent_type not in AGENT_CONFIGS:
                raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found")
    
    formatted_prompt = format_agent_prompt(agent_type, query)
    config = get_agent_config(agent_type)
    
    return {
        "agent_type": agent_type,
        "agent_name": config["name"],
        "query": query,
        "formatted_prompt": formatted_prompt,
        "focus_areas": config["focus"],
        "capabilities": config.get("capabilities", []),
        "instructions": config.get("instructions", ""),
        "response_format": config.get("response_format", "markdown"),
        "language": config.get("language", "nl"),
        "temperature": config.get("temperature", 0.7),
        "max_tokens": config.get("max_tokens", 1500)
    }

@app.post("/api/agent-features")
async def manage_agent_features(request: dict):
    """Manage advanced agent features via API"""
    agent_type = request.get("agent_type")
    action = request.get("action")  # "add_capability", "set_instruction", "update_format"
    
    if not agent_type or agent_type not in AGENT_CONFIGS:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    config = AGENT_CONFIGS[agent_type]
    
    if action == "add_capability":
        capability = request.get("capability")
        if capability and capability not in config.get("capabilities", []):
            if "capabilities" not in config:
                config["capabilities"] = []
            config["capabilities"].append(capability)
            
    elif action == "set_instruction":
        instruction = request.get("instruction", "")
        config["instructions"] = instruction
        
    elif action == "update_format":
        format_type = request.get("format", "markdown")
        if format_type in ["markdown", "html", "text", "json"]:
            config["response_format"] = format_type
            
    elif action == "set_language":
        language = request.get("language", "nl")
        if language in ["nl", "en", "fr", "de"]:
            config["language"] = language
    
    # Try to sync with Directus if available
    if DIRECTUS_AVAILABLE and directus_manager.is_enabled():
        try:
            await directus_manager.update_agent_config(agent_type, config)
        except Exception as e:
            logger.warning(f"Failed to sync feature update to Directus: {e}")
    
    return {
        "message": f"Agent {agent_type} {action} completed",
        "updated_config": config
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint with AI service status"""
    return {
        "status": "healthy",
        "azure_openai_available": AZURE_OPENAI_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
        "agents_configured": len(AGENT_CONFIGS)
    }


@app.post("/api/input_task")
@app.post("/input_task")  # Legacy support for frontend compatibility
async def input_task_endpoint(input_task: InputTask, request: Request):
    """
    Receive the initial input task from the user.
    Returns a proper response structure that the frontend expects.
    """
    
    try:
        # Get all available agents from agent-tools endpoint
        available_agents_data = [
            {"agent": "hr", "name": "HR Specialist", "expertise": "hr"},
            {"agent": "marketing", "name": "Marketing Expert", "expertise": "marketing"},
            {"agent": "product", "name": "Product Specialist", "expertise": "product"},
            {"agent": "procurement", "name": "Procurement Agent", "expertise": "procurement"},
            {"agent": "tech_support", "name": "Tech Support Agent", "expertise": "tech_support"},
            {"agent": "generic", "name": "Generic Agent", "expertise": "generic"},
            {"agent": "planner", "name": "Planner Agent", "expertise": "planner"}
        ]
        
        # Filter agents based on selected_agents if provided
        if input_task.selected_agents:
            available_agents_data = [
                agent for agent in available_agents_data 
                if agent["expertise"] in input_task.selected_agents
            ]
        
        # Generate AI responses for selected agents only
        agent_responses = []
        for agent_data in available_agents_data:
            try:
                ai_response = await generate_ai_response(
                    agent_data["expertise"], 
                    input_task.description
                )
                
                agent_responses.append({
                    "agent_name": agent_data["name"],
                    "agent_expertise": agent_data["expertise"],
                    "response": ai_response
                })
                
            except Exception as agent_error:
                # Enhanced fallback for individual agent failures with context
                expertise_context = {
                    "hr": f"📊 Voor '{input_task.description}' - kritieke HR overwegingen: talent behoeften, organisatie impact, change management. Specifieke skills gap analyse nodig.",
                    "marketing": f"📢 Voor '{input_task.description}' - kern marketing vragen: doelgroep identificatie, positioning strategie, kanaal effectiviteit. Markt research aanbevolen.",
                    "product": f"🚀 Voor '{input_task.description}' - product focus punten: user needs analysis, technical feasibility, market fit assessment. User research starten.",
                    "procurement": f"🛒 Voor '{input_task.description}' - sourcing prioriteiten: vendor landscape, cost analysis, risk assessment. Supplier evaluation nodig.",
                    "tech_support": f"⚙️ Voor '{input_task.description}' - technische aspecten: infrastructure requirements, security overwegingen, scalability planning. Technical assessment starten.",
                    "generic": f"💼 Voor '{input_task.description}' - strategische focus: business alignment, resource planning, ROI assessment. Strategic review aanbevolen.",
                    "planner": f"📋 Voor '{input_task.description}' - planning prioriteiten: milestone definitie, resource allocatie, risk management. Project planning opstarten."
                }
                
                context_response = expertise_context.get(agent_data["expertise"], 
                    f"Analyse voor '{input_task.description}' - context-specifieke inzichten worden voorbereid.")
                
                agent_responses.append({
                    "agent_name": agent_data["name"],
                    "agent_expertise": agent_data["expertise"],
                    "response": f"{context_response}\n\n⚠️ AI analyse tijdelijk niet beschikbaar - herstart voor volledige strategische inzichten."
                })
                logger.warning(f"Agent {agent_data['name']} response failed: {agent_error}")
        
        # Return enhanced response structure
        return {
            "status": "success",
            "session_id": input_task.session_id,
            "agent_responses": agent_responses,
            "message": "AI analyse voltooid - strategische inzichten van alle specialisten"
        }
        
    except Exception as e:
        logger.error(f"Input task processing failed: {e}")
        # Return basic error response
        return {
            "status": "error", 
            "session_id": input_task.session_id,
            "agent_responses": [],
            "message": f"Er is een probleem opgetreden: {str(e)}"
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
@app.get("/specialists")  # Legacy support for frontend compatibility  
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
        # Haal agents uit Directus
        if DIRECTUS_AVAILABLE and directus_manager.is_enabled():
            directus_configs = directus_manager.get_agent_configs_sync()
            if directus_configs:
                # Maak een visueel en functioneel agent tools object
                available_agents = []
                for agent_type, config in directus_configs.items():
                    available_agents.append({
                        "agent": agent_type,
                        "function": f"create_{agent_type}_agent",
                        "description": config.get("instructions", config.get("prompt", config.get("name", "AI Agent"))),
                        "arguments": "session_id, user_id, temperature (optional)",
                        "name": config.get("name", agent_type),
                        "focus": config.get("focus", []),
                        "system_prompt": config.get("system_prompt", ""),
                        "example_responses": config.get("example_responses", []),
                        "capabilities": config.get("capabilities", []),
                        "response_format": config.get("response_format", "markdown"),
                        "language": config.get("language", "nl"),
                        "temperature": config.get("temperature", 0.7),
                        "max_tokens": config.get("max_tokens", 1500),
                        "model_override": config.get("model_override", ""),
                        "custom_features": config.get("custom_features", {})
                    })
                return available_agents
        # fallback: geen directus, return lege lijst
        return []
    except Exception as e:
        logger.error(f"Error getting agent tools: {e}")
        return []


# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_kernel:app", host="0.0.0.0", port=8000)
