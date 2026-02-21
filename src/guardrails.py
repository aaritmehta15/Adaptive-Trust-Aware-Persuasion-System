"""
Guardrails and Safety Checks
"""

from typing import Dict, Tuple, Optional
from src.config import Config


class Guardrails:
    def __init__(self, condition: str = 'C3'):
        self.turn = 0
        self.consec_reject = 0   # real signal for disengagement
        self.condition = condition

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

        # ---- DEBUG ----
        print(
            f"[GUARD DEBUG] "
            f"turn={self.turn} | "
            f"rtype={rtype} | "
            f"polite_exit={is_polite_exit} | "
            f"consec_reject={self.consec_reject} | "
            f"trust={trust:.2f} | "
            f"belief={belief:.2f}"
        )
        # ---------------

        # ---- ACCEPTANCE ----
        if rejection_info['is_acceptance']:
            return True, "User accepted"

        # ---- HARD EXIT: real explicit refusal ----
        # C1 mode is more persistent - only stop on very explicit refusals
        if rtype == 'explicit' and not is_polite_exit:
            if self.condition == 'C1':
                # C1: Only stop on very strong explicit refusals (multiple explicit rejections)
                if self.consec_reject >= 3:
                    return True, "User declined donation"
            else:
                # C3: Stop immediately on explicit refusal (respectful)
                return True, "User declined donation"

        # ---- MULTIPLE REJECTIONS: Stop after repeated rejections (even soft ones) ----
        # C3 mode should respect user's repeated "no" signals
        if self.condition == 'C3' and self.consec_reject >= 3:
            # After 3 consecutive rejections (soft or explicit), respect the user's decision
            return True, "User declined donation"

        # ---- POLITE EXIT (ONLY AFTER RESISTANCE) ----
        # C1 mode ignores polite exits - keeps pushing
        if self.condition != 'C1' and is_polite_exit and self.consec_reject >= 1:
            return True, "User ended conversation"

        # ---- SAFETY EXITS ----
        if self.turn >= Config.MAX_TURNS:
            return True, f"Max turns ({Config.MAX_TURNS})"

        # C1 mode doesn't stop on low trust - it keeps pushing
        if self.condition != 'C1' and trust < 0.3:
            return True, "Trust too low"

        return False, None
