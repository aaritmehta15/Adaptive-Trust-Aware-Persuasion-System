"""
Voice Bridge Module for ATLAS
Wraps the core DialogueManager with Google Gemini Live API.
"""

import os
import asyncio
import logging
import json
from typing import Dict, Any, AsyncGenerator
from dotenv import load_dotenv

# Ensure env vars are loaded in this process (critical for Windows spawn)
load_dotenv()

import sys

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.adk.agents import Agent
from google.adk.tools import BaseTool
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .session_store import sessions, list_sessions

# Configure logging
logger = logging.getLogger(__name__)

# --- Voice Agent Definition ---


class AtlasTool(BaseTool):
    """
    Exposes ATLAS DialogueManager as a tool to Gemini.
    """

    def __init__(self, _ignored_sessions=None):
        super().__init__(
            name="atlas_tool",
            description="Send user input to the ATLAS persuasion system and return the agent's response.",
        )
        # Use the global store directly
        self.sessions = sessions

        # Define the function explicitly for Gemini
        self.fn = self.process_message
        self.schema = {
            "name": "process_message",
            "description": "Send user input to the ATLAS persuasion system and return the agent's response.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "user_message": {
                        "type": "STRING",
                        "description": "The text message from the user.",
                    },
                    "session_id": {
                        "type": "STRING",
                        "description": "The active session ID.",
                    },
                },
                "required": ["user_message", "session_id"],
            },
        }

    def process_message(self, user_message: str, session_id: str) -> str:
        """
        Processes a message through ATLAS core logic.
        """
        logger.info(
            f"[ATLAS-VOICE] Processing for session {session_id}: {user_message}"
        )

        if session_id not in self.sessions:
            return "System Notice: I am connected, but I cannot find your active session. Please click 'Setup Scenario' and then 'Save & Start' to initialize the persuasion system."

        dm = self.sessions[session_id]

        try:
            # === BLACK-BOX INTEGRATION ===
            # We call the exact same method the text API uses
            result = dm.process(user_message)

            agent_response = result["agent_msg"]
            logger.info(f"[ATLAS-VOICE] ATLAS Response: {agent_response}")

            # Return ONLY the text response for Gemini to speak
            return agent_response

        except Exception as e:
            logger.error(f"[ATLAS-VOICE] Error: {e}")
            return "I'm having trouble connecting to the system right now."


def init_voice_layer(app: FastAPI, _ignored_sessions: Dict[str, Any]):
    """
    Initializes the voice layer and mounts the WebSocket endpoint.
    """
    logger.info("Initializing ATLAS Voice Layer...")

    # 1. Define the Agent
    # We use a trick: System instruction forces Gemini to be a "Pass-through"
    # It MUST call the tool and speak the result verbatim.
    voice_agent = Agent(
        name="atlas_voice_agent",
        model="gemini-2.0-flash-exp",  # Using 2.0 Flash for speed/cost
        tools=[AtlasTool()],
        instruction=(
            "You are a voice interface for the ATLAS persuasion system. "
            "Your ONLY job is to: "
            "1. Listen to the user. "
            "2. Call the 'process_message' tool with their text and session ID. "
            "3. Speak the tool's output EXACTLY as written. "
            "Do NOT add your own introduction, pleasantries, or summary. "
            "Do NOT make up information. "
            "Just act as a voice bridge."
        ),
    )

    # 2. Setup ADK Components
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="atlas-voice", agent=voice_agent, session_service=session_service
    )

    # 3. Mount WebSocket Endpoint
    @app.websocket("/ws/voice/{session_id}")
    async def voice_endpoint(websocket: WebSocket, session_id: str):
        # Debugging Identity
        from .session_store import sessions as store_sessions

        print(f"DEBUG: Voice Endpoint hit. Store ID: {id(store_sessions)}")
        print(
            f"DEBUG: Voice connecting for {session_id}. Active sessions: {list(store_sessions.keys())}"
        )
        logger.info(f"Voice connection request: {session_id}")
        await websocket.accept()

        # Check if ATLAS session exists
        if session_id not in store_sessions:
            logger.warning(
                f"Voice connection warning: Session {session_id} not found in ATLAS store. Proceeding anyway (Tool will handle error)."
            )
            # We DO NOT close the socket. We let the agent tell the user.

        # Setup RunConfig for Native Audio (Bidi Streaming)
        # We use AUDIO output to get speech synthesis from Gemini
        run_config = RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=["AUDIO"],  # We want it to speak!
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
        )

        # Get/Create ADK Session (wraps the connection context)
        # We use the same session_id for simplicity
        flow_session = await session_service.get_session(
            app_name="atlas-voice", user_id="default-user", session_id=session_id
        )
        if not flow_session:
            await session_service.create_session(
                app_name="atlas-voice", user_id="default-user", session_id=session_id
            )

        live_queue = LiveRequestQueue()

        # --- Bidi-Demo Pattern Implementation ---

        async def upstream():
            """Client -> Gemini (Audio)"""
            try:
                while True:
                    msg = await websocket.receive()

                    if "bytes" in msg:
                        # Forward audio chunk
                        blob = types.Blob(
                            mime_type="audio/pcm;rate=16000", data=msg["bytes"]
                        )
                        live_queue.send_realtime(blob)

                    elif "text" in msg:
                        # Handle control messages if any
                        pass

            except WebSocketDisconnect:
                logger.info("Voice client disconnected")
            except Exception as e:
                logger.error(f"Upstream error: {e}")
            finally:
                live_queue.close()

        async def downstream():
            """Gemini -> Client (Audio + Events)"""
            try:
                # IMPORTANT: inject session_id into tool calls implicitly or context
                # The prompt tells Gemini to pass session_id, but we need to ensure it knows it.
                # For this simple bridge, we might need a workaround if Gemini "forgets".
                # But since the tool call happens in the Turn, we rely on the Prompt context.

                # We start the runner loop
                async for event in runner.run_live(
                    user_id="default-user",
                    session_id=session_id,
                    live_request_queue=live_queue,
                    run_config=run_config,
                ):
                    # Forward event to client as JSON
                    await websocket.send_text(
                        event.model_dump_json(exclude_none=True, by_alias=True)
                    )
            except Exception as e:
                logger.error(f"Downstream error: {e}")

        # Run both directions
        try:
            await asyncio.gather(upstream(), downstream())
        except Exception as e:
            logger.error(f"Voice session error: {e}")
        finally:
            live_queue.close()
            logger.info(f"Voice session {session_id} ended")
