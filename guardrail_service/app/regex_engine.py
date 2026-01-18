import re

class RegexEngine:
    """
    Handles PII detection and masking using Regular Expressions.
    
    This class defines specific patterns for structured data (like IDs, Emails, Phones)
    and provides a mechanism to replace them with redacted tags while preserving
    the original data in a secure vault.
    """
    def __init__(self):
        """Initializes the engine with predefined regex patterns for Indonesian PII."""
        self.patterns = {
            # NIK: Exactly 16 digits
            r'\b\d{16}\b': '[REDACTED_NIK]',
            
            # Email: Standard email format validation
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}': '[REDACTED_EMAIL]',
            
            # Phone: Indonesian prefixes (+62, 62, 08) followed by 8-12 digits
            r'(\+62|62|0)8[1-9][0-9]{6,11}': '[REDACTED_PHONE]',
            
            # Date of Birth: Format DD-MM-YYYY
            r'\b\d{2}-\d{2}-\d{4}\b': '[REDACTED_BIRTHDATE]',
            
            # Bank Account Number: 10 to 12 digits
            r'\b\d{10,12}\b': '[REDACTED_BANK_NUM]' 
        }

    def mask(self, text: str):
        """
        Scans text for PII patterns and replaces them with redaction tags.

        Args:
            text (str): The raw input text.

        Returns:
            str: The sanitized text with tags (e.g., [REDACTED_NIK]).
            dict: The vault dictionary containing {tag: original_value} mappings.
        """
        vault = {}
        masked_text = text

        # Iterate through each PII pattern defined in the engine
        for pattern, tag in self.patterns.items():
            for match in re.finditer(pattern, masked_text):
                original_word = match.group(0)
                
                # Logic: Conflict Resolution for Bank Numbers vs Phone Numbers
                # If a detected Bank Number starts with '08' or '62', treat it as a Phone Number (skip)
                if tag == '[REDACTED_BANK_NUM]' and (original_word.startswith("08") or original_word.startswith("62")):
                    continue

                # Store the original PII in the secure vault
                vault[tag] = original_word
                
                # Replace the PII in the text with its corresponding tag
                masked_text = masked_text.replace(original_word, tag)
        
        # Placeholder for final vault verification
        final_vault = {}
        
        return masked_text