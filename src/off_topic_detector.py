"""
Off-Topic Detection Module
Detects if user messages are off-topic and unrelated to the donation conversation
"""

import re
from typing import Dict, List


class OffTopicDetector:
    """
    Detects if user messages are off-topic (unrelated to donation/fundraising)
    """
    
    # Topics that are considered ON-TOPIC
    ON_TOPIC_PATTERNS = [
        # Donation-related
        r'\b(donate|donation|give|contribute|support|help|fund|fundraising)\b',
        r'\b(money|payment|pay|amount|rupee|₹|dollar|usd)\b',
        r'\b(charity|charitable|cause|organization|ngo|nonprofit)\b',
        
        # Cause-related
        r'\b(education|children|kids|school|students|learning|teach)\b',
        r'\b(help|support|assist|aid|benefit|impact|difference)\b',
        r'\b(need|needy|underprivileged|poor|poverty|disadvantaged)\b',
        
        # Trust/legitimacy questions
        r'\b(trust|legitimate|real|genuine|verify|prove|authentic)\b',
        r'\b(where.*money|how.*used|transparency|accountability)\b',
        
        # Information requests
        r'\b(tell.*more|explain|information|details|about|what|how|why|when|where)\b',
        r'\b(question|ask|curious|interested|learn|know|understand)\b',
        
        # Responses to agent
        r'\b(yes|no|maybe|sure|ok|okay|thanks|thank|appreciate)\b',
        r'\b(interested|not interested|later|now|think|consider)\b',
        
        # Greetings and conversation flow
        r'\b(hello|hi|hey|greetings|good|morning|afternoon|evening)\b',
        r'\b(bye|goodbye|see.*you|later|talk|chat|conversation)\b',
    ]
    
    # Strong off-topic indicators
    OFF_TOPIC_PATTERNS = [
        # Completely unrelated topics
        r'\b(weather|rain|sun|cloud|temperature|forecast)\b',
        r'\b(sports|football|soccer|basketball|game|match|team|player)\b',
        r'\b(movie|film|actor|actress|cinema|theater|show|tv|television)\b',
        r'\b(food|restaurant|recipe|cooking|eat|meal|dinner|lunch|breakfast)\b',
        r'\b(travel|vacation|trip|hotel|flight|airplane|beach|holiday)\b',
        r'\b(shopping|buy|purchase|store|mall|shop|product|item)\b',
        r'\b(work|job|career|office|boss|colleague|meeting|project)\b',
        r'\b(relationship|dating|girlfriend|boyfriend|marriage|wedding)\b',
        r'\b(health|doctor|hospital|medicine|sick|ill|disease|treatment)\b',
        r'\b(politics|election|vote|president|government|policy|law)\b',
        r'\b(technology|computer|phone|app|software|internet|website)\b',
        r'\b(car|vehicle|drive|road|traffic|parking|gas|fuel)\b',
        r'\b(pet|dog|cat|animal|pet|veterinary)\b',
        r'\b(hobby|interest|pastime|activity|fun|entertainment)\b',
    ]
    
    def __init__(self, donation_context: Dict):
        """
        Initialize with donation context to check relevance
        
        Args:
            donation_context: Dictionary with 'organization', 'cause', 'amounts', 'impact'
        """
        self.ctx = donation_context
        self._build_context_patterns()
    
    def _build_context_patterns(self):
        """Build patterns from donation context"""
        self.context_patterns = []
        
        # Extract keywords from context
        org_words = self.ctx.get('organization', '').lower().split()
        cause_words = self.ctx.get('cause', '').lower().split()
        
        # Add organization and cause words as on-topic
        for word in org_words + cause_words:
            if len(word) > 3:  # Only meaningful words
                self.context_patterns.append(r'\b' + re.escape(word) + r'\b')
    
    def detect(self, user_message: str) -> Dict:
        """
        Detect if message is off-topic
        
        Returns:
            Dict with:
                - is_off_topic: bool
                - confidence: float (0.0 to 1.0)
                - reason: str (explanation)
        """
        msg = user_message.lower().strip()
        
        # Check for strong off-topic indicators first
        off_topic_matches = sum(1 for pattern in self.OFF_TOPIC_PATTERNS 
                               if re.search(pattern, msg, re.IGNORECASE))
        
        # Check for on-topic indicators
        on_topic_matches = sum(1 for pattern in self.ON_TOPIC_PATTERNS 
                              if re.search(pattern, msg, re.IGNORECASE))
        
        # Check context-specific patterns
        context_matches = sum(1 for pattern in self.context_patterns 
                             if re.search(pattern, msg, re.IGNORECASE))
        
        # Decision logic
        if off_topic_matches >= 2:
            # Strong off-topic signal
            return {
                'is_off_topic': True,
                'confidence': min(0.9, 0.5 + (off_topic_matches * 0.15)),
                'reason': 'Message contains multiple off-topic topics'
            }
        elif off_topic_matches >= 1 and on_topic_matches == 0 and context_matches == 0:
            # Off-topic with no on-topic signals
            return {
                'is_off_topic': True,
                'confidence': 0.7,
                'reason': 'Message appears unrelated to donation conversation'
            }
        elif on_topic_matches >= 1 or context_matches >= 1:
            # Has on-topic signals
            return {
                'is_off_topic': False,
                'confidence': 0.8 if (on_topic_matches + context_matches) >= 2 else 0.6,
                'reason': 'Message is relevant to donation conversation'
            }
        elif len(msg.split()) <= 2:
            # Very short messages might be greetings/responses - assume on-topic
            return {
                'is_off_topic': False,
                'confidence': 0.5,
                'reason': 'Short message, assumed relevant'
            }
        else:
            # Ambiguous - check if it's a question or statement
            is_question = msg.strip().endswith('?')
            if is_question and off_topic_matches == 0:
                # Question without off-topic signals - likely on-topic
                return {
                    'is_off_topic': False,
                    'confidence': 0.6,
                    'reason': 'Question without clear off-topic indicators'
                }
            else:
                # Ambiguous - lean towards off-topic if no clear signals
                return {
                    'is_off_topic': off_topic_matches > 0,
                    'confidence': 0.5,
                    'reason': 'Ambiguous message'
                }
    
    def _match(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any pattern"""
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
