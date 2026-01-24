# Trust Recovery Flow - How It Works

## Fixed Issues

### 1. Trust Increasing When User Says "I Don't Trust You"
**Problem**: Trust was increasing even when users expressed distrust.

**Root Cause**: The `elif` chain in `TrustTracker.update()` was allowing recovery conditions to overwrite trust erosion.

**Fix**: 
- Trust concerns now ALWAYS decrease trust (priority check)
- Recovery only happens when there's NO trust concern
- Increased trust concern penalty from 0.6×BETA to 0.8×BETA

### 2. Improved Trust Concern Detection
Added more patterns to detect trust concerns:
- "I do not trust you"
- "I don't trust you"
- "not trustworthy"
- "distrust", "mistrust"
- "fake", "fraudulent", "dishonest"
- "lying", "lies"

## Recovery Flow: Negative → Recovery → Donation

### Phase 1: Starting Negative (Trust Drops Below 0.5)

**User says**: "I don't trust you" or "This seems like a scam"

**What happens**:
1. **Rejection Detection**: Detects `trust_concern = True`
2. **Trust Update**: Trust decreases by `-0.8 × BETA = -0.32` (from 0.9 → ~0.58)
   - If trust drops below 0.5 → **Recovery Mode Activated**
3. **Strategy Adaptation**: 
   - Current strategy weight decreases ×0.5
   - Transparency weight increases ×1.5
   - Empathy weight increases ×1.2
4. **Strategy Selection**: Only "Empathy" or "Transparency" available
5. **Response**: Recovery mode prompt - apologetic, transparent, no pressure

### Phase 2: Recovery Mode (Trust < 0.5)

**System Behavior**:
- Only uses "Empathy" or "Transparency" strategies
- Responses focus on:
  - Sincere apologies
  - Complete transparency about where money goes
  - No pressure - explicitly states no obligation
  - Answering questions honestly
  - Showing genuine care for concerns

**Trust Recovery Mechanisms**:
1. **Transparency Strategy**: +GAMMA = +0.15 per turn
2. **User Curiosity**: +0.3×GAMMA = +0.045 per turn
3. **Positive Sentiment**: +0.2×GAMMA = +0.03 per turn

**Example Recovery Turn**:
- User: "How do I know you're legitimate?"
- System: Uses Transparency strategy
- Trust: +0.15 (if trust was 0.4, now 0.55)
- **Recovery Mode Exits** (trust ≥ 0.5)

### Phase 3: Post-Recovery (Trust ≥ 0.5, Back to Normal)

**System Behavior**:
- All 5 strategies available again
- Can use Impact, SocialProof, EthicalUrgency
- Still respectful (C3 mode), but can actively persuade
- Trust continues to recover through positive interactions

**Example Post-Recovery Turn**:
- User: "Okay, tell me more about the impact"
- System: Can use Impact strategy
- Trust: +0.03 (positive sentiment)
- Belief: +0.25 (curiosity detected)

### Phase 4: Securing Donation

**System Behavior**:
- Uses adapted strategies based on what worked
- If Transparency worked well, it has higher weight
- If user shows acceptance signals → belief increases
- Eventually user says "I'll donate" → conversation ends successfully

## Key Configuration Values

- **BETA = 0.4**: Trust learning rate (how fast trust changes)
- **GAMMA = 0.15**: Trust recovery rate (how fast trust rebuilds)
- **TRUST_THRESHOLD = 0.5**: Recovery mode trigger
- **Trust Concern Penalty**: -0.8 × BETA = -0.32 per turn
- **Transparency Recovery**: +GAMMA = +0.15 per turn

## Example Conversation Flow

**Turn 1**: 
- User: "Hello"
- Trust: 0.9, Belief: 0.15
- Mode: Normal

**Turn 2**:
- User: "I don't trust you, this seems fake"
- Trust: 0.9 → 0.58 (trust concern detected)
- Belief: 0.15 → 0.08 (trust concern penalty)
- Mode: Normal (still above 0.5)

**Turn 3**:
- User: "No really, I think this is a scam"
- Trust: 0.58 → 0.26 (trust concern again, drops below 0.5)
- **Recovery Mode Activated**
- System: Uses Transparency, apologizes, explains legitimacy

**Turn 4**:
- User: "Okay, how do I know where my money goes?"
- Trust: 0.26 → 0.41 (Transparency strategy +0.15)
- System: Explains transparency, shows financial reports
- Mode: Still Recovery (trust < 0.5)

**Turn 5**:
- User: "That's helpful, thank you"
- Trust: 0.41 → 0.56 (positive sentiment +0.03, Transparency +0.15)
- **Recovery Mode Exits** (trust ≥ 0.5)
- System: Can now use all strategies, gently reintroduces cause

**Turn 6**:
- User: "Tell me about the impact"
- Trust: 0.56 → 0.59 (curiosity +0.045)
- Belief: 0.08 → 0.16 (curiosity +0.25)
- System: Uses Impact strategy, shares concrete outcomes

**Turn 7**:
- User: "I'll donate ₹200"
- Trust: 0.59 → 0.74 (acceptance)
- Belief: 0.16 → 0.90 (acceptance)
- **Conversation ends successfully**

## Testing the Recovery Flow

To test the full recovery flow:

1. **Start conversation** - System greets you
2. **Express distrust** - Say "I don't trust you" or "This seems fake"
   - Trust should drop significantly
   - If trust < 0.5, recovery mode activates
3. **Ask questions in recovery** - Ask "How do I know you're legitimate?"
   - System should use Transparency
   - Trust should increase
4. **Show openness** - Say "That's helpful" or "I see"
   - Trust should continue recovering
   - Once trust ≥ 0.5, recovery mode exits
5. **Show interest** - Ask "Tell me more about the impact"
   - System can use all strategies again
   - Belief should increase
6. **Accept donation** - Say "I'll donate" or "I want to donate"
   - Conversation ends successfully

## Debugging

If trust isn't decreasing when you say "I don't trust you":
- Check that `trust_concern` is being detected (should be True)
- Check that trust update is using the concern branch (not recovery branch)
- Trust should decrease by -0.32 per turn when concern is expressed

If recovery isn't working:
- Check that Transparency strategy is being selected in recovery mode
- Trust should increase by +0.15 per turn when Transparency is used
- Check that recovery mode exits when trust ≥ 0.5
