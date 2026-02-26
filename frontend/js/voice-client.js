/**
 * VoiceClient — Simple voice extension for ATLAS text chat.
 * 
 * This is NOT a separate AI. It uses the browser's built-in:
 *   - SpeechRecognition → transcribes user's voice to text
 *   - SpeechSynthesis → speaks the agent's text response out loud
 * 
 * The transcribed text goes through the EXACT same pipeline as typed text:
 *   User speaks → transcribed → /api/session/message → response → spoken back
 *   All metrics (belief, trust, strategy) update normally.
 */
class VoiceClient {
    constructor() {
        this.isActive = false;
        this.recognition = null;
        this.synth = window.speechSynthesis;
        this.isSpeaking = false;
    }

    start() {
        if (this.isActive) return;

        // Check browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert('Your browser does not support Speech Recognition. Use Chrome.');
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.lang = 'en-US';       // Force English
        this.recognition.continuous = true;      // Keep listening
        this.recognition.interimResults = false; // Only final results

        this.recognition.onresult = (event) => {
            // Get the last final result
            const lastResult = event.results[event.results.length - 1];
            if (lastResult.isFinal) {
                const transcript = lastResult[0].transcript.trim();
                if (transcript) {
                    console.log('🎤 You said:', transcript);
                    this._handleVoiceInput(transcript);
                }
            }
        };

        this.recognition.onerror = (event) => {
            console.error('🎤 Speech recognition error:', event.error);
            if (event.error === 'not-allowed') {
                alert('Microphone access denied. Please allow microphone access.');
                this.stop();
            }
        };

        this.recognition.onend = () => {
            // Auto-restart if still active (recognition stops after silence)
            if (this.isActive && !this.isSpeaking) {
                try {
                    this.recognition.start();
                } catch (e) {
                    // Already started, ignore
                }
            }
        };

        try {
            this.recognition.start();
            this.isActive = true;
            console.log('🎤 Voice mode started — listening in English...');

            // Speak the current agent message if there is one
            this._speakLastAgentMessage();

            // Update UI
            if (typeof updateVoiceUI === 'function') {
                updateVoiceUI(true);
            }
        } catch (e) {
            console.error('Failed to start voice:', e);
            alert('Could not start voice: ' + e.message);
        }
    }

    stop() {
        this.isActive = false;

        if (this.recognition) {
            try { this.recognition.stop(); } catch (_) { }
            this.recognition = null;
        }

        // Stop any ongoing speech
        if (this.synth) {
            this.synth.cancel();
        }
        this.isSpeaking = false;

        console.log('🛑 Voice mode stopped.');

        if (typeof updateVoiceUI === 'function') {
            updateVoiceUI(false);
        }
    }

    /**
     * Handle voice input — sends it through the SAME pipeline as text chat.
     * This calls handleSendMessage from app.js with the transcribed text.
     */
    async _handleVoiceInput(transcript) {
        // Pause recognition while processing (so it doesn't pick up the agent's voice)
        if (this.recognition) {
            try { this.recognition.stop(); } catch (_) { }
        }

        // Use the SAME send message flow as text chat
        // This updates all metrics, belief, trust, etc.
        if (typeof sendVoiceMessage === 'function') {
            const agentResponse = await sendVoiceMessage(transcript);
            if (agentResponse) {
                await this._speak(agentResponse);
            }
        }

        // Resume listening after speaking
        if (this.isActive && this.recognition) {
            try {
                this.recognition.start();
            } catch (e) {
                // Already started
            }
        }
    }

    /**
     * Speak text using browser's built-in Text-to-Speech.
     * Returns a promise that resolves when done speaking.
     */
    _speak(text) {
        return new Promise((resolve) => {
            if (!this.synth || !text) {
                resolve();
                return;
            }

            // Cancel any ongoing speech
            this.synth.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-US';
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;

            // Try to pick a good English voice
            const voices = this.synth.getVoices();
            const englishVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Google'))
                || voices.find(v => v.lang.startsWith('en-US'))
                || voices.find(v => v.lang.startsWith('en'));
            if (englishVoice) {
                utterance.voice = englishVoice;
            }

            this.isSpeaking = true;

            utterance.onend = () => {
                this.isSpeaking = false;
                resolve();
            };
            utterance.onerror = () => {
                this.isSpeaking = false;
                resolve();
            };

            this.synth.speak(utterance);
        });
    }

    /**
     * Speak the last agent message in the chat (for when voice mode starts mid-conversation)
     */
    _speakLastAgentMessage() {
        const messages = document.querySelectorAll('.message.agent .message-bubble');
        if (messages.length > 0) {
            const lastMsg = messages[messages.length - 1].textContent;
            this._speak(lastMsg);
        }
    }
}

window.voiceClient = new VoiceClient();
