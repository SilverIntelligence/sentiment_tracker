"""Entity extraction for precious metals domain."""

import re
from collections import Counter
from typing import Dict, List, Set

from app.nlp.text_processor import TextProcessor
from app.nlp.vocabulary import (
    ETFS,
    FUTURES,
    METALS,
    MINERS,
    get_entity_category,
    get_normalized_entity,
)


class EntityExtractor:
    """Extracts entities (metals, tickers, instruments) from text."""

    def __init__(self):
        """Initialize entity extractor."""
        self.text_processor = TextProcessor()

        # Build entity patterns
        self._build_patterns()

    def _build_patterns(self):
        """Build regex patterns for entity matching."""
        self.patterns = {}

        # Metal patterns (multi-word support)
        metal_terms = []
        for terms in METALS.values():
            metal_terms.extend(terms)

        # Sort by length (longest first) to match multi-word phrases first
        metal_terms.sort(key=len, reverse=True)

        # Escape special regex characters
        escaped_terms = [re.escape(term) for term in metal_terms]
        self.patterns["metals"] = re.compile(
            r"\b(" + "|".join(escaped_terms) + r")\b", re.IGNORECASE
        )

        # Ticker patterns (must be whole word, case-sensitive for some)
        all_tickers = list(ETFS.keys()) + list(FUTURES.keys()) + list(MINERS.keys())

        # Special handling for ambiguous tickers
        # 'AG' could be a word, so require it to be uppercase or with $ prefix
        self.ambiguous_tickers = {"AG", "AU", "SI", "GC"}

        ticker_patterns = []
        for ticker in all_tickers:
            if ticker in self.ambiguous_tickers:
                # Require $ prefix or all uppercase in context
                ticker_patterns.append(rf"\${ticker}\b|(?<![a-z]){ticker}(?![a-z])")
            else:
                ticker_patterns.append(rf"\b{re.escape(ticker)}\b")

        self.patterns["tickers"] = re.compile(
            "(" + "|".join(ticker_patterns) + ")", re.IGNORECASE
        )

    def extract(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities from text.

        Args:
            text: Input text

        Returns:
            Dict with entity categories and their occurrences
        """
        if not text:
            return {}

        # Normalize text for better matching
        normalized = self.text_processor.clean(text)

        entities = {"metals": [], "tickers": []}

        # Extract metals
        metal_matches = self.patterns["metals"].findall(normalized)
        entities["metals"] = [m.lower() for m in metal_matches]

        # Extract tickers (keep original text for case sensitivity)
        ticker_matches = self.patterns["tickers"].findall(text)
        # Flatten matches (regex groups may create tuples)
        ticker_matches = [m if isinstance(m, str) else m[0] for m in ticker_matches]
        entities["tickers"] = [
            m.strip().lstrip("$").upper() for m in ticker_matches if m
        ]

        return entities

    def extract_unique(self, text: str) -> Set[str]:
        """
        Extract unique normalized entities from text.

        Args:
            text: Input text

        Returns:
            Set of unique normalized entity names
        """
        entities_by_category = self.extract(text)

        unique_entities = set()

        # Add normalized metals
        for entity in entities_by_category.get("metals", []):
            normalized = get_normalized_entity(entity)
            unique_entities.add(normalized)

        # Add tickers as-is (already normalized)
        for entity in entities_by_category.get("tickers", []):
            unique_entities.add(entity)

        return unique_entities

    def extract_with_counts(self, text: str) -> Dict[str, int]:
        """
        Extract entities with occurrence counts.

        Args:
            text: Input text

        Returns:
            Dict mapping entity -> count
        """
        entities_by_category = self.extract(text)

        all_entities = []

        # Normalize metals
        for entity in entities_by_category.get("metals", []):
            normalized = get_normalized_entity(entity)
            all_entities.append(normalized)

        # Add tickers
        all_entities.extend(entities_by_category.get("tickers", []))

        # Count occurrences
        return dict(Counter(all_entities))

    def has_entity(self, text: str, entity: str) -> bool:
        """
        Check if text contains a specific entity.

        Args:
            text: Input text
            entity: Entity to search for

        Returns:
            True if entity is found
        """
        entities = self.extract_unique(text)
        return entity.lower() in {e.lower() for e in entities}

    def get_primary_entity(self, text: str) -> str:
        """
        Get the primary (most mentioned) entity in text.

        Args:
            text: Input text

        Returns:
            Primary entity name or empty string
        """
        counts = self.extract_with_counts(text)

        if not counts:
            return ""

        # Return most common entity
        return max(counts.items(), key=lambda x: x[1])[0]
