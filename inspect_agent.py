from google.adk.agents import Agent
try:
    print("Agent fields:", Agent.model_fields.keys())
except Exception as e:
    print(f"Error inspecting Agent: {e}")
