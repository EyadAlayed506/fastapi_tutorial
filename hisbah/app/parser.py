"""Bilingual rule-based transaction parser.

Turns raw bank SMS / notification text and statement descriptions (Arabic or
English) into structured fields: amount, direction, merchant, date, channel,
card, balance. Every rule that fires is recorded so the UI can show *why* a
field was extracted.
"""

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime

from .text import has_arabic, normalize, normalize_digits

CURRENCY = r"(?:SAR|SR|S\.R\.?|ريال(?:\s*سعودي)?|ر\.\s?س\.?|رس)"
NUMBER = r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"

_BALANCE = re.compile(
    rf"(?:available\s+balance|avail\.?\s*bal(?:ance)?|balance|bal\.?|الرصيد\s+المتاح|الرصيد|رصيد)"
    rf"\s*(?:is)?\s*[:：]?\s*(?:{CURRENCY}\s*)?{NUMBER}(?:\s*{CURRENCY})?",
    re.IGNORECASE,
)
_AMOUNT_LABELED = re.compile(
    rf"(?:amount|amt|مبلغ|بمبلغ|المبلغ)\s*[:：]?\s*(?:{CURRENCY}\s*)?{NUMBER}", re.IGNORECASE
)
_AMOUNT_CUR_FIRST = re.compile(rf"{CURRENCY}\s*{NUMBER}", re.IGNORECASE)
_AMOUNT_CUR_LAST = re.compile(rf"{NUMBER}\s*{CURRENCY}", re.IGNORECASE)

_CARD = [
    re.compile(r"(?:card|بطاقة|بطاقه)\D{0,20}?(\d{4})\b", re.IGNORECASE),
    re.compile(r"ending\s*(?:with|in)?\s*\**(\d{4})\b", re.IGNORECASE),
    re.compile(r"\*{2,}\s*(\d{4})\b"),
]

_STOP = r"(?=\s*(?:\n|$|في\s*[:：]|بتاريخ|on\s*[:：]|\bon\s+\d|\busing\b|\bvia\b|\bwith\b|date\s*[:：]|[.;]\s|\.$|،))"
_MERCHANT = [
    ("merchant_label", re.compile(rf"(?:لدى|لدي|عند|merchant|at)\s*[:：]\s*(.+?){_STOP}", re.IGNORECASE)),
    ("merchant_inline", re.compile(rf"\bat\s+([A-Za-z0-9&'.\- ]{{2,40}}?){_STOP}", re.IGNORECASE)),
    ("merchant_inline_ar", re.compile(rf"(?:لدى|لدي)\s+(.+?){_STOP}")),
    ("biller_label", re.compile(rf"(?:biller|المفوتر|الجهة|الجهه|مفوتر)\s*[:：]?\s*(.+?){_STOP}", re.IGNORECASE)),
    ("payee_label", re.compile(rf"(?:to|الى|إلى|للمستفيد|المستفيد)\s*[:：]\s*(.+?){_STOP}", re.IGNORECASE)),
    ("payer_label", re.compile(rf"(?:from|من)\s*[:：]\s*([^\d\n].+?){_STOP}", re.IGNORECASE)),
    ("payer_inline", re.compile(rf"\bfrom\s+([A-Za-z][A-Za-z .'\-]{{1,40}}?){_STOP}", re.IGNORECASE)),
    ("payee_inline", re.compile(rf"\bto\s+([A-Za-z][A-Za-z .'\-]{{1,40}}?){_STOP}", re.IGNORECASE)),
]

_DATES = [
    ("date_ymd", re.compile(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?:[ T]+(\d{1,2}):(\d{2}))?"), "ymd"),
    ("date_dmy", re.compile(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})(?:\s+(\d{1,2}):(\d{2}))?"), "dmy"),
    ("date_short", re.compile(r"\b(\d{2})[-/](\d{2})[-/](\d{2})\s+(\d{1,2}):(\d{2})"), "yymd"),
]

# (keyword, direction, strength) — earliest strong match wins.
_DIRECTION_KEYWORDS = [
    ("راتب", "credit"), ("ايداع", "credit"), ("استرداد", "credit"), ("مرتجع", "credit"),
    ("حواله وارده", "credit"), ("تحويل وارد", "credit"), ("salary", "credit"),
    ("deposit", "credit"), ("credited", "credit"), ("refund", "credit"), ("received", "credit"),
    ("incoming", "credit"), ("transfer from", "credit"), ("cashback", "credit"),
    ("شراء", "debit"), ("سحب", "debit"), ("خصم", "debit"), ("سداد", "debit"), ("دفع", "debit"),
    ("مدفوعات", "debit"), ("حواله صادره", "debit"), ("تحويل صادر", "debit"),
    ("purchase", "debit"), ("withdrawal", "debit"), ("debited", "debit"), ("debit", "debit"),
    ("paid", "debit"), ("payment", "debit"), ("spent", "debit"), ("transfer to", "debit"),
    ("outgoing", "debit"), ("pos", "debit"),
]

_CHANNELS = [
    ("salary", ["راتب", "salary", "payroll"]),
    ("refund", ["استرداد", "مرتجع", "refund"]),
    ("atm", ["صراف", "سحب نقدي", "atm", "cash withdrawal"]),
    ("bill", ["سداد", "فاتوره", "sadad", "bill"]),
    ("transfer", ["حواله", "تحويل", "transfer"]),
    ("apple_pay", ["apple pay", "ابل باي", "mada pay"]),
    ("online", ["انترنت", "اونلاين", "online", "internet", "e-commerce", "ecom"]),
    ("pos", ["نقاط البيع", "pos", "mada", "مدى", "purchase", "شراء"]),
]

# Prefixes/suffixes stripped from bank-feed descriptions to recover a clean merchant.
_DESC_NOISE = [
    r"pos\s+purchase", r"online\s+purchase", r"e-?commerce\s+purchase", r"apple\s+pay", r"mada\s+pay",
    r"purchase", r"mada", r"visa", r"mastercard", r"sadad\s+bill\s+payment", r"bill\s+payment",
    r"payment", r"شراء\s+عبر\s+نقاط\s+البيع", r"شراء\s+انترنت", r"شراء\s+إنترنت", r"شراء",
    r"سداد\s+فاتورة", r"سداد\s+فاتوره", r"سداد", r"دفع", r"عبر\s+أبل\s+باي", r"ابل\s+باي",
    r"حوال[ةه]\s+صادر[ةه]\s+(?:الى|إلى)", r"local\s+transfer", r"transfer\s+to", r"card\s*\d{4}", r"\*+\d{4}", r"\b\d{4,}\b",
]
_CITIES = [
    "riyadh", "jeddah", "dammam", "khobar", "mecca", "makkah", "madinah", "medina", "abha", "ksa", "sa",
    "الرياض", "جدة", "جده", "الدمام", "الخبر", "مكة", "مكه", "المدينة", "المدينه", "السعودية",
]


@dataclass
class ParsedTransaction:
    raw: str
    language: str
    amount: float | None = None
    currency: str = "SAR"
    direction: str | None = None
    merchant: str | None = None
    occurred_at: str | None = None
    channel: str | None = None
    card_last4: str | None = None
    balance: float | None = None
    confidence: float = 0.0
    rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _to_float(number: str) -> float:
    return float(number.replace(",", ""))


def _clean_merchant(value: str) -> str | None:
    value = re.sub(r"\s+", " ", value).strip(" :：-–,.;*\"'")
    value = re.sub(rf"\s*(?:{CURRENCY})\s*{NUMBER}.*$", "", value, flags=re.IGNORECASE)
    if not value or re.fullmatch(r"[\d\s*]+", value):
        return None
    return value[:60]


def _parse_date(text: str, rules: list[str]) -> str | None:
    for name, pattern, kind in _DATES:
        m = pattern.search(text)
        if not m:
            continue
        a, b, c, hh, mm = m.groups()
        try:
            if kind == "ymd":
                dt = datetime(int(a), int(b), int(c))
            elif kind == "dmy":
                dt = datetime(int(c), int(b), int(a))
            else:
                dt = datetime(2000 + int(a), int(b), int(c))
            if hh is not None:
                dt = dt.replace(hour=int(hh), minute=int(mm))
        except ValueError:
            continue
        rules.append(name)
        return dt.isoformat(timespec="minutes")
    return None


def detect_channel(normalized: str) -> str | None:
    for channel, terms in _CHANNELS:
        if any(normalize(t) in normalized for t in terms):
            return channel
    return None


def detect_direction(normalized: str) -> tuple[str | None, str | None]:
    best: tuple[int, str, str] | None = None
    for keyword, direction in _DIRECTION_KEYWORDS:
        kw = normalize(keyword)
        if has_arabic(kw):
            idx = normalized.find(kw)
        else:
            m = re.search(rf"(?<![a-z]){re.escape(kw)}(?![a-z])", normalized)
            idx = m.start() if m else -1
        if idx >= 0 and (best is None or idx < best[0]):
            best = (idx, direction, keyword)
    if best:
        return best[1], best[2]
    return None, None


def parse_message(raw: str) -> ParsedTransaction:
    """Parse a bank SMS / push notification in Arabic or English."""
    text = normalize_digits(raw)
    result = ParsedTransaction(raw=raw, language="ar" if has_arabic(raw) else "en")
    rules = result.rules

    # Balance first, then blank it out so it is never mistaken for the amount.
    if m := _BALANCE.search(text):
        result.balance = _to_float(m.group(1))
        rules.append("balance")
        text_wo_balance = text[: m.start()] + " " * (m.end() - m.start()) + text[m.end():]
    else:
        text_wo_balance = text

    for name, pattern in (
        ("amount_labeled", _AMOUNT_LABELED),
        ("amount_currency_prefix", _AMOUNT_CUR_FIRST),
        ("amount_currency_suffix", _AMOUNT_CUR_LAST),
    ):
        if m := pattern.search(text_wo_balance):
            result.amount = _to_float(m.group(1))
            rules.append(name)
            break

    normalized = normalize(text)
    result.direction, keyword = detect_direction(normalized)
    if keyword:
        rules.append(f"direction:{keyword}")

    result.channel = detect_channel(normalized)
    if result.channel:
        rules.append(f"channel:{result.channel}")

    for pattern in _CARD:
        if m := pattern.search(text_wo_balance):
            result.card_last4 = m.group(1)
            rules.append("card")
            break

    for name, pattern in _MERCHANT:
        if name.startswith("payer") and result.direction != "credit":
            continue
        if name == "payee_inline" and result.channel != "transfer":
            continue
        if m := pattern.search(text_wo_balance):
            if merchant := _clean_merchant(m.group(1)):
                result.merchant = merchant
                rules.append(name)
                break
    if result.merchant is None and result.channel == "salary":
        result.merchant = "راتب" if result.language == "ar" else "Salary"
        rules.append("merchant:salary")

    result.occurred_at = _parse_date(text_wo_balance, rules)

    weights = {"amount": 0.4, "direction": 0.2, "merchant": 0.25, "occurred_at": 0.15}
    result.confidence = round(sum(w for k, w in weights.items() if getattr(result, k) is not None), 2)
    return result


def clean_description(description: str) -> str:
    """Recover a readable merchant name from a raw statement / bank-feed description."""
    parts = re.split(r"\s+-\s+", normalize_digits(description))
    for part in reversed(parts):
        if merchant := _strip_noise(part):
            return merchant
    return description.strip()


def _strip_noise(text: str) -> str | None:
    for noise in _DESC_NOISE:
        text = re.sub(noise, " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\.(?:com|sa|net)\b", "", text, flags=re.IGNORECASE)
    tokens = [t for t in re.split(r"\s+", text) if t]
    cities = {normalize(c) for c in _CITIES}
    while tokens and normalize(tokens[-1]) in cities:
        tokens.pop()
    merchant = " ".join(tokens).strip(" -:،,.")
    if not merchant or normalize(merchant) in cities:
        return None
    if not has_arabic(merchant) and merchant.isupper() and len(merchant) > 3:
        merchant = merchant.title().replace("'S", "'s")
    return merchant
