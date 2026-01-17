import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .core_agent import DomiAgent

app = FastAPI(title="Infomedia Agent Service (Brain)")

base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- INITIALIZATION ---
agent = None

@app.on_event("startup")
def startup_event():
    global agent
    try:
        agent = DomiAgent()
        print("✅ DomiAgent initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Agent: {e}")

# --- MODELS ---
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    debug: dict

# --- ROUTES ---
@app.get("/")
async def read_index():
    """Route untuk melayani UI index.html"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "UI file not found. Please check agent_service/app/static/index.html"}

@app.get("/health")
def health_check():
    if agent:
        return {"status": "healthy", "service": "agent-service"}
    return {"status": "unhealthy", "reason": "agent not initialized"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    # PERUBAHAN DI SINI: Tambahkan 'await'
    result = await agent.chat(req.message)
    
    return ChatResponse(
        reply=result["reply"],
        debug=result["debug_info"]
    )