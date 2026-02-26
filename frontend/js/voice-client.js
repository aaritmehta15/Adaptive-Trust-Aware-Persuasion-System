/**
 * ATLAS Voice Client  (voice-client.js — loaded by index.html)
 *
 * Backend protocol (backend/main.py  /ws/voice/{session_id}):
 *   UPSTREAM   JSON text: { mime_type: "audio/pcm", data: "<base64 Int16 PCM @ 16 kHz>" }
 *   DOWNSTREAM JSON text: { type:"audio", data:"<base64>", turn_complete:bool }
 *                         { type:"turn_complete" }
 *                         { type:"interrupted" }
 *                         { type:"error", message:"..." }
 */

class VoiceClient {
    constructor() {
        this.isActive = false;
        this.socket = null;
        this.audioCtx = null;   // recording context (device native rate)
        this.mediaStream = null;
        this.workletNode = null;
        this.sourceNode = null;
        this._sent = 0;      // chunk counter for logging

        // Playback — single shared context, chunks scheduled on audio clock
        this._playCtx = null;   // AudioContext at 24 kHz (Gemini output rate)
        this._scheduleAt = 0;      // next chunk start time on the audio clock
    }

    // ─────────────────────────────────────────────────────── Public API ───────

    async start() {
        if (this.isActive) return;

        // currentSessionId is `let` at top-level in app.js — NOT on window,
        // but IS in the shared global scope when accessed at call time.
        const sid = currentSessionId;
        if (!sid) {
            alert('Please start a text session first before using voice mode.');
            updateVoiceUI(false);
            return;
        }

        try {
            this.isActive = true;
            updateVoiceUI(true, 'Connecting…');
            console.log('[VC] start() sid=', sid);

            // Create AudioContext NOW (synchronous, on the click gesture thread)
            // so the browser doesn't treat it as an autoplay violation.
            if (!this.audioCtx || this.audioCtx.state === 'closed') {
                this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (this.audioCtx.state === 'suspended') {
                await this.audioCtx.resume();
            }
            console.log('[VC] AudioContext state:', this.audioCtx.state,
                'sampleRate:', this.audioCtx.sampleRate);

            // Load the inline AudioWorklet module
            await this._loadWorklet();

            // Open WebSocket to backend
            const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = location.host.replace(/8080/, '8000');
            const url = `${proto}//${host}/ws/voice/${sid}`;
            console.log('[VC] WS connecting to', url);
            this.socket = new WebSocket(url);

            this.socket.onopen = async () => {
                try {
                    console.log('[VC] WS open — requesting microphone');
                    updateVoiceUI(true, 'Listening…');
                    await this._startCapture();
                    console.log('[VC] ✅ Microphone capture active — speak now');
                } catch (err) {
                    console.error('[VC] ❌ _startCapture failed:', err);
                    alert(
                        'Microphone error: ' + err.message +
                        '\n\nPlease allow microphone access when the browser asks, then click Start Talking again.'
                    );
                    this.stop();
                }
            };
            this.socket.onmessage = (e) => this._onMessage(e);
            this.socket.onclose = (e) => { console.log('[VC] WS closed', e.code); this.stop(); };
            this.socket.onerror = (e) => { console.error('[VC] WS error', e); this.stop(); };

        } catch (err) {
            console.error('[VC] start() error:', err);
            this.stop();
            alert('Voice error: ' + err.message);
        }
    }

    stop() {
        if (!this.isActive && !this.socket) return;
        console.log('[VC] stop() — chunks sent:', this._sent);
        this.isActive = false;
        this._sent = 0;
        this._stopCapture();
        if (this.socket) { this.socket.close(); this.socket = null; }
        updateVoiceUI(false);
    }

    // ──────────────────────────────────────────── AudioWorklet ────────────────

    async _loadWorklet() {
        const code = `
            class Rec extends AudioWorkletProcessor {
                constructor() {
                    super();
                    this._buf    = [];
                    // currentSampleRate may not be a bare global in all browsers;
                    // use typeof guard and fall back to 48000 (standard device rate).
                    const _rate = (typeof currentSampleRate !== 'undefined') ? currentSampleRate : 48000;
                    this._limit  = Math.round(_rate * 0.1);
                }
                process(inputs) {
                    const ch = inputs[0] && inputs[0][0];
                    if (!ch) return true;
                    for (let i = 0; i < ch.length; i++) this._buf.push(ch[i]);
                    if (this._buf.length >= this._limit) {
                        this.port.postMessage(new Float32Array(this._buf));
                        this._buf = [];
                    }
                    return true;
                }
            }
            registerProcessor('atlas-rec', Rec);
        `;
        const blob = new Blob([code], { type: 'application/javascript' });
        const burl = URL.createObjectURL(blob);
        try { await this.audioCtx.audioWorklet.addModule(burl); }
        finally { URL.revokeObjectURL(burl); }
        console.log('[VC] AudioWorklet loaded');
    }

    // ──────────────────────────────────────────── Microphone ─────────────────

    async _startCapture() {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('[VC] Microphone access granted');
        console.log('[VC] Track:', JSON.stringify(
            this.mediaStream.getAudioTracks()[0].getSettings()));

        const deviceRate = this.audioCtx.sampleRate;
        this.sourceNode = this.audioCtx.createMediaStreamSource(this.mediaStream);
        this.workletNode = new AudioWorkletNode(this.audioCtx, 'atlas-rec');

        this.workletNode.port.onmessage = (ev) => {
            if (!this.isActive) return;
            // Synchronous linear-interpolation resample → no OfflineAudioContext
            const pcm = this._resampleTo16k(ev.data, deviceRate);
            this._sendPCM(pcm);
        };

        this.sourceNode.connect(this.workletNode);
        this.workletNode.connect(this.audioCtx.destination);
        console.log('[VC] Capture pipeline running at', deviceRate, 'Hz');
    }

    _stopCapture() {
        this.workletNode?.disconnect(); this.workletNode = null;
        this.sourceNode?.disconnect(); this.sourceNode = null;
        this.mediaStream?.getTracks().forEach(t => t.stop());
        this.mediaStream = null;
    }

    // ──────────────────────────────────────────── Resampling ─────────────────

    _resampleTo16k(f32, fromRate) {
        if (fromRate === 16000) return f32;
        // Fast synchronous linear interpolation — no OfflineAudioContext needed.
        const ratio = fromRate / 16000;
        const outLen = Math.round(f32.length / ratio);
        const out = new Float32Array(outLen);
        for (let i = 0; i < outLen; i++) {
            const pos = i * ratio;
            const lo = Math.floor(pos);
            const hi = Math.min(lo + 1, f32.length - 1);
            out[i] = f32[lo] + (f32[hi] - f32[lo]) * (pos - lo);
        }
        return out;
    }

    // ──────────────────────────────────────────── Sending ────────────────────

    _sendPCM(f32) {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;

        // Float32 → Int16
        const i16 = new Int16Array(f32.length);
        for (let i = 0; i < f32.length; i++) {
            const s = Math.max(-1, Math.min(1, f32[i]));
            i16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Int16 → base64
        const raw = new Uint8Array(i16.buffer);
        let b = '';
        for (let i = 0; i < raw.byteLength; i++) b += String.fromCharCode(raw[i]);

        this.socket.send(JSON.stringify({ mime_type: 'audio/pcm', data: btoa(b) }));
        this._sent++;
        if (this._sent <= 3 || this._sent % 50 === 0) {
            console.log(`[VC] → chunk #${this._sent}  samples=${i16.length}`);
        }
    }

    // ──────────────────────────────────────────── Receiving ──────────────────

    _onMessage(ev) {
        let msg;
        try { msg = JSON.parse(ev.data); } catch { return; }

        switch (msg.type) {
            case 'audio':
                this._enqueue(msg.data);
                break;
            case 'interrupted':
                console.log('[VC] interrupted');
                this._playQueue = []; this._playing = false;
                updateVoiceUI(true, 'Listening…');
                break;
            case 'turn_complete':
                console.log('[VC] turn_complete');
                break;
            case 'error':
                console.error('[VC] server error:', msg.message);
                alert('Voice error: ' + msg.message);
                this.stop();
                break;
            default:
                console.log('[VC] unknown msg type:', msg.type);
        }
    }

    // ──────────────────────────────────── Gapless streaming playback ──────────
    //
    // Gemini returns many small ~40ms PCM chunks.  Creating a new AudioContext
    // per chunk causes audible gaps and glitches.  Instead we keep ONE shared
    // AudioContext at 24 kHz and schedule each chunk on the audio clock so they
    // play back-to-back with sample-accurate timing.

    _ensurePlayCtx() {
        if (this._playCtx && this._playCtx.state !== 'closed') return;
        this._playCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
        this._scheduleAt = 0;
        console.log('[VC] Playback AudioContext created at 24 kHz');
    }

    _enqueue(b64) {
        updateVoiceUI(true, 'Speaking…');
        try {
            this._ensurePlayCtx();
            const ctx = this._playCtx;

            // Resume if suspended (autoplay policy)
            if (ctx.state === 'suspended') ctx.resume();

            // base64 → Int16 → Float32
            const bin = atob(b64);
            const raw = new Uint8Array(bin.length);
            for (let i = 0; i < bin.length; i++) raw[i] = bin.charCodeAt(i);
            const i16 = new Int16Array(raw.buffer);
            const f32 = new Float32Array(i16.length);
            for (let i = 0; i < i16.length; i++) f32[i] = i16[i] / 32768;

            // Build buffer
            const buf = ctx.createBuffer(1, f32.length, 24000);
            buf.getChannelData(0).set(f32);

            // Schedule immediately after the previous chunk ends.
            // Add a small 50 ms lead-in on the very first chunk so the context
            // has time to start before we need audio.
            const now = ctx.currentTime;
            const start = Math.max(now + 0.05, this._scheduleAt);
            this._scheduleAt = start + buf.duration;

            const src = ctx.createBufferSource();
            src.buffer = buf;
            src.connect(ctx.destination);
            src.onended = () => {
                // After the last scheduled chunk finishes, update UI
                if (this._scheduleAt <= ctx.currentTime + 0.05) {
                    if (this.isActive) updateVoiceUI(true, 'Listening…');
                }
            };
            src.start(start);

        } catch (e) {
            console.error('[VC] playback error:', e);
        }
    }
}

// ── Boot ──────────────────────────────────────────────────────────────────────
window.voiceClient = new VoiceClient();

document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('voiceToggleBtn');
    if (!btn) return;
    // Clone to wipe ALL existing listeners, then REMOVE the onclick="toggleVoice()"
    // attribute that index.html bakes in — otherwise cloneNode(true) copies it and
    // every click fires TWICE (onclick → start, addEventListener → stop immediately).
    const fresh = btn.cloneNode(true);
    fresh.removeAttribute('onclick');
    btn.parentNode.replaceChild(fresh, btn);
    fresh.addEventListener('click', () => {
        window.voiceClient.isActive
            ? window.voiceClient.stop()
            : window.voiceClient.start();
    });
});
