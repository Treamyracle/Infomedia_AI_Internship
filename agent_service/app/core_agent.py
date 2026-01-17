import os
import requests
import asyncio
from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types 
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
        4. Jika Tool return BERHASIL, sampaikan hasilnya ke user.
        5. JANGAN PERNAH MENEBak atau MENGISI DATA YANG DISENSOR.
        6. JIKA DATA TIDAK LENGKAP, tolak permintaan dengan sopan.
        7. JANGAN MEMBERIKAN INFORMASI SENSITIF APAPUN KEPADA USER. 
        """

        self.adk_agent = Agent(
            model='gemini-2.5-flash',
            name='domi_agent',
            instruction=self.system_prompt,
            tools=self.my_tools
        )

        # 3. Setup Runner
        self.app_name = "infomedia_wallet_app" 
        self.runner = InMemoryRunner(
            agent=self.adk_agent,
            app_name=self.app_name
        )
        
        self.session_id = "global_session_v1"
        self.user_id = "user_demo" 
        self.session_ready = False

    async def ensure_session(self):
        """Membuat session di dalam Memory Runner jika belum ada"""
        if not self.session_ready:
            # Cek apakah session sudah ada sebelumnya (untuk menghindari error Duplicate)
            try:
                await self.runner.session_service.create_session(
                    app_name=self.app_name, 
                    session_id=self.session_id,
                    user_id=self.user_id
                )
                print(f"✅ Session Created: {self.session_id}")
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower():
                    print(f"ℹ️ Session already exists: {self.session_id}")
                else:
                    print(f"⚠️ Session creation WARNING: {error_msg}")
            
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
        # 1. Guardrail Process
        guard_data = self.call_guardrail(user_message)
        cleaned_text = guard_data.get("cleaned_text", user_message)
        session_vault = guard_data.get("vault", {})

        # 2. Inject Context
        self.tools_instance.set_context(session_vault)

        # 3. ADK Execution
        reply_text = ""
        try:
            await self.ensure_session()
            
            msg_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=cleaned_text)]
            )

            # [DEBUG] Print sebelum run
            print(f"🚀 Running Agent... Session: {self.session_id}, App: {self.app_name}")

            async for event in self.runner.run_async(
                session_id=self.session_id,
                user_id=self.user_id,
                new_message=msg_content
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            reply_text += part.text
            
            if not reply_text:
                reply_text = "Maaf, tidak ada respon dari Agent (Empty Response)."

        except Exception as e:
            reply_text = f"Error ADK: {str(e)}"
            import traceback
            traceback.print_exc()

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