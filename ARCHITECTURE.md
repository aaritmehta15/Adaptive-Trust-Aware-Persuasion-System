# System Architecture

## Overview

The Adaptive Persuasion System is built with a modular architecture that separates concerns and makes iteration easy. The system consists of three main parts:

1. **Core Logic** (`src/`) - Modular Python classes
2. **Backend API** (`backend/`) - FastAPI REST API
3. **Frontend** (`frontend/`) - HTML/CSS/JavaScript web interface

## Architecture Diagram

```
┌─────────────────┐
│   Frontend      │
│  (HTML/CSS/JS)  │
└────────┬────────┘
         │ HTTP/REST
         │
┌────────▼────────┐
│  FastAPI        │
│  Backend        │
│  (main.py)      │
└────────┬────────┘
         │
┌────────▼────────┐
│  Core Modules   │
│  (src/)         │
│                 │
│  - DialogueMgr  │
│  - RejectionDet│
│  - Trackers     │
│  - Strategies   │
│  - LLMAgent     │
└─────────────────┘
```

## Core Modules (`src/`)

### `config.py`
- Centralized configuration
- **To modify system parameters**: Edit values here
- No other changes needed

### `rejection_detector.py`
- Analyzes user messages for rejection patterns
- Detects sentiment, trust concerns, curiosity
- **To modify detection logic**: Edit pattern lists or detection methods

### `trackers.py`
- `BeliefTracker`: Tracks donation probability
- `TrustTracker`: Tracks trust score and recovery mode
- **To modify tracking logic**: Edit update methods

### `strategy_adapter.py`
- Manages persuasion strategy selection and adaptation
- **To modify strategies**: Edit strategy list in `config.py` and add handling in `llm_agent.py`

### `guardrails.py`
- Safety checks and exit conditions
- **To modify safety rules**: Edit `check()` method

### `llm_agent.py`
- Generates responses using LLM
- **To modify response generation**: Edit prompt templates

### `dialogue_manager.py`
- Main orchestrator
- Coordinates all components
- **To modify conversation flow**: Edit `process()` method

## Backend API (`backend/main.py`)

### Endpoints

- `POST /api/session/create` - Create new conversation
- `POST /api/session/message` - Send message, get response
- `GET /api/session/{id}/metrics` - Get current metrics
- `POST /api/session/{id}/reset` - Reset session
- `POST /api/scenario/setup` - Setup campaign parameters

### State Management

- Sessions stored in memory (`sessions` dict)
- Each session is a `DialogueManager` instance
- Session state persists until reset or deletion

## Frontend (`frontend/`)

### Structure

- `index.html` - Structure and layout
- `styles.css` - Styling (dark theme, modern design)
- `app.js` - Application logic and API communication

### Key Functions

- `createSession()` - Initialize conversation
- `handleSendMessage()` - Send user message
- `updateMetricsDisplay()` - Render metrics dashboard
- `handleModeChange()` - Switch between C1/C3 modes

## Iteration Workflow

### Changing Model Logic

1. **Modify core module** (e.g., `src/trackers.py`)
2. **Restart backend** - Changes take effect immediately
3. **No frontend changes needed** - API contract remains the same

### Adding New Metrics

1. **Update `DialogueManager._metrics()`** in `src/dialogue_manager.py`
   - Add new metric to return dict
2. **Update `updateMetricsDisplay()`** in `frontend/app.js`
   - Add UI element to display new metric
3. **Restart backend** and refresh frontend

### Modifying UI

1. **Styling**: Edit `frontend/styles.css`
2. **Structure**: Edit `frontend/index.html`
3. **Behavior**: Edit `frontend/app.js`
4. **No backend changes needed**

### Adding New Strategies

1. **Add to `Config.STRATEGIES`** in `src/config.py`
2. **Add prompt guide** in `LLMAgent._strategy_prompt()` in `src/llm_agent.py`
3. **Add fallback** in `LLMAgent._fallback()` in `src/llm_agent.py`
4. **Restart backend** - Strategy automatically available

### Changing LLM Model

1. **Update `Config.MODEL_NAME`** in `src/config.py`
2. **Restart backend** - New model will be used

## Data Flow

### Message Processing Flow

```
User Input
    ↓
Frontend (app.js)
    ↓ HTTP POST
Backend (main.py) → /api/session/message
    ↓
DialogueManager.process()
    ↓
RejectionDetector.detect()
    ↓
BeliefTracker.update()
    ↓
TrustTracker.update()
    ↓
Guardrails.check()
    ↓
StrategyAdapter.select()
    ↓
LLMAgent.generate()
    ↓
Return response + metrics
    ↓
Frontend displays
```

### Metrics Update Flow

```
Backend calculates metrics
    ↓
Returned in API response
    ↓
Frontend receives
    ↓
updateMetricsDisplay() renders
```

## Key Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **API-First**: Frontend and backend communicate via REST API
3. **Stateless Frontend**: All state managed on backend
4. **Modular Backend**: Easy to swap or modify components
5. **Configuration-Driven**: Parameters in `config.py` for easy tuning

## Testing Changes

### Backend Changes

1. Make change to core module
2. Restart backend: `python start_backend.py`
3. Test via API: Visit `http://localhost:8000/docs`
4. Or test via frontend

### Frontend Changes

1. Make change to HTML/CSS/JS
2. Refresh browser (or restart frontend server)
3. Test in browser

### Full Stack Changes

1. Make backend changes
2. Make frontend changes if needed
3. Restart backend
4. Refresh frontend
5. Test end-to-end

## Common Modifications

### Adjust Learning Rates

Edit `src/config.py`:
```python
ALPHA = 0.35  # Belief learning rate
BETA = 0.4   # Trust learning rate
GAMMA = 0.15 # Recovery rate
```

### Change Initial Values

Edit `src/config.py`:
```python
INITIAL_BELIEF = 0.15
INITIAL_TRUST = 0.9
TRUST_THRESHOLD = 0.5
```

### Modify Rejection Patterns

Edit `src/rejection_detector.py`:
- Add patterns to `EXPLICIT_PATTERNS`, `SOFT_PATTERNS`, etc.

### Change Strategy Weights

Edit `src/strategy_adapter.py`:
- Modify `adapt()` method for different weight adjustments
- Modify `select()` for different selection logic

## Best Practices

1. **Always restart backend** after changing core modules
2. **Test in isolation** - Use API docs to test backend independently
3. **Version control** - Commit changes incrementally
4. **Document changes** - Note what was modified and why
5. **Test both modes** - Verify C1 and C3 modes work after changes
