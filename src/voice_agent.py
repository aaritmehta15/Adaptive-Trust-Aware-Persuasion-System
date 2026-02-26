"""
VoiceAgent — Google ADK Live (Bidi-Streaming) Implementation
Provides the VoiceAgent class used by backend/main.py.

Architecture:
  - One Runner + InMemorySessionService per VoiceAgent instance.
  - Each WebSocket connection gets a unique session ID.
  - process_stream() calls runner.run_live() and yields raw ADK events.
"""

import os
import uuid
import logging
from typing import AsyncGenerator, Optional

from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.config import Config

logger = logging.getLogger(__name__)

# ── Shared app-name constant ──────────────────────────────────────────────────
_APP_NAME = "atlas-voice"
_USER_ID  = "atlas-user"


def _build_system_instruction(mode: str, donation_context: Optional[dict]) -> str:
    """Build the system prompt for the voice agent based on mode and context."""

    ctx = donation_context or {}
    org   = ctx.get("organization", "our organization")
    cause = ctx.get("cause", "an important cause")
    amounts = ctx.get("amounts", "200, 500, 1000")
    impact = ctx.get("impact", "every donation makes a difference")

    if mode == "C1":
        style = (
            "You are a persistent and persuasive fundraising voice assistant. "
            "Your PRIMARY goal is to secure a donation. "
            "Be empathetic but always redirect the conversation back to making a donation. "
            "Don't let objections stop you — reframe them as opportunities. "
        )
    else:  # C3 — ATLAS mode
        style = (
            "You are a thoughtful, trust-aware fundraising voice assistant powered by ATLAS. "
            "Build genuine rapport. Listen carefully to the donor. "
            "Adjust your persuasion strategy based on their responses. "
            "Prioritise trust above pressure. "
        )

    return (
        f"{style}\n\n"
        f"You are raising funds for {org}, working on {cause}.\n"
        f"Suggested donation amounts: ₹{amounts}.\n"
        f"Impact: {impact}.\n\n"
        "Keep your spoken responses short (under 40 words). "
        "Speak naturally and conversationally. "
        "Never mention that you are an AI unless directly asked."
    )


class VoiceAgent:
    """
    Wraps a Google ADK Runner for bidirectional live audio streaming.
    Interface expected by backend/main.py:
      - generate_session_id() -> str
      - set_mode(mode, donation_context)
      - async get_or_create_session(session_id)
      - async process_stream(session_id, live_queue) -> AsyncGenerator
      - async delete_session(session_id)
    """

    def __init__(self):
        self._mode: str = "C3"
        self._donation_context: Optional[dict] = None
        self._session_service = InMemorySessionService()
        self._runner: Optional[Runner] = None
        self._agent: Optional[Agent] = None
        self._build_runner()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_runner(self):
        """Construct (or rebuild) the ADK Agent + Runner."""
        instruction = _build_system_instruction(self._mode, self._donation_context)

        self._agent = Agent(
            name="atlas_voice_agent",
            model=Config.ADK_VOICE_MODEL,
            instruction=instruction,
        )

        self._runner = Runner(
            app_name=_APP_NAME,
            agent=self._agent,
            session_service=self._session_service,
        )
        logger.info(
            f"[VoiceAgent] Runner built — mode={self._mode}, "
            f"model={Config.ADK_VOICE_MODEL}"
        )

    def _make_run_config(self) -> RunConfig:
        """Build RunConfig for native-audio bidi streaming."""
        model_name = Config.ADK_VOICE_MODEL.lower()
        is_native = "native-audio" in model_name

        if is_native:
            return RunConfig(
                streaming_mode=StreamingMode.BIDI,
                response_modalities=["AUDIO"],
                input_audio_transcription=types.AudioTranscriptionConfig(),
                output_audio_transcription=types.AudioTranscriptionConfig(),
            )
        else:
            # Half-cascade / flash models: respond with audio via BIDI
            return RunConfig(
                streaming_mode=StreamingMode.BIDI,
                response_modalities=["AUDIO"],
            )

    # ── Public interface (called by backend/main.py) ──────────────────────────

    def generate_session_id(self) -> str:
        """Return a new unique session ID string."""
        return str(uuid.uuid4())

    def set_mode(self, mode: str, donation_context: Optional[dict] = None):
        """
        Change the agent's persuasion mode and/or donation context.
        Rebuilds the Runner so the agent instruction is updated.
        """
        self._mode = mode
        self._donation_context = donation_context
        self._build_runner()
        logger.info(f"[VoiceAgent] Mode set to {mode}")

    async def get_or_create_session(self, session_id: str):
        """
        Get an existing ADK session or create a new one.
        Must be called before process_stream().
        """
        session = await self._session_service.get_session(
            app_name=_APP_NAME,
            user_id=_USER_ID,
            session_id=session_id,
        )
        if not session:
            session = await self._session_service.create_session(
                app_name=_APP_NAME,
                user_id=_USER_ID,
                session_id=session_id,
            )
            logger.info(f"[VoiceAgent] Created ADK session: {session_id}")
        else:
            logger.info(f"[VoiceAgent] Reused ADK session: {session_id}")
        return session

    async def process_stream(self, session_id: str, live_queue) -> AsyncGenerator:
        """
        Bidirectional streaming: starts runner.run_live() and yields
        raw ADK Event objects.  backend/main.py inspects each event for
        audio content, interruptions, and turn_complete markers.
        """
        run_config = self._make_run_config()

        async for event in self._runner.run_live(
            user_id=_USER_ID,
            session_id=session_id,
            live_request_queue=live_queue,
            run_config=run_config,
        ):
            yield event

    async def delete_session(self, session_id: str):
        """
        Clean up the ADK session on WebSocket disconnect.
        Silently ignores sessions that no longer exist.
        """
        try:
            await self._session_service.delete_session(
                app_name=_APP_NAME,
                user_id=_USER_ID,
                session_id=session_id,
            )
            logger.info(f"[VoiceAgent] Deleted session: {session_id}")
        except Exception as e:
            logger.warning(f"[VoiceAgent] Could not delete session {session_id}: {e}")
