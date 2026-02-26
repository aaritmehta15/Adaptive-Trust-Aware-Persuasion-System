"""
ATLAS Voice Feature - Comprehensive Test Suite
"""
import os, sys, importlib, importlib.util, ast, re, json

sys.path.insert(0, '.')
results = {}

print("=" * 60)
print("ATLAS VOICE FEATURE - COMPREHENSIVE TEST REPORT")
print("=" * 60)

# === TEST 1: Dependency Check ===
print("\n[TEST 1] Dependency Availability")
deps = {
    'google.adk': 'google-adk (ADK core)',
    'google.adk.runners': 'google-adk.runners (LiveRequestQueue)',
    'google.adk.agents': 'google-adk.agents (Agent, RunConfig)',
    'google.adk.sessions': 'google-adk.sessions (InMemorySessionService)',
    'google.genai': 'google-genai (types)',
    'google.genai.types': 'google-genai.types (Blob, SpeechConfig)',
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'websockets': 'websockets',
    'huggingface_hub': 'huggingface_hub',
    'textblob': 'textblob',
    'numpy': 'numpy',
}
dep_results = {}
for mod, label in deps.items():
    try:
        m = importlib.import_module(mod)
        ver = getattr(m, '__version__', 'installed')
        status = 'PASS'
        dep_results[label] = (status, ver)
        print(f"  PASS  {label}: {ver}")
    except ImportError as e:
        status = 'FAIL'
        dep_results[label] = (status, str(e))
        print(f"  FAIL  {label}: {e}")
results['dependencies'] = dep_results

# === TEST 2: Environment Variables ===
print("\n[TEST 2] Environment Variables")
hf = os.getenv('HF_TOKEN')
gemini = os.getenv('GEMINI_API_KEY')
google = os.getenv('GOOGLE_API_KEY')
env_results = {
    'HF_TOKEN': 'SET' if hf else 'NOT SET',
    'GEMINI_API_KEY': 'SET' if gemini else 'NOT SET',
    'GOOGLE_API_KEY': 'SET' if google else 'NOT SET',
}
for k, v in env_results.items():
    status = 'PASS' if v == 'SET' else 'FAIL'
    print(f"  {status}  {k}: {v}")
results['env_vars'] = env_results

# === TEST 3: Core Module Imports ===
print("\n[TEST 3] Core Module Imports (non-voice)")
core_mods = ['src.config','src.trackers','src.rejection_detector','src.off_topic_detector',
             'src.strategy_adapter','src.guardrails','src.llm_agent','src.dialogue_manager']
core_results = {}
for m in core_mods:
    try:
        importlib.import_module(m)
        core_results[m] = 'PASS'
        print(f"  PASS  {m}")
    except Exception as e:
        core_results[m] = f'FAIL: {e}'
        print(f"  FAIL  {m}: {e}")
results['core_imports'] = core_results

# === TEST 4: voice_agent.py Syntax ===
print("\n[TEST 4] voice_agent.py Syntax Check")
with open('src/voice_agent.py', 'r', encoding='utf-8') as f:
    va_source = f.read()
try:
    ast.parse(va_source)
    results['voice_agent_syntax'] = 'PASS'
    print("  PASS  voice_agent.py syntax OK")
except SyntaxError as e:
    results['voice_agent_syntax'] = f'FAIL: {e}'
    print(f"  FAIL  Syntax error: {e}")

# Extract and check imports from voice_agent.py
print("\n[TEST 5] voice_agent.py Import Analysis")
va_imports = []
for node in ast.walk(ast.parse(va_source)):
    if isinstance(node, ast.ImportFrom):
        entry = f"from {node.module} import {[a.name for a in node.names]}"
        va_imports.append(entry)
        print(f"  {entry}")
    elif isinstance(node, ast.Import):
        entry = f"import {[a.name for a in node.names]}"
        va_imports.append(entry)
        print(f"  {entry}")
results['voice_agent_imports'] = va_imports

# === TEST 6: voice_agent.py Runtime Import ===
print("\n[TEST 6] voice_agent.py Runtime Import")
try:
    from src.voice_agent import VoiceAgent
    results['voice_agent_import'] = 'PASS'
    print("  PASS  VoiceAgent imported OK")
except Exception as e:
    results['voice_agent_import'] = f'FAIL: {type(e).__name__}: {e}'
    print(f"  FAIL  {type(e).__name__}: {e}")

# === TEST 7: backend/main.py Import ===
print("\n[TEST 7] backend/main.py Runtime Import")
try:
    spec = importlib.util.spec_from_file_location('backend_main', 'backend/main.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    results['backend_import'] = 'PASS'
    print("  PASS  backend/main.py imported OK")
except Exception as e:
    results['backend_import'] = f'FAIL: {type(e).__name__}: {e}'
    print(f"  FAIL  {type(e).__name__}: {e}")

# === TEST 8: Frontend voice-client.js Analysis ===
print("\n[TEST 8] Frontend voice-client.js Feature Checks")
with open('frontend/js/voice-client.js', 'r', encoding='utf-8') as f:
    vc_source = f.read()
frontend_checks = {
    'WebSocket instantiation': 'new WebSocket' in vc_source,
    'Unique session ID generation': '_generateSessionId' in vc_source,
    'Microphone getUserMedia': 'getUserMedia' in vc_source,
    'AudioWorklet module load': 'addModule' in vc_source,
    'AudioWorkletNode creation': 'AudioWorkletNode' in vc_source,
    'PCM mime_type sent to server': '"audio/pcm"' in vc_source,
    'Base64 encoding (btoa)': 'btoa(' in vc_source,
    'Int16 conversion': 'Int16Array' in vc_source,
    'Audio playback (playAudio)': 'playAudio' in vc_source,
    'Interruption handling': "'interrupted'" in vc_source,
    'Turn complete handling': 'turn_complete' in vc_source,
    'Mic track cleanup on stop': 'getTracks' in vc_source,
    'AudioContext cleanup on stop': 'audioContext.close' in vc_source,
    'Input audio forwarded to WS': "'input_audio'" in vc_source,
    'WS URL uses ws:// protocol': "replace('http', 'ws')" in vc_source,
    'Connection to /ws/voice/ path': '/ws/voice/' in vc_source,
}
fc = {}
for k, v in frontend_checks.items():
    s = 'PASS' if v else 'FAIL'
    fc[k] = s
    print(f"  {s}  {k}")
results['frontend_voice_client'] = fc

# === TEST 9: audio-processor.js Analysis ===
print("\n[TEST 9] audio-processor.js (AudioWorklet) Feature Checks")
with open('frontend/js/audio-processor.js', 'r', encoding='utf-8') as f:
    ap_source = f.read()
audio_checks = {
    'Extends AudioWorkletProcessor': 'extends AudioWorkletProcessor' in ap_source,
    'Ring buffer (writeIndex)': 'writeIndex' in ap_source,
    'Ring buffer (readIndex)': 'readIndex' in ap_source,
    'Mic input forwarded (input_audio)': "'input_audio'" in ap_source,
    'Playback output channel written': 'outputChannel' in ap_source,
    'registerProcessor called': "registerProcessor('pcm-processor'" in ap_source,
    'Int16 to Float32 (/ 32768)': '32768' in ap_source,
    'Buffer clear on interruption': "'clear_buffer'" in ap_source,
    'Incoming audio handled': "'audio_chunk'" in ap_source,
}
ac = {}
for k, v in audio_checks.items():
    s = 'PASS' if v else 'FAIL'
    ac[k] = s
    print(f"  {s}  {k}")
results['audio_processor'] = ac

# === TEST 10: Model Name Consistency ===
print("\n[TEST 10] Model Name Consistency")
va_model_m = re.search(r"self\.model_name\s*=\s*[\"'](.*?)[\"']", va_source)
cfg_source = open('src/config.py', 'r').read()
cfg_model_m = re.search(r"ADK_VOICE_MODEL\s*=\s*[\"'](.*?)[\"']", cfg_source)
va_model = va_model_m.group(1) if va_model_m else 'NOT FOUND'
cfg_model = cfg_model_m.group(1) if cfg_model_m else 'NOT FOUND'
match = va_model == cfg_model
print(f"  voice_agent.py model: {va_model}")
print(f"  config.py ADK_VOICE_MODEL: {cfg_model}")
print(f"  {'WARN' if not match else 'PASS'}  Models {'DO NOT match' if not match else 'match'}")
results['model_consistency'] = {
    'voice_agent_model': va_model,
    'config_ADK_VOICE_MODEL': cfg_model,
    'match': match
}

# === TEST 11: WebSocket Protocol Check ===
print("\n[TEST 11] WebSocket Protocol in Frontend Config")
with open('frontend/config.js', 'r') as f:
    cfg_js = f.read()
localhost_mode = 'localhost:8000' in cfg_js
deployed_active = 'onrender.com' in cfg_js and not all(
    l.strip().startswith('//') for l in cfg_js.split('\n') if 'onrender.com' in l
)
print(f"  Target: {'localhost:8000' if localhost_mode else 'deployed'}")
print(f"  Deployed URL active: {deployed_active}")
results['frontend_config'] = {
    'mode': 'localhost' if localhost_mode else 'deployed',
    'deployed_url_active': deployed_active
}

# === TEST 12: voice_agent.py Logic Checks ===
print("\n[TEST 12] voice_agent.py Logic Checks")
logic_checks = {
    'generate_session_id() defined': 'def generate_session_id' in va_source,
    'get_or_create_session() defined': 'def get_or_create_session' in va_source,
    'delete_session() defined': 'def delete_session' in va_source,
    'process_stream() async generator': 'async def process_stream' in va_source,
    'runner.run_live() used': 'run_live' in va_source,
    'RunConfig with AUDIO modality': 'AUDIO' in va_source,
    'SpeechConfig defined': 'SpeechConfig' in va_source,
    'PrebuiltVoiceConfig defined': 'PrebuiltVoiceConfig' in va_source,
    'Voice name set (Puck)': 'Puck' in va_source,
    'InMemorySessionService used': 'InMemorySessionService' in va_source,
    'GEMINI_API_KEY checked at init': 'GEMINI_API_KEY' in va_source,
    'Session cleanup on disconnect': 'delete_session' in va_source,
}
lc = {}
for k, v in logic_checks.items():
    s = 'PASS' if v else 'FAIL'
    lc[k] = s
    print(f"  {s}  {k}")
results['voice_agent_logic'] = lc

# === SUMMARY ===
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

critical_fails = []

# Check critical deps
for label, (status, _) in dep_results.items():
    if status == 'FAIL' and 'google' in label.lower():
        critical_fails.append(f"Missing dependency: {label}")

# Check env vars
if env_results['GEMINI_API_KEY'] == 'NOT SET':
    critical_fails.append("GEMINI_API_KEY environment variable not set")
if env_results['GOOGLE_API_KEY'] == 'NOT SET':
    critical_fails.append("GOOGLE_API_KEY environment variable not set")

# Check imports
if 'FAIL' in results.get('voice_agent_import', ''):
    critical_fails.append("src.voice_agent cannot be imported at runtime")
if 'FAIL' in results.get('backend_import', ''):
    critical_fails.append("backend/main.py cannot be imported (backend will crash on start)")

# Check model mismatch
if not results['model_consistency']['match']:
    critical_fails.append(f"Model name mismatch: voice_agent uses '{va_model}' but config has '{cfg_model}'")

print(f"\nTotal Critical Issues Found: {len(critical_fails)}")
for i, f in enumerate(critical_fails, 1):
    print(f"  {i}. {f}")

results['summary'] = {
    'critical_issues': critical_fails,
    'voice_feature_functional': len(critical_fails) == 0
}

print(f"\nVoice Feature Status: {'WORKING' if len(critical_fails) == 0 else 'BROKEN - ' + str(len(critical_fails)) + ' critical issues'}")

with open('voice_test_report.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)
print("\nFull report saved to voice_test_report.json")
