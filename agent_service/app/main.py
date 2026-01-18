import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .core_agent import DomiAgent

# Initialize the main FastAPI application for the Agent Service
app = FastAPI(title="Infomedia Agent Service (Brain)")

# Configure static file paths for serving the Frontend UI
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")

# Mount the static directory to serve CSS/JS files if it exists
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- INITIALIZATION ---
# Global variable to hold the agent instance across requests
agent = None

@app.on_event("startup")
def startup_event():
    """
    Application Startup Handler.
    
    Initializes the DomiAgent (LLM + Tools) once when the server starts.
    This prevents re-initializing the model for every request.
    """
    global agent
    try:
        agent = DomiAgent()
        print("✅ DomiAgent initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Agent: {e}")

# --- MODELS ---
class ChatRequest(BaseModel):
    """Schema for incoming chat messages."""
    message: str

class ChatResponse(BaseModel):
    """Schema for agent responses, including debug metadata."""
    reply: str
    debug: dict

# --- ROUTES ---
@app.get("/")
async def read_index():
    """
    Root Endpoint.
    
    Serves the main 'index.html' UI for the DompetKu Agent demo.
    """
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "UI file not found. Please check agent_service/app/static/index.html"}

@app.get("/health")
def health_check():
    """
    Health Check Endpoint.
    
    Used by Kubernetes/Docker to verify if the service is up 
    and the Agent is successfully initialized.
    """
    if agent:
        return {"status": "healthy", "service": "agent-service"}
    return {"status": "unhealthy", "reason": "agent not initialized"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Main Chat Endpoint.
    
    Receives user input, processes it through the DomiAgent pipeline 
    (Guardrail -> Vault -> LLM -> Tools), and returns the response.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    # Asynchronously process the chat message
    result = await agent.chat(req.message)
    
    return ChatResponse(
        reply=result["reply"],
        debug=result["debug_info"]
    )