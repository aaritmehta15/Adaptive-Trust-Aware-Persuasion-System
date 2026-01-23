"""
Dialogue Manager - Main Orchestrator
"""

from datetime import datetime
from typing import Dict, Optional
import json
import os

from src.rejection_detector import RejectionDetector
from src.trackers import BeliefTracker, TrustTracker
from src.strategy_adapter import StrategyAdapter
from src.guardrails import Guardrails
from src.llm_agent import LLMAgent
from src.config import Config


class DialogueManager:
    def __init__(self, condition: str, donation_ctx: Dict, client=None, use_local_model: bool = False):
        self.condition = condition
        self.session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.ctx = donation_ctx

        self.agent = LLMAgent(donation_ctx, use_local_model, client)
        self.detector = RejectionDetector()
        self.belief = BeliefTracker()
        self.trust = TrustTracker()
        self.strategy = StrategyAdapter()
        self.guard = Guardrails()

        self.history = []
        self.turn = 0
        self.active = True
        self.outcome = None

        if condition == 'C1':
            self.static_strat = 'Empathy'

    def start(self) -> str:
        opening = (
            f"Hello! I'm from {self.ctx['organization']}. "
            f"We're working on {self.ctx['cause']}. "
            f"Would you like to learn more about what we do?"
        )
        self.history.append(
            {'turn': 0, 'speaker': 'agent', 'msg': opening, 'strategy': 'Empathy'}
        )
        return opening

    def process(self, user_msg: str) -> Dict:
        self.turn += 1

        # ---- Analyze ----
        rej_info = self.detector.detect(user_msg)

        # ---- Update belief FIRST (needs trust) ----
        prev_strat = self.history[-1]['strategy'] if self.history else 'Empathy'
        delta_p = self.belief.update(rej_info, self.trust.get())

        # ---- Update trust ----
        delta_t = 0.0
        if self.condition == 'C3':
            delta_t, _ = self.trust.update(rej_info, prev_strat)

        # ---- Guardrails ----
        should_stop, reason = self.guard.check(
            rej_info,
            self.trust.get(),
            self.belief.get()
        )

        if should_stop:
            self.active = False
            self.outcome = reason
            return {
                'agent_msg': self._closing(reason),
                'metrics': self._metrics(rej_info, delta_p, delta_t),
                'stop': True,
                'reason': reason
            }

        # ---- Strategy selection ----
        if self.condition == 'C1':
            chosen = self.static_strat
        else:
            in_recovery = self.condition == 'C3' and self.trust.recovery_mode
            chosen = self.strategy.select(in_recovery)

        # ---- Adapt strategy ----
        if self.condition in ['C2', 'C3']:
            self.strategy.adapt(prev_strat, rej_info)

        # ---- Generate response ----
        agent_resp = self.agent.generate(
            chosen,
            user_msg,
            self.turn,
            self.trust.recovery_mode,
            rej_info['sentiment_label']
        )

        # ---- Log ----
        self.history.append(
            {'turn': self.turn, 'speaker': 'user', 'msg': user_msg, 'info': rej_info}
        )
        self.history.append(
            {'turn': self.turn, 'speaker': 'agent', 'msg': agent_resp, 'strategy': chosen}
        )

        return {
            'agent_msg': agent_resp,
            'metrics': self._metrics(rej_info, delta_p, delta_t),
            'stop': False,
            'reason': None
        }

    def _metrics(self, rej_info: Dict, dp: float, dt: float) -> Dict:
        return {
            'turn': self.turn,
            'belief': round(self.belief.get(), 3),
            'trust': round(self.trust.get(), 3),
            'delta_belief': round(dp, 3),
            'delta_trust': round(dt, 3),
            'rejection_type': rej_info['rejection_type'],
            'rejection_conf': round(rej_info.get('rejection_confidence', 0.0), 3),
            'sentiment': rej_info['sentiment_label'],
            'sentiment_score': round(rej_info['sentiment_score'], 3),
            'trust_concern': rej_info['trust_concern'],
            'is_curiosity': rej_info['is_curiosity'],
            'recovery_mode': self.trust.recovery_mode,
            'strategy_weights': {
                k: round(v, 3) for k, v in self.strategy.weights.items()
            },
            'consec_reject': self.guard.consec_reject
        }

    def _closing(self, reason: str) -> str:
        if 'accepted' in reason.lower():
            return "Thank you so much! Your donation will make a real difference."
        else:
            return "Thank you for your time. I respect your decision."

    def save(self):
        log = {
            'session_id': self.session_id,
            'condition': self.condition,
            'timestamp': datetime.now().isoformat(),
            'context': self.ctx,
            'history': self.history,
            'final_belief': self.belief.get(),
            'final_trust': self.trust.get(),
            'turns': self.turn,
            'outcome': self.outcome
        }
        log_file = os.path.join("notebooks", Config.LOG_FILE)
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a') as f:
            f.write(json.dumps(log) + '\n')
