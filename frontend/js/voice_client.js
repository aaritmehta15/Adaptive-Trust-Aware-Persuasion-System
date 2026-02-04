/**
 * ATLAS Voice Client
 * Adapts the application to use Voice Bridge
 */

class VoiceManager {
    constructor() {
        this.isActive = false;
        this.socket = null;
        this.audioProcessor = new window.AudioProcessor();
        this.retryCount = 0;
        this.maxRetries = 3;
    }

    async toggle() {
        if (this.isActive) {
            this.stop();
        } else {
            await this.start();
        }
    }

    async start() {
        if (!window.sessionId) {
            alert("Please start a session first!");
            return;
        }

        try {
            this.isActive = true;
            this.updateUI(true); // Show "Connecting..."

            // Connect WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host.replace('8080', '8000')}/ws/voice/${window.sessionId}`;

            console.log("Connecting to Voice Bridge:", wsUrl);
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = async () => {
                console.log("Voice Bridge Connected");
                this.updateUI(true, "Listening");

                // Start Audio Capture
                await this.audioProcessor.startRecording((chunk) => {
                    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                        // Send binary audio
                        this.socket.send(chunk);
                    }
                });
            };

            this.socket.onmessage = async (event) => {
                const data = JSON.parse(event.data);

                // Handle different event types from Gemini
                // We mainly care about AUDIO output

                if (data.serverContent && data.serverContent.modelTurn && data.serverContent.modelTurn.parts) {
                    for (const part of data.serverContent.modelTurn.parts) {
                        if (part.inlineData && part.inlineData.mimeType.startsWith('audio/pcm')) {
                            // Decode Base64 audio
                            const binaryString = window.atob(part.inlineData.data);
                            const len = binaryString.length;
                            const bytes = new Uint8Array(len);
                            for (let i = 0; i < len; i++) {
                                bytes[i] = binaryString.charCodeAt(i);
                            }

                            // Play Audio
                            this.updateUI(true, "Speaking");
                            await this.audioProcessor.playAudio(bytes.buffer);

                            // Visual feedback timeout to return to "Listening"
                            setTimeout(() => this.updateUI(true, "Listening"), 2000);
                        }
                    }
                }
            };

            this.socket.onclose = (event) => {
                console.log("Voice Socket Closed", event);
                this.stop();
                if (event.code !== 1000 && this.retryCount < this.maxRetries) {
                    // Graceful fallback logic could go here
                    console.warn("Abnormal closure, checking fallback.");
                }
            };

            this.socket.onerror = (error) => {
                console.error("Voice Socket Error", error);
                this.stop();
            };

        } catch (e) {
            console.error("Failed to start voice mode:", e);
            this.stop();
            alert("Could not start voice mode. Please check microphone permissions.");
        }
    }

    stop() {
        this.isActive = false;
        this.updateUI(false);

        if (this.audioProcessor) {
            this.audioProcessor.stopRecording();
        }

        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }

    updateUI(active, statusText = "") {
        const btn = document.getElementById('voiceToggleBtn');
        const indicator = document.getElementById('voiceStatus');
        const text = document.getElementById('voiceStatusText');

        if (active) {
            btn.classList.add('active');
            indicator.style.display = 'flex';
            text.textContent = statusText || "Connecting...";
            btn.innerHTML = '🎤 Stop Voice';
        } else {
            btn.classList.remove('active');
            indicator.style.display = 'none';
            btn.innerHTML = '🎤 Voice Mode';
        }
    }
}

// Initialize
window.voiceManager = new VoiceManager();

// Hook up button
document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('voiceToggleBtn');
    if (btn) {
        btn.addEventListener('click', () => window.voiceManager.toggle());
    }
});
