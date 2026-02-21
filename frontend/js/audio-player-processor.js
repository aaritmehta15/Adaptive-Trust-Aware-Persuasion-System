/**
 * PCMPlayerProcessor — Playback-only AudioWorklet for ATLAS.
 *
 * Responsibilities:
 *   - Receives Int16Array chunks from main thread (server → speaker path)
 *   - Converts Int16 → Float32 (divides by 32768) into a large ring buffer
 *   - process() drains the ring buffer into the Web Audio output channel
 *   - Outputs silence when buffer is empty (no underflow crash)
 *   - Overflow-safe: write index never stomps past read index
 *
 * Buffer size: 24000 * 60 = 1,440,000 samples ≈ 60 seconds at 24kHz.
 * This is far larger than any realistic Gemini response burst, so no overflow.
 *
 * Messages accepted from main thread:
 *   - ArrayBuffer (raw)          → Int16Array of audio samples to enqueue
 *   - { command: 'clear' }      → flush ring buffer (on interruption)
 *
 * Registered as: 'pcm-player-processor'
 */
class PCMPlayerProcessor extends AudioWorkletProcessor {
    constructor() {
        super();

        // 60 seconds of Float32 at 24kHz
        this.bufferSize = 24000 * 60;
        this.buffer = new Float32Array(this.bufferSize);
        this.writeIndex = 0;
        this.readIndex = 0;

        this.port.onmessage = (event) => {
            if (event.data && event.data.command === 'clear') {
                // Flush ring buffer on interruption
                this.readIndex = this.writeIndex;
                return;
            }
            // Incoming audio chunk: Int16Array transferred from main thread
            if (event.data instanceof Int16Array) {
                this._enqueue(event.data);
            }
        };
    }

    /** Push Int16 samples into the ring buffer, converting to Float32. */
    _enqueue(int16Samples) {
        for (let i = 0; i < int16Samples.length; i++) {
            this.buffer[this.writeIndex] = int16Samples[i] / 32768.0;
            const nextWrite = (this.writeIndex + 1) % this.bufferSize;
            // Overflow protection: advance read if write would lap it
            if (nextWrite === this.readIndex) {
                this.readIndex = (this.readIndex + 1) % this.bufferSize;
            }
            this.writeIndex = nextWrite;
        }
    }

    process(inputs, outputs, parameters) {
        const output = outputs[0];
        if (!output || output.length === 0) return true;

        const outputChannel = output[0];
        for (let i = 0; i < outputChannel.length; i++) {
            if (this.readIndex !== this.writeIndex) {
                outputChannel[i] = this.buffer[this.readIndex];
                this.readIndex = (this.readIndex + 1) % this.bufferSize;
            } else {
                outputChannel[i] = 0.0; // Silence on underflow
            }
        }

        // Copy mono to additional channels if any (stereo output)
        for (let ch = 1; ch < output.length; ch++) {
            output[ch].set(outputChannel);
        }

        return true; // Keep processor alive
    }
}

registerProcessor('pcm-player-processor', PCMPlayerProcessor);
