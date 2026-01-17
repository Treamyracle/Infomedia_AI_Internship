import os
from transformers import AutoTokenizer, AutoModelForTokenClassification

model_name = "treamyracle/indobert-ner-pii-guardrail"
save_directory = "./model_cache"

print(f"Sedang mendownload model: {model_name}...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)

tokenizer.save_pretrained(save_directory)
model.save_pretrained(save_directory)

print("✅ Model berhasil didownload dan disimpan!")