import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "guardrail-service"}

@app.post("/clean", response_model=GuardrailResponse)
def clean_text(req: GuardrailRequest):
    text = req.text
    vault = {}

    # --- PHASE 1: REGEX MASKING ---
    patterns = regex_engine.patterns
    for pattern, tag_label in patterns.items():
        matches = list(re.finditer(pattern, text))
        
        for match in reversed(matches):
            original = match.group(0)
            
            if tag_label == '[REDACTED_BANK_NUM]' and (original.startswith("08") or original.startswith("62")):
                continue

            # Masukkan ke Vault
            vault[tag_label] = original 
            
            # Ganti teks
            start, end = match.span()
            text = text[:start] + tag_label + text[end:]

    # --- PHASE 2: NER MASKING (Contextual) ---
    try:
        ner_results = ner_engine.predict(text)
        
        # Identifikasi yang sudah di-replace oleh regex
        forbidden_zones = []
        for match in re.finditer(r'\[REDACTED_[A-Z]+\]', text):
            forbidden_zones.append((match.start(), match.end()))

        # Sort entitas dari belakang ke depan untuk replacement aman
        ner_results.sort(key=lambda x: x['start'], reverse=True)
        
        valid_labels = ['PERSON', 'ADDRESS', 'LOCATION', 'ORGANIZATION']
        
        for ent in ner_results:
            label = ent['entity_group']
            start, end = ent['start'], ent['end']
            
            # Cek Konflik: Apakah entitas ini bertabrakan dengan tag Regex?
            is_conflict = False
            for f_start, f_end in forbidden_zones:
                # Jika overlap
                if (start < f_end and end > f_start):
                    is_conflict = True
                    break
            
            if is_conflict:
                continue

            if label in valid_labels:
                real_word = text[start:end]
                tag = f"[REDACTED_{label}]"
                
                # Simpan ke Vault
                vault[tag] = real_word
                
                # Replace Text
                text = text[:start] + tag + text[end:]
                
    except Exception as e:
        print(f"Warning: NER Error - {e}")
        # Jika NER gagal, minimal kita kembalikan hasil regex
        pass

    return GuardrailResponse(
        original_text=req.text,
        cleaned_text=text,
        vault=vault
    )