import os
import requests
import asyncio
from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner
from .tools import WalletTools, DATABASE_USER

class DomiAgent:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.guardrail_url = os.getenv("GUARDRAIL_SERVICE_URL", "http://guardrail-service:80/clean")

        if not self.api_key:
            print("WARNING: GOOGLE_API_KEY not found.")

        # 1. Init Tools
        self.tools_instance = WalletTools()
        self.my_tools = [
            self.tools_instance.ganti_password,
            self.tools_instance.request_kartu_fisik,
            self.tools_instance.withdraw_ke_bank
        ]

        # 2. Define Agent
        self.system_prompt = """
        Kamu adalah 'Domi', AI Customer Service E-Wallet.
        PROTOKOL KEAMANAN:
        1. User data sudah disensor menjadi tag seperti [REDACTED_NIK].
        2. GUNAKAN TAG TERSEBUT APA ADANYA saat memanggil tools.
        3. Jika Tool return GAGAL, tolak permintaan dengan sopan.
        """

        # Perbaikan: Langsung masukkan string nama model
        self.adk_agent = Agent(
            model='gemini-2.0-flash-exp', # Pastikan nama model valid
            name='domi_agent',
            instruction=self.system_prompt,
            tools=self.my_tools
        )

        # 3. Setup Runner
        self.runner = InMemoryRunner(
            agent=self.adk_agent,
            app_name="infomedia_wallet_app"
        )
        
        self.session_id = "global_session_v1"
        self.session_ready = False

    async def ensure_session(self):
        if not self.session_ready:
            # InMemoryRunner biasanya tidak butuh create_session manual yang rumit,
            # tapi kita inisialisasi state jika perlu.
            # Untuk versi ADK terbaru, runner.run() seringkali sudah menangani sesi.
            self.session_ready = True

    def call_guardrail(self, text: str):
        try:
            response = requests.post(self.guardrail_url, json={"text": text}, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"cleaned_text": text, "vault": {}, "entities": [], "performance": {}}
        except Exception:
            return {"cleaned_text": text, "vault": {}, "entities": [], "performance": {}}

    async def chat(self, user_message: str):
        # 1. Guardrail
        guard_data = self.call_guardrail(user_message)
        cleaned_text = guard_data.get("cleaned_text", user_message)
        session_vault = guard_data.get("vault", {})

        # 2. Inject Context
        self.tools_instance.set_context(session_vault)

        # 3. ADK Execution
        reply_text = "Maaf, terjadi kesalahan sistem."
        try:
            # Runner eksekusi
            result = await self.runner.run(
                session_id=self.session_id,
                input=cleaned_text
            )
            # Ambil teks jawaban (sesuaikan dengan return object ADK versi Anda)
            # Jika result adalah string:
            if isinstance(result, str):
                reply_text = result
            # Jika result punya atribut text/content:
            elif hasattr(result, 'text'):
                reply_text = result.text
            elif hasattr(result, 'content'):
                reply_text = result.content
            else:
                reply_text = str(result)
            
        except Exception as e:
            reply_text = f"Error ADK: {str(e)}"

        # 4. Return Data
        return {
            "reply": reply_text,
            "debug_info": {
                "original": user_message,
                "final_clean": cleaned_text,
                "session_data": session_vault,
                "entities": guard_data.get("entities", []),
                "performance": guard_data.get("performance", {}),
                "database": DATABASE_USER
            }
        }