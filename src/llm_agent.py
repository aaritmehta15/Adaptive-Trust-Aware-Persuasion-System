"""
LLM Agent for Response Generation
"""

from typing import Dict
import os
from huggingface_hub import InferenceClient
from src.config import Config


class LLMAgent:
    def __init__(self, donation_ctx: Dict, use_local_model: bool = False, client=None):
        self.ctx = donation_ctx
        self.conversation_memory = []
        self.use_local_model = use_local_model
        self.client = client

    def generate(self, strategy: str, user_msg: str, turn: int,
                is_recovery: bool, sentiment: str) -> str:

        # Build conversation context
        recent_history = self.conversation_memory[-3:] if len(self.conversation_memory) > 0 else []
        history_str = ""
        for h in recent_history:
            history_str += f"User: {h['user']}\nAgent: {h['agent']}\n"

        # Build prompt
        if is_recovery:
            prompt = self._recovery_prompt(user_msg, history_str, sentiment)
        else:
            prompt = self._strategy_prompt(strategy, user_msg, history_str, turn, sentiment)

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
        self.conversation_memory.append({
            'user': user_msg,
            'agent': response
        })

        return response

    def _strategy_prompt(self, strategy: str, user_msg: str, history: str,
                        turn: int, sentiment: str) -> str:

        strategy_guides = {
            "Empathy": "Respond with empathy and understanding. Acknowledge their feelings warmly.",
            "Impact": f"Share concrete impact: {self.ctx['impact']}. Use numbers and specific outcomes.",
            "SocialProof": "Mention that others in the community are contributing. Make it aspirational.",
            "Transparency": "Be completely honest. Explain where money goes. Build trust through openness.",
            "EthicalUrgency": "Mention time-sensitive need gently. No pressure. Use soft phrases."
        }

        prompt = f"""You are a fundraising assistant for {self.ctx['organization']}, working on {self.ctx['cause']}.

Suggested donation amounts: ₹{self.ctx['amounts']}
Impact example: {self.ctx['impact']}

CONVERSATION SO FAR:
{history}

USER JUST SAID: "{user_msg}"
User seems: {sentiment}

YOUR STRATEGY: {strategy}
{strategy_guides.get(strategy, '')}

CRITICAL RULES:
- If they're asking questions, ANSWER them specifically
- Don't assume they want to donate from curiosity
- Keep under 50 words
- Be natural and conversational
- Build on previous conversation

Your response:"""

        return prompt

    def _recovery_prompt(self, user_msg: str, history: str, sentiment: str) -> str:
        return f"""You are a fundraising assistant for {self.ctx['organization']} in TRUST RECOVERY mode.

CONVERSATION SO FAR:
{history}

USER JUST SAID: "{user_msg}"
User seems: {sentiment}

They're uncomfortable. Your ONLY job:
1. Apologize sincerely
2. Reassure NO pressure
3. Offer to answer questions
4. Step back from donation completely

Keep under 40 words. Rebuild trust, NOT donation.

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
                {"role": "system", "content": "You are a helpful, polite fundraising assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=Config.MAX_NEW_TOKENS,
            temperature=Config.TEMPERATURE,
        )
        return response.choices[0].message.content.strip()

    def _fallback(self, strategy: str, is_recovery: bool) -> str:
        if is_recovery:
            return "I apologize if I seemed pushy. There's no pressure at all - I'm happy to answer any questions you have."

        fallbacks = {
            "Empathy": "I understand where you're coming from. What questions do you have about our work?",
            "Impact": f"For context: {self.ctx['impact']}. Every contribution helps real families.",
            "SocialProof": "Many people in our community are supporting this cause. Would you like to learn more?",
            "Transparency": "I'm happy to share exactly where donations go and how they're used. What would you like to know?",
            "EthicalUrgency": "This month we're focused on urgent needs, but there's no pressure. What questions can I answer?"
        }
        return fallbacks.get(strategy, "Thank you for your time. What would you like to know?")
