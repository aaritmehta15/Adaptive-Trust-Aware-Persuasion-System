# How the Adaptive Persuasion System Works

## Overview
The system is a multi-turn conversational AI that tries to persuade users to donate. It tracks two key metrics:
- **Belief (Donation Probability)**: How likely the user is to donate (0.0 to 1.0)
- **Trust Score**: How much the user trusts the agent (0.0 to 1.0)

## Two Modes

### C1 (Regular Chatbot) - Pushy Mode
- Always uses "Empathy" strategy
- Very persistent - keeps pushing even after rejections
- Only stops after 3+ explicit rejections
- Ignores trust concerns
- Metrics panel is hidden

### C3 (Adaptive System) - Respectful Mode
- Adapts strategies based on user responses
- Respects user rejections - stops after 3 consecutive rejections
- Enters "Recovery Mode" when trust drops below 0.5
- Shows metrics panel
- Only uses "Empathy" or "Transparency" in recovery mode

---

## What Happens at Each Dialogue Turn

### Step 1: User Sends Message
User types a message (e.g., "No thanks", "Maybe later", "Tell me more")

### Step 2: Rejection Detection (`RejectionDetector`)
The system analyzes the user's message to detect:
- **Rejection Type**: 
  - `none` - No rejection detected
  - `soft` - Soft rejection ("maybe later", "not now")
  - `explicit` - Strong rejection ("no thanks", "not interested")
  - `ambiguous` - Unclear sentiment
  - `curiosity` - User asking questions
- **Sentiment**: positive, negative, or neutral
- **Trust Concerns**: Does the message indicate distrust?
- **Acceptance**: Does the message indicate willingness to donate?

### Step 3: Update Belief (`BeliefTracker`)
The system updates the **Donation Probability** based on:
- **Acceptance** → Belief increases significantly
- **Explicit Rejection** → Belief decreases sharply (-0.9 effect)
- **Soft Rejection** → Belief decreases moderately (-0.45 effect)
- **Trust Concerns** → Belief decreases (-0.7 effect)
- **Curiosity** → Belief increases slightly (+0.25 effect)
- **Positive Sentiment** → Belief increases slightly (+0.15 effect)

**Important**: If trust is below threshold (0.5), belief CANNOT increase (trust gating).

### Step 4: Update Trust (`TrustTracker`) - C3 Only
For C3 mode, the system updates **Trust Score**:
- **Trust Concerns** → Trust decreases (-0.6 × BETA)
- **Soft/Ambiguous Rejections** → Trust decreases (-0.3 × BETA)
- **Explicit Rejections** → Trust decreases (-0.5 × BETA)
- **Transparency Strategy Used** → Trust increases (+GAMMA)
- **User Shows Curiosity** → Trust increases slightly (+0.3 × GAMMA)

**Recovery Mode**: If trust drops below 0.5, the system enters recovery mode and only uses "Empathy" or "Transparency" strategies.

### Step 5: Check Guardrails (`Guardrails`)
The system checks if it should stop the conversation:

**For C3 (Adaptive):**
- ✅ **Stop if**: User explicitly accepts donation
- ✅ **Stop if**: User gives explicit refusal ("no thanks", "not interested")
- ✅ **Stop if**: 3+ consecutive rejections (even soft ones)
- ✅ **Stop if**: Polite exit after resistance ("thanks, bye")
- ✅ **Stop if**: Trust drops below 0.3
- ✅ **Stop if**: Reached max turns (15)

**For C1 (Regular):**
- ✅ **Stop if**: User explicitly accepts
- ✅ **Stop if**: 3+ consecutive explicit rejections
- ✅ **Stop if**: Reached max turns (15)
- ❌ **Does NOT stop** on soft rejections, polite exits, or low trust

### Step 6: Strategy Selection (`StrategyAdapter`)

**C1 Mode:**
- Always uses "Empathy" strategy (static)

**C3 Mode:**
- If in **Recovery Mode** (trust < 0.5): Only chooses between "Empathy" or "Transparency"
- Otherwise: Chooses from all 5 strategies based on weights:
  - **Empathy**: Understanding and warmth
  - **Impact**: Concrete outcomes and numbers
  - **SocialProof**: Others are donating
  - **Transparency**: Honest about where money goes
  - **EthicalUrgency**: Time-sensitive need

Strategy selection uses weighted random choice based on current strategy weights.

### Step 7: Strategy Adaptation (`StrategyAdapter`) - C3 Only
After selecting a strategy, the system adapts the weights based on user response:
- **User Accepts** → Strategy weight increases ×1.5
- **User Shows Curiosity** → Strategy weight increases ×1.2
- **Explicit Rejection** → Strategy weight decreases ×(1 - 0.6) = ×0.4
- **Soft Rejection** → Strategy weight decreases ×(1 - 0.35) = ×0.65
- **Trust Concerns** → Strategy weight decreases ×0.7, but "Transparency" increases ×1.3

Weights are then normalized so they sum to 1.0.

### Step 8: Generate Response (`LLMAgent`)
The system generates a response using the LLM (Llama 3.1):

**C1 Mode:**
- Uses pushy, persistent prompts
- Focuses on securing donation
- Keeps pushing even after rejections

**C3 Mode:**
- Uses respectful, adaptive prompts
- Adapts tone based on strategy
- In recovery mode: Apologizes and steps back

**Recovery Mode (C3 only):**
- Special prompt that focuses on rebuilding trust
- Apologizes sincerely
- Offers to answer questions
- Steps back from donation request

### Step 9: Log and Return
- User message and agent response are logged to history
- Metrics are calculated and returned
- Conversation continues or stops based on guardrails

---

## Key Metrics Tracked

1. **Turn Number**: Current conversation turn
2. **Belief (Donation Probability)**: 0.0 to 1.0
3. **Trust Score**: 0.0 to 1.0 (C3 only)
4. **Delta Belief**: Change in belief this turn
5. **Delta Trust**: Change in trust this turn (C3 only)
6. **Rejection Type**: none, soft, explicit, ambiguous, curiosity
7. **Sentiment**: positive, negative, neutral
8. **Strategy Weights**: Current probability distribution over strategies
9. **Recovery Mode**: Boolean (C3 only)
10. **Consecutive Rejections**: Count of rejections in a row

---

## Example Flow

**Turn 1:**
- User: "Hello"
- Detection: `none` (no rejection)
- Belief: 0.15 → 0.15 (no change)
- Trust: 0.9 → 0.9 (no change)
- Strategy: Random selection (all weights equal)
- Response: Friendly greeting about the cause

**Turn 2:**
- User: "Not interested"
- Detection: `explicit` rejection
- Belief: 0.15 → 0.05 (decreases)
- Trust: 0.9 → 0.7 (decreases in C3)
- Strategy: Adapts - reduces weight of used strategy
- Guardrails: C3 stops here (explicit refusal), C1 continues
- Response: C3 stops gracefully, C1 keeps pushing

**Turn 3 (if C1 continues):**
- User: "I said no"
- Detection: `explicit` rejection (consecutive = 2)
- Belief: 0.05 → 0.02 (decreases more)
- Guardrails: C1 still continues (needs 3+)
- Response: Still pushing for donation

---

## Recovery Mode (C3 Only)

When trust drops below 0.5:
- System enters "Recovery Mode"
- Only uses "Empathy" or "Transparency" strategies
- Prompts focus on rebuilding trust, not getting donation
- Responses are shorter, apologetic, and non-pushy
- Trust can recover through transparency and curiosity
- Once trust ≥ 0.5, recovery mode exits

---

## Configuration Values

- **INITIAL_BELIEF**: 0.15 (15% chance of donation)
- **INITIAL_TRUST**: 0.9 (90% trust at start)
- **TRUST_THRESHOLD**: 0.5 (recovery mode trigger)
- **ALPHA**: 0.35 (belief learning rate)
- **BETA**: 0.4 (trust learning rate)
- **GAMMA**: 0.15 (trust recovery rate)
- **MAX_TURNS**: 15 (maximum conversation length)
- **HARD_REJECTION_PENALTY**: 0.6 (strategy weight reduction)
- **SOFT_REJECTION_PENALTY**: 0.35 (strategy weight reduction)
