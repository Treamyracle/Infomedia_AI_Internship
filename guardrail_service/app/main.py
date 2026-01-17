from fastapi import FastAPI
from pydantic import BaseModel
from .regex_engine import process_regex
from .ner_engine import load_model, process_ner

app = FastAPI(title="Guardrail Service")

class GuardRequest(BaseModel):
    message: str

@app.on_event("startup")
async def startup_event():
    load_model()

@app.post("/sanitize")
def sanitize(req: GuardRequest):
    text = req.message
    session_map = {}
    
    # 1. Lapis 1: Regex
    text, session_map = process_regex(text, session_map)
    
    # 2. Lapis 2: NER
    text, session_map = process_ner(text, session_map)
    
    return {
        "clean_text": text,
        "session_map": session_map
    }