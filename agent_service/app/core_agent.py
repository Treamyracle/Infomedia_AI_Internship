# agent_service/app/core_agent.py
import os
import requests
import google.generativeai as genai
from .tools import WalletTools, DATABASE_USER # Import DATABASE_USER untuk dikirim ke frontend

class DomiAgent:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.guardrail_url = os.getenv("GUARDRAIL_SERVICE_URL", "http://guardrail-service:80/clean")

        genai.configure(api_key=self.api_key)
        self.tools_instance = WalletTools()
        self.my_tools = [
            self.tools_instance.ganti_password,
            self.tools_instance.request_kartu_fisik,
            self.tools_instance.withdraw_ke_bank
        ]

        self.system_prompt = """
        Kamu adalah 'Domi', AI Customer Service E-Wallet.
        Gunakan tag [REDACTED_...] apa adanya saat memanggil tools.
        Jika tool return GAGAL, tolak permintaan dengan sopan.
        """

        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
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
        try:
            response = requests.post(self.guardrail_url, json={"text": text}, timeout=10)
            if response.status_code == 200:
                return response.json() # Return full JSON object
            return {"cleaned_text": text, "vault": {}, "entities": [], "performance": {}}
        except Exception:
            return {"cleaned_text": text, "vault": {}, "entities": [], "performance": {}}

    def chat(self, user_message: str):
        # 1. Guardrail
        guard_data = self.call_guardrail(user_message)
        cleaned_text = guard_data.get("cleaned_text", user_message)
        session_vault = guard_data.get("vault", {})
        
        # 2. Inject Context
        self.tools_instance.set_context(session_vault)

        # 3. LLM
        try:
            chat_session = self.model.start_chat(enable_automatic_function_calling=True)
            response = chat_session.send_message(cleaned_text)
            reply_text = response.text if response.parts else "Maaf, tidak ada respon teks."
        except Exception as e:
            reply_text = f"Error System: {str(e)}"

        # 4. Construct Debug Info (Sesuai nama variabel di index.html)
        return {
            "reply": reply_text,
            "debug_info": {
                "original": user_message,
                "final_clean": cleaned_text,       # Matches index.html
                "session_data": session_vault,     # Matches index.html
                "entities": guard_data.get("entities", []),
                "performance": guard_data.get("performance", {}),
                "database": DATABASE_USER          # Kirim state DB real-time
            }
        }