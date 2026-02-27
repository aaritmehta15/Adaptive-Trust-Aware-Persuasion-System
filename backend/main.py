"""
FastAPI Backend for ATLAS (Adaptive Trust Limited Action System)
"""

import os
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional, List
from huggingface_hub import InferenceClient, login
import uvicorn

from src.dialogue_manager import DialogueManager
from src.voice_agent import VoiceAgent
from src.config import Config
import asyncio
import json
import base64


# Initialize FastAPI app
app = FastAPI(title="ATLAS API - Adaptive Trust Limited Action System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
sessions: Dict[str, DialogueManager] = {}
voice_agent = None
hf_client = None
use_local_model = False


# Initialize HuggingFace client
def init_hf_client():
    global hf_client, use_local_model
    HF_TOKEN = os.getenv("HF_TOKEN")
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN environment variable not set. Please set it before starting the server.")
    
    try:
        login(token=HF_TOKEN, add_to_git_credential=False)
        hf_client = InferenceClient(api_key=HF_TOKEN)
        print("✓ HuggingFace client initialized successfully")
    except Exception as e:
        print(f"[X] Failed to initialize HF client: {e}")
        raise


# Request/Response models
class SessionCreate(BaseModel):
    condition: str  # 'C1' for regular chatbot, 'C3' for ATLAS (Adaptive Trust Limited Action System)
    donation_context: Dict


class MessageRequest(BaseModel):
    session_id: str
    message: str


class ScenarioSetup(BaseModel):
    organization: str
    cause: str
    amounts: str
    impact: str


@app.on_event("startup")
async def startup_event():
    # Initialize HuggingFace Client (Text Mode)
    try:
        init_hf_client()
        print("✓ Backend initialized successfully")
    except Exception as e:
        print(f"[X] HF Client initialization failed: {e}")
        print("The server will start but based text chat may not work.")

    # Initialize Voice Agent (Voice Mode)
    try:
        global voice_agent
        voice_agent = VoiceAgent()
        print("✓ Voice Agent initialized")
        
        # DEBUG: Check API Key
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            print(f"✓ GEMINI_API_KEY found: {api_key[:5]}...{api_key[-5:]}")
        else:
            print("❌ GEMINI_API_KEY NOT FOUND!")
            
    except Exception as e:
        print(f"[X] Voice Agent initialization failed: {e}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ATLAS API - Adaptive Trust Limited Action System",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint for connection testing"""
    return {"status": "healthy", "backend": "running"}


@app.post("/api/session/create")
async def create_session(data: SessionCreate):
    """Create a new conversation session"""
    try:
        if hf_client is None:
            raise HTTPException(
                status_code=503,
                detail="Backend not fully initialized. Please check HF_TOKEN and restart the server."
            )
        
        donation_ctx = data.donation_context
        condition = data.condition
        
        if condition not in ['C1', 'C3']:
            raise HTTPException(status_code=400, detail="Condition must be 'C1' or 'C3'")
        
        dm = DialogueManager(condition, donation_ctx, hf_client, use_local_model)
        opening = dm.start()
        
        sessions[dm.session_id] = dm
        
        return {
            "session_id": dm.session_id,
            "opening_message": opening,
            "condition": condition
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session/message")
async def process_message(data: MessageRequest):
    """Process a user message and return agent response with metrics"""
    try:
        if data.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        dm = sessions[data.session_id]
        
        if not dm.active:
            return {
                "agent_msg": dm._closing(dm.outcome or "Session ended"),
                "metrics": {
                    "turn": dm.turn,
                    "belief": round(dm.belief.get(), 3),
                    "trust": round(dm.trust.get(), 3),
                    "stop": True,
                    "reason": dm.outcome
                },
                "stop": True
            }
        
        result = dm.process(data.message)
        
        # Include history for frontend
        result["history"] = dm.history
        # Include belief/trust history for graph
        result["metrics"]["belief_history"] = [round(b, 3) for b in dm.belief.history]
        result["metrics"]["trust_history"] = [round(t, 3) for t in dm.trust.history]
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}/metrics")
async def get_metrics(session_id: str):
    """Get current metrics for a session"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        dm = sessions[session_id]
        
        # Get last rejection info if available
        last_rej_info = None
        if dm.history and len(dm.history) > 0:
            last_entry = dm.history[-1]
            if last_entry.get('speaker') == 'user' and 'info' in last_entry:
                last_rej_info = last_entry['info']
        
        # Create metrics in the same format as process() returns
        metrics = {
            "turn": dm.turn,
            "belief": round(dm.belief.get(), 3),
            "trust": round(dm.trust.get(), 3),
            "delta_belief": 0.0,  # No delta for standalone metrics call
            "delta_trust": 0.0,
            "rejection_type": last_rej_info.get('rejection_type', 'none') if last_rej_info else 'none',
            "rejection_conf": round(last_rej_info.get('rejection_confidence', 0.0), 3) if last_rej_info else 0.0,
            "sentiment": last_rej_info.get('sentiment_label', 'neutral') if last_rej_info else 'neutral',
            "sentiment_score": round(last_rej_info.get('sentiment_score', 0.0), 3) if last_rej_info else 0.0,
            "trust_concern": last_rej_info.get('trust_concern', False) if last_rej_info else False,
            "is_curiosity": last_rej_info.get('is_curiosity', False) if last_rej_info else False,
            "recovery_mode": dm.trust.recovery_mode,
            "strategy_weights": {
                k: round(v, 3) for k, v in dm.strategy.weights.items()
            },
            "consec_reject": dm.guard.consec_reject,
            "belief_history": [round(b, 3) for b in dm.belief.history],
            "trust_history": [round(t, 3) for t in dm.trust.history],
            "active": dm.active,
            "outcome": dm.outcome
        }
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset a session (create new one with same ID)"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        old_dm = sessions[session_id]
        condition = old_dm.condition
        donation_ctx = old_dm.ctx
        
        # Save old session before resetting
        old_dm.save()
        
        # Create new session
        dm = DialogueManager(condition, donation_ctx, hf_client, use_local_model)
        dm.session_id = session_id  # Keep same ID
        opening = dm.start()
        
        sessions[session_id] = dm
        
        return {
            "session_id": session_id,
            "opening_message": opening,
            "message": "Session reset"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        dm = sessions[session_id]
        dm.save()  # Save before deleting
        del sessions[session_id]
        
        return {"message": "Session deleted and saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scenario/setup")
async def setup_scenario(data: ScenarioSetup):
    """Set up campaign scenario - returns donation context"""
    return {
        "donation_context": {
            "organization": data.organization,
            "cause": data.cause,
            "amounts": data.amounts,
            "impact": data.impact
        }
    }


class VoiceModeRequest(BaseModel):
    mode: str  # 'C1' or 'C3'
    donation_context: Optional[Dict] = None


@app.post("/api/voice/set-mode")
async def set_voice_mode(data: VoiceModeRequest):
    """Set the voice agent's mode and donation context"""
    if voice_agent is None:
        raise HTTPException(status_code=503, detail="Voice agent not initialized")
    
    if data.mode not in ['C1', 'C3']:
        raise HTTPException(status_code=400, detail="Mode must be 'C1' or 'C3'")
    
    voice_agent.set_mode(data.mode, data.donation_context)
    return {"status": "ok", "mode": data.mode}


@app.websocket("/ws/voice/{session_id}")
async def voice_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket Endpoint for ADK Voice (Bidirectional).
    
    Architecture:
    - Each connection gets a unique session via get-or-create.
    - Session is cleaned up on disconnect.
    - Two concurrent tasks: upstream (mic→model) and downstream (model→speaker).
    """
    # ── None guard — VoiceAgent failed to init ──
    if voice_agent is None:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "Voice agent failed to initialize. Check GEMINI_API_KEY and server logs."
        })
        await websocket.close(1011)
        return

    # ── Lazy imports — only inside this handler, never at module level ──
    # Keeps ADK failures isolated to /ws/voice only; text endpoints still work.
    from google.adk.runners import LiveRequestQueue
    from google.genai import types

    # ── Generate unique session ID per connection ──
    # The frontend sends a UUID, but even if it sends "default_session",
    # we override to guarantee uniqueness.
    actual_session_id = voice_agent.generate_session_id()
    print(f"🔌 WS Connection Request: client={session_id} → actual={actual_session_id}")
    
    await websocket.accept()
    print(f"✅ WS Accepted: {actual_session_id}")

    live_queue = None
    
    try:
        # ── Step 1: Get or Create ADK Session ──
        print(f"📦 Step 1: Getting/Creating ADK Session...")
        try:
            await voice_agent.get_or_create_session(actual_session_id)
            print(f"✅ Step 1 PASSED: Session ready: {actual_session_id}")
        except Exception as e:
            print(f"❌ Step 1 FAILED: {e}")
            import traceback; traceback.print_exc()
            await websocket.send_json({"type": "error", "message": str(e)})
            return

        # ── Step 2: Create Live Queue ──
        print(f"📦 Step 2: Creating LiveRequestQueue...")
        try:
            live_queue = LiveRequestQueue()
            print(f"✅ Step 2 PASSED")
        except Exception as e:
            print(f"❌ Step 2 FAILED: {e}")
            import traceback; traceback.print_exc()
            await websocket.send_json({"type": "error", "message": str(e)})
            return

        # ── Upstream: Client Mic → ADK Model ──
        async def receive_from_client():
            try:
                chunk_count = 0
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    mime_type = data.get("mime_type")
                    content_data = data.get("data")

                    if mime_type == "audio/pcm":
                        audio_bytes = base64.b64decode(content_data)
                        chunk_count += 1
                        if chunk_count <= 3 or chunk_count % 100 == 0:
                            print(f"🎤 Chunk #{chunk_count}: {len(audio_bytes)} bytes")
                        live_queue.send_realtime(
                            types.Blob(mime_type="audio/pcm;rate=16000", data=audio_bytes)
                        )
                    elif mime_type == "text/plain":
                        print(f"📩 Text: {content_data}")
            except Exception as e:
                print(f"❌ Upstream error: {e}")
            finally:
                print("🛑 Closing live queue (client done)")
                if live_queue:
                    live_queue.close()  # Synchronous — no await

        # ── Downstream: ADK Model → Client Speaker ──
        async def send_to_client():
            try:
                print("🎧 Step 3: Starting model stream...")
                async for event in voice_agent.process_stream(actual_session_id, live_queue):
                    # Log event type
                    event_type = type(event).__name__
                    print(f"📤 Event: {event_type}")

                    # Audio content
                    if hasattr(event, 'content') and event.content:
                        for part in event.content.parts:
                            if (hasattr(part, 'inline_data') and part.inline_data
                                    and part.inline_data.mime_type.startswith("audio/pcm")):
                                chunk_bytes = len(part.inline_data.data)
                                chunk_samples = chunk_bytes // 2  # Int16 = 2 bytes per sample
                                print(f"🎧 Audio chunk: {part.inline_data.mime_type}, "
                                      f"{chunk_bytes} bytes ({chunk_samples} samples, "
                                      f"{chunk_samples/24000:.3f}s at 24kHz)")
                                b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                                await websocket.send_json({
                                    "type": "audio",
                                    "data": b64,
                                    "turn_complete": getattr(event, 'turn_complete', False)
                                })

                    # Interruption
                    if getattr(event, 'interrupted', False):
                        print("❗ Interruption")
                        await websocket.send_json({"type": "interrupted"})

                    # Turn complete
                    if getattr(event, 'turn_complete', False):
                        print("✅ Turn complete")
                        await websocket.send_json({"type": "turn_complete", "turn_complete": True})

            except Exception as e:
                print(f"❌ Downstream error: {e}")
                import traceback; traceback.print_exc()

        # ── Step 4: Run both concurrently ──
        print("🚀 Step 4: Starting concurrent upstream + downstream...")
        await asyncio.gather(receive_from_client(), send_to_client())

    except Exception as e:
        print(f"❌ CRITICAL voice error: {e}")
        import traceback; traceback.print_exc()
    finally:
        # ── Cleanup: delete session on disconnect ──
        print(f"🔌 Disconnecting: {actual_session_id}")
        await voice_agent.delete_session(actual_session_id)
        print(f"🧹 Session cleaned up: {actual_session_id}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
