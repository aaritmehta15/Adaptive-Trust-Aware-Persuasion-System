/**
 * audio-utils.js
 * Handles AudioContext, WorkletNode, and PCM processing capabilities
 * Reference: Google Bidi-streaming demo
 */

class AudioProcessor {
    constructor() {
        this.audioContext = null;
        this.mediaStream = null;
        this.workletNode = null;
        this.isRecording = false;
        this.onAudioData = null;
    }

    async initialize() {
        if (!window.AudioContext && !window.webkitAudioContext) {
            throw new Error("Browser does not support Web Audio API");
        }

        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 16000, // Gemini prefers 16kHz
        });

        // Load the AudioWorklet processor
        // We inline the processor code here to avoid another file request which might 404
        const processorCode = `
            class RecorderProcessor extends AudioWorkletProcessor {
                constructor() {
                    super();
                    this.bufferSize = 2048; // Send chunks of this size
                    this.buffer = new Float32Array(this.bufferSize);
                    this.bytesWritten = 0;
                }

                process(inputs, outputs, parameters) {
                    const input = inputs[0];
                    if (!input || input.length === 0) return true;
                    
                    const channelData = input[0];
                    
                    // Simple downsampling/buffering could go here if context wasn't 16kHz
                    // Since we requested 16kHz, we just pass data through
                    
                    this.port.postMessage(channelData);
                    return true;
                }
            }
            registerProcessor('recorder-processor', RecorderProcessor);
        `;

        const blob = new Blob([processorCode], { type: "application/javascript" });
        const url = URL.createObjectURL(blob);

        await this.audioContext.audioWorklet.addModule(url);
    }

    async startRecording(onAudioDataCallback) {
        if (!this.audioContext) {
            await this.initialize();
        }
        if (this.isRecording) return;

        this.onAudioData = onAudioDataCallback;

        try {
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            // Monitor track lifecycle
            this.mediaStream.getAudioTracks().forEach(track => {
                track.onended = (event) => {
                    console.warn("[AudioProcessor] Audio track ended automatically!", event);
                };
                console.log("[AudioProcessor] Track started:", track.label, track.readyState);
            });

            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.workletNode = new AudioWorkletNode(this.audioContext, 'recorder-processor');

            this.workletNode.port.onmessage = (event) => {
                if (this.isRecording && this.onAudioData) {
                    // Convert Float32Array to Int16 PCM
                    const float32 = event.data;
                    const int16 = this.floatTo16BitPCM(float32);
                    this.onAudioData(int16); // Send raw bytes
                }
            };

            source.connect(this.workletNode);
            this.workletNode.connect(this.audioContext.destination); // Keep alive

            this.isRecording = true;
            console.log("[AudioProcessor] Audio recording started");

        } catch (error) {
            console.error("[AudioProcessor] Error starting recording:", error);
            throw error;
        }
    }

    stopRecording() {
        console.trace("[AudioProcessor] stopRecording called");
        if (!this.isRecording) return;

        console.log("[AudioProcessor] Stopping recording routines...");

        this.isRecording = false;

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => {
                console.log("[AudioProcessor] Stopping track:", track.label);
                track.stop();
            });
            this.mediaStream = null;
        }

        if (this.workletNode) {
            this.workletNode.disconnect();
            this.workletNode = null;
        }

        console.log("[AudioProcessor] Audio recording stopped completely");
    }

    floatTo16BitPCM(input) {
        const output = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
            const s = Math.max(-1, Math.min(1, input[i]));
            output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return output.buffer;
    }

    // Playback functionality for raw PCM
    async playAudio(arrayBuffer) {
        if (!this.audioContext) await this.initialize();

        // Basic PCM player (assuming 16kHz, 1 channel, 16bit from Gemini)
        // Note: Real implementation usually involves a jitter buffer.
        // For simplicity, we just decode/play chunks as they come.

        const int16 = new Int16Array(arrayBuffer);
        const float32 = new Float32Array(int16.length);
        for (let i = 0; i < int16.length; i++) {
            float32[i] = int16[i] / 32768.0;
        }

        const buffer = this.audioContext.createBuffer(1, float32.length, 16000);
        buffer.getChannelData(0).set(float32);

        const source = this.audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(this.audioContext.destination);
        source.start();
    }
}

// Expose globally
window.AudioProcessor = AudioProcessor;
