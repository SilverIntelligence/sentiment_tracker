"""Sentiment analysis with VADER + custom rules."""

import re
from typing import Dict, List, Optional

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.nlp.text_processor import TextProcessor
from app.nlp.vocabulary import BEARISH_VERBS, BULLISH_VERBS, NOISE_PATTERNS


class SentimentAnalyzer:
    """Sentiment analyzer using VADER with domain-specific rules."""

    def __init__(self):
        """Initialize sentiment analyzer."""
        self.vader = SentimentIntensityAnalyzer()
        self.text_processor = TextProcessor()

        # Compile patterns
        self.noise_patterns = [re.compile(p, re.IGNORECASE) for p in NOISE_PATTERNS]
        self.bullish_pattern = re.compile(
            r"\b(" + "|".join(BULLISH_VERBS) + r")\b", re.IGNORECASE
        )
        self.bearish_pattern = re.compile(
            r"\b(" + "|".join(BEARISH_VERBS) + r")\b", re.IGNORECASE
        )

    def analyze(self, text: str, entities: Optional[List[str]] = None) -> Dict:
        """
        Analyze sentiment of text.

        Args:
            text: Input text
            entities: Optional list of entities mentioned in text

        Returns:
            Dict with sentiment scores and metadata
        """
        if not text:
            return {
                "compound": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
                "adjusted_compound": 0.0,
                "confidence": 0.0,
            }

        # Normalize text
        normalized_text = self.text_processor.normalize(text)

        # Get base VADER scores
        vader_scores = self.vader.polarity_scores(normalized_text)

        # Apply rule-based adjustments
        adjusted_compound = self._apply_rules(
            normalized_text, vader_scores["compound"], entities
        )

        # Calculate confidence based on score magnitude and text length
        confidence = self._calculate_confidence(adjusted_compound, text)

        return {
            "compound": vader_scores["compound"],
            "positive": vader_scores["pos"],
            "negative": vader_scores["neg"],
            "neutral": vader_scores["neu"],
            "adjusted_compound": adjusted_compound,
            "confidence": confidence,
        }

    def _apply_rules(
        self, text: str, base_score: float, entities: Optional[List[str]] = None
    ) -> float:
        """
        Apply domain-specific rules to adjust sentiment.

        Args:
            text: Normalized text
            base_score: Base VADER compound score
            entities: List of mentioned entities

        Returns:
            Adjusted sentiment score
        """
        adjusted = base_score

        # Rule 1: Check for noise/meme patterns - dampen sentiment
        noise_count = sum(
            1 for pattern in self.noise_patterns if pattern.search(text)
        )
        if noise_count > 0:
            # Dampen by 30% per noise pattern (max 70% dampening)
            dampen_factor = max(0.3, 1.0 - (noise_count * 0.3))
            adjusted *= dampen_factor

        # Rule 2: Boost if directional verbs present with entities
        if entities:
            # Check for bullish verbs near entities
            bullish_matches = self.bullish_pattern.findall(text)
            bearish_matches = self.bearish_pattern.findall(text)

            if bullish_matches:
                # Boost positive sentiment
                adjusted = adjusted + (1.0 - abs(adjusted)) * 0.2
            elif bearish_matches:
                # Boost negative sentiment
                adjusted = adjusted - (1.0 - abs(adjusted)) * 0.2

        # Rule 3: Reduce confidence for very short text
        if len(text.split()) < 5:
            adjusted *= 0.7

        # Clamp to [-1, 1]
        adjusted = max(-1.0, min(1.0, adjusted))

        return adjusted

    def _calculate_confidence(self, score: float, text: str) -> float:
        """
        Calculate confidence in sentiment score.

        Args:
            score: Sentiment compound score
            text: Original text

        Returns:
            Confidence value [0, 1]
        """
        # Base confidence on score magnitude
        confidence = abs(score)

        # Adjust based on text length
        word_count = len(text.split())

        if word_count < 5:
            confidence *= 0.5
        elif word_count < 10:
            confidence *= 0.7
        elif word_count > 50:
            confidence *= 1.2

        # Check for uncertainty words
        uncertainty_words = [
            "maybe",
            "perhaps",
            "might",
            "could",
            "possibly",
            "uncertain",
        ]
        if any(word in text.lower() for word in uncertainty_words):
            confidence *= 0.8

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    def classify(self, text: str, entities: Optional[List[str]] = None) -> str:
        """
        Classify text sentiment as bullish, bearish, or neutral.

        Args:
            text: Input text
            entities: Optional list of entities

        Returns:
            'bullish', 'bearish', or 'neutral'
        """
        result = self.analyze(text, entities)
        score = result["adjusted_compound"]

        if score > 0.2:
            return "bullish"
        elif score < -0.2:
            return "bearish"
        else:
            return "neutral"

    def batch_analyze(
        self, texts: List[str], entities_list: Optional[List[List[str]]] = None
    ) -> List[Dict]:
        """
        Analyze sentiment for multiple texts.

        Args:
            texts: List of text strings
            entities_list: Optional list of entity lists (one per text)

        Returns:
            List of sentiment result dicts
        """
        results = []

        for i, text in enumerate(texts):
            entities = entities_list[i] if entities_list else None
            result = self.analyze(text, entities)
            results.append(result)

        return results
