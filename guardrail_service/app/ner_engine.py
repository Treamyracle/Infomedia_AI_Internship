import os
from transformers import pipeline

class NEREngine:
    """
    Singleton wrapper for the Named Entity Recognition (NER) model.
    
    This class ensures the heavy BERT model is loaded only once in memory
    (Singleton Pattern) and provides a simplified interface for inference.
    """
    _instance = None

    def __new__(cls):
        """
        Singleton implementation to prevent multiple model instances.
        """
        if cls._instance is None:
            cls._instance = super(NEREngine, cls).__new__(cls)
            # Fetch model path from env or default to the fine-tuned IndoBERT
            cls._instance.model_name = os.getenv("MODEL_NAME", "treamyracle/indobert-ner-pii-guardrail")
            cls._instance.nlp = None
        return cls._instance

    def load_model(self):
        """
        Loads the HuggingFace NER pipeline into memory.
        
        Configured to run on CPU (device=-1) by default.
        """
        if self.nlp is None:
            print(f"📦 Loading NER Model: {self.model_name}...")
            try:
                # device=-1 for CPU, change to 0 for GPU support
                self.nlp = pipeline(
                    "ner", 
                    model=self.model_name, 
                    tokenizer=self.model_name, 
                    aggregation_strategy="simple", # Merges sub-tokens into words
                    device=-1 
                )
                print("✅ NER Model loaded successfully.")
            except Exception as e:
                print(f"❌ Failed to load NER Model: {e}")
                raise e

    def predict(self, text: str):
        """
        Performs NER inference on the provided text.
        
        Ensures the model is loaded (Lazy Loading) before predicting.
        """
        if not self.nlp:
            self.load_model()
        return self.nlp(text)