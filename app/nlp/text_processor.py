"""Text preprocessing and normalization."""

import re
from typing import Optional


class TextProcessor:
    """Handles text normalization and cleaning."""

    def __init__(self):
        """Initialize text processor."""
        # URL pattern
        self.url_pattern = re.compile(r"https?://\S+|www\.\S+")

        # Code block pattern (markdown)
        self.code_pattern = re.compile(r"`{1,3}[^`]*`{1,3}")

        # Quote pattern (markdown)
        self.quote_pattern = re.compile(r"^>.*$", re.MULTILINE)

        # Multiple whitespace
        self.whitespace_pattern = re.compile(r"\s+")

        # Special characters to remove
        self.special_chars = re.compile(r"[^\w\s\.\,\!\?\-\$\%]")

    def normalize(self, text: str) -> str:
        """
        Normalize text for processing.

        Args:
            text: Raw text

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        text = self.url_pattern.sub(" ", text)

        # Remove code blocks
        text = self.code_pattern.sub(" ", text)

        # Remove quotes
        text = self.quote_pattern.sub(" ", text)

        # Remove excessive special characters (keep basic punctuation)
        text = self.special_chars.sub(" ", text)

        # Normalize whitespace
        text = self.whitespace_pattern.sub(" ", text)

        return text.strip()

    def clean(self, text: str) -> str:
        """
        Clean text more aggressively (for entity extraction).

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        text = self.normalize(text)

        # Remove all punctuation for cleaner matching
        text = re.sub(r"[^\w\s]", " ", text)

        # Normalize whitespace again
        text = self.whitespace_pattern.sub(" ", text)

        return text.strip()

    def is_valid(
        self,
        text: str,
        min_length: int = 10,
        max_length: int = 10000,
        language: str = "en",
    ) -> bool:
        """
        Check if text is valid for processing.

        Args:
            text: Text to validate
            min_length: Minimum character length
            max_length: Maximum character length
            language: Expected language (only 'en' supported)

        Returns:
            True if valid
        """
        if not text or not text.strip():
            return False

        # Check length
        if len(text) < min_length or len(text) > max_length:
            return False

        # Simple English check (most chars should be ASCII)
        ascii_ratio = sum(1 for c in text if ord(c) < 128) / len(text)
        if ascii_ratio < 0.7:
            return False

        return True

    def extract_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitting
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def remove_noise_patterns(self, text: str, patterns: list[str]) -> str:
        """
        Remove noise patterns from text.

        Args:
            text: Input text
            patterns: List of regex patterns to remove

        Returns:
            Text with patterns removed
        """
        for pattern in patterns:
            text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

        # Clean up whitespace
        text = self.whitespace_pattern.sub(" ", text)

        return text.strip()
