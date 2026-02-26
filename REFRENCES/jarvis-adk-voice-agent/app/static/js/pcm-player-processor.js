class PCMPlayerProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.audioQueue = [];
        this.currentBuffer = null;
        this.bufferIndex = 0;
        this.sampleRate = 24000; // Input sample rate from agent (audio/pcm;rate=24000)
        this.outputSampleRate = 48000; // Browser sample rate
        this.resampleRatio = this.outputSampleRate / this.sampleRate; // 2.0
        this.resampleIndex = 0;
        
        this.port.onmessage = (event) => {
            if (event.data.type === 'playAudio') {
                this.queueAudio(event.data.audioData);
            }
        };
    }

    process(inputs, outputs, parameters) {
        const output = outputs[0];
        if (output.length > 0) {
            const outputChannel = output[0];
            
            for (let i = 0; i < outputChannel.length; i++) {
                if (this.currentBuffer && this.bufferIndex < this.currentBuffer.length) {
                    // Convert int16 to float32 and output
                    const sample = this.currentBuffer[this.bufferIndex] / 32768.0;
                    outputChannel[i] = sample;
                    
                    // Simple upsampling: repeat each sample twice (24000 -> 48000)
                    this.resampleIndex++;
                    if (this.resampleIndex >= this.resampleRatio) {
                        this.resampleIndex = 0;
                        this.bufferIndex++;
                    }
                } else {
                    // No audio data, output silence
                    outputChannel[i] = 0;
                    
                    // Try to get next buffer
                    if (this.audioQueue.length > 0) {
                        this.currentBuffer = new Int16Array(this.audioQueue.shift());
                        this.bufferIndex = 0;
                        this.resampleIndex = 0;
                    } else {
                        this.currentBuffer = null;
                    }
                }
            }
        }
        
        return true;
    }

    queueAudio(audioData) {
        this.audioQueue.push(audioData);
    }
}

registerProcessor('pcm-player-processor', PCMPlayerProcessor);
