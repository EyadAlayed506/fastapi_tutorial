"""Bilingual (Arabic / English) text normalisation helpers."""

import re

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫٬", "01234567890123456789.,")
_DIACRITICS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_ARABIC = re.compile("[؀-ۿ]")
_AR_LETTER = "ء-غف-يٮ-ۓ"  # letters only — not ؟ ، ؛ or digits


def normalize_digits(text: str) -> str:
    """Convert Arabic-Indic / Persian digits and separators to ASCII."""
    return text.translate(_DIGITS)


def normalize_arabic(text: str) -> str:
    """Remove diacritics/tatweel and unify common letter variants."""
    text = _DIACRITICS.sub("", text)
    text = re.sub("[إأآٱ]", "ا", text)
    return text.replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")


def normalize(text: str) -> str:
    """Full normalisation used for matching: digits, Arabic letters, lowercase, spaces."""
    text = normalize_arabic(normalize_digits(text)).lower()
    return re.sub(r"\s+", " ", text).strip()


def has_arabic(text: str) -> bool:
    return bool(_ARABIC.search(text))


def contains_term(normalized_text: str, term: str) -> bool:
    """Match a keyword on word boundaries.

    Arabic terms may carry a ال/لل/و/ب/ل prefix and a possessive suffix (ميزانيتي، اشتراكاتي).
    """
    term = normalize(term)
    if has_arabic(term):
        pattern = f"(?<![{_AR_LETTER}])(?:ال|لل|و|ب|ل)?{re.escape(term)}(?:ي|ك|ه|ها|نا|هم|كم)?(?![{_AR_LETTER}])"
        return re.search(pattern, normalized_text) is not None
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", normalized_text) is not None
