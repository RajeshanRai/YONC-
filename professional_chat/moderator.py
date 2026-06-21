"""
AI-powered content moderation for professional chat.
Detects hate speech, bullying, spam, and other toxicity.
"""

import re
from typing import Tuple


class ContentModerator:
    """Detect and flag toxic content in chat messages."""

    # Keywords for hate speech detection
    HATE_SPEECH_KEYWORDS = [
        'hate', 'despise', 'detest', 'racist', 'sexist', 'ableist',
        'discriminat', 'prejudice', 'bigot', 'intolerant'
    ]

    # Keywords for bullying detection
    BULLYING_KEYWORDS = [
        'stupid', 'idiot', 'dumb', 'loser', 'worthless', 'pathetic',
        'retard', 'ugly', 'fat', 'mockery', 'humiliat', 'shame', 'coward',
        'weak', 'pathetic', 'bully', 'harass'
    ]

    # Patterns for spam detection
    SPAM_PATTERNS = [
        r'(.)\1{9,}',  # Repeated character 10+ times
        r'(?:https?://|www\.)\S+',  # URLs
        r'(?:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # Emails
        r'(?:\d{3}[-.]?\d{3}[-.]?\d{4})',  # Phone numbers
        r'(?:buy|click|visit|check|link|subscribe|follow|pm|dm|message).{0,10}(?:http|www|telegram|whatsapp)',
    ]

    # Threshold for toxicity scoring
    TOXICITY_THRESHOLD = 0.3

    @classmethod
    def detect_hate_speech(cls, text: str) -> Tuple[bool, float]:
        """Detect hate speech in text."""
        text_lower = text.lower()
        matches = sum(1 for keyword in cls.HATE_SPEECH_KEYWORDS if keyword in text_lower)
        score = min(1.0, matches * 0.15)
        return score > cls.TOXICITY_THRESHOLD, score

    @classmethod
    def detect_bullying(cls, text: str) -> Tuple[bool, float]:
        """Detect bullying language in text."""
        text_lower = text.lower()
        matches = sum(1 for keyword in cls.BULLYING_KEYWORDS if keyword in text_lower)
        score = min(1.0, matches * 0.12)
        return score > cls.TOXICITY_THRESHOLD, score

    @classmethod
    def detect_spam(cls, text: str) -> Tuple[bool, float]:
        """Detect spam in text."""
        score = 0.0
        
        # Check for repeated characters
        for pattern in cls.SPAM_PATTERNS:
            if re.search(pattern, text):
                score += 0.3
        
        # Check for excessive caps
        if len(text) > 5:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.7:
                score += 0.2
        
        # Check for excessive punctuation
        punctuation_count = sum(1 for c in text if c in '!?.')
        if len(text) > 0 and punctuation_count / len(text) > 0.3:
            score += 0.2
        
        score = min(1.0, score)
        return score > cls.TOXICITY_THRESHOLD, score

    @classmethod
    def moderate(cls, text: str) -> dict:
        """
        Perform full content moderation on text.
        
        Returns:
            {
                'is_flagged': bool,
                'toxicity_score': float,
                'toxicity_reason': str,  # 'hate_speech', 'bullying', 'spam', 'other', or ''
            }
        """
        hate_flagged, hate_score = cls.detect_hate_speech(text)
        bully_flagged, bully_score = cls.detect_bullying(text)
        spam_flagged, spam_score = cls.detect_spam(text)

        # Determine the highest scoring toxicity reason
        scores = {
            'hate_speech': hate_score,
            'bullying': bully_score,
            'spam': spam_score,
        }

        is_flagged = hate_flagged or bully_flagged or spam_flagged
        overall_score = max(hate_score, bully_score, spam_score)
        
        if is_flagged:
            reason = max(scores, key=scores.get) if any(scores.values()) else 'other'
        else:
            reason = ''

        return {
            'is_flagged': is_flagged,
            'toxicity_score': overall_score,
            'toxicity_reason': reason,
        }
