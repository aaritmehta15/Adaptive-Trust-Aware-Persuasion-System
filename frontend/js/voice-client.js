/**
 * ATLAS Voice Client  (voice-client.js — loaded by index.html)
 *
 * Handles bidirectional audio streaming with the ATLAS backend WebSocket.
 *
 * Backend protocol (backend/main.py /ws/voice/{session_id}):
 *   UPSTREAM (client → server): JSON text frames
 *     { mime_type: "audio/pcm", data: "<base64 PCM Int16@16kHz>" }
 *
 *   DOWNSTREAM (server → client): JSON text frames
 *     { type: "audio",        data: "<base64 PCM Int16@24kHz>", turn_complete: bool }
 *     { type: "turn_complete", turn_complete: true }
 *     { type: "interrupted" }
 *     { type: "error",       message: "..." }
 */

class VoiceClient {
    constructor() {
        this.isActive       = false;
        this.socket         = null;
        this.audioContext   = null;
        this.mediaStream    = null;
        this.workletNode    = null;
        this.sourceNode     = null;

        // Playback queue (sequential, non-overlapping)
        this._playQueue     = [];
        this._playing       = false;
    }

    // ── Public API ────────────────────────────────────────────────────────────

    async start() {
        if (this.isActive) return;

        // Require an active session
        const sessionId = window.currentSessionId;
        if (!sessionId) {
            alert('Please start a text session first before using voice mode.');
            updateVoiceUI(false);
            return;
        }

        try {
            this.isActive = true;
            updateVoiceUI(true, 'Connecting…');

            // 1. Initialise audio context + worklet
            await this._initAudio();

            // 2. Connect WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host     = window.location.host.replace(/8080/, '8000');
            const wsUrl    = `${protocol}//${host}/ws/voice/${sessionId}`;
            console.log('[VoiceClient] Connecting to', wsUrl);

            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = async () => {
                console.log('[VoiceClient] WebSocket open');
                updateVoiceUI(true, 'Listening…');
                await this._startCapture();
            };

            this.socket.onmessage = (event) => this._onMessage(event);

            this.socket.onclose = (ev) => {
                console.log('[VoiceClient] Closed', ev.code, ev.reason);
                this.stop();
            };

            this.socket.onerror = (err) => {
                console.error('[VoiceClient] Error', err);
                this.stop();
            };

        } catch (err) {
            console.error('[VoiceClient] start() failed:', err);
            this.stop();
            alert('Could not start voice mode: ' + err.message);
        }
    }

    stop() {
        if (!this.isActive && !this.socket) return;
        console.log('[VoiceClient] stop()');
        this.isActive = false;

        this._stopCapture();

        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }

        updateVoiceUI(false);
    }

    // ── Audio initialisation ──────────────────────────────────────────────────

    async _initAudio() {
        if (this.audioContext) return;   // Already initialised

        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 16000,
        });

        // Inline worklet processor to avoid a 404 on a separate file
        const processorCode = `
            class RecorderProcessor extends AudioWorkletProcessor {
                constructor() {
                    super();
                    this._buffer   = [];
                    this._target   = 1024;   // ~64 ms @ 16 kHz
                }
                process(inputs) {
                    const ch = inputs[0] && inputs[0][0];
                    if (!ch) return true;
                    for (let i = 0; i < ch.length; i++) this._buffer.push(ch[i]);
                    if (this._buffer.length >= this._target) {
                        this.port.postMessage(new Float32Array(this._buffer));
                        this._buffer = [];
                    }
                    return true;
                }
            }
            registerProcessor('atlas-recorder', RecorderProcessor);
        `;
        const blob = new Blob([processorCode], { type: 'application/javascript' });
        const url  = URL.createObjectURL(blob);
        await this.audioContext.audioWorklet.addModule(url);
        URL.revokeObjectURL(url);
    }

    // ── Microphone capture ────────────────────────────────────────────────────

    async _startCapture() {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount:      1,
                sampleRate:        16000,
                echoCancellation:  true,
                noiseSuppression:  true,
            },
        });

        this.sourceNode  = this.audioContext.createMediaStreamSource(this.mediaStream);
        this.workletNode = new AudioWorkletNode(this.audioContext, 'atlas-recorder');

        this.workletNode.port.onmessage = (ev) => {
            if (!this.isActive) return;
            this._sendAudioChunk(ev.data);   // Float32Array
        };

        this.sourceNode.connect(this.workletNode);
        this.workletNode.connect(this.audioContext.destination);
        console.log('[VoiceClient] Microphone capture started');
    }

    _stopCapture() {
        if (this.workletNode)  { this.workletNode.disconnect();  this.workletNode  = null; }
        if (this.sourceNode)   { this.sourceNode.disconnect();   this.sourceNode   = null; }
        if (this.mediaStream)  {
            this.mediaStream.getTracks().forEach(t => t.stop());
            this.mediaStream = null;
        }
    }

    // ── Audio sending ──────────────────────────────────────────────────────────

    _sendAudioChunk(float32) {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;

        // Convert Float32 → Int16 PCM
        const int16 = new Int16Array(float32.length);
        for (let i = 0; i < float32.length; i++) {
            const s = Math.max(-1, Math.min(1, float32[i]));
            int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Base64-encode
        const bytes  = new Uint8Array(int16.buffer);
        let   binary = '';
        for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
        const b64 = btoa(binary);

        // Send as JSON text frame (what backend/main.py expects)
        this.socket.send(JSON.stringify({ mime_type: 'audio/pcm', data: b64 }));
    }

    // ── Receiving + playback ──────────────────────────────────────────────────

    _onMessage(event) {
        let msg;
        try { msg = JSON.parse(event.data); } catch { return; }

        switch (msg.type) {
            case 'audio':
                this._enqueueAudio(msg.data);
                break;
            case 'interrupted':
                console.log('[VoiceClient] Interrupted — clearing queue');
                this._playQueue = [];
                this._playing   = false;
                updateVoiceUI(true, 'Listening…');
                break;
            case 'turn_complete':
                console.log('[VoiceClient] Turn complete');
                break;
            case 'error':
                console.error('[VoiceClient] Server error:', msg.message);
                alert('Voice error: ' + msg.message);
                this.stop();
                break;
        }
    }

    _enqueueAudio(base64Data) {
        this._playQueue.push(base64Data);
        if (!this._playing) this._drainQueue();
    }

    async _drainQueue() {
        this._playing = true;
        while (this._playQueue.length > 0) {
            const b64 = this._playQueue.shift();
            await this._playPCM(b64);
        }
        this._playing = false;
        if (this.isActive) updateVoiceUI(true, 'Listening…');
    }

    async _playPCM(base64Data) {
        try {
            updateVoiceUI(true, 'Speaking…');

            if (!this.audioContext || this.audioContext.state === 'closed') {
                await this._initAudio();
            }
            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }

            // Decode base64 → Int16 → Float32
            const binary  = atob(base64Data);
            const bytes   = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
            const int16   = new Int16Array(bytes.buffer);
            const float32 = new Float32Array(int16.length);
            for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768;

            // Play at 24 kHz (Gemini native audio output rate)
            const playCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
            const buf     = playCtx.createBuffer(1, float32.length, 24000);
            buf.getChannelData(0).set(float32);

            await new Promise((resolve) => {
                const src = playCtx.createBufferSource();
                src.buffer = buf;
                src.connect(playCtx.destination);
                src.onended = () => { playCtx.close(); resolve(); };
                src.start();
            });
        } catch (err) {
            console.error('[VoiceClient] Playback error:', err);
        }
    }
}

// ── Global instance ─────────────────────────────────────────────────────────
window.voiceClient = new VoiceClient();

// Hook the toggle button defined in app.js / index.html
document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('voiceToggleBtn');
    if (btn) {
        // Remove any existing listeners and add ours
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        newBtn.addEventListener('click', () => {
            if (window.voiceClient.isActive) {
                window.voiceClient.stop();
            } else {
                window.voiceClient.start();
            }
        });
    }
});
