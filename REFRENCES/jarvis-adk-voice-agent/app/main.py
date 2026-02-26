import asyncio
import base64
import json
import logging
import os
from typing import AsyncGenerator, Dict, Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from google.adk import Runner
from google.adk.runners import LiveRequestQueue
from google.adk.agents import Agent, RunConfig
from google.adk.tools import google_search
from google.adk.sessions import InMemorySessionService
from google.adk.flows.llm_flows.contents import types

# Load environment variables from parent directory
import sys
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log API key status (without exposing the key)
api_key = os.getenv("GOOGLE_API_KEY")
if api_key and api_key != "PASTE_YOUR_ACTUAL_API_KEY_HERE":
    logger.info(f"✅ Google API key loaded (length: {len(api_key)})")
else:
    logger.error("❌ Google API key not configured properly in .env file")

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global session storage
sessions: Dict[str, Dict[str, Any]] = {}

# Shared session service
session_service = InMemorySessionService()

# Import Jarvis agent
from jarvis.agent import root_agent


async def start_agent_session(session_id: str, is_audio: bool = False):
    """Initialize ADK session for a client."""
    logger.info(f"Starting agent session for {session_id}, audio: {is_audio}")
    
    # Create session first
    session = await session_service.create_session(
        app_name="jarvis",
        user_id="user",
        session_id=session_id
    )
    
    # Create runner with shared session service
    runner = Runner(
        app_name="jarvis",
        agent=root_agent,
        session_service=session_service
    )
    
    # Create live request queue for sending input to agent
    live_request_queue = LiveRequestQueue()
    
    # Configure response modality based on mode
    response_modalities = ["AUDIO"] if is_audio else ["TEXT"]
    run_config = RunConfig(response_modalities=response_modalities)
    
    logger.info(f"Starting live runner with response_modalities: {response_modalities}")
    
    # Start the runner in live mode and get live events
    live_events = runner.run_live(
        user_id="user",
        session_id=session_id,
        live_request_queue=live_request_queue,
        run_config=run_config
    )
    
    # Store session info
    sessions[session_id] = {
        "runner": runner,
        "live_request_queue": live_request_queue,
        "live_events": live_events,
        "is_audio": is_audio,
        "session": session
    }
    
    return live_events, live_request_queue


async def agent_to_client_messaging(websocket: WebSocket, live_events: AsyncGenerator):
    """Handle messages from agent to client."""
    try:
        logger.info("Starting agent_to_client_messaging loop")
        has_sent_partial = False  # Track if we've sent partial chunks
        last_input_transcription = None  # Track last input transcription to send only final
        last_output_transcription = None  # Track last output transcription
        
        async for event in live_events:
            # Log event with transcription info
            input_transcription = getattr(event, 'input_transcription', None)
            output_transcription = getattr(event, 'output_transcription', None)
            
            logger.info(f"Received event: turn_complete={event.turn_complete}, has_content={event.content is not None}, "
                       f"author={getattr(event, 'author', None)}, partial={getattr(event, 'partial', None)}, "
                       f"input_transcription={input_transcription}, output_transcription={output_transcription}")
            
            # Handle and send transcriptions
            if input_transcription:
                # Log the full transcription object structure
                logger.info(f"Input transcription object: {input_transcription}")
                
                # Extract text and finished status from transcription object
                transcription_text = None
                is_finished = None
                
                if hasattr(input_transcription, 'text'):
                    transcription_text = input_transcription.text
                    is_finished = getattr(input_transcription, 'finished', None)
                elif isinstance(input_transcription, str):
                    transcription_text = input_transcription
                    is_finished = True
                
                if transcription_text:
                    # Update last seen transcription
                    last_input_transcription = transcription_text
                    
                    logger.info(f"📝 Input transcription: text='{transcription_text}', finished={is_finished}")
                    
                    # Send when finished is True or None (final transcription)
                    if is_finished is True or is_finished is None:
                        logger.info(f"✅ Sending FINAL input transcription to client")
                        # Send input transcription to client as user message
                        await websocket.send_json({
                            "mime_type": "text/plain",
                            "data": transcription_text,
                            "turn_complete": False,
                            "is_user_transcription": True
                        })
                    else:
                        logger.info(f"⏭️ Skipping partial input transcription")
            
            if output_transcription:
                # Log the full transcription object structure
                logger.info(f"Output transcription object: {output_transcription}")
                
                # Extract text and finished status from transcription object
                transcription_text = None
                is_finished = None
                
                if hasattr(output_transcription, 'text'):
                    transcription_text = output_transcription.text
                    is_finished = getattr(output_transcription, 'finished', None)
                elif isinstance(output_transcription, str):
                    transcription_text = output_transcription
                    is_finished = True
                
                if transcription_text:
                    # Update last seen transcription
                    last_output_transcription = transcription_text
                    
                    logger.info(f"📝 Output transcription: text='{transcription_text}', finished={is_finished}")
                    
                    # Send when finished is True or None (final transcription)
                    if is_finished is True or is_finished is None:
                        logger.info(f"✅ Sending FINAL output transcription to client")
                        # Send output transcription to client as agent message
                        await websocket.send_json({
                            "mime_type": "text/plain",
                            "data": transcription_text,
                            "turn_complete": False,
                            "is_agent_transcription": True
                        })
                    else:
                        logger.info(f"⏭️ Skipping partial output transcription")
            
            # Only process events from the model (not user echo)
            if hasattr(event, 'author') and event.author == 'user':
                logger.info("Skipping user echo event")
                continue
            
            # Handle content first
            if event.content:
                # Check if this is a partial event (streaming chunk) or final event
                is_partial = getattr(event, 'partial', False)
                
                # Handle text content
                if hasattr(event.content, 'parts') and event.content.parts:
                    for idx, part in enumerate(event.content.parts):
                        # Try to access text
                        text_value = getattr(part, 'text', None)
                        
                        if text_value:
                            # Only send partial chunks, skip the final complete text if we already sent partials
                            if is_partial:
                                logger.info(f"Sending partial text to client (len={len(text_value)}): {text_value[:50]}...")
                                await websocket.send_json({
                                    "mime_type": "text/plain",
                                    "data": text_value,
                                    "turn_complete": False
                                })
                                has_sent_partial = True
                            elif not has_sent_partial:
                                # Only send final text if we didn't send partials (non-streaming mode)
                                logger.info(f"Sending final text to client (len={len(text_value)}): {text_value[:100]}...")
                                await websocket.send_json({
                                    "mime_type": "text/plain",
                                    "data": text_value,
                                    "turn_complete": False
                                })
                            else:
                                logger.info(f"Skipping final complete text (already sent {len(text_value)} chars as partials)")
                        # Check for thought (reasoning)
                        elif getattr(part, 'thought', None):
                            logger.info(f"Agent is thinking...")
                        # Check for function call
                        elif getattr(part, 'function_call', None):
                            logger.info(f"Agent is calling function")
                        # Check for function response
                        elif getattr(part, 'function_response', None):
                            logger.info(f"Received function response")
                        # Check for inline data (audio)
                        elif getattr(part, 'inline_data', None):
                            inline_data = part.inline_data
                            mime_type = getattr(inline_data, 'mime_type', '')
                            
                            # Check if it's audio (handle both 'audio/pcm' and 'audio/pcm;rate=24000')
                            if mime_type and mime_type.startswith('audio/pcm'):
                                data = getattr(inline_data, 'data', None)
                                if data:
                                    base64_audio = base64.b64encode(data).decode('utf-8')
                                    logger.info(f"[AGENT TO CLIENT]: Sending audio/pcm: {len(data)} bytes, mime_type: {mime_type}")
                                    await websocket.send_json({
                                        "mime_type": "audio/pcm",
                                        "data": base64_audio,
                                        "turn_complete": False
                                    })
            
            # Handle turn completion
            if event.turn_complete is True:
                logger.info("Sending turn completion signal")
                await websocket.send_json({
                    "mime_type": "text/plain",
                    "data": "",
                    "turn_complete": True
                })
                # Reset for next turn
                has_sent_partial = False
    except Exception as e:
        logger.error(f"Error in agent_to_client_messaging: {e}")
        raise


async def client_to_agent_messaging(websocket: WebSocket, live_request_queue: LiveRequestQueue):
    """Handle messages from client to agent."""
    try:
        logger.info("Starting client_to_agent_messaging loop")
        message_count = 0
        
        async for message in websocket.iter_text():
            message_count += 1
            logger.info(f"[MESSAGE #{message_count}] Received raw message (length: {len(message)})")
            
            try:
                data = json.loads(message)
                mime_type = data.get("mime_type")
                content_data = data.get("data")
                
                logger.info(f"[MESSAGE #{message_count}] Parsed: mime_type={mime_type}, data_length={len(str(content_data)) if content_data else 0}")
                
                if mime_type == "text/plain":
                    logger.info(f"Processing text message: {content_data}")
                    # Create proper Content object for text
                    content = types.Content(
                        role="user",
                        parts=[types.Part(text=content_data)]
                    )
                    live_request_queue.send_content(content)
                    logger.info("✅ Text content sent to agent")
                elif mime_type == "audio/pcm":
                    # Decode base64 audio and send to agent
                    logger.info(f"Decoding base64 audio data...")
                    audio_data = base64.b64decode(content_data)
                    logger.info(f"[CLIENT TO AGENT]: Decoded {len(audio_data)} bytes of audio data")
                    
                    # Create Blob object for audio with sample rate
                    audio_blob = types.Blob(
                        mime_type="audio/pcm;rate=16000",
                        data=audio_data
                    )
                    logger.info(f"Created audio Blob, sending to agent...")
                    live_request_queue.send_realtime(audio_blob)
                    logger.info(f"✅ Audio blob sent successfully (message #{message_count})")
                else:
                    logger.warning(f"Unknown mime_type: {mime_type}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Raw message: {message[:200]}...")
            except Exception as e:
                logger.error(f"Error processing client message: {e}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Error in client_to_agent_messaging: {e}", exc_info=True)
        raise


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for client connections."""
    await websocket.accept()
    
    # Check if this is an audio connection
    is_audio = websocket.query_params.get("is_audio", "false").lower() == "true"
    
    logger.info(f"Client #{session_id} connected, audio mode: {is_audio}")
    
    try:
        # Start agent session
        live_events, live_request_queue = await start_agent_session(session_id, is_audio)
        
        # Run both messaging functions concurrently
        await asyncio.gather(
            agent_to_client_messaging(websocket, live_events),
            client_to_agent_messaging(websocket, live_request_queue),
            return_exceptions=True
        )
        
    except WebSocketDisconnect:
        logger.info(f"Client #{session_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        # Clean up session
        if session_id in sessions:
            del sessions[session_id]


@app.get("/")
async def get_index():
    """Serve the main HTML page."""
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
