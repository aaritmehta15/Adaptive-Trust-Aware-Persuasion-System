"""
Voice Agent ΓÇö ADK Integration for ATLAS
Handles session lifecycle, model streaming, and cleanup.
"""
import os
import uuid
import logging

from google.adk import Runner
from google.adk.runners import LiveRequestQueue
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig          # Fix 1: correct import path
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = "ATLAS_System"
USER_ID = "atlas_user"


class VoiceAgent:
    def __init__(self):
        """Initialize the Voice Agent with ADK components."""
        # ΓöÇΓöÇ API Key check + routing (Fix 6) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        # ADK authenticates via GOOGLE_API_KEY.
        # If only GEMINI_API_KEY is set, bridge it here so ADK picks it up.
        gemini_key = os.getenv("GEMINI_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")

        if gemini_key and not google_key:
            os.environ["GOOGLE_API_KEY"] = gemini_key
            logger.info("Γ£ô Bridged GEMINI_API_KEY ΓåÆ GOOGLE_API_KEY for ADK")
        elif not gemini_key and not google_key:
            logger.error("Γ¥î Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set. Voice mode will fail.")
            print("Γ¥î Set GEMINI_API_KEY before starting the backend to use Voice Mode.")

        # ΓöÇΓöÇ Model (Fix 4: single source of truth via config.py) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        self.model_name = Config.ADK_VOICE_MODEL
        self.output_modality = "AUDIO"

        # ΓöÇΓöÇ Session Service ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        self.session_service = InMemorySessionService()

        # ΓöÇΓöÇ Agent (Fix 3: pass model= in constructor, no hasattr dance) ΓöÇΓöÇ
        self.agent = Agent(
            name="atlas_voice_agent",
            description="ATLAS Voice Agent for bidirectional audio",
            model=self.model_name,
            instruction=(
                "You are a helpful and friendly AI assistant. "
                "You are talking to the user via voice. "
                "Keep your responses concise and natural for a spoken conversation."
            ),
        )

        # ΓöÇΓöÇ Runner ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        self.runner = Runner(
            agent=self.agent,
            session_service=self.session_service,
            app_name=APP_NAME,
        )

        logger.info(f"Γ£ô Voice Agent initialized ΓÇö model: {self.model_name}")

    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # Session lifecycle
    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    @staticmethod
    def generate_session_id() -> str:
        """Generate a unique session ID (UUID-based)."""
        return f"voice_{uuid.uuid4().hex[:12]}"

    async def get_or_create_session(self, session_id: str):
        """
        Create a fresh session or reuse an existing one.
        Never crashes on duplicate creates (race-condition safe).
        """
        try:
            existing = await self.session_service.get_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id,
            )
            if existing:
                logger.info(f"≡ƒöä Reusing existing session: {session_id}")
                return existing
        except Exception:
            pass  # Session doesn't exist yet ΓÇö create it below

        try:
            session = await self.session_service.create_session(
                session_id=session_id,
                user_id=USER_ID,
                app_name=APP_NAME,
            )
            logger.info(f"Γ£¿ Created new session: {session_id}")
            return session
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"≡ƒöä Session {session_id} created concurrently, fetching it.")
                return await self.session_service.get_session(
                    app_name=APP_NAME,
                    user_id=USER_ID,
                    session_id=session_id,
                )
            raise

    async def delete_session(self, session_id: str):
        """Clean up session on disconnect. Best-effort, never raises."""
        try:
            await self.session_service.delete_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id,
            )
            logger.info(f"≡ƒùæ∩╕Å Deleted session: {session_id}")
        except Exception as e:
            logger.warning(f"Session cleanup failed (non-fatal): {e}")

    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # RunConfig (voice output settings)
    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    def create_run_config(self) -> RunConfig:
        """Create RunConfig for ADK Voice Mode."""
        return RunConfig(
            response_modalities=[self.output_modality],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Puck"  # Options: Puck, Charon, Kore, Fenrir, Aoede
                    )
                )
            ),
        )

    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # Streaming (Model Γåö Client)
    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    async def process_stream(self, session_id: str, live_queue: LiveRequestQueue):
        """
        Async generator that yields events from the ADK Runner.
        Downstream (Agent ΓåÆ Client) half of the bidirectional loop.
        """
        run_config = self.create_run_config()
        async for event in self.runner.run_live(
            session_id=session_id,
            user_id=USER_ID,
            live_request_queue=live_queue,
            run_config=run_config,
        ):
            yield event
