import re

PATTERNS = {
    r'\b\d{16}\b': '[REDACTED_NIK]',
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}': '[REDACTED_EMAIL]',
    r'(\+62|62|0)8[1-9][0-9]{6,11}': '[REDACTED_PHONE]',
    r'\b\d{2}-\d{2}-\d{4}\b': '[REDACTED_BIRTHDATE]', 
    r'\b\d{10,12}\b': '[REDACTED_BANK_NUM]' 
}

def process_regex(text: str, session_map: dict):
    for pattern, tag in PATTERNS.items():
        for match in re.finditer(pattern, text):
            original = match.group(0)
            # Skip jika Bank Num mirip HP
            if tag == '[REDACTED_BANK_NUM]' and (original.startswith("08") or original.startswith("62")):
                continue
            
            session_map[tag] = original
            text = text.replace(original, tag)
    return text, session_map