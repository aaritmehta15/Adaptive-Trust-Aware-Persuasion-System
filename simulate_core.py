
"""
Simulation of a non-HTTP caller (e.g., Voice Agent, CLI, background worker)
interacting with AtlasCore.
"""
import sys
import os
import json

# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.atlas_core import AtlasCore, AtlasRequest
from backend.session_store import add_session
from src.dialogue_manager import DialogueManager

# Mock Donation Context
MOCK_CTX = {
    "organization": "TestOrg",
    "cause": "Testing",
    "amounts": "10,20,30",
    "impact": "Test Impact"
}

class MockClient:
    """Simulate HF Client"""
    def text_generation(self, prompt, **kwargs):
        return "This is a simulated AI response."

def run_simulation():
    print("--- Starting AtlasCore Simulation ---")
    
    # 1. Initialize Core
    core = AtlasCore()
    print("1. AtlasCore initialized.")

    # 2. Manual Session Injection (Simulating separate setup)
    session_id = "sim_session_001"
    # We use a mock client for the DM to avoid needing real HF_TOKEN
    dm = DialogueManager(condition="C1", donation_ctx=MOCK_CTX, client=MockClient())
    dm.session_id = session_id
    add_session(session_id, dm)
    print(f"2. Session {session_id} injected into global store.")

    # 3. Simulate Turn 1 (User Input)
    user_text = "Tell me more about your cause."
    print(f"3. Processing input: '{user_text}'")
    
    req = AtlasRequest(session_id=session_id, text=user_text)
    response = core.process(req)
    
    # 4. output Analysis
    print("\n--- Response Received ---")
    print(f"Agent Message: {response['agent_msg']}")
    print(f"Metrics: Belief={response['metrics']['belief']}, Trust={response['metrics']['trust']}")
    print(f"Stop: {response['stop']}")
    
    if "history" in response:
        print(f"History items: {len(response['history'])}")
    
    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_simulation()
