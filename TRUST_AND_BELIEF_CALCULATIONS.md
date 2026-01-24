# How Trust and Donation Probability Are Calculated

## Overview

The system tracks two key metrics:
1. **Belief (Donation Probability)**: 0.0 to 1.0 - How likely the user is to donate
2. **Trust Score**: 0.0 to 1.0 - How much the user trusts the system (C3 only)

Both start at initial values and update each turn based on user responses.

---

## Initial Values

```python
INITIAL_BELIEF = 0.15  # 15% chance of donation at start
INITIAL_TRUST = 0.9    # 90% trust at start (C3 only)
TRUST_THRESHOLD = 0.5  # Recovery mode triggers when trust < 0.5
```

---

## Donation Probability (Belief) Calculation

### Formula
```
new_belief = old_belief + (ALPHA × effect)
```
Where:
- `ALPHA = 0.35` (learning rate - how fast belief changes)
- `effect` depends on user's response (see below)
- Final value is clamped between 0.0 and 1.0

### Effect Values (Priority Order)

The system checks conditions in this order (first match wins):

| Condition | Effect | Delta Calculation | Example |
|-----------|--------|-------------------|---------|
| **User accepts donation** | `(1 - belief) × 0.9` | `ALPHA × effect` | If belief=0.2, effect=0.72, delta=+0.252 |
| **Explicit rejection** ("no thanks", "not interested") | `-0.9` | `ALPHA × -0.9` | delta = **-0.315** |
| **Trust concern** ("I don't trust you") | `-0.7` | `ALPHA × -0.7` | delta = **-0.245** |
| **Soft rejection** ("maybe later", "not now") | `-0.45` | `ALPHA × -0.45` | delta = **-0.158** |
| **Ambiguous rejection** (negative sentiment, unclear) | `-0.25` | `ALPHA × -0.25` | delta = **-0.088** |
| **Curiosity** ("tell me more", "how does it work") | `+0.25` | `ALPHA × 0.25` | delta = **+0.088** |
| **Positive sentiment** (sentiment > 0.3) | `+0.15` | `ALPHA × 0.15` | delta = **+0.053** |
| **Neutral/No signal** | `0.0` | `ALPHA × 0.0` | delta = **0.0** |

### Trust Gating (Critical Feature)

**If trust < 0.5 AND delta > 0 (trying to increase belief):**
```
delta = 0.0  # Belief CANNOT increase without trust
```

This means:
- If user doesn't trust the system, belief cannot go up
- System must rebuild trust first before belief can increase
- Only applies in C3 mode (C1 doesn't track trust)

### Example Belief Updates

**Scenario 1: User says "No thanks"**
- Current belief: 0.15
- Effect: -0.9 (explicit rejection)
- Delta: 0.35 × -0.9 = -0.315
- New belief: max(0, 0.15 - 0.315) = **0.0** (clamped to minimum)

**Scenario 2: User says "Tell me more"**
- Current belief: 0.15
- Effect: +0.25 (curiosity)
- Delta: 0.35 × 0.25 = +0.088
- New belief: min(1.0, 0.15 + 0.088) = **0.238**

**Scenario 3: User says "I'll donate"**
- Current belief: 0.15
- Effect: (1 - 0.15) × 0.9 = 0.765
- Delta: 0.35 × 0.765 = +0.268
- New belief: min(1.0, 0.15 + 0.268) = **0.418**

**Scenario 4: User says "I don't trust you" (trust < 0.5)**
- Current belief: 0.15
- Effect: -0.7 (trust concern)
- Delta: 0.35 × -0.7 = -0.245
- New belief: max(0, 0.15 - 0.245) = **0.0**
- **Even if user later shows curiosity, belief cannot increase until trust ≥ 0.5**

---

## Trust Score Calculation (C3 Only)

### Formula
```
new_trust = old_trust + delta
```
Where `delta` depends on user's response and strategy used (see below)
- Final value is clamped between 0.0 and 1.0

### Delta Values (Priority Order)

The system checks conditions in this order (first match wins):

| Condition | Delta | Calculation | Example |
|-----------|-------|-------------|---------|
| **Trust concern expressed** ("I don't trust you", "scam") | `-BETA × 0.8` | `-0.4 × 0.8` | delta = **-0.32** |
| **Explicit rejection** ("no thanks") | `-BETA × 0.5` | `-0.4 × 0.5` | delta = **-0.20** |
| **Soft/Ambiguous rejection** ("maybe later") | `-BETA × 0.3` | `-0.4 × 0.3` | delta = **-0.12** |
| **Transparency strategy used** (no rejection) | `+GAMMA` | `+0.15` | delta = **+0.15** |
| **User shows curiosity** (no rejection) | `+GAMMA × 0.3` | `+0.15 × 0.3` | delta = **+0.045** |
| **Positive sentiment** (sentiment > 0.2, no rejection) | `+GAMMA × 0.2` | `+0.15 × 0.2` | delta = **+0.03** |
| **Neutral/No signal** | `0.0` | - | delta = **0.0** |

Where:
- `BETA = 0.4` (trust learning rate - how fast trust changes)
- `GAMMA = 0.15` (trust recovery rate - how fast trust rebuilds)

### Recovery Mode Logic

After updating trust:
```python
if trust < 0.5:
    recovery_mode = True  # Enter recovery mode
elif trust >= 0.5:
    recovery_mode = False  # Exit recovery mode
```

### Example Trust Updates

**Scenario 1: User says "I don't trust you"**
- Current trust: 0.9
- Delta: -0.4 × 0.8 = -0.32
- New trust: max(0, 0.9 - 0.32) = **0.58**
- Recovery mode: False (still above 0.5)

**Scenario 2: User says "This seems like a scam" (second trust concern)**
- Current trust: 0.58
- Delta: -0.32 (trust concern again)
- New trust: max(0, 0.58 - 0.32) = **0.26**
- Recovery mode: **True** (trust < 0.5)

**Scenario 3: System uses Transparency strategy, user asks "How do I know you're legitimate?"**
- Current trust: 0.26
- Delta: +0.15 (Transparency strategy)
- New trust: min(1.0, 0.26 + 0.15) = **0.41**
- Recovery mode: True (still below 0.5)

**Scenario 4: User shows positive sentiment "That's helpful, thank you"**
- Current trust: 0.41
- Delta: +0.03 (positive sentiment)
- New trust: min(1.0, 0.41 + 0.03) = **0.44**
- Recovery mode: True (still below 0.5)

**Scenario 5: System uses Transparency again, user says "I see, that makes sense"**
- Current trust: 0.44
- Delta: +0.15 (Transparency) + 0.03 (positive sentiment) = **+0.18**
- New trust: min(1.0, 0.44 + 0.18) = **0.62**
- Recovery mode: **False** (trust ≥ 0.5)

---

## How They Vary Together

### Normal Flow (Trust High)

```
Turn 1: Trust=0.9, Belief=0.15
User: "Hello"
→ Trust: 0.9 (no change)
→ Belief: 0.15 (no change)

Turn 2: Trust=0.9, Belief=0.15
User: "Tell me more"
→ Trust: 0.9 → 0.945 (+0.045 curiosity)
→ Belief: 0.15 → 0.238 (+0.088 curiosity)

Turn 3: Trust=0.945, Belief=0.238
User: "I'll donate"
→ Trust: 0.945 (no change, acceptance doesn't affect trust)
→ Belief: 0.238 → 0.506 (+0.268 acceptance)
```

### Trust Loss Flow

```
Turn 1: Trust=0.9, Belief=0.15
User: "I don't trust you"
→ Trust: 0.9 → 0.58 (-0.32 trust concern)
→ Belief: 0.15 → 0.0 (-0.245 trust concern)

Turn 2: Trust=0.58, Belief=0.0
User: "This seems fake"
→ Trust: 0.58 → 0.26 (-0.32 trust concern, enters recovery)
→ Belief: 0.0 (cannot increase, trust < 0.5)

Turn 3: Trust=0.26, Belief=0.0 (Recovery Mode)
System: Uses Transparency strategy
User: "How do I know you're legitimate?"
→ Trust: 0.26 → 0.41 (+0.15 Transparency)
→ Belief: 0.0 → 0.088 (+0.088 curiosity, trust gating removed)

Turn 4: Trust=0.41, Belief=0.088 (Recovery Mode)
System: Uses Transparency strategy
User: "That's helpful"
→ Trust: 0.41 → 0.44 (+0.03 positive sentiment)
→ Belief: 0.088 → 0.141 (+0.053 positive sentiment)

Turn 5: Trust=0.44, Belief=0.141 (Recovery Mode)
System: Uses Transparency strategy
User: "I understand now"
→ Trust: 0.44 → 0.59 (+0.15 Transparency, exits recovery)
→ Belief: 0.141 → 0.194 (+0.053 positive sentiment)
```

---

## Key Parameters

### Learning Rates
- **ALPHA = 0.35**: How fast belief changes per turn
- **BETA = 0.4**: How fast trust changes per turn
- **GAMMA = 0.15**: How fast trust recovers per turn

### Effect Multipliers
- **Trust concern**: -0.8×BETA = -0.32 (strongest negative)
- **Explicit rejection (trust)**: -0.5×BETA = -0.20
- **Soft rejection (trust)**: -0.3×BETA = -0.12
- **Transparency recovery**: +GAMMA = +0.15 (strongest positive)
- **Curiosity recovery**: +0.3×GAMMA = +0.045
- **Positive sentiment recovery**: +0.2×GAMMA = +0.03

### Belief Effect Multipliers
- **Acceptance**: (1-belief)×0.9 (adaptive - larger when belief is low)
- **Explicit rejection**: -0.9 (strongest negative)
- **Trust concern**: -0.7
- **Soft rejection**: -0.45
- **Ambiguous**: -0.25
- **Curiosity**: +0.25
- **Positive sentiment**: +0.15

---

## Important Behaviors

### 1. Trust Gating
- If trust < 0.5, belief **cannot increase**
- This forces the system to rebuild trust before continuing persuasion
- Only applies in C3 mode

### 2. Recovery Mode
- Automatically enters when trust < 0.5
- Only uses "Empathy" or "Transparency" strategies
- Exits when trust ≥ 0.5

### 3. Clamping
- Both trust and belief are clamped between 0.0 and 1.0
- Prevents impossible values

### 4. Priority Order
- Conditions are checked in priority order
- First matching condition determines the effect
- Trust concerns take highest priority in trust calculation

### 5. Acceptance Special Case
- When user accepts donation, belief increases by `(1 - current_belief) × 0.9`
- This means:
  - If belief is low (0.1), acceptance gives large boost (+0.81)
  - If belief is high (0.8), acceptance gives smaller boost (+0.18)
  - This prevents overshooting and makes the system more realistic

---

## Differences: C1 vs C3

### C1 (Regular Mode)
- **Trust**: Not tracked (stays at 0.9, never changes)
- **Belief**: Updates normally (no trust gating)
- **Recovery Mode**: Never enters (trust never changes)

### C3 (Adaptive Mode)
- **Trust**: Tracked and updated each turn
- **Belief**: Updates with trust gating (cannot increase if trust < 0.5)
- **Recovery Mode**: Enters when trust < 0.5

---

## Mathematical Summary

### Belief Update
```
effect = f(user_response)  # Based on rejection type, sentiment, etc.
delta = ALPHA × effect
if trust < 0.5 and delta > 0:
    delta = 0.0  # Trust gating
new_belief = clip(old_belief + delta, 0, 1)
```

### Trust Update (C3 only)
```
if trust_concern:
    delta = -BETA × 0.8
elif explicit_rejection:
    delta = -BETA × 0.5
elif soft_rejection:
    delta = -BETA × 0.3
elif no_rejection:
    if strategy == 'Transparency':
        delta = GAMMA
    elif curiosity:
        delta = GAMMA × 0.3
    elif positive_sentiment:
        delta = GAMMA × 0.2
    else:
        delta = 0.0

new_trust = clip(old_trust + delta, 0, 1)
recovery_mode = (new_trust < 0.5)
```

---

## Visual Example: Full Conversation

```
Turn | User Input              | Trust | Belief | Delta Trust | Delta Belief | Notes
-----|-------------------------|-------|--------|-------------|--------------|------------------
0    | (Start)                 | 0.90  | 0.15   | -           | -            | Initial values
1    | "Hello"                 | 0.90  | 0.15   | 0.00        | 0.00         | No signal
2    | "I don't trust you"     | 0.58  | 0.00   | -0.32       | -0.245       | Trust concern
3    | "This seems fake"       | 0.26  | 0.00   | -0.32       | 0.00         | Recovery mode!
4    | "How do I know?"         | 0.41  | 0.088  | +0.15       | +0.088       | Transparency
5    | "That's helpful"        | 0.44  | 0.141  | +0.03       | +0.053       | Positive
6    | "I understand"          | 0.59  | 0.194  | +0.15       | +0.053       | Exit recovery!
7    | "Tell me about impact"  | 0.635 | 0.282  | +0.045      | +0.088       | Curiosity
8    | "I'll donate ₹200"      | 0.635 | 0.550  | 0.00        | +0.268       | Acceptance
```

This shows the complete flow from trust loss → recovery → successful donation.
