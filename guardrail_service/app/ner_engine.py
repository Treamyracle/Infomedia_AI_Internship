import os
from transformers import pipeline

class NEREngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NEREngine, cls).__new__(cls)
            cls._instance.model_name = os.getenv("MODEL_NAME", "treamyracle/indobert-ner-pii-guardrail")
            cls._instance.nlp = None
        return cls._instance

    def load_model(self):
        if self.nlp is None:
            print(f"📦 Loading NER Model: {self.model_name}...")
            try:
                # device=-1 CPU, device=0 GPU
                self.nlp = pipeline(
                    "ner", 
                    model=self.model_name, 
                    tokenizer=self.model_name, 
                    aggregation_strategy="simple",
                    device=-1 
                )
                print("✅ NER Model loaded successfully.")
            except Exception as e:
                print(f"❌ Failed to load NER Model: {e}")
                raise e

    def predict(self, text: str):
        if not self.nlp:
            self.load_model()
        return self.nlp(text)