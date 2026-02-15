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
        Robust Echo Server for WebSocket Stability Testing.
        Handles binary frames correctly and logs data flow.
        """
        await websocket.accept()
        logger.info(f"[VOICE-AGENT-ECHO] Connected session: {session_id}")

        try:
            while True:
                # Receive raw ASGI message
                message = await websocket.receive()
                
                # Check for disconnect message type
                if message["type"] == "websocket.disconnect":
                    logger.info(f"[VOICE-AGENT-ECHO] Disconnect message received: {session_id}")
                    break
                
                # Check for binary data
                if "bytes" in message:
                    data = message["bytes"]
                    # Log size but limit output
                    logger.info(f"[VOICE-AGENT-ECHO] Received binary frame: {len(data)} bytes")
                    
                    # Echo back a simple text acknowledgment to keep client happy
                    # (Client expects JSON text response for events)
                    ack_msg = json.dumps({
                        "text": f"Ack binary {len(data)} bytes",
                        "serverContent": { "modelTurn": { "parts": [ { "text": "Ack binary" } ] } } # Dummy structure
                    })
                    await websocket.send_text(ack_msg)
                    
                # Check for text data
                elif "text" in message:
                    text = message["text"]
                    logger.info(f"[VOICE-AGENT-ECHO] Received text frame: {text}")
                    
                    # Echo back
                    echo_msg = json.dumps({
                        "text": f"Echo: {text}",
                        "serverContent": { "modelTurn": { "parts": [ { "text": f"Echo: {text}" } ] } } # Dummy structure
                    })
                    await websocket.send_text(echo_msg)
                    
        except WebSocketDisconnect:
            logger.info(f"[VOICE-AGENT-ECHO] WebSocketDisconnect exception: {session_id}")
        except Exception as e:
            logger.error(f"[VOICE-AGENT-ECHO] Unexpected Error: {e}")
            logger.error(traceback.format_exc())
            
        logger.info(f"[VOICE-AGENT-ECHO] Connection closed: {session_id}")
