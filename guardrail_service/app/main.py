# guardrail_service/app/main.py
import re
import time
import os
import psutil
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from .ner_engine import NEREngine
from .regex_engine import RegexEngine

app = FastAPI(title="Infomedia Guardrail Service (Security)")

ner_engine = NEREngine()
regex_engine = RegexEngine()

@app.on_event("startup")
def startup_event():
    ner_engine.load_model()

class GuardrailRequest(BaseModel):
    text: str

class GuardrailResponse(BaseModel):
    original_text: str
    cleaned_text: str
    vault: dict
    entities: List[Dict[str, Any]] = []
    performance: Dict[str, Any] = {}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/clean", response_model=GuardrailResponse)
def clean_text(req: GuardrailRequest):
    start_time = time.time()
    text = req.text
    vault = {}
    detected_entities = []

    # --- PHASE 1: REGEX MASKING ---
    patterns = regex_engine.patterns
    for pattern, tag_label in patterns.items():
        matches = list(re.finditer(pattern, text))
        for match in reversed(matches):
            original = match.group(0)
            if tag_label == '[REDACTED_BANK_NUM]' and (original.startswith("08") or original.startswith("62")):
                continue

            # Simpan ke Vault & List Entities
            vault[tag_label] = original
            detected_entities.append({
                "text": original,
                "label": tag_label.replace("[REDACTED_", "").replace("]", ""),
                "source": "REGEX"
            })
            
            # Masking
            start, end = match.span()
            text = text[:start] + tag_label + text[end:]

    # --- PHASE 2: NER MASKING ---
    try:
        ner_results = ner_engine.predict(text)
        
        # Cek zona terlarang (yg sudah di-mask regex)
        forbidden_zones = []
        for match in re.finditer(r'\[REDACTED_[A-Z]+\]', text):
            forbidden_zones.append((match.start(), match.end()))

        ner_results.sort(key=lambda x: x['start'], reverse=True)
        valid_labels = ['PERSON', 'ADDRESS', 'LOCATION', 'ORGANIZATION', 'NIK', 'EMAIL', 'PHONE', 'BIRTHDATE', 'BANK_NUM']
        
        for ent in ner_results:
            label = ent['entity_group']
            start, end = ent['start'], ent['end']
            
            is_conflict = False
            for f_start, f_end in forbidden_zones:
                if (start < f_end and end > f_start):
                    is_conflict = True; break
            
            if is_conflict: continue

            if label in valid_labels:
                real_word = text[start:end]
                tag = f"[REDACTED_{label}]"
                
                vault[tag] = real_word
                detected_entities.append({
                    "text": real_word,
                    "label": label,
                    "source": "NER Model"
                })
                
                text = text[:start] + tag + text[end:]
                
    except Exception as e:
        print(f"NER Error: {e}")

    # --- CALCULATE PERFORMANCE ---
    end_time = time.time()
    process = psutil.Process(os.getpid())
    perf_stats = {
        "latency_ms": round((end_time - start_time) * 1000, 2),
        "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
        "cpu_percent": process.cpu_percent(interval=0.2)
    }

    return GuardrailResponse(
        original_text=req.text,
        cleaned_text=text,
        vault=vault,
        entities=detected_entities,
        performance=perf_stats
    )