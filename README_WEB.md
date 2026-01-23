# Adaptive Persuasion System - Web Interface

A modern web interface for the Adaptive Persuasion System with real-time conversation and metrics visualization.

## Features

- **Dual Mode Support**: Toggle between Regular Chatbot (C1) and Adaptive Persuasion System (C3) modes
- **Real-time Metrics**: Live dashboard showing trust score, donation probability, strategy weights, and more
- **Scenario Setup**: Easy configuration of campaign parameters (organization, cause, amounts, impact)
- **Modern UI**: Clean, responsive design with dark theme
- **Modular Architecture**: Easy to iterate and modify without breaking the system

## Project Structure

```
.
├── src/                    # Core system modules
│   ├── config.py          # Configuration settings
│   ├── rejection_detector.py
│   ├── trackers.py        # Belief and Trust trackers
│   ├── strategy_adapter.py
│   ├── guardrails.py
│   ├── llm_agent.py
│   └── dialogue_manager.py
├── backend/               # FastAPI backend
│   └── main.py           # API endpoints
├── frontend/             # Web frontend
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── start_backend.py      # Backend startup script
└── requirements_web.txt  # Web app dependencies
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements_web.txt
```

### 2. Set Environment Variable

Set your HuggingFace token:

```bash
# Windows (PowerShell)
$env:HF_TOKEN="your_token_here"

# Linux/Mac
export HF_TOKEN="your_token_here"
```

### 3. Start the Backend

```bash
python start_backend.py
```

The backend will start on `http://localhost:8000`

### 4. Open the Frontend

Open `frontend/index.html` in your web browser, or serve it using a simple HTTP server:

```bash
# Python 3
cd frontend
python -m http.server 8080

# Then open http://localhost:8080 in your browser
```

Or simply open `frontend/index.html` directly in your browser (some browsers may have CORS restrictions).

## Usage

1. **Setup Scenario**: Click "Setup Scenario" to configure the campaign parameters
2. **Toggle Mode**: Use the toggle switch at the top to switch between Regular and Adaptive modes
3. **Start Conversation**: The agent will greet you automatically
4. **View Metrics**: Real-time metrics are displayed on the right panel
5. **Reset**: Click "Reset" to start a new conversation

## API Endpoints

- `POST /api/session/create` - Create a new conversation session
- `POST /api/session/message` - Send a message and get response
- `GET /api/session/{session_id}/metrics` - Get current metrics
- `POST /api/session/{session_id}/reset` - Reset a session
- `POST /api/scenario/setup` - Setup campaign scenario

API documentation available at: `http://localhost:8000/docs`

## Architecture Notes

The system is designed for easy iteration:

- **Modular Components**: Each component (rejection detector, trackers, strategies) is in a separate module
- **API-based**: Frontend and backend communicate via REST API, making it easy to swap frontends
- **State Management**: Session state is managed on the backend, allowing for stateless frontend
- **Configuration**: All system parameters are in `src/config.py` for easy tuning

## Modifying the System

### Changing Model Logic

- Edit the relevant module in `src/` (e.g., `rejection_detector.py`, `trackers.py`)
- The API endpoints will automatically use the updated logic
- No frontend changes needed

### Adding New Metrics

1. Update `DialogueManager._metrics()` in `src/dialogue_manager.py`
2. Update `updateMetricsDisplay()` in `frontend/app.js` to display the new metric

### Changing UI

- Modify `frontend/styles.css` for styling
- Modify `frontend/index.html` for structure
- Modify `frontend/app.js` for behavior

## Troubleshooting

- **CORS Errors**: Make sure the backend is running and accessible
- **HF_TOKEN Error**: Ensure the environment variable is set correctly
- **Connection Refused**: Check that the backend is running on port 8000
