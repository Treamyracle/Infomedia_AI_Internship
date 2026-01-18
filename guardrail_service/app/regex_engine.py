import re

class RegexEngine:
    def __init__(self):
        self.patterns = {
            # NIK: 16 digit angka
            r'\b\d{16}\b': '[REDACTED_NIK]',
            
            # Email: format standar email
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}': '[REDACTED_EMAIL]',
            
            # Phone: +62/62/08 diikuti 8-12 digit
            r'(\+62|62|0)8[1-9][0-9]{6,11}': '[REDACTED_PHONE]',
            
            # Tanggal Lahir: DD-MM-YYYY
            r'\b\d{2}-\d{2}-\d{4}\b': '[REDACTED_BIRTHDATE]',
            
            # Nomor Rekening: 10-12 digit
            r'\b\d{10,12}\b': '[REDACTED_BANK_NUM]' 
        }

    def mask(self, text: str):
        """
        Mengganti pattern regex dengan tag [REDACTED_...].
        Returns:
            masked_text (str): Teks yang sudah disensor regex.
            vault (dict): Dictionary {tag: original_value}.
        """
        vault = {}
        masked_text = text

        for pattern, tag in self.patterns.items():
            for match in re.finditer(pattern, masked_text):
                original_word = match.group(0)
                
                # Logic Khusus: Membedakan No Rekening vs No HP
                # Jika terdeteksi BANK_NUM tapi diawali 08/62, skip (kemungkinan itu HP)
                if tag == '[REDACTED_BANK_NUM]' and (original_word.startswith("08") or original_word.startswith("62")):
                    continue

                # Simpan ke Vault
                vault[tag] = original_word
                
                # Replace sederhana
                masked_text = masked_text.replace(original_word, tag)
        
        # Re-scan untuk mengisi vault dengan benar sesuai teks akhir
        final_vault = {}
        
        return masked_text