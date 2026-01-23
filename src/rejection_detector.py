"""
Rejection Detection Module
"""

import re
from typing import Dict, List, Tuple
from textblob import TextBlob


class RejectionDetector:

    EXPLICIT_PATTERNS = [
        r'\b(no thanks|no thank you|not interested|don\'t want|won\'t donate)\b',
        r'\b(nope|nah|never|absolutely not|definitely not)\b',
        r'\b(leave me alone|stop asking|not doing|refuse)\b'
    ]

    POLITE_EXIT_PATTERNS = [
        r'\b(okay thanks|ok thanks|okay thank you|ok thank you)\b',
        r'\b(thank you|thanks|appreciate it)\b$',
        r'\b(that\'s all|that is all|nothing else)\b',
        r'\b(i\'m good|all good|we\'re good)\b'
    ]

    SOFT_PATTERNS = [
        r'\b(maybe later|not now|not right now|some other time|another time)\b',
        r'\b(not today|can\'t right now|busy right now)\b',
        r'\b(not sure|unsure|uncertain|hesitant|doubtful)\b',
        r'\b(can\'t afford|no money|tight budget|broke|expensive)\b',
        r'\b(i\'ll think|let me think|need time|consider)\b'
    ]

    TRUST_PATTERNS = [
        r'\b(pushy|aggressive|pressure|uncomfortable|sketchy|scam|fraud)\b',
        r'\b(suspicious|don\'t trust|seems fake|sounds fake)\b',
        r'\b(why are you|what\'s your motive|prove it)\b'
    ]

    CURIOSITY_PATTERNS = [
        r'\b(tell me more|tell me about|what about|explain|how does|how do)\b',
        r'\b(more info|more details|details|information)\b',
        r'\b(curious|interested in learning|want to know|want to hear)\b',
        r'\b(what is|who are|where does|when|why)\b',
        r'\b(can you|could you|would you.*explain|show me)\b'
    ]

    ACCEPTANCE_PATTERNS = [
        r'\b(yes.*i.*donate|i will donate|i\'ll donate|i want to donate)\b',
        r'\b(sign me up|count me in|i\'m in)\b',
        r'\b(where do i donate|how do i donate|how can i donate)\b',
        r'\b(i\'ll give|i will give|i want to give ₹|i can give ₹)\b',
        r'\b(okay.*donate|ok.*donate|sure.*donate|let\'s do it)\b',
        r'\b(take my donation|here\'s my donation|ready to donate)\b'
    ]

    def __init__(self):
        self.sentiment = None

    def detect(self, user_message: str) -> Dict:
        msg = user_message.lower().strip()

        # ---- Polite exit (NOT a refusal) ----
        is_polite_exit = self._match(msg, self.POLITE_EXIT_PATTERNS)

        # ---- Acceptance ----
        if self._match(msg, self.ACCEPTANCE_PATTERNS):
            return {
                'rejection_type': 'none',
                'rejection_confidence': 0.0,
                'trust_concern': False,
                'sentiment_score': 0.9,
                'sentiment_label': 'positive',
                'is_acceptance': True,
                'is_curiosity': False,
                'is_polite_exit': False
            }

        # Curiosity
        is_curiosity = self._match(msg, self.CURIOSITY_PATTERNS)

        # Rejection
        rejection_type = 'none'
        confidence = 0.0

        if self._match(msg, self.EXPLICIT_PATTERNS):
            rejection_type = 'explicit'
            confidence = 0.9
        elif self._match(msg, self.SOFT_PATTERNS):
            rejection_type = 'soft'
            confidence = 0.7

        trust_concern = self._match(msg, self.TRUST_PATTERNS)
        sent_score, sent_label = self._get_sentiment(user_message)

        if is_curiosity and rejection_type == 'none':
            rejection_type = 'curiosity'
            sent_score = max(0.2, sent_score)

        if sent_score < -0.4 and rejection_type == 'none':
            rejection_type = 'ambiguous'
            confidence = 0.5

        if sent_score < -0.6 and rejection_type == 'soft':
            rejection_type = 'explicit'
            confidence = 0.85

        return {
            'rejection_type': rejection_type,
            'rejection_confidence': confidence,
            'trust_concern': trust_concern,
            'sentiment_score': sent_score,
            'sentiment_label': sent_label,
            'is_acceptance': False,
            'is_curiosity': is_curiosity,
            'is_polite_exit': is_polite_exit
        }

    def _match(self, text: str, patterns: List[str]) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def _get_sentiment(self, text: str) -> Tuple[float, str]:
        blob = TextBlob(text)
        pol = blob.sentiment.polarity
        label = 'positive' if pol > 0 else ('negative' if pol < 0 else 'neutral')
        return pol, label
