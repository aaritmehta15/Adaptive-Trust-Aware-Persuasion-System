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
│  - RejectionDet │
│  - Trackers     │
│  - Strategies   │
│  - LLMAgent     │
└─────────────────┘
```

---

## Core Modules (`src/`)

### `config.py` - Configuration Parameters

**Purpose:** Centralized configuration for all system parameters.

**Key Parameters:**
```python
# Initial values
INITIAL_BELIEF = 0.15    # 15% donation probability at start
INITIAL_TRUST = 0.9      # 90% trust at start (C3 only)
TRUST_THRESHOLD = 0.5    # Recovery mode trigger

# Learning rates
ALPHA = 0.35   # Belief learning rate - how fast belief changes
BETA = 0.4     # Trust learning rate - how fast trust changes  
GAMMA = 0.15   # Trust recovery rate - how fast trust rebuilds

# Strategies
STRATEGIES = ['Empathy', 'Impact', 'SocialProof', 'Transparency', 'EthicalUrgency']

# LLM Configuration
MODEL_NAME = "meta-llama/Llama-3.1-70B-Instruct"
TEMPERATURE = 0.7
MAX_NEW_TOKENS = 150
```

**To modify:** Edit values here - no other changes needed.

---

### `dialogue_manager.py` - Main Orchestrator

**Purpose:** Coordinates all components for each conversation turn.

**Key Methods:**

#### `__init__(condition, donation_ctx, client, use_local_model)` (Lines 20-39)
Initializes all components:
```python
self.detector = RejectionDetector()      # Analyzes user messages
self.belief = BeliefTracker()            # Tracks donation probability
self.trust = TrustTracker()              # Tracks trust score
self.strategy = StrategyAdapter()        # Selects strategies
self.agent = LLMAgent()                  # Generates responses
self.guard = Guardrails()                # Safety checks
```

#### `process(user_msg)` (Lines 52-147) - **THE MAIN LOOP**

**Step-by-step execution:**
```python
# Line 54: Analyze user message
rej_info = self.detector.detect(user_msg)

# Line 58: Update belief (donation probability)
delta_p = self.belief.update(rej_info, self.trust.get())

# Lines 62-63: Update trust (C3 only)
if self.condition == 'C3':
    delta_t, _ = self.trust.update(rej_info, prev_strat)

# Lines 66-70: Check if conversation should end
should_stop, reason = self.guard.check(rej_info, self.trust.get(), self.belief.get())

# Lines 86-89: Select strategy
chosen = self.strategy.select(in_recovery)

# Lines 98-103: Generate response
agent_resp = self.agent.generate(chosen, user_msg, turn, is_recovery, sentiment)
```

**Order matters:** Belief updated before trust, trust gating happens inside `belief.update()`.

---

### `rejection_detector.py` - User Response Analysis

**Purpose:** Analyzes user messages to extract interpretable signals.

**Pattern Lists (Lines 11-40):**
```python
EXPLICIT_PATTERNS = ['no', 'not interested', 'leave me alone', 'stop', ...]
SOFT_PATTERNS = ['maybe later', 'not right now', 'busy', 'not sure', ...]
TRUST_PATTERNS = ["don't trust", 'scam', 'suspicious', 'fake', ...]
CURIOSITY_PATTERNS = ['tell me more', 'how does', 'what is', ...]
ACCEPTANCE_PATTERNS = ['yes', "i'll donate", 'i want to', 'sure', ...]
```

**`detect(user_msg)` Method (Lines 59-120):**

Returns a dictionary:
```python
{
    'rejection_type': 'explicit' | 'soft' | 'ambiguous' | 'none',
    'sentiment_score': -1.0 to 1.0,  # TextBlob sentiment
    'sentiment_label': 'positive' | 'negative' | 'neutral',
    'trust_concern': True/False,
    'is_curiosity': True/False,
    'is_acceptance': True/False
}
```

**Called from:** `dialogue_manager.py:54`

---

### `trackers.py` - Belief and Trust Tracking

#### **BeliefTracker** (Lines 10-47)

**Purpose:** Tracks donation probability (0.0 to 1.0).

**`update(rejection_info, trust)` Method:**

**Step 1: Determine effect value (Lines 22-37)**
```python
if is_accept:
    effect = (1 - self.belief) * 0.9    # Large increase
elif rtype == 'explicit':
    effect = -0.9                        # Large decrease
elif trust_concern:
    effect = -0.7                        # Moderate decrease
elif rtype == 'soft':
    effect = -0.45                       # Small decrease
elif rtype == 'ambiguous':
    effect = -0.25                       # Very small decrease
elif is_curious:
    effect = 0.25                        # Small increase
elif sent > 0.3:
    effect = 0.15                        # Tiny increase
else:
    effect = 0.0                         # No change
```

**Step 2: Apply learning rate (Line 39)**
```python
delta = Config.ALPHA * effect  # ALPHA = 0.35
```

**Step 3: Trust gating (Lines 41-43)** ⚠️ **CRITICAL**
```python
if trust < Config.TRUST_THRESHOLD and delta > 0:
    delta = 0.0  # Cannot increase belief without trust!
```

**Step 4: Update belief (Line 45)**
```python
self.belief = np.clip(self.belief + delta, 0, 1)
self.history.append(self.belief)
```

**Key Insight:** Trust gating is the core innovation - belief cannot increase when trust is low.

---

#### **TrustTracker** (Lines 49-94)

**Purpose:** Tracks trust score (0.0 to 1.0) - C3 only.

**`update(rejection_info, strategy)` Method:**

**Step 1: Determine delta (Lines 67-83)**
```python
if concern:
    delta = -Config.BETA * 0.8           # -0.32 (trust concern)
elif rtype == 'explicit':
    delta = -Config.BETA * 0.5           # -0.20 (explicit rejection)
elif rtype in ['soft', 'ambiguous']:
    delta = -Config.BETA * 0.3           # -0.12 (soft rejection)
elif rtype == 'none' and not concern:
    # Trust recovery
    if strategy == 'Transparency':
        delta = Config.GAMMA              # +0.15
    elif is_curiosity:
        delta = Config.GAMMA * 0.3        # +0.045
    elif sent > 0.2:
        delta = Config.GAMMA * 0.2        # +0.03
```

**Step 2: Update trust (Line 85)**
```python
self.trust = np.clip(self.trust + delta, 0, 1)
self.history.append(self.trust)
```

**Step 3: Recovery mode logic (Lines 88-92)**
```python
if self.trust < Config.TRUST_THRESHOLD:
    self.recovery_mode = True   # Enter recovery mode
elif self.trust >= Config.TRUST_THRESHOLD:
    self.recovery_mode = False  # Exit recovery mode
```

**Key Insight:** Trust decreases faster than it recovers. Transparency is the best recovery strategy.

---

### `strategy_adapter.py` - Strategy Selection & Adaptation

**Purpose:** Selects persuasion strategies and adapts weights based on effectiveness.

**`select(in_recovery)` Method (Lines 23-42):**
```python
if in_recovery:
    # Recovery mode: only Empathy or Transparency
    return 'Empathy' if self.weights['Empathy'] > self.weights['Transparency'] else 'Transparency'
else:
    # Normal mode: weighted random selection
    probs = np.array(list(self.weights.values()))
    probs = probs / probs.sum()  # Normalize
    return np.random.choice(list(self.weights.keys()), p=probs)
```

**`adapt(prev_strategy, rejection_info)` Method (Lines 44-67):**
```python
# Adjust weights based on user response
if is_accept:
    self.weights[prev_strat] *= 1.5  # Boost successful strategy
elif is_curious or sent > 0.3:
    self.weights[prev_strat] *= 1.2  # Increase for positive response
elif rtype == 'explicit':
    self.weights[prev_strat] *= (1 - 0.6)  # Reduce for failure
elif rtype == 'soft':
    self.weights[prev_strat] *= (1 - 0.35)  # Moderate reduction
elif trust_concern:
    self.weights[prev_strat] *= 0.7  # Reduce failed strategy
    self.weights['Transparency'] *= 1.3  # Boost Transparency

# Normalize weights
total = sum(self.weights.values())
self.weights = {k: v/total for k, v in self.weights.items()}
```

---

### `llm_agent.py` - Response Generation

**Purpose:** Generates natural language responses using LLM.

**Key Methods:**

#### `generate(strategy, user_msg, turn, is_recovery, sentiment)` (Lines 19-53)

**Prompt selection:**
```python
if is_recovery:
    prompt = self._recovery_prompt(...)  # Recovery mode
elif self.condition == 'C1':
    prompt = self._c1_prompt(...)        # Pushy C1 mode
else:
    prompt = self._strategy_prompt(...)  # Normal C2/C3 mode
```

#### Strategy Prompts (Lines 55-92)

**Normal mode (C2/C3):**
```python
strategy_guides = {
    "Empathy": "Respond with empathy and understanding. Acknowledge their feelings warmly.",
    "Impact": f"Share concrete impact: {self.ctx['impact']}. Use numbers and specific outcomes.",
    "SocialProof": "Mention that others in the community are contributing.",
    "Transparency": "Be completely honest. Explain where money goes. Build trust.",
    "EthicalUrgency": "Mention time-sensitive need gently. No pressure."
}
```

**C1 mode (Lines 94-132):**
```python
strategy_guides = {
    "Empathy": "Use empathy strategically to overcome objections. Redirect to donation.",
    "Impact": "Emphasize impact strongly. Make the need urgent and compelling.",
    "SocialProof": "Use strong social proof. Create FOMO.",
    ...
}

CRITICAL RULES FOR C1 MODE:
1. Your PRIMARY goal is to secure a donation - be persistent
2. Acknowledge reluctance briefly but immediately pivot back to donation
3. Use urgency, scarcity, and emotional appeals effectively
4. Don't give up easily - reframe objections as opportunities
```

**Recovery mode (Lines 134-154):**
```python
CRITICAL: The user has lost trust. Your PRIMARY goal is to rebuild trust through:
1. Sincere apology for making them uncomfortable
2. Complete transparency - explain exactly where donations go
3. No pressure - explicitly state there's no obligation
4. Answer their questions honestly and thoroughly
5. Show genuine care for their concerns, not just the donation

Rebuild trust FIRST, donation comes later (if at all).
```

---

### `guardrails.py` - Safety Checks

**Purpose:** Determines when conversation should end.

**`check(rejection_info, trust, belief)` Method (Lines 15-50):**

**C3 (Adaptive) stops if:**
- User accepts donation
- Explicit refusal ("no thanks")
- 3+ consecutive rejections (any type)
- Polite exit after resistance
- Trust drops below 0.3
- Reached max turns (15)

**C1 (Regular) stops if:**
- User accepts donation
- 3+ consecutive **explicit** rejections
- Reached max turns (15)

**Key difference:** C3 is more respectful, C1 is more persistent.

---

## Backend API (`backend/main.py`)

### Key Endpoints

**`POST /api/session/create`** (Lines 96-125)
```python
# Creates a new DialogueManager instance
dm = DialogueManager(condition, donation_ctx, hf_client, use_local_model)
sessions[session_id] = dm
opening_msg = dm.start()
return {'session_id': session_id, 'opening_message': opening_msg}
```

**`POST /api/session/message`** (Lines 128-160)
```python
# Processes user message
result = dm.process(user_msg)
return {
    'agent_message': result['agent_msg'],
    'metrics': result['metrics'],
    'stop': result['stop'],
    'reason': result['reason']
}
```

**`GET /api/session/{id}/metrics`** (Lines 163-205)
```python
# Returns current state
return {
    'belief': dm.belief.get(),
    'trust': dm.trust.get(),
    'belief_history': dm.belief.history,
    'trust_history': dm.trust.history,
    'recovery_mode': dm.trust.recovery_mode,
    'strategy_weights': dm.strategy.weights
}
```

### State Management
- Sessions stored in memory (`sessions` dict)
- Each session is a separate `DialogueManager` instance
- Session state persists until reset or deletion

---

## Frontend (`frontend/`)

### Structure

**`index.html`** - Layout and structure
- Mode selector (C1/C2/C3)
- Chat interface
- Metrics dashboard
- Scenario setup modal

**`styles.css`** - Styling
- Dark theme with modern design
- Glassmorphism effects
- Responsive layout

**`app.js`** - Application logic
- API communication
- Chart rendering (Chart.js)
- UI updates

### Key Functions

**`createSession()`** - Initialize conversation
```javascript
const response = await fetch(`${API_URL}/api/session/create`, {
    method: 'POST',
    body: JSON.stringify({ condition, donation_context })
});
```

**`handleSendMessage()`** - Send user message
```javascript
const response = await fetch(`${API_URL}/api/session/message`, {
    method: 'POST',
    body: JSON.stringify({ session_id, message })
});
updateMetricsDisplay(data.metrics);
```

**`updateMetricsDisplay()`** - Render metrics
```javascript
beliefChart.data.datasets[0].data.push(metrics.belief);
trustChart.data.datasets[0].data.push(metrics.trust);
beliefChart.update();
trustChart.update();
```

---

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

---

## Code Locations Reference

### Configuration Parameters
**File:** `src/config.py`
- Lines 11-13: Initial values (INITIAL_BELIEF, INITIAL_TRUST, TRUST_THRESHOLD)
- Lines 19-21: Learning rates (ALPHA, BETA, GAMMA)
- Lines 23-27: Strategies list

### Belief Calculation
**File:** `src/trackers.py`
**Class:** `BeliefTracker`
**Method:** `update()` (Lines 15-47)
- Lines 22-37: Effect values based on user response
- Line 39: Delta calculation (`delta = ALPHA * effect`)
- Lines 41-43: **Trust gating** (prevents belief increase when trust < 0.5)
- Line 45: Final update (`self.belief = clip(belief + delta, 0, 1)`)

### Trust Calculation
**File:** `src/trackers.py`
**Class:** `TrustTracker`
**Method:** `update()` (Lines 59-94)
- Lines 67-83: Delta values based on rejection type and strategy
- Line 85: Final update (`self.trust = clip(trust + delta, 0, 1)`)
- Lines 88-92: Recovery mode logic

### Trust Recovery Flow
**File:** `src/trackers.py`, `src/llm_agent.py`

**Phase 1: Trust Drops**
- User says "I don't trust you"
- Trust decreases by -0.32 (BETA * 0.8)
- If trust < 0.5 → Recovery mode activated

**Phase 2: Recovery Mode**
- Only Empathy or Transparency strategies available
- Special recovery prompts (apologetic, transparent, no pressure)
- Trust recovers through Transparency (+0.15) or curiosity (+0.045)

**Phase 3: Exit Recovery**
- Once trust ≥ 0.5, recovery mode exits
- All strategies available again
- System can resume persuasion

---

## Modification Guide

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

1. **Styling:** Edit `frontend/styles.css`
2. **Structure:** Edit `frontend/index.html`
3. **Behavior:** Edit `frontend/app.js`
4. **No backend changes needed**

### Adding New Strategies

1. **Add to `Config.STRATEGIES`** in `src/config.py`
2. **Add prompt guide** in `LLMAgent._strategy_prompt()` in `src/llm_agent.py`
3. **Add fallback** in `LLMAgent._fallback()` in `src/llm_agent.py`
4. **Restart backend** - Strategy automatically available

### Changing LLM Model

1. **Update `Config.MODEL_NAME`** in `src/config.py`
2. **Restart backend** - New model will be used

---

## Key Design Principles

1. **Separation of Concerns** - Each module has a single responsibility
2. **API-First** - Frontend and backend communicate via REST API
3. **Stateless Frontend** - All state managed on backend
4. **Modular Backend** - Easy to swap or modify components
5. **Configuration-Driven** - Parameters in `config.py` for easy tuning

---

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

---

## Best Practices

1. **Always restart backend** after changing core modules
2. **Test in isolation** - Use API docs to test backend independently
3. **Version control** - Commit changes incrementally
4. **Document changes** - Note what was modified and why
5. **Test both modes** - Verify C1 and C3 modes work after changes
