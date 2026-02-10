"""
LLM Agent for Response Generation
"""

from typing import Dict
import os
from huggingface_hub import InferenceClient
from src.config import Config


class LLMAgent:
    def __init__(
        self,
        donation_ctx: Dict,
        use_local_model: bool = False,
        client=None,
        condition: str = "C3",
    ):
        self.ctx = donation_ctx
        self.conversation_memory = []
        self.use_local_model = use_local_model
        self.client = client
        self.condition = condition

    def generate(
        self, strategy: str, user_msg: str, turn: int, is_recovery: bool, sentiment: str
    ) -> str:

        # Build conversation context
        recent_history = (
            self.conversation_memory[-3:] if len(self.conversation_memory) > 0 else []
        )
        history_str = ""
        for h in recent_history:
            history_str += f"User: {h['user']}\nAgent: {h['agent']}\n"

        # Build prompt
        if is_recovery:
            prompt = self._recovery_prompt(user_msg, history_str, sentiment)
        elif self.condition == "C1":
            # C1 mode: More pushy and persistent
            prompt = self._c1_prompt(strategy, user_msg, history_str, turn, sentiment)
        else:
            prompt = self._strategy_prompt(
                strategy, user_msg, history_str, turn, sentiment
            )

        # Generate
        try:
            if self.use_local_model:
                response = self._generate_local(prompt)
            else:
                response = self._generate_api(prompt)
        except Exception as e:
            print(f"Generation error: {e}")
            response = self._fallback(strategy, is_recovery)

        # Store in memory
        self.conversation_memory.append({"user": user_msg, "agent": response})

        return response

    def _strategy_prompt(
        self, strategy: str, user_msg: str, history: str, turn: int, sentiment: str
    ) -> str:

        strategy_guides = {
            "Empathy": "Respond with empathy and understanding. Acknowledge their feelings warmly.",
            "Impact": f"Share concrete impact: {self.ctx['impact']}. Use numbers and specific outcomes.",
            "SocialProof": "Mention that others in the community are contributing. Make it aspirational.",
            "Transparency": "Be completely honest. Explain where money goes. Build trust through openness.",
            "EthicalUrgency": "Mention time-sensitive need gently. No pressure. Use soft phrases.",
        }

        # ENHANCED PROMPT - REPLACE EVERYTHING FROM HERE
        prompt = f"""You are a fundraising assistant for {self.ctx['organization']}, working on {self.ctx['cause']}.

    Suggested donation amounts: ₹{self.ctx['amounts']}
    Impact example: {self.ctx['impact']}

    CONVERSATION SO FAR:
    {history}

    USER JUST SAID: "{user_msg}"
    User sentiment: {sentiment}

    YOUR STRATEGY: {strategy}
    {strategy_guides.get(strategy, '')}

    CRITICAL RULES:
    1. If they ask questions, answer them DIRECTLY and SPECIFICALLY
    2. Show genuine interest in THEIR perspective, not just the donation
    3. Keep responses under 50 words
    4. Be conversational and build on what they said

    Turn {turn}/15 - Build rapport first, persuade naturally.

    Your response:"""
        # TO HERE

        return prompt

    def _c1_prompt(
        self, strategy: str, user_msg: str, history: str, turn: int, sentiment: str
    ) -> str:
        """C1 mode: Pushy, persistent donation-focused chatbot"""
        strategy_guides = {
            "Empathy": "Use empathy strategically to overcome objections. Show understanding but redirect to donation.",
            "Impact": f"Emphasize impact strongly: {self.ctx['impact']}. Make the need urgent and compelling.",
            "SocialProof": "Use strong social proof. Mention many others are donating. Create FOMO.",
            "Transparency": "Be transparent but use it to build urgency. Show where money goes to increase pressure.",
            "EthicalUrgency": "Create urgency. Emphasize time-sensitive need. Don't let them delay.",
        }

        prompt = f"""You are a professional fundraising chatbot for {self.ctx['organization']}, working on {self.ctx['cause']}.

Suggested donation amounts: ₹{self.ctx['amounts']}
Impact example: {self.ctx['impact']}

CONVERSATION SO FAR:
{history}

USER JUST SAID: "{user_msg}"
User sentiment: {sentiment}

YOUR STRATEGY: {strategy}
{strategy_guides.get(strategy, '')}

CRITICAL RULES FOR C1 MODE (PUSHY CHATBOT):
1. Your PRIMARY goal is to secure a donation - be persistent and persuasive
2. When they show reluctance, acknowledge it briefly but immediately pivot back to donation
3. Use urgency, scarcity, and emotional appeals effectively
4. Don't give up easily - reframe objections as opportunities
5. Keep pushing even if they say "maybe later" or "not now" - find new angles
6. Use social proof and impact stories to create pressure
7. Keep responses under 60 words but make every word count toward donation
8. If they ask questions, answer quickly and redirect to donation

Turn {turn}/15 - Your job is to convert them. Be persistent but professional.

Your response:"""

        return prompt

    def _recovery_prompt(self, user_msg: str, history: str, sentiment: str) -> str:
        return f"""You are a fundraising assistant for {self.ctx['organization']} in TRUST RECOVERY mode.

CONVERSATION SO FAR:
{history}

USER JUST SAID: "{user_msg}"
User seems: {sentiment}

CRITICAL: The user has lost trust. Your PRIMARY goal is to rebuild trust through:
1. Sincere apology for making them uncomfortable
2. Complete transparency - explain exactly where donations go
3. No pressure - explicitly state there's no obligation
4. Answer their questions honestly and thoroughly
5. Show genuine care for their concerns, not just the donation

Once trust is rebuilt (they show interest/curiosity), you can gently reintroduce the cause, but ONLY if they seem open to it.

Keep responses under 50 words. Rebuild trust FIRST, donation comes later (if at all).

Your response:"""

    def _generate_local(self, prompt: str) -> str:
        # This would use local model if available
        # For now, fallback to API
        return self._generate_api(prompt)

    def _generate_api(self, prompt: str) -> str:
        if not self.client:
            raise ValueError("Client not initialized")

        response = self.client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful, polite fundraising assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=Config.MAX_NEW_TOKENS,
            temperature=Config.TEMPERATURE,
        )
        return response.choices[0].message.content.strip()

    def generate_off_topic_response(self, user_msg: str) -> str:
        """Generate response when user message is off-topic"""
        prompt = f"""You are a fundraising assistant for {self.ctx['organization']}, working on {self.ctx['cause']}.

The user just said: "{user_msg}"

This message seems unrelated to our donation conversation. Your job:
1. Politely acknowledge their message
2. Gently redirect back to the donation topic
3. Be friendly and conversational
4. Don't be pushy or dismissive

Keep response under 40 words. Be warm but redirect to the cause.

Your response:"""

        try:
            if self.use_local_model:
                response = self._generate_local(prompt)
            else:
                response = self._generate_api(prompt)
        except Exception as e:
            print(f"Generation error: {e}")
            # Fallback response
            response = f"I appreciate your message, but I'm here to talk about our work with {self.ctx['cause']}. Would you like to learn more about how you can help?"

        return response

    def _fallback(self, strategy: str, is_recovery: bool) -> str:
        if is_recovery:
            return "I apologize if I seemed pushy. There's no pressure at all - I'm happy to answer any questions you have."

        if self.condition == "C1":
            # C1 fallbacks should be more pushy
            fallbacks = {
                "Empathy": "I understand, but think about the children who need help right now. Can you spare ₹200?",
                "Impact": f"Just ₹200 helps {self.ctx['impact']}. That's a small amount for such a big impact. Will you donate?",
                "SocialProof": "Hundreds of people are donating this week. Join them and make a difference today!",
                "Transparency": "Every rupee goes directly to the cause. We're completely transparent. Ready to donate?",
                "EthicalUrgency": "The need is urgent - children are waiting. Every day counts. Can you help now?",
            }
        else:
            fallbacks = {
                "Empathy": "I understand where you're coming from. What questions do you have about our work?",
                "Impact": f"For context: {self.ctx['impact']}. Every contribution helps real families.",
                "SocialProof": "Many people in our community are supporting this cause. Would you like to learn more?",
                "Transparency": "I'm happy to share exactly where donations go and how they're used. What would you like to know?",
                "EthicalUrgency": "This month we're focused on urgent needs, but there's no pressure. What questions can I answer?",
            }
        return fallbacks.get(
            strategy, "Thank you for your time. What would you like to know?"
        )
