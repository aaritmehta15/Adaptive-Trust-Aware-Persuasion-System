import sys, importlib.util
sys.path.insert(0, '.')
results = []

# 1. VoiceAgent import
try:
    from src.voice_agent import VoiceAgent
    results.append('PASS  src/voice_agent.py imports cleanly')
except Exception as e:
    results.append(f'FAIL  src/voice_agent.py: {e}')

# 2. backend/main.py import
try:
    spec = importlib.util.spec_from_file_location('main', 'backend/main.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    results.append('PASS  backend/main.py imports cleanly')
except Exception as e:
    results.append(f'FAIL  backend/main.py: {e}')

# 3. Check bad old imports are gone from main.py
main_src = open('backend/main.py', encoding='utf-8').read()
bad = ['AtlasVoiceAgent', 'atlas_core', 'session_store', 'from .']
for b in bad:
    results.append(('FAIL' if b in main_src else 'PASS') + f'  backend clean of: {b}')

# 4. Required features in main.py
checks = [
    ('voice_agent is None guard',         'if voice_agent is None'),
    ('Lazy LiveRequestQueue import',       'from google.adk.runners import LiveRequestQueue'),
    ('Lazy types import',                  'from google.genai import types'),
    ('WS route /ws/voice/',               '/ws/voice/{session_id}'),
    ('Upstream receive_from_client',       'receive_from_client'),
    ('Downstream send_to_client',          'send_to_client'),
    ('asyncio.gather concurrent run',      'asyncio.gather'),
    ('Session cleanup in finally',         'delete_session'),
]
for label, token in checks:
    results.append(('PASS' if token in main_src else 'FAIL') + f'  {label}')

# 5. voice_agent.py checks
va_src = open('src/voice_agent.py', encoding='utf-8').read()
va_checks = [
    ('GEMINI->GOOGLE_API_KEY bridge',   'os.environ["GOOGLE_API_KEY"] = gemini_key'),
    ('Model from Config',               'Config.ADK_VOICE_MODEL'),
    ('ATLAS system instruction',        'You are ATLAS'),
    ('RunConfig correct import',        'from google.adk.agents.run_config import RunConfig'),
    ('Runner from google.adk',          'from google.adk import Runner'),
]
for label, token in va_checks:
    results.append(('PASS' if token in va_src else 'FAIL') + f'  {label}')

with open('restore_verify.txt', 'w') as f:
    f.write('\n'.join(results))
print('\n'.join(results))
