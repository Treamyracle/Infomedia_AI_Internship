# agent_service/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .core_agent import DomiAgent

app = FastAPI(title="Infomedia Agent Service (Brain)")

# Inisialisasi Agent saat startup
# Agar model tidak diload berulang kali setiap request
agent = None

@app.on_event("startup")
def startup_event():
    global agent
    try:
        agent = DomiAgent()
        print("✅ DomiAgent initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Agent: {e}")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    debug: dict

@app.get("/health")
def health_check():
    if agent:
        return {"status": "healthy", "service": "agent-service"}
    return {"status": "unhealthy", "reason": "agent not initialized"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    result = agent.chat(req.message)
    
    return ChatResponse(
        reply=result["reply"],
        debug=result["debug_info"]
    )