import os
from transformers import pipeline

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_NAME = "treamyracle/indobert-ner-pii-guardrail"

# Load Model sekali saat startup
ner_pipeline = None

def load_model():
    global ner_pipeline
    print("Loading NER Model...")
    ner_pipeline = pipeline(
        "ner", 
        model=MODEL_NAME, 
        tokenizer=MODEL_NAME, 
        aggregation_strategy="simple",
        token=HF_TOKEN,
        device=-1 # CPU
    )
    print("NER Model Loaded!")

def process_ner(text: str, session_map: dict):
    if not ner_pipeline: return text, session_map
    
    results = ner_pipeline(text)
    
    # Sort reverse agar replace tidak merusak index
    results.sort(key=lambda x: x['start'], reverse=True)
    
    valid_labels = ['PERSON', 'ADDRESS', 'NIK', 'EMAIL', 'PHONE', 'BIRTHDATE', 'BANK_NUM']
    
    for item in results:
        label = item['entity_group']
        if label in valid_labels:
            # Cek jika sudah di-redact oleh Regex (Simple check)
            if "[REDACTED_" in text[item['start']:item['end']]:
                continue

            tag = f"[REDACTED_{label}]"
            original = text[item['start']:item['end']]
            session_map[tag] = original
            text = text[:item['start']] + tag + text[item['end']:]
            
    return text, session_map