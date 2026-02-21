/**
 * PCMRecorderProcessor — Mic-only AudioWorklet for ATLAS.
 *
 * Responsibilities:
 *   - Receives raw mic frames via inputs[0][0] (Float32, at recorderContext sampleRate = 16kHz)
 *   - Copies the buffer (avoids recycled-memory corruption) and posts to main thread
 *   - Has NO ring buffer and does NOT write to outputs — it is purely a capture node
 *
 * IMPORTANT: This worklet runs in the AudioWorkletGlobalScope.
 * It cannot access window, DOM, or any main-thread objects.
 *
 * Registered as: 'pcm-recorder-processor'
 */
class PCMRecorderProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
    }

    process(inputs, outputs, parameters) {
        if (inputs.length > 0 && inputs[0].length > 0) {
            // Copy the buffer — Chrome reuses the same Float32 backing store
            // between process() calls. Without this copy the main thread
            // receives stale/overwritten data.
            const inputCopy = new Float32Array(inputs[0][0]);
            this.port.postMessage(inputCopy);
        }
        return true; // Keep processor alive
    }
}

registerProcessor('pcm-recorder-processor', PCMRecorderProcessor);
