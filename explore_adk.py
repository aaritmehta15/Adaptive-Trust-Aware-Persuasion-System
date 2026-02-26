from google.adk.agents import Agent
import inspect

print("Agent dir:", dir(Agent))
try:
    print("Agent init signature:", inspect.signature(Agent.__init__))
except Exception as e:
    print("Could not get signature:", e)

from google.adk.sessions import InMemorySessionService
try:
    print("SessionService.create_session signature:", inspect.signature(InMemorySessionService.create_session))
except Exception as e:
    print("Could not get signature:", e)
