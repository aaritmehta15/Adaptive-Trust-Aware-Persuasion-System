"""
Belief and Trust Tracking Modules
"""

from typing import Dict
import numpy as np
from src.config import Config


class BeliefTracker:
    def __init__(self):
        self.belief = Config.INITIAL_BELIEF
        self.history = [self.belief]

    def update(self, rejection_info: Dict, trust: float) -> float:
        rtype = rejection_info['rejection_type']
        is_accept = rejection_info['is_acceptance']
        is_curious = rejection_info['is_curiosity']
        trust_concern = rejection_info['trust_concern']
        sent = rejection_info['sentiment_score']

        if is_accept:
            effect = (1 - self.belief) * 0.9
        elif rtype == 'explicit':
            effect = -0.9
        elif trust_concern:
            effect = -0.7
        elif rtype == 'soft':
            effect = -0.45
        elif rtype == 'ambiguous':
            effect = -0.25
        elif is_curious:
            effect = 0.25
        elif sent > 0.3:
            effect = 0.15
        else:
            effect = 0.0

        delta = Config.ALPHA * effect

        # Trust gating
        if trust < Config.TRUST_THRESHOLD and delta > 0:
            delta = 0.0

        self.belief = np.clip(self.belief + delta, 0, 1)
        self.history.append(self.belief)
        return delta

    def get(self) -> float:
        return self.belief


class TrustTracker:
    def __init__(self):
        self.trust = Config.INITIAL_TRUST
        self.history = [self.trust]
        self.recovery_mode = False

    def update(self, rejection_info: Dict, strategy: str):
        rtype = rejection_info['rejection_type']
        concern = rejection_info['trust_concern']

        delta = 0.0

        # Trust erosion
        if concern:
            delta = -Config.BETA * 0.6
        elif rtype in ['soft', 'ambiguous']:
            delta = -Config.BETA * 0.3
        elif rtype == 'explicit':
            delta = -Config.BETA * 0.5

        # Trust recovery
        elif strategy == 'Transparency':
            delta = Config.GAMMA
        elif rejection_info['is_curiosity']:
            delta = Config.GAMMA * 0.3

        self.trust = np.clip(self.trust + delta, 0, 1)
        self.history.append(self.trust)

        # Recovery mode logic
        if self.trust < Config.TRUST_THRESHOLD:
            self.recovery_mode = True
        elif self.trust >= Config.TRUST_THRESHOLD:
            self.recovery_mode = False

        return delta, self.recovery_mode

    def get(self):
        return self.trust
