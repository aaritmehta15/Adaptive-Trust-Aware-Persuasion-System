# ATLAS Voice Pipeline — Changelog & Reconstruction Document

**Purpose:** This document allows any engineer or AI agent to deterministically rebuild the complete, working Gemini ADK voice pipeline for the ATLAS system from a fresh clone. It records every change required, why it was required, and the exact implementation.

---

## Table of Contents

1. [Voice Architecture Overview](#1-voice-architecture-overview)
2. [Environment Requirements](#2-environment-requirements)
3. [Configuration Changes — `src/config.py`](#3-configuration-changes--srcconfigpy)
4. [Backend — `src/voice_agent.py` (New File)](#4-backend--srcvoice_agentpy-new-file)
5. [Backend — `backend/main.py` Modifications](#5-backend--backendmainpy-modifications)
6. [Frontend — `frontend/js/voice-client.js` (New File)](#6-frontend--frontendjsvoice-clientjs-new-file)
7. [Frontend — `frontend/js/audio-processor.js` (New File)](#7-frontend--frontendjsaudio-processorjs-new-file)
8. [Common Failures and Fixes](#8-common-failures-and-fixes)
9. [Clean Rebuild Checklist](#9-clean-rebuild-checklist)

---

## 1. Voice Architecture Overview

The voice pipeline is a fully bidirectional, real-time audio streaming system. Below is the complete data flow:

```
Browser Microphone
      │
      ▼
getUserMedia({ audio: { channelCount: 1, sampleRate: 16000 } })
      │
      ▼
AudioWorklet (pcm-processor — audio-processor.js)
  - Captures Float32 mic frames in process() callback
  - Forwards raw Float32 arrays to main thread via port.postMessage({ type: 'input_audio' })
      │
      ▼
VoiceClient.sendAudio() — voice-client.js
  - Converts Float32 → Int16 (multiply by 0x7FFF for positive, 0x8000 for negative)
  - Converts Int16 binary data → Base64 string via btoa()
  - Sends JSON over WebSocket: { mime_type: "audio/pcm", data: "<base64>" }
      │
      ▼
WebSocket ws://localhost:8000/ws/voice/{session_id}
      │
      ▼
FastAPI WebSocket handler — backend/main.py
  - Accepts connection
  - Creates LiveRequestQueue (ADK)
  - Creates ADK session via VoiceAgent.get_or_create_session()
  - Starts two concurrent async tasks via asyncio.gather():
      ├── receive_from_client() — Upstream task
      │     - Reads JSON text frames from WebSocket
      │     - Decodes Base64 → raw bytes
      │     - Calls live_queue.send_realtime(types.Blob(mime_type="audio/pcm;rate=16000", data=...))
      │
      └── send_to_client() — Downstream task
            - Calls VoiceAgent.process_stream() which is an async generator over runner.run_live()
            - For each event emitted by the ADK runner:
                - If event has audio content (inline_data with mime_type starting "audio/pcm"):
                    → Base64-encodes the raw bytes
                    → Sends: { type: "audio", data: "<base64>", turn_complete: bool }
                - If event.interrupted == True:
                    → Sends: { type: "interrupted" }
                - If event.turn_complete == True:
                    → Sends: { type: "turn_complete", turn_complete: true }
      │
      ▼
VoiceAgent.process_stream() — src/voice_agent.py
  - Wraps runner.run_live() as an async generator
  - runner is a google.adk.Runner instance wrapping the Agent
  - Agent is configured with model=Config.ADK_VOICE_MODEL
  - RunConfig specifies response_modalities=["AUDIO"] and SpeechConfig with voice_name="Puck"
      │
      ▼
Google ADK Runner → Gemini model (gemini-2.5-flash-native-audio-preview-12-2025)
  - Receives PCM audio stream
  - Generates audio response
  - Emits streaming events back through the runner
      │
      ▼
Back through send_to_client() → WebSocket → Browser
      │
      ▼
VoiceClient.playAudio() — voice-client.js
  - Base64 decodes the received data → Uint8Array
  - Reinterprets as Int16Array
  - Posts to AudioWorklet: port.postMessage({ type: 'audio_chunk', data: int16Data })
      │
      ▼
PCMProcessor.handleIncomingAudio() — audio-processor.js
  - Converts Int16 → Float32 by dividing by 32768.0
  - Writes into ring buffer (bufferSize = 4096 Float32 frames)
      │
      ▼
PCMProcessor.process() output stage
  - Reads from ring buffer into Web Audio output channel
  - Outputs silence (0.0) when buffer is empty
  - AudioContext is configured at sampleRate: 24000 (Gemini output rate)
      │
      ▼
Browser Speaker Output
```

### Session Lifecycle

Each WebSocket connection:
1. Generates a unique session ID on the backend with `VoiceAgent.generate_session_id()` (not the client-provided one, to prevent collisions).
2. Creates an ADK in-memory session via `InMemorySessionService`.
3. Runs the bidirectional stream.
4. On disconnect (any reason), `finally` block calls `VoiceAgent.delete_session()` to free ADK memory.

---

## 2. Environment Requirements

### Python Packages

```
google-adk==1.25.1     # Must be exactly this or higher; earlier versions have wrong import paths
google-genai>=1.64.0   # Required for types.Blob, types.SpeechConfig, types.VoiceConfig
fastapi
uvicorn
websockets
huggingface_hub
textblob
numpy
```

**Install ADK:**
```powershell
pip install google-adk
```

### Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | **Yes** | Gemini API authentication. Set before starting backend. |
| `GOOGLE_API_KEY` | Auto-set | ADK reads this; bridged automatically from `GEMINI_API_KEY` inside `VoiceAgent.__init__` |
| `HF_TOKEN` | Yes (for text mode) | HuggingFace token for Llama text model |

### PowerShell Startup

```powershell
# Set key
$env:GEMINI_API_KEY = "AIza..."

# Start backend (from project root)
python start_backend.py

# In a second terminal, start frontend
python start_frontend.py
```

### Gemini Model

The model used for voice:
```
gemini-2.5-flash-native-audio-preview-12-2025
```
This model supports `bidiGenerateContent` (bidirectional real-time audio). It must be specified via `Config.ADK_VOICE_MODEL` in `src/config.py`. Do **not** use `gemini-2.0-flash-exp` for voice — that model does not support the native audio preview required for live streaming.

---

## 3. Configuration Changes — `src/config.py`

### Change Required

Add `ADK_VOICE_MODEL` as a class-level attribute inside the `Config` class, near the other LLM model constants.

### Before

```python
class Config:
    MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
    TEMPERATURE = 0.8
    MAX_NEW_TOKENS = 64
    ...
```

### After

```python
class Config:
    MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
    ADK_VOICE_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
    TEMPERATURE = 0.8
    MAX_NEW_TOKENS = 64
    ...
```

### Why

`src/voice_agent.py` reads `Config.ADK_VOICE_MODEL` at init time. Without this constant, `VoiceAgent.__init__` raises `AttributeError`. Centralising the model name here means you only update it in one place if switching Gemini models.

---

## 4. Backend — `src/voice_agent.py` (New File)

This file did not exist in the original ATLAS codebase and must be created in full.

### Complete Final Implementation

```python
"""
Voice Agent — ADK Integration for ATLAS
Handles session lifecycle, model streaming, and cleanup.
"""
import os
import uuid
import logging

from google.adk import Runner
from google.adk.runners import LiveRequestQueue
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig          # CRITICAL: must use this path in v1.25.1
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = "ATLAS_System"
USER_ID = "atlas_user"


class VoiceAgent:
    def __init__(self):
        """Initialize the Voice Agent with ADK components."""
        # ── API Key Bridge ────────────────────────────────────────────
        # ADK authenticates via GOOGLE_API_KEY.
        # If only GEMINI_API_KEY is set, bridge it here so ADK picks it up.
        gemini_key = os.getenv("GEMINI_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")

        if gemini_key and not google_key:
            os.environ["GOOGLE_API_KEY"] = gemini_key
            logger.info("✓ Bridged GEMINI_API_KEY → GOOGLE_API_KEY for ADK")
        elif not gemini_key and not google_key:
            logger.error("❌ Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set. Voice mode will fail.")
            print("❌ Set GEMINI_API_KEY before starting the backend to use Voice Mode.")

        # ── Model ─────────────────────────────────────────────────────
        self.model_name = Config.ADK_VOICE_MODEL
        self.output_modality = "AUDIO"

        # ── Session Service ───────────────────────────────────────────
        self.session_service = InMemorySessionService()

        # ── Agent ─────────────────────────────────────────────────────
        # CRITICAL: pass model= directly in the constructor.
        # Do NOT try to set self.agent.model after construction via hasattr guard.
        self.agent = Agent(
            name="atlas_voice_agent",
            description="ATLAS Voice Agent for bidirectional audio",
            model=self.model_name,
            instruction=(
                "You are ATLAS, a natural conversational voice assistant.\n"
                "Speak clearly and naturally.\n"
                "Keep responses concise.\n"
                "Avoid long monologues.\n"
                "Pause naturally between ideas.\n"
                "Wait until the user finishes speaking before responding.\n"
                "Maintain conversational memory across turns.\n"
                "Do not rush your speech.\n"
                "Sound calm and human."
            ),
        )

        # ── Runner ────────────────────────────────────────────────────
        self.runner = Runner(
            agent=self.agent,
            session_service=self.session_service,
            app_name=APP_NAME,
        )

        logger.info(f"✓ Voice Agent initialized — model: {self.model_name}")

    @staticmethod
    def generate_session_id() -> str:
        """Generate a unique session ID (UUID-based)."""
        return f"voice_{uuid.uuid4().hex[:12]}"

    async def get_or_create_session(self, session_id: str):
        """
        Create a fresh session or reuse an existing one.
        Race-condition safe: handles 'already exists' errors gracefully.
        """
        try:
            existing = await self.session_service.get_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id,
            )
            if existing:
                logger.info(f"🔄 Reusing existing session: {session_id}")
                return existing
        except Exception:
            pass  # Session doesn't exist yet — create it below

        try:
            session = await self.session_service.create_session(
                session_id=session_id,
                user_id=USER_ID,
                app_name=APP_NAME,
            )
            logger.info(f"✨ Created new session: {session_id}")
            return session
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"🔄 Session {session_id} created concurrently, fetching it.")
                return await self.session_service.get_session(
                    app_name=APP_NAME,
                    user_id=USER_ID,
                    session_id=session_id,
                )
            raise

    async def delete_session(self, session_id: str):
        """Clean up session on disconnect. Best-effort — never raises."""
        try:
            await self.session_service.delete_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id,
            )
            logger.info(f"🗑️ Deleted session: {session_id}")
        except Exception as e:
            logger.warning(f"Session cleanup failed (non-fatal): {e}")

    def create_run_config(self) -> RunConfig:
        """Create RunConfig for ADK Voice Mode."""
        return RunConfig(
            response_modalities=[self.output_modality],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Puck"  # Options: Puck, Charon, Kore, Fenrir, Aoede
                    )
                )
            ),
        )

    async def process_stream(self, session_id: str, live_queue: LiveRequestQueue):
        """
        Async generator that yields events from the ADK Runner.
        Downstream (Agent → Client) half of the bidirectional loop.
        """
        run_config = self.create_run_config()
        async for event in self.runner.run_live(
            session_id=session_id,
            user_id=USER_ID,
            live_request_queue=live_queue,
            run_config=run_config,
        ):
            yield event
```

### Critical Implementation Notes

| Detail | Correct | Incorrect (do not use) |
|---|---|---|
| `RunConfig` import | `from google.adk.agents.run_config import RunConfig` | `from google.adk.agents import RunConfig` |
| `Runner` import | `from google.adk import Runner` | `from google.adk.runners import Runner` |
| Agent model | `Agent(model=self.model_name, ...)` in constructor | Post-construction `self.agent.model = ...` with `hasattr` guard |
| API key for ADK | `os.environ["GOOGLE_API_KEY"] = gemini_key` (bridged) | Expecting ADK to read `GEMINI_API_KEY` directly |

---

## 5. Backend — `backend/main.py` Modifications

### Changes Required vs Original File

The correct final version of `backend/main.py` must have all of the following. Any version that uses `AtlasVoiceAgent`, `atlas_core`, or `session_store` is an intermediate broken state and must be fully replaced.

#### 5.1 — Remove all AtlasVoiceAgent / atlas_core / session_store references

Delete any of the following if present:
```python
from .atlas_voice_agent import AtlasVoiceAgent    # DELETE
from src.atlas_core import AtlasCore, AtlasRequest  # DELETE
from .session_store import sessions, add_session, get_session  # DELETE
atlas_core = AtlasCore()  # DELETE
```

Replace sessions with the simple in-memory dict:
```python
sessions: Dict[str, DialogueManager] = {}
```

#### 5.2 — Import VoiceAgent at module level (safe)

```python
from src.voice_agent import VoiceAgent
```

This import is safe at module level because `VoiceAgent.__init__` does not call ADK until instantiated.

#### 5.3 — Move ADK imports to lazy (inside handler only)

Remove from module level:
```python
# DELETE these if present at module level:
from google.adk.runners import LiveRequestQueue
from google.genai import types
```

Add inside the `voice_websocket` handler body only:
```python
@app.websocket("/ws/voice/{session_id}")
async def voice_websocket(websocket: WebSocket, session_id: str):
    ...
    # Lazy imports — only here, never at module level
    from google.adk.runners import LiveRequestQueue
    from google.genai import types
    ...
```

**Why:** If ADK is broken or not installed, module-level ADK imports crash the entire server on startup — even for text-only requests. Lazy imports isolate the failure to the voice endpoint only.

#### 5.4 — Global voice_agent variable and startup init

```python
voice_agent = None  # Global, None until startup_event succeeds

@app.on_event("startup")
async def startup_event():
    # HF client init first...

    try:
        global voice_agent
        voice_agent = VoiceAgent()
        print("✓ Voice Agent initialized")

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            print(f"✓ GEMINI_API_KEY found: {api_key[:5]}...{api_key[-5:]}")
        else:
            print("❌ GEMINI_API_KEY NOT FOUND!")

    except Exception as e:
        print(f"✗ Voice Agent initialization failed: {e}")
        # voice_agent stays None — endpoint will reject gracefully
```

#### 5.5 — None guard at the top of the WebSocket handler

```python
@app.websocket("/ws/voice/{session_id}")
async def voice_websocket(websocket: WebSocket, session_id: str):
    if voice_agent is None:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "Voice agent failed to initialize. Check GEMINI_API_KEY and server logs."
        })
        await websocket.close(1011)
        return
```

Without this guard, if `VoiceAgent.__init__` failed, the first call to `voice_agent.generate_session_id()` raises `AttributeError: 'NoneType' object has no attribute 'generate_session_id'`.

#### 5.6 — Full WebSocket handler body (upstream + downstream)

```python
    from google.adk.runners import LiveRequestQueue
    from google.genai import types

    actual_session_id = voice_agent.generate_session_id()
    print(f"🔌 WS Connection: client={session_id} → actual={actual_session_id}")

    await websocket.accept()
    live_queue = None

    try:
        await voice_agent.get_or_create_session(actual_session_id)
        live_queue = LiveRequestQueue()

        async def receive_from_client():
            try:
                chunk_count = 0
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data.get("mime_type") == "audio/pcm":
                        audio_bytes = base64.b64decode(data["data"])
                        chunk_count += 1
                        if chunk_count <= 3 or chunk_count % 100 == 0:
                            print(f"🎤 Chunk #{chunk_count}: {len(audio_bytes)} bytes")
                        live_queue.send_realtime(
                            types.Blob(mime_type="audio/pcm;rate=16000", data=audio_bytes)
                        )
            except Exception as e:
                print(f"❌ Upstream error: {e}")
            finally:
                if live_queue:
                    live_queue.close()

        async def send_to_client():
            try:
                async for event in voice_agent.process_stream(actual_session_id, live_queue):
                    if hasattr(event, 'content') and event.content:
                        for part in event.content.parts:
                            if (hasattr(part, 'inline_data') and part.inline_data
                                    and part.inline_data.mime_type.startswith("audio/pcm")):
                                b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                                await websocket.send_json({
                                    "type": "audio",
                                    "data": b64,
                                    "turn_complete": getattr(event, 'turn_complete', False)
                                })
                    if getattr(event, 'interrupted', False):
                        await websocket.send_json({"type": "interrupted"})
                    if getattr(event, 'turn_complete', False):
                        await websocket.send_json({"type": "turn_complete", "turn_complete": True})
            except Exception as e:
                print(f"❌ Downstream error: {e}")
                import traceback; traceback.print_exc()

        await asyncio.gather(receive_from_client(), send_to_client())

    except Exception as e:
        print(f"❌ CRITICAL voice error: {e}")
        import traceback; traceback.print_exc()
    finally:
        await voice_agent.delete_session(actual_session_id)
```

---

## 6. Frontend — `frontend/js/voice-client.js` (New File)

This file must be created at `frontend/js/voice-client.js` and loaded by the main HTML page.

### Responsibilities

- Per-connection unique session ID generation (prevents "session already exists" on reconnection)
- AudioContext creation at 24000 Hz (Gemini output sample rate)
- AudioWorklet module loading (`audio-processor.js`)
- WebSocket lifecycle (connect, message handling, error, close)
- Microphone capture via `getUserMedia` at 16000 Hz mono
- `Float32 → Int16` PCM conversion
- Base64 encoding and JSON wrapping for upstream audio
- Base64 decoding and `Int16Array` creation for downstream audio
- Posting audio chunks to AudioWorklet for playback
- Buffer clear on interruption
- Full cleanup of mic tracks, AudioContext, and WebSocket on stop

### Complete Final Implementation

```javascript
/**
 * VoiceClient — Browser-side voice integration for ATLAS.
 */
class VoiceClient {
    constructor() {
        this.websocket = null;
        this.audioContext = null;
        this.workletNode = null;
        this.mediaStream = null;
        this.isActive = false;
        this.baseSampleRate = 16000;
    }

    _generateSessionId() {
        return 'voice_' + Math.random().toString(36).substring(2, 14);
    }

    async start() {
        if (this.isActive) return;
        try {
            console.log("🎙️ Starting Voice Client...");

            // AudioContext at 24kHz (Gemini output rate)
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 24000,
                latencyHint: 'interactive'
            });

            // Load AudioWorklet
            await this.audioContext.audioWorklet.addModule('js/audio-processor.js');

            // WebSocket with unique session ID
            const sessionId = this._generateSessionId();
            const baseUrl = (window.DEPLOYED_API_URL || 'http://localhost:8000').replace('http', 'ws');
            const wsUrl = `${baseUrl}/ws/voice/${sessionId}`;
            console.log(`🔌 Connecting to: ${wsUrl}`);
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log("✅ Voice WebSocket Connected");
                this.isActive = true;
                this.updateUI(true);
            };

            this.websocket.onmessage = async (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'audio') {
                        this.playAudio(msg.data);
                    } else if (msg.type === 'interrupted') {
                        this.clearAudioBuffer();
                    } else if (msg.type === 'error') {
                        console.error("🔴 Server Error:", msg.message);
                    } else if (msg.type === 'turn_complete') {
                        console.log("✅ Agent turn complete");
                    }
                } catch (e) {
                    console.error("Message parse error:", e);
                }
            };

            this.websocket.onclose = (event) => {
                console.log(`🔌 Voice WebSocket Closed (code: ${event.code})`);
                this.stop();
            };

            this.websocket.onerror = (error) => {
                console.error("❌ WebSocket Error:", error);
            };

            // Microphone at 16kHz mono
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: { channelCount: 1, sampleRate: 16000 }
            });

            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.workletNode = new AudioWorkletNode(this.audioContext, 'pcm-processor');

            this.workletNode.port.onmessage = (event) => {
                if (event.data.type === 'input_audio') {
                    this.sendAudio(event.data.data);
                }
            };

            source.connect(this.workletNode);
            this.workletNode.connect(this.audioContext.destination);
            console.log("🎤 Microphone active, streaming audio...");

        } catch (e) {
            console.error("❌ Failed to start voice client:", e);
            alert("Could not start voice mode: " + e.message);
            this.stop();
        }
    }

    stop() {
        this.isActive = false;
        this.updateUI(false);
        if (this.websocket) {
            try { this.websocket.close(); } catch (e) {}
            this.websocket = null;
        }
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        if (this.audioContext) {
            try { this.audioContext.close(); } catch (e) {}
            this.audioContext = null;
        }
        this.workletNode = null;
        console.log("🛑 Voice client stopped.");
    }

    sendAudio(float32Array) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) return;

        // Float32 → Int16
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            let s = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Int16 → Base64
        const uint8Array = new Uint8Array(int16Array.buffer);
        let binary = '';
        for (let i = 0; i < uint8Array.byteLength; i++) {
            binary += String.fromCharCode(uint8Array[i]);
        }

        this.websocket.send(JSON.stringify({
            mime_type: "audio/pcm",
            data: btoa(binary)
        }));
    }

    playAudio(base64Data) {
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        const int16Data = new Int16Array(bytes.buffer);

        if (this.workletNode) {
            this.workletNode.port.postMessage({ type: 'audio_chunk', data: int16Data });
        }
    }

    clearAudioBuffer() {
        if (this.workletNode) {
            this.workletNode.port.postMessage({ type: 'clear_buffer' });
        }
    }

    updateUI(active) {
        const btn = document.getElementById('voice-mode-btn');
        if (btn) {
            btn.textContent = active ? "🔴 Stop Voice" : "🎙️ Start Voice";
            btn.style.backgroundColor = active ? "#ff4444" : "";
        }
        const inputContainer = document.querySelector('.chat-input-container');
        if (inputContainer) {
            inputContainer.style.display = active ? 'none' : 'flex';
        }
    }
}

window.voiceClient = new VoiceClient();
```

### Key Design Decisions

- **`_generateSessionId()` in the browser:** Even though the WebSocket URL includes a session ID, the server overrides it with `voice_agent.generate_session_id()`. The browser generates its own unique ID just to keep the URL unique per connection attempt, preventing any WebSocket caching issues.
- **AudioContext at 24000 Hz:** Gemini's native audio output is 24kHz. The playback context must match this rate or audio will be pitched incorrectly.
- **Mic at 16000 Hz:** Gemini's audio input expects 16kHz PCM. The server sends `mime_type: "audio/pcm;rate=16000"` explicitly in the `Blob` metadata.
- **No reconnect logic:** Each session is unique and ephemeral. On close, stop is called. User must click Start Voice again.

---

## 7. Frontend — `frontend/js/audio-processor.js` (New File)

This file must be created at `frontend/js/audio-processor.js`. It runs inside an `AudioWorkletGlobalScope` — **not** in the main thread. It cannot access DOM or `window`.

### Complete Final Implementation

```javascript
class PCMProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bufferSize = 4096;
        this.buffer = new Float32Array(this.bufferSize);
        this.writeIndex = 0;
        this.readIndex = 0;

        this.port.onmessage = (event) => {
            if (event.data.type === 'audio_chunk') {
                this.handleIncomingAudio(event.data.data);
            } else if (event.data.type === 'clear_buffer') {
                this.writeIndex = 0;
                this.readIndex = 0;
            }
        };
    }

    handleIncomingAudio(int16Array) {
        for (let i = 0; i < int16Array.length; i++) {
            const floatVal = int16Array[i] / 32768.0;
            this.buffer[this.writeIndex] = floatVal;
            this.writeIndex = (this.writeIndex + 1) % this.bufferSize;
        }
    }

    process(inputs, outputs, parameters) {
        // Input: mic → main thread
        const input = inputs[0];
        if (input && input.length > 0) {
            this.port.postMessage({
                type: 'input_audio',
                data: input[0]   // Float32Array for channel 0
            });
        }

        // Output: ring buffer → speaker
        const output = outputs[0];
        if (output && output.length > 0) {
            const outputChannel = output[0];
            for (let i = 0; i < outputChannel.length; i++) {
                if (this.readIndex !== this.writeIndex) {
                    outputChannel[i] = this.buffer[this.readIndex];
                    this.readIndex = (this.readIndex + 1) % this.bufferSize;
                } else {
                    outputChannel[i] = 0;  // silence when empty
                }
            }
            for (let ch = 1; ch < output.length; ch++) {
                output[ch].set(outputChannel);
            }
        }

        return true;  // keep processor alive
    }
}

registerProcessor('pcm-processor', PCMProcessor);
```

### Ring Buffer Behavior

- `bufferSize = 4096` Float32 frames
- Write pointer advances modulo bufferSize
- Read pointer follows write pointer
- When `readIndex === writeIndex`, the buffer is empty → silence output (0.0)
- On `clear_buffer` message (interruption), both indices reset to 0, immediately silencing output
- No overflow protection (if write outruns read, old samples are overwritten — acceptable for real-time audio)

### Conversion

- **Incoming (server → speaker):** Int16 `/ 32768.0` → Float32 in range `[-1.0, 1.0]`
- **Outgoing (mic → server):** `Float32 * 0x7FFF` (positive) or `* 0x8000` (negative) → Int16, done in `voice-client.js`'s `sendAudio()`

---

## 8. Common Failures and Fixes

### F1 — `ModuleNotFoundError: No module named 'google.adk'`

**Symptom:** Server crashes immediately on startup or `from src.voice_agent import VoiceAgent` fails.

**Cause:** `google-adk` package not installed.

**Fix:**
```powershell
pip install google-adk
```

**Verify:**
```python
import google.adk; print(google.adk.__version__)
# Expected: 1.25.1 or higher
```

---

### F2 — `ImportError: cannot import name 'RunConfig' from 'google.adk.agents'`

**Symptom:** `VoiceAgent.__init__` raises ImportError at module load time.

**Cause:** In ADK v1.25.1, `RunConfig` is NOT exported from `google.adk.agents`. It lives at `google.adk.agents.run_config`.

**Wrong:**
```python
from google.adk.agents import Agent, RunConfig  # BROKEN in v1.25.1
```

**Correct:**
```python
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig  # CORRECT
```

---

### F3 — Model does not support `bidiGenerateContent`

**Symptom:** `runner.run_live()` raises an API error about the model not supporting live streaming.

**Cause:** Using `gemini-2.0-flash-exp` or another non-native-audio model.

**Fix:** Set `Config.ADK_VOICE_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"` in `src/config.py`.

---

### F4 — `AttributeError: 'NoneType' object has no attribute 'generate_session_id'`

**Symptom:** WebSocket connection accepted but immediately raises 500 error.

**Cause:** `voice_agent` global is `None` because `VoiceAgent.__init__` failed, but there is no None guard at the start of the WebSocket handler.

**Fix:** Add at the very top of `voice_websocket()`:
```python
if voice_agent is None:
    await websocket.accept()
    await websocket.send_json({"type": "error", "message": "Voice agent failed to initialize."})
    await websocket.close(1011)
    return
```

---

### F5 — ADK auth error / `GOOGLE_API_KEY` not set

**Symptom:** `VoiceAgent` initializes, session creates, but `runner.run_live()` returns an authentication error immediately.

**Cause:** ADK authenticates via `GOOGLE_API_KEY`, but the user set `GEMINI_API_KEY`. These are different environment variable names; ADK does not read `GEMINI_API_KEY` automatically.

**Fix:** In `VoiceAgent.__init__`, bridge the key:
```python
gemini_key = os.getenv("GEMINI_API_KEY")
google_key = os.getenv("GOOGLE_API_KEY")
if gemini_key and not google_key:
    os.environ["GOOGLE_API_KEY"] = gemini_key
```

This is applied before the Runner is constructed, so ADK picks it up at runtime.

---

### F6 — `AttributeError: type object 'Config' has no attribute 'ADK_VOICE_MODEL'`

**Symptom:** `VoiceAgent.__init__` crashes at `self.model_name = Config.ADK_VOICE_MODEL`.

**Cause:** `ADK_VOICE_MODEL` was not added to the `Config` class in `src/config.py`.

**Fix:** Add to `Config`:
```python
ADK_VOICE_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
```

---

### F7 — WebSocket opens then immediately closes (code 1011)

**Symptom:** Browser console shows `✅ Voice WebSocket Connected` then `🔌 Voice WebSocket Closed (code: 1011)` within milliseconds.

**Cause:** `voice_agent is None` guard correctly fired, meaning `VoiceAgent.__init__` failed silently. Check server logs for the actual error.

**Debug:** Look in the backend terminal for lines starting with `✗ Voice Agent initialization failed:`.

---

### F8 — API key reported as leaked by GitHub / Google

**Symptom:** GitHub or Google sends an automatic email saying a Gemini API key was detected in a commit.

**Cause:** The API key was committed to a file (e.g., hardcoded in source or accidentally included in a committed `.env`, `.txt`, or `.json` file).

**Fix:**
1. Revoke the compromised key at [Google AI Studio](https://aistudio.google.com/apikey)
2. Generate a new key
3. Never hardcode API keys — always use `$env:GEMINI_API_KEY = "..."` in the terminal session only
4. Add `.env` and any output `.txt` files to `.gitignore`

---

### F9 — `uvicorn --reload` causes double-import crash

**Symptom:** Server starts cleanly once but crashes on reload.

**Cause:** Uvicorn's reload mode re-imports modules. Some ADK objects may not handle re-import cleanly.

**Fix:** Start without `--reload`:
```powershell
python start_backend.py
# or explicitly:
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## 9. Clean Rebuild Checklist

Use this checklist on a fresh clone of the ATLAS repository to bring the voice pipeline to full working state.

### Prerequisites

```
[ ] Python 3.10+ installed
[ ] pip available
[ ] Valid Gemini API key from https://aistudio.google.com/apikey
[ ] Valid HuggingFace token from https://huggingface.co/settings/tokens
```

### Step 1 — Install Dependencies

```powershell
pip install google-adk google-genai fastapi uvicorn websockets huggingface_hub textblob numpy
```

Verify ADK version:
```powershell
python -c "import google.adk; print(google.adk.__version__)"
# Must print: 1.25.1 or higher
```

Verify all required ADK symbols exist:
```python
from google.adk import Runner
from google.adk.runners import LiveRequestQueue
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig
from google.adk.sessions import InMemorySessionService
from google.genai import types
assert hasattr(types, 'Blob')
assert hasattr(types, 'SpeechConfig')
assert hasattr(types, 'VoiceConfig')
assert hasattr(types, 'PrebuiltVoiceConfig')
print("All ADK symbols OK")
```

### Step 2 — Add `ADK_VOICE_MODEL` to `src/config.py`

Open `src/config.py`. Inside the `Config` class, add after `MODEL_NAME`:
```python
ADK_VOICE_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
```

### Step 3 — Create `src/voice_agent.py`

Create the file with the complete implementation from [Section 4](#4-backend--srcvoice_agentpy-new-file) of this document.

### Step 4 — Update `backend/main.py`

Apply all changes from [Section 5](#5-backend--backendmainpy-modifications):

```
[ ] VoiceAgent imported at module level (not ADK submodules)
[ ] voice_agent global initialized to None
[ ] startup_event() instantiates VoiceAgent() and catches exceptions
[ ] GEMINI_API_KEY check logged at startup
[ ] @app.websocket("/ws/voice/{session_id}") handler defined
[ ] voice_agent is None guard at top of handler
[ ] Lazy imports of LiveRequestQueue and types inside handler
[ ] receive_from_client() upstream task implemented
[ ] send_to_client() downstream task implemented
[ ] asyncio.gather() runs both tasks concurrently
[ ] finally block calls voice_agent.delete_session()
```

### Step 5 — Create `frontend/js/audio-processor.js`

Create the file with the complete implementation from [Section 7](#7-frontend--frontendjsaudio-processorjs-new-file).

### Step 6 — Create `frontend/js/voice-client.js`

Create the file with the complete implementation from [Section 6](#6-frontend--frontendjsvoice-clientjs-new-file).

Ensure it is loaded in `frontend/index.html`:
```html
<script src="js/audio-processor.js"></script>
<script src="js/voice-client.js"></script>
```

Ensure the Start Voice button exists with the correct ID:
```html
<button id="voice-mode-btn" onclick="window.voiceClient.start()">🎙️ Start Voice</button>
```

### Step 7 — Verify Import Chain

```powershell
cd <project_root>
python verify_restore.py
# All checks must print PASS
```

Or manually:
```python
import sys; sys.path.insert(0, '.')
from src.voice_agent import VoiceAgent
print("VoiceAgent: OK")
```

### Step 8 — Start Backend

```powershell
$env:GEMINI_API_KEY = "AIza..."
$env:HF_TOKEN = "hf_..."
python start_backend.py
```

Expected startup log lines:
```
✓ Bridged GEMINI_API_KEY → GOOGLE_API_KEY for ADK
INFO:src.voice_agent:✓ Voice Agent initialized — model: gemini-2.5-flash-native-audio-preview-12-2025
✓ Voice Agent initialized
✓ GEMINI_API_KEY found: AIza...xxxxx
```

### Step 9 — Start Frontend

```powershell
python start_frontend.py
```

### Step 10 — Browser Test

```
[ ] Open frontend in Chrome or Edge (Firefox has stricter AudioWorklet policies)
[ ] Open DevTools (F12) → Console tab
[ ] Click "🎙️ Start Voice"
[ ] Grant microphone permission when prompted
[ ] Expected console output:
      🎙️ Starting Voice Client...
      🔌 Connecting to: ws://localhost:8000/ws/voice/voice_abc123...
      ✅ Voice WebSocket Connected
      🎤 Microphone active, streaming audio...
[ ] Expected backend log output:
      🔌 WS Connection: client=voice_abc... → actual=voice_xyz...
      ✅ WS Accepted: voice_xyz...
      📦 Step 1: Getting/Creating ADK Session...
      ✅ Step 1 PASSED: Session ready
      📦 Step 2: Creating LiveRequestQueue...
      ✅ Step 2 PASSED
      🚀 Step 4: Starting concurrent upstream + downstream...
      🎤 Chunk #1: 512 bytes
      🎤 Chunk #2: 512 bytes
      📤 Event: LiveServerMessage
[ ] Speak into microphone — agent should respond with audio
[ ] Click "🔴 Stop Voice" — connection closes cleanly
[ ] Backend log shows:
      🔌 Disconnecting: voice_xyz...
      🗑️ Deleted session: voice_xyz...
      🧹 Session cleaned up: voice_xyz...
```

---

*Document generated February 2026. Reflects ADK v1.25.1, google-genai v1.64.0, and gemini-2.5-flash-native-audio-preview-12-2025.*
