/**
 * VoiceClient — Browser-side voice integration for ATLAS.
 *
 * Two-AudioContext architecture (matches Google ADK bidi-demo reference):
 *
 *   recorderContext (16kHz)
 *     └── getUserMedia stream → pcm-recorder-processor worklet
 *           └── port.onmessage → Float32 frames → sendAudio() → WebSocket
 *
 *   playerContext (24kHz)  ← matches Gemini native audio output rate
 *     └── pcm-player-processor worklet (ring buffer: 60 s × 24kHz)
 *           └── connected to playerContext.destination → speakers
 *
 * This separation ensures:
 *   - Mic is captured at the exact rate Gemini expects (16kHz)
 *   - Playback runs at the exact rate Gemini produces (24kHz)
 *   - Mic audio is NOT looped back through the speakers
 *   - No unintended resampling by the browser
 */
class VoiceClient {
    constructor() {
        this.websocket = null;

        // Two separate AudioContexts — one per direction
        this.recorderContext = null;   // 16 kHz  — mic capture only
        this.playerContext = null;   // 24 kHz  — server audio playback only

        this.recorderNode = null;      // pcm-recorder-processor worklet node
        this.playerNode = null;      // pcm-player-processor worklet node

        this.mediaStream = null;       // Raw getUserMedia stream (for cleanup)
        this.isActive = false;
    }

    // ── Session ID ─────────────────────────────────────────────────────────
    _generateSessionId() {
        return 'voice_' + Math.random().toString(36).substring(2, 14);
    }

    // ── Start ──────────────────────────────────────────────────────────────
    async start() {
        if (this.isActive) return;

        try {
            console.log('🎙️ Starting Voice Client...');

            // ── 1. Player AudioContext at 24kHz (Gemini output rate) ───────
            this.playerContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 24000,
                latencyHint: 'interactive',
            });
            console.log(`🔊 Player AudioContext: sampleRate=${this.playerContext.sampleRate}`);
            await this.playerContext.audioWorklet.addModule('js/audio-player-processor.js');

            this.playerNode = new AudioWorkletNode(this.playerContext, 'pcm-player-processor');
            this.playerNode.connect(this.playerContext.destination);

            // ── 2. Recorder AudioContext at 16kHz (Gemini input rate) ─────
            this.recorderContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000,
                latencyHint: 'interactive',
            });
            console.log(`🎤 Recorder AudioContext: sampleRate=${this.recorderContext.sampleRate}`);
            await this.recorderContext.audioWorklet.addModule('js/audio-processor.js');

            // ── 3. Microphone (captured at 16kHz via recorderContext) ─────
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                }
            });

            const source = this.recorderContext.createMediaStreamSource(this.mediaStream);
            this.recorderNode = new AudioWorkletNode(this.recorderContext, 'pcm-recorder-processor');

            // Mic frames arrive as Float32 at 16kHz → convert and send upstream
            this.recorderNode.port.onmessage = (event) => {
                this.sendAudio(event.data); // event.data is a copied Float32Array
            };

            // Recorder chain: mic → recorder worklet (NOT connected to destination)
            source.connect(this.recorderNode);
            // NOTE: recorderNode intentionally NOT connected to destination — no mic loopback

            // ── 4. WebSocket ───────────────────────────────────────────────
            const sessionId = this._generateSessionId();
            const baseUrl = (window.DEPLOYED_API_URL || 'http://localhost:8000').replace('http', 'ws');
            const wsUrl = `${baseUrl}/ws/voice/${sessionId}`;
            console.log(`🔌 Connecting to: ${wsUrl}`);
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('✅ Voice WebSocket Connected');
                this.isActive = true;
                this.updateUI(true);
            };

            this.websocket.onmessage = async (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'audio') {
                        this.playAudio(msg.data);
                    } else if (msg.type === 'interrupted') {
                        console.log('❗ Interrupted — clearing audio buffer');
                        this.clearAudioBuffer();
                    } else if (msg.type === 'turn_complete') {
                        console.log('✅ Agent turn complete');
                    } else if (msg.type === 'error') {
                        console.error('🔴 Server Error:', msg.message);
                    }
                } catch (e) {
                    console.error('Message parse error:', e);
                }
            };

            this.websocket.onclose = (event) => {
                console.log(`🔌 Voice WebSocket Closed (code: ${event.code})`);
                this.stop();
            };

            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket Error:', error);
            };

            console.log('🎤 Microphone active, streaming audio at 16kHz...');

        } catch (e) {
            console.error('❌ Failed to start voice client:', e);
            alert('Could not start voice mode: ' + e.message);
            this.stop();
        }
    }

    // ── Stop ───────────────────────────────────────────────────────────────
    stop() {
        this.isActive = false;
        this.updateUI(false);

        if (this.websocket) {
            try { this.websocket.close(); } catch (_) { }
            this.websocket = null;
        }
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        if (this.recorderContext) {
            try { this.recorderContext.close(); } catch (_) { }
            this.recorderContext = null;
        }
        if (this.playerContext) {
            try { this.playerContext.close(); } catch (_) { }
            this.playerContext = null;
        }
        this.recorderNode = null;
        this.playerNode = null;
        console.log('🛑 Voice client stopped.');
    }

    // ── Upstream: mic → server ─────────────────────────────────────────────
    /**
     * Convert Float32 (from 16kHz recorderContext) → Int16 → Base64 → WebSocket.
     * float32Array is already a copy (made in audio-processor.js), safe to read.
     */
    sendAudio(float32Array) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) return;

        // Float32 → Int16 (signed, symmetric clamp)
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Int16 binary → Base64
        const uint8 = new Uint8Array(int16Array.buffer);
        let binary = '';
        for (let i = 0; i < uint8.byteLength; i++) {
            binary += String.fromCharCode(uint8[i]);
        }

        this.websocket.send(JSON.stringify({
            mime_type: 'audio/pcm',
            data: btoa(binary),
        }));
    }

    // ── Downstream: server → speaker ───────────────────────────────────────
    /**
     * Decode Base64 audio from server → Int16Array → player worklet ring buffer.
     * Server sends audio/pcm;rate=24000 Int16 mono little-endian.
     */
    playAudio(base64Data) {
        console.log(`🔊 Received audio chunk: ${base64Data.length} base64 chars`);
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        // Reinterpret raw bytes as Int16 (little-endian, as sent by Gemini)
        const int16Data = new Int16Array(bytes.buffer);
        console.log(`   → ${int16Data.length} Int16 samples (${(int16Data.length / 24000).toFixed(3)}s at 24kHz)`);

        if (this.playerNode) {
            // Transfer Int16Array to worklet — postMessage with transferable
            // (Int16Array is a view, transfer the underlying buffer)
            const transferBuffer = int16Data.buffer.slice(0); // own copy
            const transferArray = new Int16Array(transferBuffer);
            this.playerNode.port.postMessage(transferArray, [transferBuffer]);
        }
    }

    // ── Buffer clear (on interruption) ─────────────────────────────────────
    clearAudioBuffer() {
        if (this.playerNode) {
            this.playerNode.port.postMessage({ command: 'clear' });
        }
    }

    // ── UI helpers ─────────────────────────────────────────────────────────
    updateUI(active) {
        const btn = document.getElementById('voice-mode-btn');
        if (btn) {
            btn.textContent = active ? '🔴 Stop Voice' : '🎙️ Start Voice';
            btn.style.backgroundColor = active ? '#ff4444' : '';
        }
        const inputContainer = document.querySelector('.chat-input-container');
        if (inputContainer) {
            inputContainer.style.display = active ? 'none' : 'flex';
        }
    }
}

window.voiceClient = new VoiceClient();
