"""
Voice Agent — ADK Integration for ATLAS
Handles session lifecycle, model streaming, and cleanup.
"""
import os
import uuid
import logging

from google.adk import Runner
from google.adk.runners import LiveRequestQueue
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode  # CRITICAL: must use this path in v1.25.1
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = "ATLAS_System"
USER_ID = "atlas_user"


class VoiceAgent:
    def __init__(self):
        """Initialize the Voice Agent with ADK components."""
        # ── API Key Bridge ────────────────────────────────────────────
        # ADK authenticates via GOOGLE_API_KEY.
        # If only GEMINI_API_KEY is set, bridge it here so ADK picks it up.
        gemini_key = os.getenv("GEMINI_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")

        if gemini_key and not google_key:
            os.environ["GOOGLE_API_KEY"] = gemini_key
            logger.info("✓ Bridged GEMINI_API_KEY → GOOGLE_API_KEY for ADK")
        elif not gemini_key and not google_key:
            logger.error("❌ Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set. Voice mode will fail.")
            print("❌ Set GEMINI_API_KEY before starting the backend to use Voice Mode.")

        # ── Model ─────────────────────────────────────────────────────
        self.model_name = Config.ADK_VOICE_MODEL
        self.output_modality = "AUDIO"

        # ── Session Service ───────────────────────────────────────────
        self.session_service = InMemorySessionService()

        # ── Agent ─────────────────────────────────────────────────────
        # CRITICAL: pass model= directly in the constructor.
        # Do NOT try to set self.agent.model after construction via hasattr guard.
        self.agent = Agent(
            name="atlas_voice_agent",
            description="ATLAS Voice Agent for bidirectional audio",
            model=self.model_name,
            instruction=(
                "You are ATLAS, a natural conversational voice assistant.\n"
                "Speak clearly and naturally.\n"
                "Keep responses concise.\n"
                "Avoid long monologues.\n"
                "Pause naturally between ideas.\n"
                "Wait until the user finishes speaking before responding.\n"
                "Maintain conversational memory across turns.\n"
                "Do not rush your speech.\n"
                "Sound calm and human."
            ),
        )

        # ── Runner ────────────────────────────────────────────────────
        self.runner = Runner(
            agent=self.agent,
            session_service=self.session_service,
            app_name=APP_NAME,
        )

        logger.info(f"✓ Voice Agent initialized — model: {self.model_name}")

    @staticmethod
    def generate_session_id() -> str:
        """Generate a unique session ID (UUID-based)."""
        return f"voice_{uuid.uuid4().hex[:12]}"

    async def get_or_create_session(self, session_id: str):
        """
        Create a fresh session or reuse an existing one.
        Race-condition safe: handles 'already exists' errors gracefully.
        """
        try:
            existing = await self.session_service.get_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id,
            )
            if existing:
                logger.info(f"🔄 Reusing existing session: {session_id}")
                return existing
        except Exception:
            pass  # Session doesn't exist yet — create it below

        try:
            session = await self.session_service.create_session(
                session_id=session_id,
                user_id=USER_ID,
                app_name=APP_NAME,
            )
            logger.info(f"✨ Created new session: {session_id}")
            return session
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"🔄 Session {session_id} created concurrently, fetching it.")
                return await self.session_service.get_session(
                    app_name=APP_NAME,
                    user_id=USER_ID,
                    session_id=session_id,
                )
            raise

    async def delete_session(self, session_id: str):
        """Clean up session on disconnect. Best-effort — never raises."""
        try:
            await self.session_service.delete_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id,
            )
            logger.info(f"🗑️ Deleted session: {session_id}")
        except Exception as e:
            logger.warning(f"Session cleanup failed (non-fatal): {e}")

    def create_run_config(self) -> RunConfig:
        """Create RunConfig for ADK Voice Mode.
        
        - StreamingMode.BIDI  : enables full bidirectional streaming (required for
                                  proper turn-taking with native-audio models)
        - response_modalities : AUDIO-only output from Gemini
        - speech_config       : Puck voice, 24kHz PCM Int16 mono output
        - input_audio_transcription : model transcribes what it hears — surfaces
                                       turn boundaries and aids debugging
        """
        return RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=[self.output_modality],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Puck"  # Options: Puck, Charon, Kore, Fenrir, Aoede
                    )
                )
            ),
            input_audio_transcription=types.AudioTranscriptionConfig(),
        )

    async def process_stream(self, session_id: str, live_queue: LiveRequestQueue):
        """
        Async generator that yields events from the ADK Runner.
        Downstream (Agent → Client) half of the bidirectional loop.
        """
        run_config = self.create_run_config()
        async for event in self.runner.run_live(
            session_id=session_id,
            user_id=USER_ID,
            live_request_queue=live_queue,
            run_config=run_config,
        ):
            yield event
