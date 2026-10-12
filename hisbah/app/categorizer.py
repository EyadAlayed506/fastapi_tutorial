"""Bilingual rule-based spending categorisation.

Rules match English and Arabic merchant names / keywords after normalisation.
User corrections are stored as per-merchant overrides and always win, so the
categoriser "learns" from the user without any data leaving the device.
"""

from .text import contains_term, normalize

# category -> (English label, Arabic label, emoji)
CATEGORIES: dict[str, tuple[str, str, str]] = {
    "groceries": ("Groceries", "بقالة", "🛒"),
    "dining": ("Dining & Coffee", "مطاعم ومقاهي", "🍔"),
    "transport": ("Transport", "مواصلات", "🚕"),
    "fuel": ("Fuel", "وقود", "⛽"),
    "shopping": ("Shopping", "تسوق", "🛍️"),
    "bills": ("Bills & Utilities", "فواتير وخدمات", "💡"),
    "subscriptions": ("Subscriptions", "اشتراكات", "🔁"),
    "health": ("Health", "صحة", "💊"),
    "housing": ("Housing & Rent", "سكن وإيجار", "🏠"),
    "entertainment": ("Entertainment", "ترفيه", "🎬"),
    "education": ("Education", "تعليم", "🎓"),
    "fitness": ("Fitness", "رياضة", "🏋️"),
    "cash": ("Cash Withdrawal", "سحب نقدي", "🏧"),
    "transfers": ("Transfers", "تحويلات", "🔄"),
    "income": ("Income", "دخل", "💰"),
    "refunds": ("Refunds", "مبالغ مستردة", "↩️"),
    "other": ("Other", "أخرى", "📦"),
}

RULES: list[tuple[str, list[str]]] = [
    ("subscriptions", ["netflix", "نتفلكس", "نتفليكس", "shahid", "شاهد", "spotify", "سبوتيفاي", "anghami",
                       "انغامي", "apple.com", "icloud", "osn", "youtube premium", "chatgpt", "google one",
                       "disney"]),
    ("fitness", ["fitness time", "وقت اللياقه", "gym", "نادي", "leejam", "body masters"]),
    ("groceries", ["panda", "بنده", "tamimi", "التميمي", "danube", "الدانوب", "othaim", "العثيمين", "lulu",
                   "لولو", "carrefour", "كارفور", "nesto", "farm superstores", "المزرعه", "bin dawood",
                   "بن داود", "supermarket", "سوبرماركت", "تموينات", "hypermarket"]),
    ("dining", ["hungerstation", "هنقرستيشن", "jahez", "جاهز", "albaik", "البيك", "starbucks", "ستاربكس",
                "barn's", "barns", "بارنز", "mcdonald's", "mcdonalds", "ماكدونالدز", "kudu", "كودو",
                "herfy", "هرفي", "dunkin", "دانكن", "half million", "هاف مليون", "keeta", "كيتا", "kfc",
                "cafe", "coffee", "مقهي", "كوفي", "restaurant", "مطعم", "shawarma", "شاورما", "the chefz",
                "ذا شفز", "tim hortons", "تيم هورتنز"]),
    ("transport", ["uber", "اوبر", "careem", "كريم", "bolt", "jeeny", "جيني", "saptco", "سابتكو", "metro",
                   "مترو", "parking", "مواقف"]),
    ("fuel", ["aldrees", "الدريس", "sasco", "ساسكو", "petromin", "بترومين", "naft", "نفط", "fuel", "petrol",
              "gas station", "محطه وقود", "بنزين"]),
    ("shopping", ["jarir", "جرير", "extra", "اكسترا", "noon", "نون", "amazon", "امازون", "centrepoint",
                  "سنتربوينت", "namshi", "نمشي", "ikea", "ايكيا", "shein", "شي ان", "h&m", "zara", "زارا",
                  "max fashion", "ماكس", "saco", "ساكو"]),
    ("bills", ["stc", "اس تي سي", "mobily", "موبايلي", "zain", "زين", "saudi electricity", "كهرباء",
               "national water", "مياه", "sadad", "فاتوره", "internet bill"]),
    ("health", ["nahdi", "النهدي", "aldawaa", "al dawaa", "الدواء", "pharmacy", "صيدليه", "hospital",
                "مستشفي", "clinic", "عياده", "dr sulaiman", "سليمان الحبيب", "medical", "طبي"]),
    ("housing", ["rent", "ايجار", "ejar", "ايجار شهري", "اسكان", "real estate", "عقار"]),
    ("entertainment", ["vox", "ڤوكس", "فوكس", "cinema", "سينما", "muvi", "موفي", "boulevard", "بوليفارد",
                       "playstation", "steam", "webook", "ويبوك"]),
    ("education", ["udemy", "coursera", "university", "جامعه", "مدرسه", "school", "tuition", "رسوم دراسيه"]),
    ("cash", ["atm", "صراف", "سحب نقدي", "cash withdrawal"]),
    ("transfers", ["transfer", "تحويل", "حواله", "stc pay", "urpay"]),
]

_NORMALIZED_RULES = [(cat, [normalize(t) for t in terms]) for cat, terms in RULES]


def merchant_key(merchant: str) -> str:
    return normalize(merchant)


def categorize(
    merchant: str | None,
    description: str = "",
    direction: str | None = "debit",
    channel: str | None = None,
    overrides: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Return (category, reason)."""
    if overrides and merchant and (cat := overrides.get(merchant_key(merchant))):
        return cat, "user_override"
    if direction == "credit":
        if channel == "refund":
            return "refunds", "credit:refund"
        if channel == "transfer":
            return "transfers", "credit:transfer"
        return "income", "credit"
    haystack = normalize(f"{merchant or ''} {description}")
    for category, terms in _NORMALIZED_RULES:
        for term in terms:
            if contains_term(haystack, term):
                return category, f"keyword:{term}"
    if channel == "atm":
        return "cash", "channel:atm"
    if channel == "transfer":
        return "transfers", "channel:transfer"
    if channel == "bill":
        return "bills", "channel:bill"
    return "other", "fallback"


def label(category: str, lang: str = "en") -> str:
    en, ar, _ = CATEGORIES.get(category, CATEGORIES["other"])
    return ar if lang == "ar" else en


# Bilingual merchant resolution: "هنقرستيشن" and "HUNGERSTATION" are the same merchant.
MERCHANT_ALIASES: list[tuple[str, list[str]]] = [
    ("HungerStation", ["hungerstation", "هنقرستيشن"]), ("Jahez", ["jahez", "جاهز"]), ("AlBaik", ["albaik", "البيك"]),
    ("Starbucks", ["starbucks", "ستاربكس"]), ("Barn's", ["barn's", "barns", "بارنز"]), ("Kudu", ["kudu", "كودو"]),
    ("Half Million", ["half million", "هاف مليون"]), ("Panda", ["panda", "بنده"]),
    ("Tamimi Markets", ["tamimi", "التميمي"]), ("Danube", ["danube", "الدانوب"]),
    ("Othaim Markets", ["othaim", "العثيمين"]), ("Lulu Hypermarket", ["lulu", "لولو"]),
    ("Aldrees", ["aldrees", "الدريس"]), ("SASCO", ["sasco", "ساسكو"]), ("Petromin", ["petromin", "بترومين"]),
    ("Uber", ["uber", "اوبر"]), ("Careem", ["careem", "كريم"]), ("Jarir Bookstore", ["jarir", "جرير"]),
    ("eXtra", ["extra", "اكسترا"]), ("Noon", ["noon", "نون"]), ("Amazon", ["amazon", "امازون"]),
    ("Centrepoint", ["centrepoint", "سنتربوينت"]), ("Nahdi Pharmacy", ["nahdi", "النهدي"]),
    ("Al-Dawaa Pharmacy", ["dawaa", "الدواء"]), ("VOX Cinemas", ["vox", "ڤوكس", "فوكس"]),
    ("Muvi Cinemas", ["muvi", "موفي"]), ("Netflix", ["netflix", "نتفلكس", "نتفليكس"]), ("Shahid", ["shahid", "شاهد"]),
    ("Spotify", ["spotify", "سبوتيفاي"]), ("STC", ["stc", "اس تي سي"]),
    ("Saudi Electricity Co.", ["saudi electricity", "كهرباء"]), ("Fitness Time", ["fitness time"]),
    ("Ejar Rent", ["ejar", "ايجار"]), ("ATM Withdrawal", ["atm", "صراف"]), ("Salary", ["salary", "payroll", "راتب"]),
]
_NORMALIZED_ALIASES = [(name, [normalize(a) for a in aliases]) for name, aliases in MERCHANT_ALIASES]


def canonical_merchant(text: str) -> str | None:
    """Return the canonical merchant name mentioned in `text`, if any."""
    haystack = normalize(text)
    for name, aliases in _NORMALIZED_ALIASES:
        if any(contains_term(haystack, a) for a in aliases):
            return name
    return None
