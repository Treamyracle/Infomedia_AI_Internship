import os
import requests
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import SafetySetting
from .tools import WalletTools

class DomiAgent:
    def __init__(self):
        # 1. Config
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        self.guardrail_url = os.getenv("GUARDRAIL_SERVICE_URL", "http://guardrail-service:80/clean")

        genai.configure(api_key=self.api_key)

        # 2. Tools Initialization
        self.tools_instance = WalletTools()
        self.my_tools = [
            self.tools_instance.ganti_password,
            self.tools_instance.request_kartu_fisik,
            self.tools_instance.withdraw_ke_bank
        ]

        # 3. System Prompt
        self.system_prompt = """
        Kamu adalah 'Domi', AI Customer Service E-Wallet Profesional.
        
        PROTOKOL KEAMANAN:
        1. User data sudah disensor (masking) menjadi tag seperti [REDACTED_NIK].
        2. GUNAKAN TAG TERSEBUT APA ADANYA saat memanggil tools. Jangan ubah/hapus tag.
        3. Jika Tool return "GAGAL", sampaikan penolakan dengan tegas dan sopan.
        4. Jika Tool return "BERHASIL", konfirmasi keberhasilan transaksi.
        """

        # 4. Model Setup
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-lite',
            tools=self.my_tools,
            system_instruction=self.system_prompt,
            safety_settings=[
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            ]
        )

    def call_guardrail(self, text: str):
        """
        Mengirim teks mentah ke Guardrail Service untuk dibersihkan.
        Return: (cleaned_text, session_map_vault)
        """
        try:
            response = requests.post(self.guardrail_url, json={"text": text}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data['cleaned_text'], data['vault']
            else:
                return text, {}
        except Exception as e:
            print(f"Guardrail Connection Error: {e}")
            return text, {}

    def chat(self, user_message: str):
        """
        Main Flow:
        1. Terima pesan user.
        2. Kirim ke Guardrail Service -> dapat Clean Text + Vault.
        3. Inject Vault ke Tools Instance.
        4. Kirim Clean Text ke Gemini.
        """
        
        # Step 1 & 2: Guardrail Processing
        cleaned_text, session_vault = self.call_guardrail(user_message)

        # Step 3: Inject Context (agar tools bisa baca data asli)
        self.tools_instance.set_context(session_vault)

        # Step 4: LLM Processing
        try:
            # Mulai chat baru (stateless per request untuk REST API)
            chat_session = self.model.start_chat(enable_automatic_function_calling=True)
            response = chat_session.send_message(cleaned_text)
            
            return {
                "reply": response.text if response.parts else "Maaf, tidak ada respon teks.",
                "debug_info": {
                    "original": user_message,
                    "cleaned": cleaned_text,
                    "vault_keys": list(session_vault.keys())
                }
            }
        except Exception as e:
            return {
                "reply": f"Terjadi kesalahan sistem: {str(e)}",
                "debug_info": {}
            }