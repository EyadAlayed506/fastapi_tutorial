"""Turn raw inputs (Open Banking feed, bank SMS, CSV statements) into structured records."""

import io
import re
from datetime import date, datetime

import pandas as pd

from .categorizer import canonical_merchant, categorize
from .parser import ParsedTransaction, clean_description, detect_channel, detect_direction
from .text import normalize


def _record(**fields) -> dict:
    fields["merchant"] = canonical_merchant(fields["merchant"]) or fields["merchant"]
    category, reason = categorize(fields["merchant"], fields.get("description", ""), fields["direction"],
                                  fields.get("channel"), fields.pop("overrides", None))
    return {**fields, "category": category, "category_reason": reason}


def from_bank_feed(txn: dict, account: dict, bank_id: str, overrides: dict) -> dict:
    desc = txn["description"]
    return _record(
        date=txn["booking_datetime"], amount=float(txn["amount"]),
        direction="credit" if txn["credit_debit_indicator"] == "Credit" else "debit",
        merchant=clean_description(desc), description=desc, channel=detect_channel(normalize(desc)),
        source="open_banking", account=f"{account['nickname']} {account['masked']}", bank=bank_id,
        external_ref=f"{bank_id}:{txn['transaction_id']}", confidence=1.0, overrides=overrides,
    )


def from_parsed_message(parsed: ParsedTransaction, overrides: dict, today: date) -> dict:
    if parsed.amount is None:
        raise ValueError("Could not find an amount in this message")
    return _record(
        date=parsed.occurred_at or datetime.combine(today, datetime.now().time()).isoformat(timespec="minutes"),
        amount=parsed.amount, direction=parsed.direction or "debit",
        merchant=parsed.merchant or "Unknown", description=parsed.raw.strip(), channel=parsed.channel,
        source="sms", account=f"Card •••• {parsed.card_last4}" if parsed.card_last4 else "SMS",
        confidence=parsed.confidence, parser_rules=parsed.rules, overrides=overrides,
    )


_COLS = {
    "date": ["date", "transaction date", "posting date", "التاريخ", "تاريخ العملية", "تاريخ"],
    "description": ["description", "details", "narrative", "الوصف", "البيان", "التفاصيل"],
    "amount": ["amount", "المبلغ", "مبلغ"],
    "debit": ["debit", "withdrawal", "مدين", "سحب", "خصم"],
    "credit": ["credit", "deposit", "دائن", "ايداع", "إيداع"],
}


def _find(columns: list[str], role: str) -> str | None:
    normalized = {normalize(str(c)): c for c in columns}
    for candidate in _COLS[role]:
        if (key := normalize(candidate)) in normalized:
            return normalized[key]
    return None


def _num(value) -> float:
    if pd.isna(value) or str(value).strip() == "":
        return 0.0
    return float(re.sub(r"[^\d.\-]", "", normalize(str(value))) or 0)


def from_statement_csv(content: bytes, overrides: dict) -> list[dict]:
    frame = pd.read_csv(io.BytesIO(content), dtype=str, encoding="utf-8-sig")
    cols = list(frame.columns)
    date_col, desc_col = _find(cols, "date"), _find(cols, "description")
    amount_col, debit_col, credit_col = _find(cols, "amount"), _find(cols, "debit"), _find(cols, "credit")
    if not date_col or not desc_col or not (amount_col or debit_col or credit_col):
        raise ValueError(f"Unrecognised statement columns: {cols}")
    records = []
    for _, row in frame.iterrows():
        desc = str(row[desc_col]).strip()
        if amount_col:
            signed = _num(row[amount_col])
            if signed == 0:
                continue
            direction = "credit" if signed > 0 else "debit"
            amount = abs(signed)
        else:
            debit, credit = _num(row.get(debit_col)), _num(row.get(credit_col))
            direction, amount = ("credit", credit) if credit else ("debit", debit)
            if not amount:
                continue
        text_direction, _ = detect_direction(normalize(desc))
        if amount_col and signed > 0 and text_direction == "debit":
            direction = "debit"  # some banks export debits as positive numbers
        when = pd.to_datetime(normalize(str(row[date_col])), dayfirst=True, errors="coerce")
        if pd.isna(when):
            continue
        records.append(_record(
            date=when.isoformat(timespec="minutes"), amount=round(amount, 2), direction=direction,
            merchant=clean_description(desc), description=desc, channel=detect_channel(normalize(desc)),
            source="statement", account="Uploaded statement", confidence=1.0, overrides=overrides,
        ))
    return records
