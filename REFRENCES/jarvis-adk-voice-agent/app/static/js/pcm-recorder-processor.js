class PCMRecorderProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bufferSize = 4096;
        this.buffer = [];
        this.downsampleFactor = 3; // 48000 / 16000 = 3
        this.sampleCounter = 0;
    }

    process(inputs, outputs) {
        const input = inputs[0];
        
        if (input && input.length > 0 && input[0]) {
            const inputChannel = input[0];
            
            // Process each sample
            for (let i = 0; i < inputChannel.length; i++) {
                this.sampleCounter++;
                
                // Downsample by taking every 3rd sample
                if (this.sampleCounter >= this.downsampleFactor) {
                    this.sampleCounter = 0;
                    this.buffer.push(inputChannel[i]);
                    
                    // Send buffer when full
                    if (this.buffer.length >= this.bufferSize) {
                        this.sendPCMData();
                    }
                }
            }
        }
        
        // Keep the processor alive
        return true;
    }

    sendPCMData() {
        if (this.buffer.length === 0) return;
        
        // Convert float32 array to int16 PCM
        const float32Array = new Float32Array(this.buffer);
        const int16Array = new Int16Array(float32Array.length);
        
        for (let i = 0; i < float32Array.length; i++) {
            // Clamp and convert to 16-bit integer
            const sample = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
        }
        
        // Send to main thread with proper structure
        this.port.postMessage({
            type: 'pcmData',
            pcmData: int16Array.buffer
        });
        
        // Clear buffer
        this.buffer = [];
    }
}

registerProcessor('pcm-recorder-processor', PCMRecorderProcessor);
