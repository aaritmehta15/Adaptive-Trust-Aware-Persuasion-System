from google.adk import Runner
import inspect

try:
    print("Runner init signature:", inspect.signature(Runner.__init__))
except Exception as e:
    print("Could not get signature:", e)
