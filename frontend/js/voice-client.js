/**
 * VoiceClient — Browser-side voice integration for ATLAS.
 * 
 * Architecture:
 * - Generates a unique session ID per connection (UUID).
 * - Captures mic audio via AudioWorklet, converts to Int16 PCM, sends as Base64 JSON.
 * - Receives audio from server, decodes, and plays via AudioWorklet ring buffer.
 * - Properly cleans up mic stream, AudioContext, and WebSocket on stop.
 */
class VoiceClient {
    constructor() {
        this.websocket = null;
        this.audioContext = null;
        this.workletNode = null;
        this.mediaStream = null;  // Store for cleanup
        this.isActive = false;
        this.baseSampleRate = 16000;
    }

    /**
     * Generate a unique session ID per voice connection.
     * This prevents "Session already exists" errors on the backend.
     */
    _generateSessionId() {
        return 'voice_' + Math.random().toString(36).substring(2, 14);
    }

    async start() {
        if (this.isActive) return;

        try {
            console.log("🎙️ Starting Voice Client...");

            // 1. Audio Context (24kHz for Gemini output)
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 24000,
                latencyHint: 'interactive'
            });

            // 2. Load AudioWorklet
            await this.audioContext.audioWorklet.addModule('js/audio-processor.js');

            // 3. WebSocket — unique session ID per connection
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
                console.log(`🔌 Voice WebSocket Closed (code: ${event.code}, reason: ${event.reason || 'none'})`);
                this.stop();
            };

            this.websocket.onerror = (error) => {
                console.error("❌ WebSocket Error:", error);
            };

            // 4. Microphone Input
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000
                }
            });

            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.workletNode = new AudioWorkletNode(this.audioContext, 'pcm-processor');

            // Forward mic audio to WebSocket
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

        // Close WebSocket
        if (this.websocket) {
            try { this.websocket.close(); } catch (e) { /* ignore */ }
            this.websocket = null;
        }

        // Stop all mic tracks (release microphone)
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        // Close AudioContext
        if (this.audioContext) {
            try { this.audioContext.close(); } catch (e) { /* ignore */ }
            this.audioContext = null;
        }

        this.workletNode = null;
        console.log("🛑 Voice client stopped.");
    }

    sendAudio(float32Array) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) return;

        // Convert Float32 → Int16
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
            this.workletNode.port.postMessage({
                type: 'audio_chunk',
                data: int16Data
            });
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

// Global instance
window.voiceClient = new VoiceClient();
