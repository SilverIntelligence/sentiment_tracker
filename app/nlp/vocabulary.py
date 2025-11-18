"""Entity vocabulary and patterns for precious metals domain."""

# Metals vocabulary
METALS = {
    "gold": [
        "gold",
        "xau",
        "au",
        "bullion",
        "gold coin",
        "gold bar",
        "gold eagle",
        "krugerrand",
        "maple leaf",
        "oz gold",
        "ounce gold",
        "physical gold",
    ],
    "silver": [
        "silver",
        "xag",
        "ag",
        "silver eagle",
        "ase",
        "90%",
        "junk silver",
        "silver bar",
        "silver coin",
        "oz silver",
        "ounce silver",
        "physical silver",
        "constitutional silver",
    ],
}

# ETF tickers
ETFS = {
    "SLV": "iShares Silver Trust",
    "GLD": "SPDR Gold Shares",
    "PSLV": "Sprott Physical Silver Trust",
    "PHYS": "Sprott Physical Gold Trust",
    "IAU": "iShares Gold Trust",
    "SIVR": "Aberdeen Silver ETF",
    "GDX": "VanEck Gold Miners ETF",
    "GDXJ": "VanEck Junior Gold Miners ETF",
    "SIL": "Global X Silver Miners ETF",
}

# Futures symbols
FUTURES = {
    "GC": "Gold Futures",
    "SI": "Silver Futures",
    "GC=F": "Gold Futures (Yahoo)",
    "SI=F": "Silver Futures (Yahoo)",
}

# Mining company tickers
MINERS = {
    "PAAS": "Pan American Silver",
    "AG": "First Majestic Silver",
    "AEM": "Agnico Eagle Mines",
    "NEM": "Newmont Corporation",
    "FSM": "Fortuna Silver Mines",
    "EXK": "Endeavour Silver",
    "MAG": "MAG Silver",
    "HL": "Hecla Mining",
    "CDE": "Coeur Mining",
    "WPM": "Wheaton Precious Metals",
    "FNV": "Franco-Nevada",
    "GOLD": "Barrick Gold",
    "KGC": "Kinross Gold",
    "AU": "AngloGold Ashanti",
}

# Bullish directional verbs
BULLISH_VERBS = [
    "buy",
    "buying",
    "bought",
    "load",
    "loading",
    "loaded",
    "accumulate",
    "accumulating",
    "long",
    "bullish",
    "moon",
    "rocket",
    "pump",
    "surge",
    "rally",
    "breakout",
]

# Bearish directional verbs
BEARISH_VERBS = [
    "sell",
    "selling",
    "sold",
    "short",
    "shorting",
    "dump",
    "dumping",
    "bearish",
    "crash",
    "drop",
    "plunge",
    "fall",
    "tank",
]

# Sarcasm and meme phrases to dampen
NOISE_PATTERNS = [
    r"to the moon",
    r"🚀+",
    r"diamond hands",
    r"💎\s*🙌",
    r"stonks",
    r"tendies",
    r"apes? together",
    r"this is the way",
    r"hodl",
    r"when lambo",
    r"sir,?\s+this\s+is\s+a\s+wendy'?s",
]

# Spam/bot patterns
SPAM_PATTERNS = [
    r"http[s]?://[^\s]+",  # URLs (except Reddit)
    r"bit\.ly",
    r"goo\.gl",
    r"follow\s+me",
    r"check\s+out\s+my",
    r"subscribe",
    r"click\s+here",
]

# Entity categories
ENTITY_CATEGORIES = {
    "metals": ["gold", "silver"],
    "etfs": list(ETFS.keys()),
    "futures": list(FUTURES.keys()),
    "miners": list(MINERS.keys()),
}


def get_all_entities():
    """Get all entity names and tickers."""
    entities = set()

    # Add metal terms
    for terms in METALS.values():
        entities.update(terms)

    # Add tickers
    entities.update(ETFS.keys())
    entities.update(FUTURES.keys())
    entities.update(MINERS.keys())

    return entities


def get_entity_category(entity: str) -> str:
    """
    Get the category for an entity.

    Args:
        entity: Entity name or ticker

    Returns:
        Category name or 'unknown'
    """
    entity_upper = entity.upper()
    entity_lower = entity.lower()

    if entity_upper in ETFS:
        return "etfs"
    elif entity_upper in FUTURES:
        return "futures"
    elif entity_upper in MINERS:
        return "miners"
    else:
        # Check metals
        for metal, terms in METALS.items():
            if entity_lower in terms:
                return "metals"

    return "unknown"


def get_normalized_entity(entity: str) -> str:
    """
    Normalize entity to canonical form.

    Args:
        entity: Raw entity string

    Returns:
        Normalized entity name
    """
    entity_lower = entity.lower()
    entity_upper = entity.upper()

    # Check if it's a ticker (keep uppercase)
    if entity_upper in ETFS or entity_upper in FUTURES or entity_upper in MINERS:
        return entity_upper

    # Check metals
    if "gold" in entity_lower:
        return "gold"
    elif "silver" in entity_lower or "ag" in entity_lower:
        return "silver"

    # Return as-is
    return entity_lower
