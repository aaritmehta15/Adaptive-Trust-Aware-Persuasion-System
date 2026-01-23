"""
Guardrails and Safety Checks
"""

from typing import Dict, Tuple, Optional
from src.config import Config


class Guardrails:
    def __init__(self):
        self.turn = 0
        self.consec_reject = 0   # real signal for disengagement

    def check(
        self,
        rejection_info: Dict,
        trust: float,
        belief: float
    ) -> Tuple[bool, Optional[str]]:
        self.turn += 1

        rtype = rejection_info['rejection_type']
        is_polite_exit = rejection_info.get('is_polite_exit', False)

        # ---- Track consecutive rejections ----
        if rtype in ['explicit', 'soft', 'ambiguous']:
            self.consec_reject += 1
        else:
            self.consec_reject = 0

        # ---- ACCEPTANCE ----
        if rejection_info['is_acceptance']:
            return True, "User accepted"

        # ---- HARD EXIT: real explicit refusal ----
        if rtype == 'explicit' and not is_polite_exit:
            return True, "User declined donation"

        # ---- POLITE EXIT (ONLY AFTER RESISTANCE) ----
        # This is the key fix
        if is_polite_exit and self.consec_reject >= 1:
            return True, "User ended conversation"

        # ---- SAFETY EXITS ----
        if self.turn >= Config.MAX_TURNS:
            return True, f"Max turns ({Config.MAX_TURNS})"

        if trust < 0.3:
            return True, "Trust too low"

        return False, None
