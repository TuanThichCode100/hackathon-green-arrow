"""Canonical language codes used by the resident registry and dispatches."""

LANGUAGE_LABELS = {
    "vi": "Tiếng Kinh",
    "hmn": "Tiếng Mông",
    "tai": "Tiếng Thái",
    "khmu": "Tiếng Khơ Mú",
    "dao": "Tiếng Dao",
    "tay": "Tiếng Tày",
    "muong": "Tiếng Mường",
}

PRIMARY_LANGUAGE_BY_ETHNIC = {
    "Kinh": "vi",
    "Mông": "hmn",
    "Thái": "tai",
    "Khơ Mú": "khmu",
    "Dao": "dao",
    "Tày": "tay",
    "Mường": "muong",
}


def primary_language_for(ethnic: str, requested: str | None = None) -> str:
    """Use a supplied known code; otherwise apply the ethnic-language default."""
    if requested in LANGUAGE_LABELS:
        return requested
    if requested:
        normalized = requested.strip().casefold()
        for code, label in LANGUAGE_LABELS.items():
            if normalized == label.casefold():
                return code
    return PRIMARY_LANGUAGE_BY_ETHNIC.get(ethnic, "vi")
