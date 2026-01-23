"""
Strategy Adaptation Module
"""

from typing import Dict
import numpy as np
from src.config import Config


class StrategyAdapter:
    # Hard allowlist for recovery mode (PDF-aligned)
    RECOVERY_ALLOWED = {'Empathy', 'Transparency'}

    def __init__(self):
        n = len(Config.STRATEGIES)
        self.weights = {s: 1.0/n for s in Config.STRATEGIES}
        self.history = {s: [1.0/n] for s in Config.STRATEGIES}
        self.count = {s: 0 for s in Config.STRATEGIES}

    def select(self, in_recovery: bool) -> str:
        # -------- HARD TRUST CONSTRAINT --------
        if in_recovery:
            available = {
                s: self.weights[s]
                for s in self.RECOVERY_ALLOWED
                if s in self.weights
            }
        else:
            available = self.weights.copy()
        # --------------------------------------

        strats = list(available.keys())
        wts = list(available.values())

        # Safety fallback (should never happen, but defensive)
        if not strats:
            strats = ['Empathy']
            wts = [1.0]

        total = sum(wts)
        if total == 0:
            wts = [1.0/len(strats)] * len(strats)
        else:
            wts = [w/total for w in wts]

        chosen = np.random.choice(strats, p=wts)
        self.count[chosen] += 1
        return chosen

    def adapt(self, strategy: str, rejection_info: Dict):
        # IMPORTANT: Do not adapt forbidden strategies in recovery
        # (weights are preserved but not used)
        rtype = rejection_info['rejection_type']
        is_accept = rejection_info['is_acceptance']
        is_curious = rejection_info['is_curiosity']

        if is_accept:
            self.weights[strategy] = min(1.0, self.weights[strategy] * 1.5)
        elif is_curious:
            self.weights[strategy] = min(1.0, self.weights[strategy] * 1.2)
        elif rtype == 'explicit':
            self.weights[strategy] = max(
                Config.MIN_STRATEGY_WEIGHT,
                self.weights[strategy] * (1 - Config.HARD_REJECTION_PENALTY)
            )
        elif rtype == 'soft':
            self.weights[strategy] = max(
                Config.MIN_STRATEGY_WEIGHT,
                self.weights[strategy] * (1 - Config.SOFT_REJECTION_PENALTY)
            )

        if rejection_info['trust_concern']:
            self.weights[strategy] = max(
                Config.MIN_STRATEGY_WEIGHT,
                self.weights[strategy] * 0.7
            )
            self.weights['Transparency'] = min(
                1.0,
                self.weights['Transparency'] * 1.3
            )

        # Renormalize
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {s: w/total for s, w in self.weights.items()}

        for s in Config.STRATEGIES:
            self.history[s].append(self.weights[s])
