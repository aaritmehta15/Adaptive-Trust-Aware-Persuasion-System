class VoiceStreamingApp {
    constructor() {
        this.websocket = null;
        this.isAudio = false;
        this.audioContext = null;
        this.audioRecorderNode = null;
        this.audioPlayerNode = null;
        this.currentMessageElement = null;
        this.sessionId = this.generateSessionId();
        
        this.initializeElements();
        this.setupEventListeners();
        this.connectWebsocket();
    }

    generateSessionId() {
        return Math.random().toString(36).substr(2, 9);
    }

    initializeElements() {
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.startAudioButton = document.getElementById('startAudioButton');
        this.stopAudioButton = document.getElementById('stopAudioButton');
        this.statusElement = document.getElementById('status');
        this.typingIndicator = document.getElementById('typingIndicator');
    }

    setupEventListeners() {
        // Text input handling
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendTextMessage();
            }
        });

        this.sendButton.addEventListener('click', () => {
            this.sendTextMessage();
        });

        // Audio controls
        this.startAudioButton.addEventListener('click', () => {
            this.startAudio();
        });

        this.stopAudioButton.addEventListener('click', () => {
            this.stopAudio();
        });
    }

    connectWebsocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.sessionId}${this.isAudio ? '?is_audio=true' : ''}`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.updateStatus('Connected', true);
            this.enableUI();
        };

        this.websocket.onmessage = (event) => {
            this.handleServerMessage(JSON.parse(event.data));
        };

        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateStatus('Disconnected', false);
            this.disableUI();
            
            // Attempt to reconnect after 3 seconds
            setTimeout(() => {
                if (!this.websocket || this.websocket.readyState === WebSocket.CLOSED) {
                    this.connectWebsocket();
                }
            }, 3000);
        };

        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateStatus('Connection Error', false);
        };
    }

    updateStatus(message, connected) {
        this.statusElement.textContent = message;
        this.statusElement.className = `status ${connected ? 'connected' : 'disconnected'}`;
    }

    enableUI() {
        this.messageInput.disabled = false;
        this.sendButton.disabled = false;
        this.startAudioButton.disabled = false;
    }

    disableUI() {
        this.messageInput.disabled = true;
        this.sendButton.disabled = true;
        this.startAudioButton.disabled = true;
    }

    handleServerMessage(data) {
        const { mime_type, data: content, turn_complete, is_user_transcription, is_agent_transcription } = data;

        if (mime_type === 'text/plain') {
            if (turn_complete) {
                // End of message
                this.hideTypingIndicator();
                this.currentMessageElement = null;
                console.log('Turn complete - ready for next message');
            } else if (content && content.trim()) {
                // Text content (only if not empty)
                this.hideTypingIndicator();
                
                // Handle user transcription (what you said)
                if (is_user_transcription) {
                    const userMessage = this.createMessageElement('user');
                    userMessage.textContent = content;
                    this.scrollToBottom();
                    console.log('Added user transcription:', content.substring(0, 50));
                }
                // Handle agent transcription (what agent said)
                else if (is_agent_transcription) {
                    if (!this.currentMessageElement) {
                        this.currentMessageElement = this.createMessageElement('agent');
                    }
                    this.currentMessageElement.textContent += content;
                    this.scrollToBottom();
                    console.log('Added agent transcription:', content.substring(0, 50));
                }
                // Handle regular text (non-audio mode)
                else {
                    if (!this.currentMessageElement) {
                        this.currentMessageElement = this.createMessageElement('agent');
                        console.log('Created new agent message element');
                    }
                    this.currentMessageElement.textContent += content;
                    this.scrollToBottom();
                    console.log('Appended text:', content.substring(0, 50));
                }
            }
        } else if (mime_type === 'audio/pcm') {
            // Audio content
            this.playAudioChunk(content);
            console.log('Playing audio chunk');
        }
    }

    createMessageElement(type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        this.messagesContainer.appendChild(messageDiv);
        return messageDiv;
    }

    sendTextMessage() {
        const messageText = this.messageInput.value.trim();
        if (!messageText || !this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            return;
        }

        // Display user message
        const userMessage = this.createMessageElement('user');
        userMessage.textContent = messageText;
        this.scrollToBottom();

        // Clear input
        this.messageInput.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        // Send to server
        this.sendMessage('text/plain', messageText);
    }

    sendMessage(mimeType, data) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                mime_type: mimeType,
                data: data
            }));
        }
    }

    showTypingIndicator() {
        this.typingIndicator.classList.add('show');
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.classList.remove('show');
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    async startAudio() {
        try {
            console.log('Starting audio mode...');
            
            // Request microphone access
            console.log('Requesting microphone access...');
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log('Microphone access granted');
            
            // Initialize audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log(`Audio context created, sample rate: ${this.audioContext.sampleRate}`);
            
            // Load audio worklets (with cache busting)
            console.log('Loading audio worklets...');
            const timestamp = Date.now();
            await this.audioContext.audioWorklet.addModule(`/static/js/pcm-recorder-processor.js?v=${timestamp}`);
            await this.audioContext.audioWorklet.addModule(`/static/js/pcm-player-processor.js?v=${timestamp}`);
            console.log('Audio worklets loaded');
            
            // Create recorder worklet
            this.audioRecorderNode = new AudioWorkletNode(this.audioContext, 'pcm-recorder-processor');
            this.audioRecorderNode.port.onmessage = (event) => {
                console.log('Received message from recorder worklet:', event.data);
                console.log('Message type:', event.data?.type, 'Keys:', Object.keys(event.data || {}));
                
                if (event.data && event.data.type === 'pcmData' && event.data.pcmData) {
                    console.log('PCM data received from worklet, calling handler');
                    this.audioRecorderHandler(event.data.pcmData);
                } else if (event.data && event.data.pcmData) {
                    // Fallback if type is missing
                    console.log('PCM data received (no type field), calling handler anyway');
                    this.audioRecorderHandler(event.data.pcmData);
                } else {
                    console.warn('Received message with unexpected structure:', event.data);
                }
            };
            console.log('Audio recorder node created and message handler attached');
            
            // Create player worklet
            this.audioPlayerNode = new AudioWorkletNode(this.audioContext, 'pcm-player-processor');
            console.log('Audio player node created');
            
            // Connect microphone to recorder
            const source = this.audioContext.createMediaStreamSource(stream);
            
            // Log audio stream info
            const audioTracks = stream.getAudioTracks();
            console.log(`Audio tracks: ${audioTracks.length}`);
            if (audioTracks.length > 0) {
                console.log(`Track 0 settings:`, audioTracks[0].getSettings());
            }
            
            source.connect(this.audioRecorderNode);
            console.log('✅ Microphone connected to recorder node');
            
            // Recorder also needs to connect to something (even if silent) for some browsers
            // We'll connect it to a gain node set to 0 to avoid feedback
            const silentGain = this.audioContext.createGain();
            silentGain.gain.value = 0;
            this.audioRecorderNode.connect(silentGain);
            silentGain.connect(this.audioContext.destination);
            console.log('Recorder connected to silent output');
            
            // Connect player to speakers
            this.audioPlayerNode.connect(this.audioContext.destination);
            console.log('✅ Player connected to speakers');
            
            // Switch to audio mode
            this.isAudio = true;
            this.startAudioButton.style.display = 'none';
            this.stopAudioButton.style.display = 'inline-block';
            this.stopAudioButton.classList.add('active');
            
            // Reconnect WebSocket with audio mode
            console.log('Reconnecting WebSocket in audio mode...');
            this.websocket.close();
            setTimeout(() => {
                this.connectWebsocket();
            }, 1000);
            
            console.log('✅ Audio mode started successfully');
            
        } catch (error) {
            console.error('❌ Error starting audio:', error);
            alert('Could not access microphone. Please check permissions.');
        }
    }

    stopAudio() {
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        this.audioRecorderNode = null;
        this.audioPlayerNode = null;
        
        this.isAudio = false;
        this.startAudioButton.style.display = 'inline-block';
        this.stopAudioButton.style.display = 'none';
        
        // Reconnect WebSocket without audio mode
        this.websocket.close();
        setTimeout(() => {
            this.connectWebsocket();
        }, 1000);
        
        console.log('Audio mode stopped');
    }

    audioRecorderHandler(pcmData) {
        // Convert PCM data to base64 and send to server
        const base64Audio = this.arrayBufferToBase64(pcmData);
        console.log(`Sending audio chunk to server: ${pcmData.byteLength} bytes`);
        this.sendMessage('audio/pcm', base64Audio);
    }

    playAudioChunk(base64Audio) {
        if (this.audioPlayerNode) {
            const audioData = this.base64ToArrayBuffer(base64Audio);
            console.log(`Playing audio chunk: ${audioData.byteLength} bytes`);
            this.audioPlayerNode.port.postMessage({
                type: 'playAudio',
                audioData: audioData
            });
        } else {
            console.warn('Audio player node not initialized, cannot play audio');
        }
    }

    // Utility functions for base64 conversion
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    base64ToArrayBuffer(base64) {
        const binaryString = atob(base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new VoiceStreamingApp();
});
