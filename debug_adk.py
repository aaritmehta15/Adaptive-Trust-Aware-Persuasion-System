from src.voice_agent import VoiceAgent
import os

# Mock API Key
os.environ["GEMINI_API_KEY"] = "fake_key"

try:
    print("Attempting to initialize VoiceAgent pipeline...")
    from google.adk.agents import Agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    
    # 1. Agent
    # Try just name/desc
    agent = Agent(name="voice_agent", description="A voice agent")
    print(f"✅ Agent initialized: {agent}")
    
    # 2. Session Service
    session_service = InMemorySessionService()
    print("✅ Session Service initialized")
    
    # 3. Runner
    # Check if we can pass model here?
    try:
        runner = Runner(agent=agent, session_service=session_service)
        print("✅ Runner initialized")
    except Exception as e:
        print(f"❌ Runner initialization failed: {e}")
        
    # Check if we can set model on agent?
    # agent.model = "gemini..."?
    if hasattr(agent, 'model'):
        print("Agent has 'model' attribute")
    else:
        print("Agent DOES NOT have 'model' attribute")
        
except Exception as e:
    print(f"❌ Pipeline failed: {e}")
    import traceback
    traceback.print_exc()
