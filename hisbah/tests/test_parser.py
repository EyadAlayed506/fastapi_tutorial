import pytest

from app.categorizer import canonical_merchant, categorize
from app.parser import clean_description, parse_message


def test_arabic_sms_with_arabic_indic_digits():
    p = parse_message("شراء عبر نقاط البيع\nبطاقة: ٤٥٢٣ مدى\nمبلغ: ٤٥٫٥٠ ر.س\nلدى: هنقرستيشن\n"
                      "في: ٢٠٢٦-١٠-٠٥ ٢١:١٤\nالرصيد: ٣٬٢١٠٫٤٠ ر.س")
    assert p.language == "ar"
    assert p.amount == 45.5
    assert p.balance == 3210.4  # balance is never mistaken for the amount
    assert p.direction == "debit"
    assert p.merchant == "هنقرستيشن"
    assert p.card_last4 == "4523"
    assert p.occurred_at == "2026-10-05T21:14"
    assert p.confidence == 1.0


def test_english_inline_sms():
    p = parse_message("PoS Purchase of SAR 45.50 at STARBUCKS on 05/10/2026 using card ending 4523. "
                      "Available balance SAR 3,210.40")
    assert (p.amount, p.direction, p.merchant, p.card_last4) == (45.5, "debit", "STARBUCKS", "4523")
    assert p.occurred_at.startswith("2026-10-05")
    assert p.balance == 3210.4


def test_short_date_and_amount_with_currency_prefix():
    p = parse_message("شراء إنترنت\nبطاقة:4523;مدى-أبل باي\nمن:3456\nمبلغ:SAR 120.00\nلدى:Noon\nفي:26-10-12 18:30")
    assert (p.amount, p.merchant, p.occurred_at) == (120.0, "Noon", "2026-10-12T18:30")


@pytest.mark.parametrize("text,direction", [
    ("إيداع راتب\nمبلغ: 14,500.00 ريال", "credit"),
    ("Your account was credited with SAR 300.00 transfer from Ahmed Ali on 2026-10-02", "credit"),
    ("Your credit card ending 1234 was used for a purchase of SAR 50 at IKEA", "debit"),
    ("سداد فاتورة\nالمفوتر: STC\nمبلغ: 230 ريال", "debit"),
])
def test_direction(text, direction):
    assert parse_message(text).direction == direction


def test_message_without_amount_has_low_confidence():
    p = parse_message("Your OTP is 4821")
    assert p.amount is None and p.confidence < 0.5


@pytest.mark.parametrize("desc,merchant", [
    ("POS PURCHASE MADA 4523 JARIR BOOKSTORE RIYADH SA", "Jarir Bookstore"),
    ("SADAD BILL PAYMENT - STC", "STC"),
    ("شراء عبر نقاط البيع هنقرستيشن الرياض", "هنقرستيشن"),
    ("ONLINE PURCHASE NETFLIX.COM", "Netflix"),
])
def test_clean_description(desc, merchant):
    assert clean_description(desc) == merchant


def test_bilingual_merchant_resolution():
    assert canonical_merchant("هنقرستيشن") == canonical_merchant("HUNGERSTATION") == "HungerStation"
    assert canonical_merchant("قانون") is None  # 'نون' must not match inside another word


@pytest.mark.parametrize("merchant,desc,expected", [
    ("Panda", "", "groceries"), ("التميمي", "", "groceries"), ("Uber", "UBER *TRIP", "transport"),
    ("Netflix", "", "subscriptions"), ("الشركة السعودية للكهرباء", "سداد فاتورة", "bills"),
    ("Mystery Shop", "", "other"),
])
def test_categorize(merchant, desc, expected):
    assert categorize(merchant, desc)[0] == expected


def test_user_override_wins():
    assert categorize("Starbucks", overrides={"starbucks": "entertainment"}) == ("entertainment", "user_override")
