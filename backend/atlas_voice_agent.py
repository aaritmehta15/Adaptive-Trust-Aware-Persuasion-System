"""
Atlas Voice Agent
Handles WebSocket connections and manages the Google ADK Live Session.
Exposes AtlasCore as a function tool to the LLM.
"""

import logging
import asyncio
import json
import traceback
from typing import Dict, Any, Optional

from fastapi import WebSocket, WebSocketDisconnect
from google.adk.agents import Agent
from google.adk.tools import BaseTool
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.atlas_core import AtlasCore, AtlasRequest

logger = logging.getLogger(__name__)

class AtlasTool(BaseTool):
    """
    Exposes ATLAS DialogueManager as a tool to Gemini.
    """
    def __init__(self, atlas: AtlasCore, session_id: str):
        super().__init__(
            name="process_user_message",
            description="Send user input to the ATLAS persuasion system to get a strategic response.",
        )
        self.atlas = atlas
        self.session_id = session_id
        # Define the function explicitly for Gemini
        self.fn = self.process_message
        self.schema = {
            "name": "process_user_message",
            "description": "Send user input to the ATLAS persuasion system to get a strategic response.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "user_message": {
                        "type": "STRING",
                        "description": "The text message from the user.",
                    },
                },
                "required": ["user_message"],
            },
        }

    def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Processes a message through ATLAS core logic.
        """
        logger.info(f"[ATLAS-TOOL] Processing for session {self.session_id}: {user_message}")
        
        try:
            request = AtlasRequest(session_id=self.session_id, text=user_message)
            # AtlasCore.process is synchronous or async?
            # From previous view_file, AtlasCore.process is synchronous (def process(...)).
            # But the tool calling might be blocking the event loop if not careful.
            # ADK tools usually run in thread pool or async if defined async.
            # BaseTool supports sync functions.
            
            result = self.atlas.process(request)
            
            # Helper to extract relevant parts for the LLM
            # We return the agent_msg and maybe some context if needed
            response_data = {
                "agent_response": result["agent_msg"],
                "conversation_status": "active" if not result.get("stop", False) else "ended",
                "metrics": result.get("metrics", {})
            }
            logger.info(f"[ATLAS-TOOL] Result: {response_data['agent_response']}")
            return response_data
            
        except Exception as e:
            logger.error(f"[ATLAS-TOOL] Error: {e}")
            logger.error(traceback.format_exc())
            return {"error": "Internal system error processing message."}


class AtlasVoiceAgent:
    """
    Manages the Google ADK Live Session and WebSocket streaming.
    """
    def __init__(self, atlas: AtlasCore):
        self.atlas = atlas
        self.session_service = InMemorySessionService()

    async def handle_websocket(self, websocket: WebSocket, session_id: str):
        """
        Handles the WebSocket connection and bidirectional streaming with Gemini.
        """
        await websocket.accept()
        logger.info(f"[VOICE-AGENT] Connected session: {session_id}")

        # 1. Define the Tool specific to this session
        atlas_tool = AtlasTool(self.atlas, session_id)

        # 2. Define the Agent
        # Instructions: Act as a voice interface. When user speaks, use the tool.
        # Speak the result.
        agent = Agent(
            name="atlas_voice_agent",
            model="gemini-2.0-flash-exp", # Or appropriate model
            tools=[atlas_tool],
            instruction=(
                "You are the voice of the ATLAS persuasion system. "
                "Your role is to listen to the user, and ALWAYS convert their speech to text "
                "and pass it to the 'process_user_message' tool. "
                "Wait for the tool to return the strategic response. "
                "Then, speak the 'agent_response' from the tool output to the user EXACTLY as written. "
                "Do not improvise or add fillers unless necessary for natural flow. "
                "Maintain a professional, persuasive tone."
            ),
        )

        # 3. Setup Runner
        runner = Runner(
            app_name="atlas-voice", 
            agent=agent, 
            session_service=self.session_service
        )

        # 4. Setup RunConfig
        # We want AUDIO output (TTS) from the model
        run_config = RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=["AUDIO"], 
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
        )

        # 5. Get/Create Session
        flow_session = await self.session_service.get_session(
            app_name="atlas-voice", user_id="default-user", session_id=session_id
        )
        if not flow_session:
            await self.session_service.create_session(
                app_name="atlas-voice", user_id="default-user", session_id=session_id
            )

        live_queue = LiveRequestQueue()

        # 6. Stream Loop
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
                        # Could be control messages
                        pass
            except WebSocketDisconnect:
                logger.info(f"[VOICE-AGENT] Client disconnected: {session_id}")
            except Exception as e:
                logger.error(f"[VOICE-AGENT] Upstream error: {e}")
            finally:
                live_queue.close()

        async def downstream():
            """Gemini -> Client (Audio + Events)"""
            try:
                # runner.run_live yields events
                async for event in runner.run_live(
                    user_id="default-user",
                    session_id=session_id,
                    live_request_queue=live_queue,
                    run_config=run_config,
                ):
                    # Forward event to client as JSON
                    # This includes audio chunks in the events
                    await websocket.send_text(
                        event.model_dump_json(exclude_none=True, by_alias=True)
                    )
            except Exception as e:
                logger.error(f"[VOICE-AGENT] Downstream error: {e}")
                logger.error(traceback.format_exc())

        # Run streams
        try:
            await asyncio.gather(upstream(), downstream())
        except Exception as e:
            logger.error(f"[VOICE-AGENT] Session error: {e}")
        finally:
            live_queue.close()
            logger.info(f"[VOICE-AGENT] Session ended: {session_id}")
