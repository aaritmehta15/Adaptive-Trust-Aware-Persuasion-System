"""
FastAPI Backend for ATLAS (Adaptive Trust Limited Action System)
"""

import os
from dotenv import load_dotenv
import sys

# Add project root to sys.path to resolve 'src' and 'backend' imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load env vars BEFORE imports that rely on them
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional, List
from huggingface_hub import InferenceClient, login
import uvicorn

from src.dialogue_manager import DialogueManager
from src.config import Config
from .voice_bridge import init_voice_layer
from src.atlas_core import AtlasCore, AtlasRequest

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
# sessions: Dict[str, DialogueManager] = {}  <-- REMOVED LOCAL DICT
from .session_store import sessions, add_session, get_session

hf_client = None
use_local_model = False
atlas_core = AtlasCore()


# Initialize HuggingFace client
def init_hf_client():
    global hf_client, use_local_model
    HF_TOKEN = os.getenv("HF_TOKEN")
    if not HF_TOKEN:
        raise ValueError(
            "HF_TOKEN environment variable not set. Please set it before starting the server."
        )

    try:
        login(token=HF_TOKEN, add_to_git_credential=False)
        hf_client = InferenceClient(api_key=HF_TOKEN)
        print("✓ HuggingFace client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize HF client: {e}")
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
    try:
        init_hf_client()
        # Initialize Voice Integration
        print(f"DEBUG: Initializing Voice Layer. Sessions dict ID: {id(sessions)}")
        # Pass the global store to voice layer (though it likely imports it directly now)
        init_voice_layer(app, sessions)
        print("✓ Backend initialized successfully")
    except Exception as e:
        print(f"✗ Backend initialization failed: {e}")
        print(
            "The server will start but may not function correctly without HuggingFace token."
        )
        print("Please set HF_TOKEN environment variable and restart the server.")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ATLAS API - Adaptive Trust Limited Action System",
        "status": "running",
        "version": "1.0.0",
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
                detail="Backend not fully initialized. Please check HF_TOKEN and restart the server.",
            )

        donation_ctx = data.donation_context
        condition = data.condition

        if condition not in ["C1", "C3"]:
            raise HTTPException(
                status_code=400, detail="Condition must be 'C1' or 'C3'"
            )

        dm = DialogueManager(condition, donation_ctx, hf_client, use_local_model)
        opening = dm.start()

        # Store in global store
        add_session(dm.session_id, dm)
        print(f"DEBUG: Session created {dm.session_id} in Store {id(sessions)}")

        return {
            "session_id": dm.session_id,
            "opening_message": opening,
            "condition": condition,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session/message")
async def process_message(data: MessageRequest):
    """Process a user message and return agent response with metrics"""
    try:
        # Delegate to Atlas Core
        request = AtlasRequest(session_id=data.session_id, text=data.message)
        result = atlas_core.process(request)
        return result
    except ValueError as e:
        # Handle session not found
        raise HTTPException(status_code=404, detail=str(e))
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
            if last_entry.get("speaker") == "user" and "info" in last_entry:
                last_rej_info = last_entry["info"]

        # Create metrics in the same format as process() returns
        metrics = {
            "turn": dm.turn,
            "belief": round(float(dm.belief.get()), 3),
            "trust": round(float(dm.trust.get()), 3),
            "delta_belief": 0.0,  # No delta for standalone metrics call
            "delta_trust": 0.0,
            "rejection_type": (
                last_rej_info.get("rejection_type", "none") if last_rej_info else "none"
            ),
            "rejection_conf": (
                round(float(last_rej_info.get("rejection_confidence", 0.0)), 3)
                if last_rej_info
                else 0.0
            ),
            "sentiment": (
                last_rej_info.get("sentiment_label", "neutral")
                if last_rej_info
                else "neutral"
            ),
            "sentiment_score": (
                round(float(last_rej_info.get("sentiment_score", 0.0)), 3)
                if last_rej_info
                else 0.0
            ),
            "trust_concern": (
                last_rej_info.get("trust_concern", False) if last_rej_info else False
            ),
            "is_curiosity": (
                last_rej_info.get("is_curiosity", False) if last_rej_info else False
            ),
            "recovery_mode": dm.trust.recovery_mode,
            "strategy_weights": {
                k: round(float(v), 3) for k, v in dm.strategy.weights.items()
            },
            "consec_reject": dm.guard.consec_reject,
            "belief_history": [round(float(b), 3) for b in dm.belief.history],
            "trust_history": [round(float(t), 3) for t in dm.trust.history],
            "active": dm.active,
            "outcome": dm.outcome,
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
            "message": "Session reset",
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
            "impact": data.impact,
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
