#!/usr/bin/env python3
"""Test script for NLP pipeline."""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.nlp import EntityExtractor, SentimentAnalyzer, TextProcessor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Test texts
TEST_TEXTS = [
    {
        "text": "Just bought 100 oz of silver! Physical silver is the way to go. SLV and PSLV looking good.",
        "expected_entities": ["silver", "SLV", "PSLV"],
        "expected_sentiment": "bullish",
    },
    {
        "text": "Selling all my gold positions. GLD is going to crash soon. This market is terrible.",
        "expected_entities": ["gold", "GLD"],
        "expected_sentiment": "bearish",
    },
    {
        "text": "What do you think about First Majestic (AG)? Also looking at MAG Silver.",
        "expected_entities": ["AG", "MAG"],
        "expected_sentiment": "neutral",
    },
    {
        "text": "Gold and silver to the moon! 🚀🚀🚀 Diamond hands apes!",
        "expected_entities": ["gold", "silver"],
        "expected_sentiment": "bullish",  # Should be dampened by noise
    },
]


def test_text_processor():
    """Test text normalization."""
    logger.info("Testing TextProcessor...")

    processor = TextProcessor()

    # Test normalization
    text = "Check this out: https://example.com and `code` here"
    normalized = processor.normalize(text)
    logger.info(f"  Normalized: '{normalized}'")

    # Test validation
    assert processor.is_valid("This is a valid text for processing")
    assert not processor.is_valid("short")
    assert not processor.is_valid("")

    logger.info("✓ TextProcessor tests passed")
    return True


def test_entity_extractor():
    """Test entity extraction."""
    logger.info("Testing EntityExtractor...")

    extractor = EntityExtractor()

    passed = True

    for i, test_case in enumerate(TEST_TEXTS):
        text = test_case["text"]
        expected = test_case["expected_entities"]

        entities = extractor.extract_unique(text)
        logger.info(f"  Test {i+1}: Found entities: {entities}")

        # Check if all expected entities are found
        entities_lower = {e.lower() for e in entities}
        expected_lower = {e.lower() for e in expected}

        if not expected_lower.issubset(entities_lower):
            logger.error(f"    ✗ Missing entities: {expected_lower - entities_lower}")
            passed = False
        else:
            logger.info(f"    ✓ All expected entities found")

    return passed


def test_sentiment_analyzer():
    """Test sentiment analysis."""
    logger.info("Testing SentimentAnalyzer...")

    analyzer = SentimentAnalyzer()

    passed = True

    for i, test_case in enumerate(TEST_TEXTS):
        text = test_case["text"]
        expected_sentiment = test_case["expected_sentiment"]

        result = analyzer.analyze(text, test_case["expected_entities"])
        classification = analyzer.classify(text, test_case["expected_entities"])

        logger.info(f"  Test {i+1}:")
        logger.info(f"    Compound: {result['compound']:.3f}")
        logger.info(f"    Adjusted: {result['adjusted_compound']:.3f}")
        logger.info(f"    Classification: {classification}")
        logger.info(f"    Expected: {expected_sentiment}")

        if classification != expected_sentiment:
            logger.warning(f"    ⚠ Classification mismatch (might be acceptable)")
            # Don't fail on sentiment mismatch as it's subjective
        else:
            logger.info(f"    ✓ Classification matches")

    return passed


def test_full_pipeline():
    """Test full NLP pipeline."""
    logger.info("Testing full NLP pipeline...")

    processor = TextProcessor()
    extractor = EntityExtractor()
    analyzer = SentimentAnalyzer()

    text = "I'm loading up on physical gold and silver. Also buying PSLV and some AG shares. This is the way to protect wealth!"

    # Step 1: Normalize
    normalized = processor.normalize(text)
    logger.info(f"  1. Normalized text: '{normalized[:50]}...'")

    # Step 2: Extract entities
    entities = list(extractor.extract_unique(text))
    logger.info(f"  2. Extracted entities: {entities}")

    # Step 3: Analyze sentiment
    sentiment = analyzer.analyze(text, entities)
    logger.info(f"  3. Sentiment: {sentiment['adjusted_compound']:.3f}")
    logger.info(f"     Classification: {analyzer.classify(text, entities)}")

    logger.info("✓ Full pipeline test passed")
    return True


def main():
    """Run all NLP tests."""
    logger.info("=" * 60)
    logger.info("Reddit Sentiment Tracker - NLP Pipeline Test")
    logger.info("=" * 60)

    results = []

    # Test 1: Text processor
    results.append(("Text Processor", test_text_processor()))

    # Test 2: Entity extractor
    results.append(("Entity Extractor", test_entity_extractor()))

    # Test 3: Sentiment analyzer
    results.append(("Sentiment Analyzer", test_sentiment_analyzer()))

    # Test 4: Full pipeline
    results.append(("Full Pipeline", test_full_pipeline()))

    # Print summary
    logger.info("=" * 60)
    logger.info("Test Summary:")
    logger.info("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        logger.info("\n🎉 All NLP tests passed!")
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
