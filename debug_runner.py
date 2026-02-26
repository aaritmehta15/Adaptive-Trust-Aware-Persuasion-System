import asyncio
from src.voice_agent import VoiceAgent
from google.adk.runners import LiveRequestQueue

async def main():
    print("Initializing VoiceAgent...")
    va = VoiceAgent()
    print("Creating Session...")
    await va.create_session("test_session")
    
    print("Testing process_stream...")
    queue = LiveRequestQueue()
    try:
        async for event in va.process_stream("test_session", queue):
            print(f"Event: {event}")
            break # Just need one to prove it starts
        print("✅ process_stream started successfully")
    except Exception as e:
        print(f"❌ process_stream failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await queue.close()

if __name__ == "__main__":
    asyncio.run(main())
