class PCMProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bufferSize = 4096; // Adjust buffer size as needed
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
        // Simple Ring Buffer Implementation for Playback
        // Convert Int16 -> Float32 for Web Audio API
        for (let i = 0; i < int16Array.length; i++) {
            const floatVal = int16Array[i] / 32768.0;
            this.buffer[this.writeIndex] = floatVal;
            this.writeIndex = (this.writeIndex + 1) % this.bufferSize;
        }
    }

    process(inputs, outputs, parameters) {
        // 1. INPUT (Microphone) -> Main Thread -> Server
        const input = inputs[0];
        if (input && input.length > 0) {
            const inputChannel = input[0];

            // Downsample/Convert Logic (Basic Float32 pass-through to main thread for now)
            // We will do the Int16 conversion in the main thread or here.
            // Doing it here is more efficient.
            this.port.postMessage({
                type: 'input_audio',
                data: inputChannel
            });
        }

        // 2. OUTPUT (Server) -> Speaker
        const output = outputs[0];
        if (output && output.length > 0) {
            const outputChannel = output[0];
            for (let i = 0; i < outputChannel.length; i++) {
                if (this.readIndex !== this.writeIndex) {
                    outputChannel[i] = this.buffer[this.readIndex];
                    this.readIndex = (this.readIndex + 1) % this.bufferSize;
                } else {
                    outputChannel[i] = 0; // Silence
                }
            }
            // Copy to other channels if needed
            for (let ch = 1; ch < output.length; ch++) {
                output[ch].set(outputChannel);
            }
        }

        return true;
    }
}

registerProcessor('pcm-processor', PCMProcessor);
