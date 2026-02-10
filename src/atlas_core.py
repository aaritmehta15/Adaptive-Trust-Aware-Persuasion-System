"""
Atlas Core Logic Wrapper
Encapsulates persuasion logic for use by API, Voice, and other clients.
"""

from typing import Dict, Optional, Any, List
from pydantic import BaseModel
from datetime import datetime
import sys
import os

# Add project root to sys.path to resolve 'backend' and 'src' imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import existing logic (DO NOT REWRITE)
from backend.session_store import get_session
from src.dialogue_manager import DialogueManager

class AtlasRequest(BaseModel):
    """Standard input for Atlas Core"""
    session_id: str
    text: str
    # Future extensibility: context, metadata, etc.


class AtlasResponse(BaseModel):
    """Standard output for Atlas Core"""
    agent_msg: str
    metrics: Dict[str, Any]
    stop: bool
    reason: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None # For frontend debug


class AtlasCore:
    """
    Core interface for ATLAS Persuasion System.
    Connects inputs (text) to the persuasion engine (DialogueManager).
    """

    def process(self, request: AtlasRequest) -> Dict[str, Any]:
        """
        Process a user message through the persuasion pipeline.
        Returns a dictionary matching the API response format.
        """
        
        # 1. Retrieve Session
        dm: Optional[DialogueManager] = get_session(request.session_id)
        
        if not dm:
            raise ValueError(f"Session not found: {request.session_id}")

        # 2. Check Active State
        if not dm.active:
            # Session already ended
            return {
                "agent_msg": dm._closing(dm.outcome or "Session ended"),
                "metrics": {
                    "turn": dm.turn,
                    "belief": round(float(dm.belief.get()), 3),
                    "trust": round(float(dm.trust.get()), 3),
                    "stop": True,
                    "reason": dm.outcome,
                },
                "stop": True,
                "reason": dm.outcome
            }

        # 3. Run Persuasion Logic (Delegate to DM)
        # This runs detection -> update belief/trust -> guardrails -> strategy -> synthesis
        result = dm.process(request.text)

        # 4. augment result with history (logic from main.py)
        # Include history for frontend
        result["history"] = dm.history
        
        # Include belief/trust history for graph
        # Initialize metrics if not present (defensive)
        if "metrics" not in result:
             # Should not happen given DM.process implementation, but good for safety
             result["metrics"] = {}

        result["metrics"]["belief_history"] = [round(float(b), 3) for b in dm.belief.history]
        result["metrics"]["trust_history"] = [round(float(t), 3) for t in dm.trust.history]

        return result
