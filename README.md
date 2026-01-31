# Adaptive Trust-Aware Persuasion System

An AI-powered conversational system that persuades users to donate while explicitly preserving trust and autonomy through adaptive, multi-turn interaction.

## 🎯 What Is This?

This system models persuasion as a **multi-turn decision process** where:
- **Donation intent is latent and probabilistic** - tracked as belief (0-100%)
- **Trust is a hard constraint** - persuasion is suppressed when trust drops
- **The system can intentionally back off** to recover user trust
- **Strategies adapt** based on what works for each user

Unlike traditional chatbots that optimize for immediate conversion, this system balances short-term donation likelihood with long-term user engagement and ethical boundaries.

## 🔬 Three Experimental Modes

| Mode | Description | Behavior |
|------|-------------|----------|
| **C1** | Regular Chatbot | Pushy, persistent, ignores trust, static "Empathy" strategy |
| **C2** | Adaptive Strategies | Learns which strategies work, no trust tracking |
| **C3** | Full System | Trust-aware, adaptive strategies, recovery mode |

**Key Innovation:** C3 enters "Recovery Mode" when trust drops below 50%, prioritizing trust rebuilding over persuasion.

## ⚡ Quick Start

### Prerequisites
- Python 3.8+
- HuggingFace account with API token

### 1. Install Dependencies

```bash
pip install -r requirements_web.txt
```

### 2. Set HuggingFace Token

**Windows (PowerShell):**
```powershell
$env:HF_TOKEN="your_huggingface_token_here"
```

**Linux/Mac:**
```bash
export HF_TOKEN="your_huggingface_token_here"
```

### 3. Start Backend

```bash
python start_backend.py
```

Backend runs on `http://localhost:8000`

### 4. Start Frontend

```bash
python start_frontend.py
```

Or open `frontend/index.html` directly in your browser.

### 5. Use the Application

1. Click "Setup Scenario" to configure campaign (optional - defaults provided)
2. Toggle between "Regular" (C1) and "Adaptive" (C3) modes
3. Start chatting - the agent greets you automatically
4. Watch real-time metrics on the right panel

## 📊 Key Features

### Trust-Aware Persuasion
- Tracks trust score in real-time (C3 only)
- **Trust Gating:** Belief cannot increase when trust < 50%
- **Recovery Mode:** System backs off when trust drops

### Adaptive Strategy Selection
Five persuasion strategies:
- **Empathy** - Understanding and warmth
- **Impact** - Concrete outcomes and numbers
- **Social Proof** - Others are donating
- **Transparency** - Honest about where money goes
- **Ethical Urgency** - Time-sensitive need

Strategies adapt based on effectiveness - successful strategies get higher weight.

### Ethical Guardrails
- Stops after 3 consecutive rejections
- Respects explicit refusals immediately
- Stops if trust drops too low (< 30%)
- Maximum 15 turns per conversation

### Real-Time Metrics Dashboard
- Belief (donation probability) graph
- Trust score graph (C3 only)
- Strategy weights visualization
- Rejection type and sentiment
- Recovery mode indicator

## 🏗️ Project Structure

```
persuation-system-master/
├── src/                    # Core logic modules
│   ├── config.py          # Configuration parameters
│   ├── dialogue_manager.py # Main orchestrator
│   ├── trackers.py        # Belief & Trust tracking
│   ├── rejection_detector.py # User response analysis
│   ├── strategy_adapter.py # Strategy selection & adaptation
│   ├── llm_agent.py       # Response generation
│   └── guardrails.py      # Safety checks
├── backend/               # FastAPI REST API
│   └── main.py
├── frontend/              # Web interface
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── notebooks/             # Analysis & logs
├── README.md              # This file
├── ARCHITECTURE.md        # Technical reference
└── RESEARCH.md           # Academic context
```

## 🔧 Troubleshooting

**Backend won't start:**
- Check `HF_TOKEN` is set: `echo $env:HF_TOKEN` (PowerShell) or `echo $HF_TOKEN` (Linux/Mac)
- Try `python start_backend_simple.py` instead
- Ensure port 8000 is not in use

**Frontend can't connect:**
- Verify backend is running: open `http://localhost:8000` in browser
- Run `python test_backend.py` to test connection
- Check browser console (F12) for errors

**CORS errors:**
- Use `python start_frontend.py` instead of opening HTML directly
- Backend CORS is configured to allow all origins

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical deep dive, code locations, calculations
- **[RESEARCH.md](RESEARCH.md)** - Theoretical foundation, C1 vs C3 comparison, experiments

## 🎓 Academic Context

This project addresses gaps in donation-focused conversational AI:
- Most systems optimize persuasion implicitly
- They ignore long-term interaction dynamics
- They treat trust as a side effect rather than a control variable

**Novel Contributions:**
- Persuasion modeled as a probability trajectory
- Trust enforced as an operational constraint
- Explicit recovery behavior
- Modular, interpretable persuasion control loop

## 🛠️ Technology Stack

- **Language:** Python 3.8+
- **LLM:** HuggingFace Inference API (Llama 3.1 70B)
- **Backend:** FastAPI
- **Frontend:** HTML/CSS/JavaScript
- **NLP:** TextBlob for sentiment analysis
- **Visualization:** Chart.js

## 📖 API Documentation

Once backend is running, visit:
- **API Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

## 🔬 Research Use

This framework is designed for:
- Academic research on ethical persuasion
- Studying trust dynamics in conversational AI
- Comparing adaptive vs static persuasion strategies
- Evaluating recovery mechanisms

All interaction data is logged for analysis (see `notebooks/` folder).

## 🤝 Contributing

This is a research prototype. To modify:
1. **Change parameters:** Edit `src/config.py`
2. **Modify calculations:** Edit `src/trackers.py`
3. **Add strategies:** Update `src/config.py` and `src/llm_agent.py`
4. **Change UI:** Edit files in `frontend/`

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed modification guide.

## 📄 License

This project is for academic and research purposes.

## 🙏 Acknowledgments

Built on research in:
- Persuasion theory and computational persuasion
- Trust modeling in human-AI interaction
- Decision-making under uncertainty (POMDP-style reasoning)
- Donation-focused conversational agents

---

**For technical details, see [ARCHITECTURE.md](ARCHITECTURE.md)**  
**For research context, see [RESEARCH.md](RESEARCH.md)**
