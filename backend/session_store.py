# Global Session Store
# This ensures that both the API and the Voice Bridge share the exact same dictionary object.

from typing import Dict, Any

# The single source of truth for active sessions
sessions: Dict[str, Any] = {}

def get_session(session_id: str):
    return sessions.get(session_id)

def add_session(session_id: str, session_obj: Any):
    sessions[session_id] = session_obj
    print(f"[STORE] Session added: {session_id}. Total: {len(sessions)}. Store ID: {id(sessions)}")

def list_sessions():
    return list(sessions.keys())
