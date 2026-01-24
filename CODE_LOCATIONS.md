# Where All Calculations Are Located in the Code

This document shows exactly where each calculation, formula, and parameter is located in the codebase.

---

## 📍 Configuration Parameters

**File**: `src/config.py`

```python
# Lines 11-13: Initial Values
INITIAL_BELIEF = 0.15    # 15% chance of donation at start
INITIAL_TRUST = 0.9     # 90% trust at start (C3 only)
TRUST_THRESHOLD = 0.5   # threshold for recovery mode

# Lines 19-21: Learning Rates
ALPHA = 0.35   # belief moves clearly each turn
BETA = 0.4     # trust reacts noticeably to skepticism
GAMMA = 0.15   # recovery is visible but not instant
```

---

## 📍 Donation Probability (Belief) Calculation

**File**: `src/trackers.py`  
**Class**: `BeliefTracker`  
**Method**: `update()` (lines 15-47)

### Initialization
```python
# Line 12: Initial belief value
self.belief = Config.INITIAL_BELIEF  # 0.15

# Line 13: History tracking
self.history = [self.belief]
```

### Effect Values (Priority Order) - Lines 22-37

```python
# Line 22-23: User accepts donation
if is_accept:
    effect = (1 - self.belief) * 0.9

# Line 24-25: Explicit rejection
elif rtype == 'explicit':
    effect = -0.9

# Line 26-27: Trust concern
elif trust_concern:
    effect = -0.7

# Line 28-29: Soft rejection
elif rtype == 'soft':
    effect = -0.45

# Line 30-31: Ambiguous rejection
elif rtype == 'ambiguous':
    effect = -0.25

# Line 32-33: Curiosity
elif is_curious:
    effect = 0.25

# Line 34-35: Positive sentiment
elif sent > 0.3:
    effect = 0.15

# Line 36-37: Neutral/No signal
else:
    effect = 0.0
```

### Delta Calculation - Line 39
```python
# Line 39: Apply ALPHA learning rate
delta = Config.ALPHA * effect  # ALPHA = 0.35
```

### Trust Gating - Lines 41-43
```python
# Lines 41-43: Trust gating (critical feature)
if trust < Config.TRUST_THRESHOLD and delta > 0:
    delta = 0.0  # Belief CANNOT increase without trust
```

### Final Update - Line 45
```python
# Line 45: Apply delta and clamp between 0.0 and 1.0
self.belief = np.clip(self.belief + delta, 0, 1)

# Line 46: Store in history
self.history.append(self.belief)
```

### Called From
**File**: `src/dialogue_manager.py`  
**Line 58**: `delta_p = self.belief.update(rej_info, self.trust.get())`

---

## 📍 Trust Score Calculation (C3 Only)

**File**: `src/trackers.py`  
**Class**: `TrustTracker`  
**Method**: `update()` (lines 59-94)

### Initialization
```python
# Line 55: Initial trust value
self.trust = Config.INITIAL_TRUST  # 0.9

# Line 56: History tracking
self.history = [self.trust]

# Line 57: Recovery mode flag
self.recovery_mode = False
```

### Delta Values (Priority Order) - Lines 65-83

```python
# Lines 67-69: Trust concern (HIGHEST PRIORITY)
if concern:
    delta = -Config.BETA * 0.8  # -0.4 × 0.8 = -0.32

# Lines 71-72: Explicit rejection
elif rtype == 'explicit':
    delta = -Config.BETA * 0.5  # -0.4 × 0.5 = -0.20

# Lines 73-74: Soft/Ambiguous rejection
elif rtype in ['soft', 'ambiguous']:
    delta = -Config.BETA * 0.3  # -0.4 × 0.3 = -0.12

# Lines 76-83: Trust recovery (only if NO rejection)
elif rtype == 'none' and not concern:
    # Line 77-78: Transparency strategy
    if strategy == 'Transparency':
        delta = Config.GAMMA  # +0.15
    
    # Line 79-80: User shows curiosity
    elif rejection_info['is_curiosity']:
        delta = Config.GAMMA * 0.3  # +0.15 × 0.3 = +0.045
    
    # Line 82-83: Positive sentiment
    elif rejection_info.get('sentiment_score', 0) > 0.2:
        delta = Config.GAMMA * 0.2  # +0.15 × 0.2 = +0.03
```

### Final Update - Line 85
```python
# Line 85: Apply delta and clamp between 0.0 and 1.0
self.trust = np.clip(self.trust + delta, 0, 1)

# Line 86: Store in history
self.history.append(self.trust)
```

### Recovery Mode Logic - Lines 88-92
```python
# Lines 88-92: Recovery mode logic
if self.trust < Config.TRUST_THRESHOLD:  # trust < 0.5
    self.recovery_mode = True  # Enter recovery mode
elif self.trust >= Config.TRUST_THRESHOLD:  # trust >= 0.5
    self.recovery_mode = False  # Exit recovery mode
```

### Called From
**File**: `src/dialogue_manager.py`  
**Lines 62-63**: 
```python
if self.condition == 'C3':
    delta_t, _ = self.trust.update(rej_info, prev_strat)
```

---

## 📍 Where Calculations Are Triggered

**File**: `src/dialogue_manager.py`  
**Class**: `DialogueManager`  
**Method**: `process()` (lines 50-115)

### Step-by-Step Execution Flow

```python
# Line 51: Increment turn counter
self.turn += 1

# Line 54: Detect rejection type, sentiment, trust concerns, etc.
rej_info = self.detector.detect(user_msg)

# Line 58: UPDATE BELIEF FIRST (needs current trust value)
prev_strat = self.history[-1]['strategy'] if self.history else 'Empathy'
delta_p = self.belief.update(rej_info, self.trust.get())
# ↑ Calls BeliefTracker.update() in src/trackers.py:15

# Lines 61-63: UPDATE TRUST (C3 only)
delta_t = 0.0
if self.condition == 'C3':
    delta_t, _ = self.trust.update(rej_info, prev_strat)
    # ↑ Calls TrustTracker.update() in src/trackers.py:59

# Lines 66-70: Check guardrails (uses updated trust and belief)
should_stop, reason = self.guard.check(
    rej_info,
    self.trust.get(),  # Current trust value
    self.belief.get()  # Current belief value
)
```

---

## 📍 Rejection Detection (Input to Calculations)

**File**: `src/rejection_detector.py`  
**Class**: `RejectionDetector`  
**Method**: `detect()` (lines 59-120)

This method analyzes user messages and returns a dictionary with:
- `rejection_type`: 'none', 'soft', 'explicit', 'ambiguous', 'curiosity'
- `sentiment_score`: -1.0 to 1.0 (from TextBlob)
- `sentiment_label`: 'positive', 'negative', 'neutral'
- `trust_concern`: boolean
- `is_curiosity`: boolean
- `is_acceptance`: boolean

**Called From**: `src/dialogue_manager.py:54`

---

## 📍 Trust Gating Implementation

**File**: `src/trackers.py`  
**Lines 41-43**:

```python
# Trust gating - prevents belief increase when trust is low
if trust < Config.TRUST_THRESHOLD and delta > 0:
    delta = 0.0  # Belief CANNOT increase without trust
```

**How it works**:
1. Belief update calculates `delta` based on user response
2. If `delta > 0` (trying to increase belief) AND `trust < 0.5`
3. Set `delta = 0.0` (prevent increase)
4. Belief stays the same or decreases, but cannot go up

---

## 📍 Recovery Mode Implementation

**File**: `src/trackers.py`  
**Lines 88-92**:

```python
# Recovery mode logic
if self.trust < Config.TRUST_THRESHOLD:  # trust < 0.5
    self.recovery_mode = True
elif self.trust >= Config.TRUST_THRESHOLD:  # trust >= 0.5
    self.recovery_mode = False
```

**Used In**:
- **File**: `src/dialogue_manager.py:86` - Strategy selection
- **File**: `src/strategy_adapter.py:41` - Limits strategies to Empathy/Transparency
- **File**: `src/llm_agent.py:29` - Uses recovery prompts

---

## 📍 History Tracking

### Belief History
**File**: `src/trackers.py`  
**Line 13**: `self.history = [self.belief]` (initialization)  
**Line 46**: `self.history.append(self.belief)` (after each update)

### Trust History
**File**: `src/trackers.py`  
**Line 56**: `self.history = [self.trust]` (initialization)  
**Line 86**: `self.history.append(self.trust)` (after each update)

### Used For
- Graph visualization (frontend)
- Metrics display
- Analysis and logging

**Returned To Frontend**: `backend/main.py:135-136`
```python
"belief_history": [round(b, 3) for b in dm.belief.history],
"trust_history": [round(t, 3) for t in dm.trust.history],
```

---

## 📍 Complete Calculation Flow

```
User sends message
    ↓
src/dialogue_manager.py:54
    ↓
src/rejection_detector.py:59 → detect() → returns rejection_info
    ↓
src/dialogue_manager.py:58
    ↓
src/trackers.py:15 → BeliefTracker.update()
    ├─ Lines 22-37: Calculate effect based on rejection_info
    ├─ Line 39: delta = ALPHA × effect
    ├─ Lines 41-43: Trust gating check
    └─ Line 45: new_belief = clip(old_belief + delta, 0, 1)
    ↓
src/dialogue_manager.py:62-63 (if C3 mode)
    ↓
src/trackers.py:59 → TrustTracker.update()
    ├─ Lines 67-83: Calculate delta based on rejection_info and strategy
    ├─ Line 85: new_trust = clip(old_trust + delta, 0, 1)
    └─ Lines 88-92: Update recovery_mode flag
    ↓
src/dialogue_manager.py:66-70
    ↓
src/guardrails.py:15 → Guardrails.check()
    └─ Uses updated trust and belief values
```

---

## 📍 Key File Locations Summary

| Component | File | Class/Method | Lines |
|-----------|------|--------------|-------|
| **Config Parameters** | `src/config.py` | `Config` class | 11-21 |
| **Belief Calculation** | `src/trackers.py` | `BeliefTracker.update()` | 15-47 |
| **Trust Calculation** | `src/trackers.py` | `TrustTracker.update()` | 59-94 |
| **Trust Gating** | `src/trackers.py` | `BeliefTracker.update()` | 41-43 |
| **Recovery Mode** | `src/trackers.py` | `TrustTracker.update()` | 88-92 |
| **Orchestration** | `src/dialogue_manager.py` | `DialogueManager.process()` | 50-115 |
| **Rejection Detection** | `src/rejection_detector.py` | `RejectionDetector.detect()` | 59-120 |
| **History Storage** | `src/trackers.py` | Both trackers | 13, 46, 56, 86 |

---

## 📍 Example: Tracing a Single Turn

**User says**: "I don't trust you"

1. **Rejection Detection** (`src/rejection_detector.py:59`)
   - Detects trust concern pattern
   - Returns: `{'trust_concern': True, 'rejection_type': 'none', ...}`

2. **Belief Update** (`src/trackers.py:15`)
   - Line 19: `trust_concern = True`
   - Line 26-27: `effect = -0.7` (trust concern)
   - Line 39: `delta = 0.35 × -0.7 = -0.245`
   - Line 42: Trust gating check (trust=0.9, so passes)
   - Line 45: `belief = clip(0.15 + (-0.245), 0, 1) = 0.0`

3. **Trust Update** (`src/trackers.py:59`) - C3 only
   - Line 61: `concern = True`
   - Line 67-69: `delta = -0.4 × 0.8 = -0.32`
   - Line 85: `trust = clip(0.9 + (-0.32), 0, 1) = 0.58`
   - Line 89: `recovery_mode = False` (trust >= 0.5)

4. **Return to Dialogue Manager** (`src/dialogue_manager.py`)
   - Line 58: `delta_p = -0.245`
   - Line 63: `delta_t = -0.32, recovery_mode = False`
   - Continues with strategy selection...

---

## 📍 Accessing Values

### Getting Current Values
```python
# Belief
current_belief = dm.belief.get()  # Returns float 0.0-1.0

# Trust
current_trust = dm.trust.get()  # Returns float 0.0-1.0

# Recovery Mode
in_recovery = dm.trust.recovery_mode  # Returns boolean
```

### Getting History
```python
# Belief history
belief_history = dm.belief.history  # List of floats

# Trust history
trust_history = dm.trust.history  # List of floats
```

---

## 📍 Testing/Modifying Calculations

To modify calculations:

1. **Change Parameters**: Edit `src/config.py` (lines 11-21)
2. **Change Effect Values**: Edit `src/trackers.py` (lines 22-37 for belief, 67-83 for trust)
3. **Change Trust Gating**: Edit `src/trackers.py` (lines 41-43)
4. **Change Recovery Threshold**: Edit `src/config.py` (line 13) or `src/trackers.py` (lines 89, 91)

All calculations happen in real-time during `DialogueManager.process()` which is called for each user message.
