<div align="center">

<img src="https://via.placeholder.com/1600x400/0f172a/6366f1?text=ATLAS+%E2%80%94+Adaptive+Trust+Limited+Action+System" alt="ATLAS Banner" width="100%" style="border-radius: 12px;" />

<br />
<br />

# ATLAS

### An AI-powered persuasion engine that adapts in real-time to donor psychology — combining trust modelling, strategy selection, and live voice interaction.

<br />

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit%20App-6366f1?style=for-the-badge&logo=vercel&logoColor=white)](https://persuation-system2.onrender.com)
[![Docs](https://img.shields.io/badge/Docs-Read%20Now-0ea5e9?style=for-the-badge&logo=gitbook&logoColor=white)](#-quickstart)
[![Report Bug](https://img.shields.io/badge/Report%20Bug-GitHub%20Issues-ef4444?style=for-the-badge&logo=github&logoColor=white)](https://github.com/aaritmehta15/Adaptive-Trust-Aware-Persuasion-System/issues)
[![Feature Request](https://img.shields.io/badge/Feature%20Request-Discussions-10b981?style=for-the-badge&logo=github&logoColor=white)](https://github.com/aaritmehta15/Adaptive-Trust-Aware-Persuasion-System/discussions)

<br />

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![Google ADK](https://img.shields.io/badge/Google%20ADK-1.25-4285F4?style=flat-square&logo=google&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini%202.5%20Flash-Native%20Audio-8B5CF6?style=flat-square&logo=google&logoColor=white)
![Llama](https://img.shields.io/badge/Llama%203.1-8B%20Instruct-F97316?style=flat-square&logo=meta&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)
![Commits](https://img.shields.io/github/commit-activity/m/aaritmehta15/Adaptive-Trust-Aware-Persuasion-System?style=flat-square&color=6366f1)

</div>

---

## What is ATLAS?

**ATLAS (Adaptive Trust Limited Action System)** is a research-grade conversational AI platform that models donor psychology in real-time and dynamically adapts its persuasion strategy to maximise both trust and donation likelihood.

Unlike conventional fundraising chatbots that loop through the same static scripts, ATLAS tracks two live psychological signals — **Belief** (donation probability) and **Trust** — and uses them to select the optimal next move from a portfolio of five evidence-based strategies. When a user starts to disengage, ATLAS detects the signal and pivots into recovery mode before the conversation breaks down.

The system ships with a full **bidirectional voice interface** powered by **Google Gemini 2.5 Flash Native Audio**, enabling natural real-time spoken conversations — indistinguishable from a human agent.

> Built as a research system studying AI-mediated persuasion and trust dynamics. All interactions are transparent and ethically framed.

---

## ✦ Why ATLAS is Different

| Traditional Chatbots | ATLAS |
|---|---|
| Fixed scripts and canned responses | Live psychological state modelling |
| No awareness of user sentiment | Sentiment + rejection type detection per turn |
| One strategy for all users | 5 adaptive strategies selected by belief/trust signal |
| Text-only | Text **and** real-time bidirectional voice (Gemini ADK) |
| Conversation ends on rejection | Trust Recovery Mode re-engages disengaged users |
| No insight into what's working | Live metrics dashboard with turn-by-turn history |

---

## ⚡ Core Features

<table>
<tr>
<td width="50%" valign="top">

### 🧠 &nbsp; Live Psychological Modelling
Tracks **Belief** (donation probability) and **Trust** as continuous signals updated every turn. Bayesian-style updates respond to sentiment, rejection type, and conversational cues.

</td>
<td width="50%" valign="top">

### 🎯 &nbsp; Adaptive Strategy Engine
Five persuasion strategies — *Empathy, Impact, Social Proof, Transparency, Ethical Urgency* — weighted dynamically. Losing strategies are penalised; winning ones are reinforced.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🛡 &nbsp; Trust Recovery Mode
When trust drops below threshold after consecutive rejections, ATLAS enters a de-pressuring recovery mode that rebuilds rapport before attempting re-engagement.

</td>
<td width="50%" valign="top">

### 🎙 &nbsp; Real-Time Voice (Gemini ADK)
Bidirectional audio streaming via WebSocket using Google's Agent Development Kit and Gemini 2.5 Flash Native Audio — 24kHz PCM output with minimal latency.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📊 &nbsp; Live Metrics Dashboard
Turn-by-turn visualisation of Donation Probability, Trust Score, Strategy Weights, and Rejection Type — updated in real-time alongside the conversation.

</td>
<td width="50%" valign="top">

### 🔬 &nbsp; A/B Research Conditions
Switch between **ATLAS mode** (C3 — trust-aware adaptive) and **Regular mode** (C1 — baseline persuasive chatbot) to study persuasion efficacy comparatively.

</td>
</tr>
</table>

---

## 🖥 UI Showcase

<div align="center">

### Dashboard Overview

<img src="https://via.placeholder.com/1400x800/0f172a/6366f1?text=ATLAS+Dashboard+%E2%80%94+Full+System+View" alt="ATLAS Dashboard" width="90%" />

*Full system view — conversation panel, live metrics, and mode controls.*

<br />

### Text Chat Interface

<img src="https://via.placeholder.com/1400x700/0f172a/10b981?text=ATLAS+Text+Chat+Interface" alt="ATLAS Chat Interface" width="90%" />

*Real-time conversation with per-turn belief and trust updates.*

<br />

### Voice Mode

<img src="https://via.placeholder.com/1400x700/0f172a/8b5cf6?text=ATLAS+Voice+Mode+%E2%80%94+Gemini+Native+Audio" alt="ATLAS Voice Mode" width="90%" />

*Bidirectional voice conversation powered by Gemini 2.5 Flash Native Audio.*

<br />

### Metrics Panel

<img src="https://via.placeholder.com/1400x700/0f172a/f59e0b?text=ATLAS+Metrics+Panel+%E2%80%94+Belief+%2F+Trust+%2F+Strategies" alt="ATLAS Metrics Panel" width="90%" />

*Live strategy weights, belief/trust trajectories, and conversation analytics.*

</div>

---

## 🏗 Architecture Overview

<div align="center">

<img src="https://via.placeholder.com/1400x700/0f172a/6366f1?text=ATLAS+System+Architecture+Diagram" alt="ATLAS Architecture" width="90%" />

</div>

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ATLAS Frontend                              │
│   Vanilla JS / HTML / CSS  ·  Port 8080                             │
│   Text Chat ──► REST API         Voice ──► WebSocket (ws://8000)    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                       FastAPI Backend  ·  Port 8000                  │
│                                                                      │
│  POST /api/session/create          ──► DialogueManager (DM)         │
│  POST /api/session/message         ──► DM.process()                 │
│  GET  /api/session/{id}/metrics    ──► DM state snapshot            │
│  WS   /ws/voice/{session_id}       ──► VoiceAgent.process_stream()  │
└───────────────┬──────────────────────────┬──────────────────────────┘
                │                          │
     ┌──────────▼──────────┐   ┌───────────▼───────────┐
     │   Persuasion Core   │   │   Google ADK Voice     │
     │                     │   │                        │
     │  OffTopicDetector   │   │  Gemini 2.5 Flash      │
     │  RejectionDetector  │   │  Native Audio Preview  │
     │  SentimentAnalyser  │   │  LiveRequestQueue      │
     │  BeliefTracker      │   │  Runner (bidi stream)  │
     │  TrustTracker       │   │  InMemorySessionSvc    │
     │  StrategyAdapter    │   └────────────────────────┘
     │  Guardrails         │
     │  LLMAgent           │
     │  (Llama 3.1 8B via  │
     │   HuggingFace API)  │
     └─────────────────────┘
```

---

## 🚀 Quickstart

### Prerequisites

- Python 3.11+
- `HF_TOKEN` — [HuggingFace API token](https://huggingface.co/settings/tokens) with access to `meta-llama/Llama-3.1-8B-Instruct`
- `GEMINI_API_KEY` — [Google AI Studio API key](https://aistudio.google.com/app/apikey) for voice mode

### 1 — Clone

```bash
git clone https://github.com/aaritmehta15/Adaptive-Trust-Aware-Persuasion-System.git
cd Adaptive-Trust-Aware-Persuasion-System
```

### 2 — Create virtual environment & install dependencies

```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3 — Set environment variables

```bash
# Windows (PowerShell)
$env:HF_TOKEN        = "hf_your_token_here"
$env:GEMINI_API_KEY  = "AIza_your_key_here"

# macOS / Linux
export HF_TOKEN="hf_your_token_here"
export GEMINI_API_KEY="AIza_your_key_here"
```

### 4 — Start the backend *(Terminal 1)*

```bash
python start_backend.py
```

Wait for:
```
✓ HuggingFace client initialized successfully
✓ Backend initialized successfully
✓ Voice Agent initialized
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 5 — Start the frontend *(Terminal 2)*

```bash
python start_frontend.py
```

Open **[http://localhost:8080](http://localhost:8080)** — the browser launches automatically.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| **Text LLM** | [Llama 3.1 8B Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) via [HuggingFace Inference API](https://huggingface.co/inference-api) |
| **Voice AI** | [Gemini 2.5 Flash Native Audio](https://deepmind.google/technologies/gemini/) via [Google ADK](https://google.github.io/adk-docs/) |
| **Voice Transport** | WebSocket · PCM 16kHz upstream · PCM 24kHz downstream |
| **Persuasion Core** | Custom belief/trust tracker, rejection detector, off-topic detector, strategy adapter |
| **Frontend** | Vanilla JS · HTML5 · CSS3 · Web Audio API · AudioWorklet |
| **Metrics Charts** | [Chart.js](https://www.chartjs.org/) |
| **Deployment** | [Render](https://render.com/) (backend) · Static HTTP (frontend) |
| **Session State** | In-memory (FastAPI) + Google ADK `InMemorySessionService` |

---

## 📁 Project Structure

```
atlas/
├── backend/
│   ├── main.py              # FastAPI app, REST + WebSocket endpoints
│   ├── atlas_voice_agent.py # Legacy voice agent (reference)
│   └── session_store.py     # Shared session dictionary
├── src/
│   ├── atlas_core.py        # Callable interface for text + voice
│   ├── dialogue_manager.py  # Conversation orchestrator
│   ├── llm_agent.py         # Prompt engineering + HF inference
│   ├── belief_tracker.py    # Bayesian belief update model
│   ├── trust_tracker.py     # Trust signal + recovery mode
│   ├── strategy_adapter.py  # Dynamic strategy weight assignment
│   ├── rejection_detector.py# Hard/soft rejection classification
│   ├── off_topic_detector.py# Off-topic message detection
│   ├── guardrails.py        # Conversation guardrails + limits
│   ├── trackers.py          # Belief + Trust tracker base classes
│   ├── voice_agent.py       # Google ADK VoiceAgent (bidi stream)
│   └── config.py            # Centralised configuration
├── frontend/
│   ├── index.html           # Single-page application shell
│   ├── app.js               # Main application logic
│   ├── styles.css           # Dark-mode design system
│   ├── config.js            # Runtime environment config
│   └── js/
│       ├── voice-client.js  # WebSocket audio client (upstream + playback)
│       └── audio-utils.js   # AudioWorklet, PCM conversion utilities
├── start_backend.py         # Backend entry point
├── start_frontend.py        # Frontend HTTP server entry point
└── requirements.txt
```

---

## 🔬 Research Context

ATLAS was developed to study **AI-mediated persuasion dynamics** in charitable giving contexts. The system operationalises several constructs from persuasion literature:

- **Elaboration Likelihood Model** — strategy selection based on cognitive engagement signals
- **Trust Repair Theory** — recovery mode mirrors trust rebuilding research
- **Bayesian Belief Updating** — continuous probability model of donation likelihood
- **Sentiment-Adaptive Communication** — real-time tonal adjustment based on affective state

The A/B condition design (C1 baseline vs C3 ATLAS) enables rigorous comparative evaluation of adaptive vs. non-adaptive persuasion approaches.

---

## 🤝 Contributing

Contributions are welcome. Here's how to get involved:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature-name`
3. **Commit** your changes: `git commit -m 'feat: add amazing feature'`
4. **Push** to the branch: `git push origin feature/your-feature-name`
5. **Open** a Pull Request

Please open an issue first for major changes. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for code style guidelines.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for full details.

---

## ⭐ Star History

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=aaritmehta15/Adaptive-Trust-Aware-Persuasion-System&type=Date)](https://star-history.com/#aaritmehta15/Adaptive-Trust-Aware-Persuasion-System&Date)

</div>

---

<div align="center">

Built by **[Aarit Mehta](https://github.com/aaritmehta15)**

If ATLAS was useful to you or your research, please consider giving it a ⭐

</div>
