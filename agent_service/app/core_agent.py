import os
import requests
import asyncio
from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types 
from .tools import WalletTools, DATABASE_USER

class DomiAgent:
    """
    Main controller for the 'Domi' AI Agent.
    
    This class orchestrates the interaction between:
    1. The PII Guardrail Service (Security Layer).
    2. The Google ADK Agent (LLM Brain).
    3. The WalletTools (Transaction Execution).
    
    It ensures that sensitive user data is masked before reaching the LLM
    and restored securely when specific tools are executed.
    """

    def __init__(self):
        """Initializes the Agent, Tools, and ADK Runner configuration."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.guardrail_url = os.getenv("GUARDRAIL_SERVICE_URL", "http://guardrail-service:80/clean")

        if not self.api_key:
            print("WARNING: GOOGLE_API_KEY not found.")

        # 1. Initialize Tools
        # Tools are defined here to be passed to the LLM for function calling capability.
        self.tools_instance = WalletTools()
        self.my_tools = [
            self.tools_instance.ganti_password,
            self.tools_instance.request_kartu_fisik,
            self.tools_instance.withdraw_ke_bank
        ]

        # 2. Define Agent Configuration
        # System prompt enforces strict security protocols regarding redacted tags.
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

        # Initialize the Google ADK Agent with the specified Gemini model
        self.adk_agent = Agent(
            model='gemini-2.5-flash',
            name='domi_agent',
            instruction=self.system_prompt,
            tools=self.my_tools
        )

        # 3. Setup Execution Runner
        # InMemoryRunner maintains the conversation state/history.
        self.app_name = "infomedia_wallet_app" 
        self.runner = InMemoryRunner(
            agent=self.adk_agent,
            app_name=self.app_name
        )
        
        # Session Configuration
        self.session_id = "global_session_v1"
        self.user_id = "user_demo" 
        self.session_ready = False

    async def ensure_session(self):
        """
        Ensures a session exists in the ADK Runner.
        
        This is required before sending messages. It handles the creation
        of a new session and gracefully catches errors if the session
        already exists (common in persistent environments).
        """
        if not self.session_ready:
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
        """
        Sends raw text to the external Guardrail Service for PII masking.

        Args:
            text (str): The raw user input containing potential PII.

        Returns:
            dict: Response containing 'cleaned_text' and 'vault' (PII mapping).
                  Returns a fallback dict if the service is unreachable.
        """
        try:
            response = requests.post(self.guardrail_url, json={"text": text}, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"cleaned_text": text, "vault": {}, "entities": [], "performance": {}}
        except Exception:
            # Fail-safe: Return original text if guardrail is down (Log this in production)
            return {"cleaned_text": text, "vault": {}, "entities": [], "performance": {}}

    async def chat(self, user_message: str):
        """
        Main pipeline for processing user messages.

        Flow:
        1. Sanitize input via Guardrail (PII Masking).
        2. Inject PII context (Vault) into Tools for execution.
        3. Send sanitized text to LLM (Gemini) via ADK.
        4. Return response and debug information.
        """
        # 1. Guardrail Process
        # Masks sensitive data (e.g., NIK -> [REDACTED_NIK])
        guard_data = self.call_guardrail(user_message)
        cleaned_text = guard_data.get("cleaned_text", user_message)
        session_vault = guard_data.get("vault", {})

        # 2. Inject Context
        # securely passes the real data (vault) to the tools class
        # so functionality works without the LLM seeing the real data.
        self.tools_instance.set_context(session_vault)

        # 3. ADK Execution
        reply_text = ""
        try:
            await self.ensure_session()
            
            # Wrap the sanitized text in the ADK compatible content type
            msg_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=cleaned_text)]
            )

            # [DEBUG] Log execution start
            print(f"🚀 Running Agent... Session: {self.session_id}, App: {self.app_name}")

            # Run the agent asynchronously and collect the response stream
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
        # Returns both the reply and debug info for the frontend dashboard
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