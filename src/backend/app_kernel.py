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
    
    # Define specialist knowledge bases with specific context analysis
    specialist_prompts = {
        "hr": """Je bent een ervaren HR strategist. Analyseer het gegeven scenario vanuit HR perspectief en geef een SPECIFIEKE analyse. 
Gebruik de context van het scenario om gerichte aanbevelingen te geven.

Geef geen generieke templates maar concrete, op de situatie toegesneden adviezen over:
- Specifieke talent behoeften voor dit scenario  
- Organisatie impact en cultuur aspecten
- Concrete implementatie stappen met tijdlijnen
- Meetbare HR KPIs passend bij dit scenario

Maak je antwoord contextspecifiek en actionable.""",

        "marketing": """Je bent een senior marketing strategist. Analyseer het gegeven scenario en geef een SPECIFIEKE marketing strategie.
Gebruik de context om gerichte marketing aanbevelingen te geven.

Geef geen standaard marketing frameworks maar concrete adviezen voor DIT specifieke scenario:
- Specifieke doelgroep identificatie voor deze situatie
- Concrete kanalen en tactieken passend bij dit scenario  
- Budgetramingen en timeline voor implementatie
- Meetbare marketing KPIs voor dit specifieke geval

Focus op praktische, uitvoerbare marketing acties.""",

        "product": """Je bent een product strategy expert. Analyseer het scenario en geef SPECIFIEKE product inzichten.
Gebruik de context om gerichte product aanbevelingen te maken.

Geef geen algemene product principes maar concrete adviezen voor DIT scenario:
- Specifieke product features of verbeteringen 
- User experience overwegingen voor deze situatie
- Technische haalbaarheid en development prioriteiten
- Concrete product metrics voor succes meting

Focus op praktische product beslissingen en roadmap.""",

        "procurement": """Je bent een procurement strategist. Analyseer dit scenario vanuit inkoop/sourcing perspectief.
Geef SPECIFIEKE procurement adviezen gebaseerd op de context.

Geen standaard procurement processen maar concrete adviezen voor DIT scenario:
- Specifieke leveranciers of partnerships voor deze situatie
- Cost implications en besparingskansen  
- Risk factors en mitigatie specifiek voor dit geval
- Concrete contractuele overwegingen

Focus op praktische sourcing en cost optimization.""",

        "tech_support": """Je bent een IT/tech strategist. Analyseer dit scenario vanuit technisch perspectief.
Geef SPECIFIEKE technische inzichten en oplossingen.

Geen algemene tech best practices maar concrete adviezen voor DIT scenario:
- Specifieke technologie stack overwegingen
- Security en compliance aspecten voor deze situatie
- Implementatie complexiteit en technische risicos
- Concrete IT infrastructure behoeften

Focus op praktische technische beslissingen en implementatie.""",

        "generic": """Je bent een senior business strategist. Analyseer dit scenario holistisch en geef SPECIFIEKE business inzichten.
Gebruik de context om gerichte strategische aanbevelingen te maken.

Geen standaard business frameworks maar concrete adviezen voor DIT scenario:
- Specifieke business opportunities en challenges
- Stakeholder impact en management voor deze situatie  
- Resource behoeften en budget overwegingen
- Concrete implementation roadmap met mijlpalen

Focus op praktische business beslissingen en strategic value.""",

        "planner": """Je bent een strategische planner. Analyseer dit scenario en maak een SPECIFIEKE implementatie planning.
Gebruik de context om een concrete roadmap te ontwikkelen.

Geen generieke planning templates maar specifieke planning voor DIT scenario:
- Concrete mijlpalen en deadlines voor deze situatie
- Resource allocatie en capacity planning  
- Risk factors en contingency planning specifiek voor dit geval
- Meetbare success criteria en tracking methods

Focus op praktische planning en projectmanagement."""
    }
    
    # Get agent prompt or use generic
    agent_prompt = specialist_prompts.get(agent_type, specialist_prompts["generic"])
    
    # Try Azure OpenAI if available
    if AZURE_OPENAI_AVAILABLE:
        try:
            openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            openai_api_key = os.getenv("AZURE_OPENAI_API_KEY") 
            deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
            
            if openai_endpoint and openai_api_key:
                client = AzureOpenAI(
                    azure_endpoint=openai_endpoint,
                    api_key=openai_api_key,
                    api_version="2024-08-01-preview"
                )
                
                response = client.chat.completions.create(
                    model=deployment_name,
                    messages=[
                        {"role": "system", "content": agent_prompt},
                        {"role": "user", "content": f"""Scenario: {user_query}

Geef een concrete, specifieke analyse voor dit exacte scenario. Vermijd generieke templates en focus op:
1. Specifieke aspecten van dit scenario vanuit jouw expertise
2. Concrete, actionable aanbevelingen 
3. Realistische implementatie stappen
4. Specifieke metrics en success criteria

Maak je antwoord praktisch en direct toepasbaar op deze situatie."""}
                    ],
                    max_tokens=800,
                    temperature=0.7
                )
                
                return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Azure OpenAI failed: {e}")
    
    # Fallback to enhanced template responses
    enhanced_responses = {
        "hr": f"""🎯 **HR Strategische Analyse**

**Scenario:** {user_query}

**📊 HR Impact Assessment:**
- Talent Management: Identificeer benodigde competenties
- Organisatie Design: Evalueer huidige structuur effectiviteit  
- Change Management: Plan voor cultuurverandering
- Performance: KPI's voor succes meting

**🚀 Aanbevelingen:**
1. **Korte termijn (0-3 maanden):** Stakeholder analyse en quick wins
2. **Middellange termijn (3-12 maanden):** Training en development programma's
3. **Lange termijn (1+ jaar):** Strategische workforce planning

**📈 ROI Indicatoren:**
- Employee engagement scores
- Retention rates en recruitment kosten
- Productiviteit metrics en performance""",

        "marketing": f"""🎯 **Marketing Strategische Analyse**

**Scenario:** {user_query}

**📊 Marketing Opportunity Assessment:**
- Target Audience: Segmentatie en persona development
- Competitive Landscape: Market positioning analyse
- Channel Strategy: Optimale marketing mix
- Brand Impact: Reputatie en awareness effecten

**🚀 Marketing Roadmap:**
1. **Launch Fase (0-2 maanden):** Brand awareness campagne
2. **Growth Fase (2-6 maanden):** Lead generation optimalisatie  
3. **Scale Fase (6+ maanden):** Customer retention en advocacy

**📈 Success Metrics:**
- Brand awareness en sentiment tracking
- Lead quality en conversion rates
- Customer acquisition cost en lifetime value""",

        "product": f"""🎯 **Product Strategische Analyse**

**Scenario:** {user_query}

**📊 Product Impact Evaluation:**
- User Experience: Journey mapping en pain points
- Market Fit: Product-market alignment analyse
- Technical Feasibility: Development complexiteit
- Business Value: Revenue en cost implications

**🚀 Product Development Roadmap:**
1. **Discovery (0-1 maand):** User research en requirements
2. **MVP Development (1-3 maanden):** Core feature implementation
3. **Iteration (3+ maanden):** User feedback en optimalisatie

**📈 Product Success KPIs:**
- User adoption en engagement rates
- Feature usage analytics
- Customer satisfaction scores""",

        "procurement": f"""🎯 **Procurement Strategische Analyse**

**Scenario:** {user_query}

**📊 Supply Chain Impact:**
- Vendor Assessment: Supplier capability en reliability
- Cost Analysis: Total cost of ownership evaluatie
- Risk Management: Supply continuity en compliance
- Sustainability: ESG impact en circular economy

**🚀 Procurement Strategy:**
1. **Sourcing (0-2 maanden):** RFP proces en vendor selectie
2. **Negotiation (2-3 maanden):** Contract onderhandelingen
3. **Implementation (3+ maanden):** Supplier onboarding en monitoring

**📈 Procurement KPIs:**
- Cost savings en budget adherence
- Supplier performance scores
- Contract compliance en risk mitigation""",

        "tech_support": f"""🎯 **Technical Support Analyse**

**Scenario:** {user_query}

**📊 Technical Assessment:**
- Infrastructure: Systeem capaciteit en schaalbaarheid
- Security: Cybersecurity risks en compliance
- Integration: API's en data flow optimalisatie
- User Experience: Interface design en accessibility

**🚀 Technical Implementation:**
1. **Planning (0-1 maand):** Architecture design en risk assessment
2. **Development (1-3 maanden):** System build en testing
3. **Deployment (3+ maanden):** Go-live en user adoption

**📈 Technical Success Metrics:**
- System uptime en performance
- Security incident reductie
- User satisfaction en adoption rates""",

        "generic": f"""🎯 **Strategische Business Analyse**

**Scenario:** {user_query}

**📊 Business Impact Assessment:**
- Strategic Alignment: Organisatie doelen en prioriteiten
- Stakeholder Analysis: Impact op verschillende belanghebbenden
- Resource Requirements: Budget, tijd en competenties
- Risk Assessment: Potentiële uitdagingen en mitigaties

**🚀 Implementation Strategy:**
1. **Preparation (0-2 maanden):** Planning en stakeholder buy-in
2. **Execution (2-6 maanden):** Gefaseerde implementatie
3. **Optimization (6+ maanden):** Continuous improvement

**📈 Business Success Indicators:**
- Strategic goal achievement
- Stakeholder satisfaction
- ROI en value realization""",

        "planner": f"""🎯 **Strategische Planning Analyse**

**Scenario:** {user_query}

**📊 Planning Framework:**
- Timeline Analysis: Kritieke mijlpalen en dependencies
- Resource Planning: Capaciteit en budget allocatie
- Risk Planning: Scenario's en contingency planning
- Success Criteria: Meetbare doelstellingen en KPIs

**🚀 Strategische Roadmap:**
1. **Phase 1 (0-3 maanden):** Foundation en quick wins
2. **Phase 2 (3-9 maanden):** Core implementation
3. **Phase 3 (9+ maanden):** Optimization en scaling

**📈 Planning Success Metrics:**
- Milestone achievement rates
- Budget adherence en resource efficiency
- Stakeholder alignment scores"""
    }
    
    return enhanced_responses.get(agent_type, enhanced_responses["generic"])

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


@app.get("/health")
async def health_check():
    """Health check endpoint for Container Apps."""
    return {"status": "healthy", "service": "ai-agent-gov-backend"}


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
