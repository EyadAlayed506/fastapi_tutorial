"""Hisbah assistant: natural-language questions → verified engine results → bilingual answers.

Pipeline (computation is separated from language generation):

    question ─► language detection ─► intent + entities (period, category, merchant)
             ─► FinanceEngine call(s)  ── the only place numbers are produced
             ─► answer template (EN / AR) grounded in those facts
             ─► optional on-device LLM rephrasing (llama.cpp server), accepted only
                if every number it writes appears in the verified facts
"""

import json
import os
import re
from datetime import date
from urllib.parse import urlparse

import httpx

from .categorizer import canonical_merchant, label
from .engine import FinanceEngine, Period, shift_month
from .text import contains_term, has_arabic, normalize, normalize_digits

MONTHS_EN = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
             "october", "november", "december"]
MONTHS_AR = ["يناير", "فبراير", "مارس", "ابريل", "مايو", "يونيو", "يوليو", "اغسطس", "سبتمبر", "اكتوبر",
             "نوفمبر", "ديسمبر"]
MONTHS_AR_DISPLAY = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر",
                     "نوفمبر", "ديسمبر"]
WORD_NUMBERS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "شهرين": 2, "ثلاث": 3, "ثلاثه": 3,
                "اربع": 4, "اربعه": 4, "خمس": 5, "سته": 6, "ست": 6}

CATEGORY_SYNONYMS: dict[str, list[str]] = {
    "dining": ["dining", "food", "restaurant", "restaurants", "eating out", "delivery", "coffee", "cafes",
               "takeout", "مطاعم", "مطعم", "اكل", "توصيل", "قهوه", "مقاهي", "كافيهات"],
    "groceries": ["groceries", "grocery", "supermarket", "بقاله", "سوبرماركت", "مقاضي", "تموينات"],
    "transport": ["transport", "transportation", "taxi", "rides", "مواصلات", "تاكسي", "مشاوير"],
    "fuel": ["fuel", "gas", "petrol", "بنزين", "وقود"],
    "shopping": ["shopping", "clothes", "electronics", "تسوق", "مشتريات", "ملابس"],
    "bills": ["bills", "utilities", "electricity", "phone bill", "فواتير", "فاتوره", "جوال"],
    "subscriptions": ["subscriptions", "subscription", "streaming", "اشتراكات", "اشتراك"],
    "health": ["health", "pharmacy", "medical", "medicine", "صحه", "صيدليه", "علاج", "ادويه"],
    "housing": ["rent", "housing", "سكن"],
    "entertainment": ["entertainment", "movies", "cinema", "fun", "ترفيه", "سينما", "افلام"],
    "fitness": ["gym", "fitness", "نادي", "رياضه"],
    "cash": ["cash", "atm", "كاش", "نقد", "صراف"],
    "transfers": ["transfers", "transfer", "تحويلات", "حوالات"],
    "education": ["education", "courses", "تعليم", "دورات"],
}

INTENTS: list[tuple[str, list[str]]] = [
    ("anomalies", ["unusual", "strange", "suspicious", "weird", "anomaly", "anomalies", "fraud", "odd",
                   "غريب", "غريبه", "غير معتاد", "غير معتاده", "غير طبيعي", "مشبوه", "مشبوهه", "احتيال"]),
    ("recurring", ["subscription", "subscriptions", "recurring", "fixed costs", "fixed cost", "commitments",
                   "اشتراك", "اشتراكات", "متكرر", "متكرره", "ثابته", "التزامات", "التزاماتي"]),
    ("budget", ["budget", "budgets", "limit", "on track", "ميزانيه", "ميزانيتي", "تجاوزت"]),
    ("compare", ["compare", "compared", "comparison", "vs", "versus", "than last", "قارن", "مقارنه", "مقارنة",
                 "مقارنه بالشهر", "من الشهر الماضي"]),
    ("forecast", ["forecast", "projected", "projection", "end of month", "end of the month", "predict",
                  "will i", "توقع", "توقعات", "نهايه الشهر", "اخر الشهر"]),
    ("advice", ["advice", "tip", "tips", "suggest", "recommend", "how can i", "help me", "reduce", "cut down",
                "insight", "insights", "نصيحه", "نصائح", "انصحني", "كيف اقدر", "كيف اوفر", "اقلل", "توصيات"]),
    ("savings", ["save", "saved", "saving", "savings", "income", "salary", "earn", "earned", "net",
                 "ادخار", "ادخرت", "وفرت", "توفير", "دخل", "دخلي", "راتب", "راتبي", "صافي"]),
    ("breakdown", ["breakdown", "categories", "by category", "distribution", "where does my money", "where my money",
                   "توزيع", "فئات", "تصنيفات", "حسب الفئه", "وين تروح فلوسي"]),
    ("top_merchants", ["where", "which merchant", "which store", "which shop", "top", "most", "وين", "اين",
                       "فين", "اكثر محل", "اكثر مكان", "اكثر متجر", "اي محل"]),
    ("balance", ["balance", "how much do i have", "رصيد", "رصيدي", "كم عندي"]),
    ("spend_total", ["how much", "spent", "spend", "spending", "total", "كم", "صرفت", "صرف", "انفقت",
                     "مصاريف", "مصروف", "مصروفاتي", "دفعت"]),
    ("greeting", ["hi", "hello", "hey", "salam", "مرحبا", "السلام", "هلا", "اهلا"]),
    ("help", ["help", "what can you", "مساعده", "وش تقدر", "ماذا تستطيع"]),
]
SPEND_VERBS = ["spent", "spend", "spending", "صرفت", "انفقت", "دفعت", "صرف"]

SUGGESTIONS = {
    "en": ["How much did I spend on dining this month?", "Am I on track with my budgets?",
           "What are my subscriptions?", "Compare this month to last month", "Any unusual transactions?",
           "How much did I save last month?", "Give me tips to save money"],
    "ar": ["كم صرفت على المطاعم هذا الشهر؟", "كيف وضع ميزانيتي؟", "وش اشتراكاتي؟",
           "قارن هذا الشهر بالشهر الماضي", "هل فيه عمليات غريبة؟", "كم وفرت الشهر الماضي؟", "انصحني كيف اوفر"],
}


def _has(text: str, terms: list[str]) -> bool:
    return any(contains_term(text, t) for t in terms)


def ar_count(n: int, singular: str, dual: str, plural: str) -> str:
    """Arabic counted noun: عملية واحدة، عمليتين، 3 عمليات، 11 عملية."""
    if n == 1:
        return singular
    if n == 2:
        return dual
    return f"{n} {plural if 3 <= n % 100 <= 10 else singular}"


def day_label(iso: str, lang: str) -> str:
    """'2026-10-09…' → '9 Oct' / '9 أكتوبر' (avoids bidi-reordered ISO dates inside Arabic text)."""
    d = date.fromisoformat(iso[:10])
    if lang == "ar":
        return f"{d.day} {MONTHS_AR_DISPLAY[d.month - 1]}"
    return f"{d.day} {MONTHS_EN[d.month - 1][:3].title()}"


def money(x: float, lang: str) -> str:
    return f"{x:,.2f} ريال" if lang == "ar" else f"SAR {x:,.2f}"


def period_label(p: dict | Period, lang: str) -> str:
    key = p["key"] if isinstance(p, dict) else p.key
    labels = {
        "this_month": ("this month", "هذا الشهر"), "last_month": ("last month", "الشهر الماضي"),
        "this_week": ("this week", "هذا الأسبوع"), "last_week": ("last week", "الأسبوع الماضي"),
        "today": ("today", "اليوم"), "yesterday": ("yesterday", "أمس"), "this_year": ("this year", "هذه السنة"),
        "last_month_same_days": ("the same days last month", "نفس الفترة من الشهر الماضي"),
    }
    if key in labels:
        return labels[key][1 if lang == "ar" else 0]
    if m := re.fullmatch(r"last_(\d+)_months", key):
        return f"آخر {m.group(1)} أشهر" if lang == "ar" else f"the last {m.group(1)} months"
    if re.fullmatch(r"\d{4}-\d{2}", key):
        y, mo = int(key[:4]), int(key[5:])
        return f"في {MONTHS_AR_DISPLAY[mo - 1]} {y}" if lang == "ar" else f"in {MONTHS_EN[mo - 1].title()} {y}"
    return key


# --------------------------------------------------------------------- understanding

def extract_periods(text: str, today: date) -> list[str]:
    """Return period keys in the order they are mentioned."""
    found: list[tuple[int, str]] = []
    phrases = [
        ("last_month", ["last month", "previous month", "الشهر الماضي", "الشهر السابق", "الشهر اللي فات", "الشهر الفائت"]),
        ("this_month", ["this month", "current month", "هذا الشهر", "الشهر الحالي", "هالشهر", "الشهر هذا"]),
        ("last_week", ["last week", "previous week", "الاسبوع الماضي", "الاسبوع اللي فات", "الاسبوع السابق"]),
        ("this_week", ["this week", "هذا الاسبوع", "هالاسبوع", "الاسبوع هذا"]),
        ("yesterday", ["yesterday", "امس", "البارحه"]),
        ("today", ["today", "اليوم"]),
        ("this_year", ["this year", "هذه السنه", "هذا العام", "هالسنه", "السنه هذي"]),
    ]
    for key, terms in phrases:
        for term in terms:
            t = normalize(term)
            if (idx := text.find(t)) >= 0 and contains_term(text, t):
                found.append((idx, key))
                break
    if m := re.search(r"(?:last|past)\s+(\d+|two|three|four|five|six)\s+months", text) or \
            re.search(r"(?:اخر|اخير)\s+(\d+|شهرين|ثلاث|ثلاثه|اربع|اربعه|خمس|ست|سته)\s*(?:اشهر|شهور)?", text):
        g = m.group(1)
        n = int(g) if g.isdigit() else WORD_NUMBERS.get(g, 3)
        found.append((m.start(), f"last_{max(1, min(n, 12))}_months"))
    for names in (MONTHS_EN, MONTHS_AR):
        for i, name in enumerate(names):
            if contains_term(text, name):
                year = today.year if i + 1 <= today.month else today.year - 1
                found.append((text.find(normalize(name)), f"{year:04d}-{i + 1:02d}"))
    found.sort()
    keys: list[str] = []
    for _, key in found:
        if key not in keys:
            keys.append(key)
    return keys


def extract_category(text: str) -> str | None:
    for category, terms in CATEGORY_SYNONYMS.items():
        if _has(text, terms):
            return category
    return None


def classify(text: str, has_entity: bool) -> str:
    hits = [name for name, terms in INTENTS if _has(text, terms)]
    if not hits:
        return "spend_total" if has_entity else "unknown"
    if has_entity and _has(text, SPEND_VERBS) and not {"compare", "anomalies", "top_merchants", "budget"} & set(hits):
        return "spend_total"
    if "top_merchants" in hits and "breakdown" in hits:
        return "breakdown"
    return hits[0]


def understand(question: str, today: date) -> dict:
    lang = "ar" if has_arabic(question) else "en"
    text = normalize(normalize_digits(question))
    merchant = canonical_merchant(question)
    category = None if merchant else extract_category(text)
    if merchant in {"Salary"}:
        merchant = None
    periods = extract_periods(text, today)
    intent = classify(text, bool(category or merchant))
    return {"language": lang, "intent": intent, "category": category, "merchant": merchant, "periods": periods}


# --------------------------------------------------------------------- answering

class Assistant:
    def __init__(self, engine: FinanceEngine, budgets: dict[str, float], balances: list[dict] | None = None):
        self.engine = engine
        self.budgets = budgets
        self.balances = balances or []

    def ask(self, question: str) -> dict:
        parsed = understand(question, self.engine.today)
        lang = parsed["language"]
        handler = getattr(self, f"_a_{parsed['intent']}", self._a_unknown)
        facts, en, ar, calls = handler(parsed)
        answer = ar if lang == "ar" else en
        result = {
            "question": question, "answer": answer, "language": lang, "understanding": parsed,
            "engine_calls": calls, "facts": facts, "generated_by": "template",
            "suggestions": [s for s in SUGGESTIONS[lang] if s != question][:4],
        }
        if (rephrased := llm_rephrase(question, answer, facts, lang)) is not None:
            result["answer"], result["generated_by"] = rephrased, "local_llm"
            result["template_answer"] = answer
        return result

    def _period(self, parsed: dict, default: str = "this_month", index: int = 0) -> Period:
        keys = parsed["periods"]
        return self.engine.period(keys[index] if len(keys) > index else default)

    # -- intents -------------------------------------------------------
    def _a_spend_total(self, p):
        period = self._period(p)
        f = self.engine.spending(period, category=p["category"], merchant=p["merchant"])
        en_what = f" at {p['merchant']}" if p["merchant"] else f" on {label(p['category']).lower()}" if p["category"] else ""
        ar_what = f" في {p['merchant']}" if p["merchant"] else f" على {label(p['category'], 'ar')}" if p["category"] else ""
        pl_en, pl_ar = period_label(period, "en"), period_label(period, "ar")
        if f["count"] == 0:
            en = f"You haven't spent anything{en_what} {pl_en}."
            ar = f"لم تصرف شيئاً{ar_what} {pl_ar}."
        else:
            en = (f"You spent {money(f['total'], 'en')}{en_what} {pl_en} across {f['count']} transactions "
                  f"(average {money(f['average'], 'en')} each).")
            ar = (f"صرفت {money(f['total'], 'ar')}{ar_what} {pl_ar} في {ar_count(f['count'], 'عملية واحدة', 'عمليتين', 'عمليات')} "
                  f"(بمتوسط {money(f['average'], 'ar')} للعملية).")
            if f["largest"]:
                big = f["largest"][0]
                en += f" The largest was {money(big['amount'], 'en')} at {big['merchant']} on {day_label(big['date'], 'en')}."
                ar += f" أكبرها {money(big['amount'], 'ar')} في {big['merchant']} بتاريخ {day_label(big['date'], 'ar')}."
        return f, en, ar, [f"spending(period={period.key}, category={p['category']}, merchant={p['merchant']})"]

    def _a_breakdown(self, p):
        period = self._period(p)
        f = self.engine.category_breakdown(period)
        top = f["categories"][:5]
        en = f"Your spending {period_label(period, 'en')} is {money(f['total'], 'en')}. Top categories: " + "; ".join(
            f"{label(c['category'])} {money(c['total'], 'en')} ({c['share']:.0f}%)" for c in top) + "."
        ar = f"مصروفاتك {period_label(period, 'ar')} {money(f['total'], 'ar')}. أعلى الفئات: " + "؛ ".join(
            f"{label(c['category'], 'ar')} {money(c['total'], 'ar')} ({c['share']:.0f}%)" for c in top) + "."
        return f, en, ar, [f"category_breakdown(period={period.key})"]

    def _a_top_merchants(self, p):
        period = self._period(p)
        f = self.engine.top_merchants(period, n=5, category=p["category"])
        if not f["merchants"]:
            return f, "No spending found for that period.", "لا توجد مصروفات في هذه الفترة.", ["top_merchants"]
        en = f"Where your money went {period_label(period, 'en')}: " + "; ".join(
            f"{m['merchant']} {money(m['total'], 'en')} ({m['count']}×)" for m in f["merchants"]) + "."
        ar = f"أكثر الأماكن التي صرفت فيها {period_label(period, 'ar')}: " + "؛ ".join(
            f"{m['merchant']} {money(m['total'], 'ar')} ({ar_count(m['count'], 'مرة', 'مرتين', 'مرات')})" for m in f["merchants"]) + "."
        return f, en, ar, [f"top_merchants(period={period.key}, category={p['category']})"]

    def _a_compare(self, p):
        if len(p["periods"]) >= 2 and set(p["periods"][:2]) != {"this_month", "last_month"}:
            a, b = self.engine.period(p["periods"][0]), self.engine.period(p["periods"][1])
            f = self.engine.compare(a, b)
        elif p["periods"] and p["periods"][0] not in ("this_month", "last_month") and \
                not (len(p["periods"]) >= 2 and set(p["periods"][:2]) == {"this_month", "last_month"}):
            a = self.engine.period(p["periods"][0])
            prev = shift_month(a.start, -1)
            f = self.engine.compare(a, self.engine.period(prev.strftime("%Y-%m")))
        else:
            f = self.engine.month_to_date_vs_last()
        la_en, lb_en = period_label(f["a"], "en"), period_label(f["b"], "en")
        la_ar, lb_ar = period_label(f["a"], "ar"), period_label(f["b"], "ar")
        rows = f["by_category"]
        if p["category"]:
            rows = [r for r in rows if r["category"] == p["category"]] or [
                {"category": p["category"], "a": 0.0, "b": 0.0, "delta": 0.0, "pct": None}]
            r = rows[0]
            word_en = "more" if r["delta"] > 0 else "less"
            word_ar = "أكثر" if r["delta"] > 0 else "أقل"
            en = (f"{label(r['category'])}: {money(r['a'], 'en')} {la_en} vs {money(r['b'], 'en')} {lb_en} — "
                  f"{money(abs(r['delta']), 'en')} {word_en}.")
            ar = (f"{label(r['category'], 'ar')}: {money(r['a'], 'ar')} {la_ar} مقابل {money(r['b'], 'ar')} {lb_ar} — "
                  f"{word_ar} بـ {money(abs(r['delta']), 'ar')}.")
            return f, en, ar, [f"compare({f['a']['key']}, {f['b']['key']})"]
        up = f["delta"] > 0
        pct = f" ({abs(f['pct']):.0f}%)" if f["pct"] is not None else ""
        en = (f"You spent {money(f['total_a'], 'en')} {la_en} vs {money(f['total_b'], 'en')} {lb_en}: "
              f"{money(abs(f['delta']), 'en')}{pct} {'more' if up else 'less'}.")
        ar = (f"صرفت {money(f['total_a'], 'ar')} {la_ar} مقابل {money(f['total_b'], 'ar')} {lb_ar}، "
              f"أي {'أكثر' if up else 'أقل'} بـ {money(abs(f['delta']), 'ar')}{pct}.")
        movers = [r for r in rows if abs(r["delta"]) >= 50][:3]
        if movers:
            en += " Biggest changes: " + "; ".join(
                f"{label(r['category'])} {'+' if r['delta'] > 0 else '−'}{money(abs(r['delta']), 'en')}" for r in movers) + "."
            ar += " أكبر التغيرات: " + "؛ ".join(
                f"{label(r['category'], 'ar')} {'+' if r['delta'] > 0 else '−'}{money(abs(r['delta']), 'ar')}" for r in movers) + "."
        return f, en, ar, [f"compare({f['a']['key']}, {f['b']['key']})"]

    def _a_budget(self, p):
        f = self.engine.budgets(self.budgets)
        items = f["items"]
        if p["category"]:
            items = [i for i in items if i["category"] == p["category"]]
            if not items:
                return f, f"You don't have a budget for {label(p['category']).lower()} yet — set one in Settings.", \
                    f"لا توجد ميزانية لفئة {label(p['category'], 'ar')} بعد — يمكنك إضافتها من الإعدادات.", ["budgets"]
        status_en = {"over": "over budget", "at_risk": "at risk", "on_track": "on track"}
        status_ar = {"over": "تجاوزت الحد", "at_risk": "معرضة للتجاوز", "on_track": "ضمن الحد"}
        en = f"Day {f['days_elapsed']} of {f['days_in_month']}. " + "; ".join(
            f"{label(i['category'])}: {money(i['spent'], 'en')} of {money(i['limit'], 'en')} ({i['pct']:.0f}%, {status_en[i['status']]}"
            + (f", projected {money(i['projected'], 'en')})" if i["status"] == "at_risk" else ")") for i in items) + "."
        ar = f"اليوم {f['days_elapsed']} من {f['days_in_month']}. " + "؛ ".join(
            f"{label(i['category'], 'ar')}: {money(i['spent'], 'ar')} من {money(i['limit'], 'ar')} ({i['pct']:.0f}%، {status_ar[i['status']]}"
            + (f"، المتوقع {money(i['projected'], 'ar')})" if i["status"] == "at_risk" else ")") for i in items) + "."
        return {**f, "items": items}, en, ar, ["budgets(this_month)"]

    def _a_recurring(self, p):
        f = self.engine.recurring()
        subs = [i for i in f["items"] if i["category"] == "subscriptions"]
        others = [i for i in f["items"] if i["category"] != "subscriptions"]
        en = (f"I found {len(subs)} subscriptions costing {money(f['subscriptions_monthly_total'], 'en')}/month: "
              + ", ".join(f"{i['merchant']} {money(i['average_amount'], 'en')} (next {day_label(i['next_date'], 'en')})" for i in subs) + ". ")
        ar = (f"وجدت {len(subs)} اشتراكات بتكلفة {money(f['subscriptions_monthly_total'], 'ar')} شهرياً: "
              + "، ".join(f"{i['merchant']} {money(i['average_amount'], 'ar')} (القادم {day_label(i['next_date'], 'ar')})" for i in subs) + ". ")
        if others:
            en += "Other fixed monthly costs: " + ", ".join(f"{i['merchant']} {money(i['average_amount'], 'en')}" for i in others) + \
                f". All recurring commitments total {money(f['monthly_total'], 'en')}/month."
            ar += "التزامات شهرية ثابتة أخرى: " + "، ".join(f"{i['merchant']} {money(i['average_amount'], 'ar')}" for i in others) + \
                f". مجموع الالتزامات المتكررة {money(f['monthly_total'], 'ar')} شهرياً."
        return f, en, ar, ["recurring()"]

    def _a_anomalies(self, p):
        period = self._period(p)
        f = self.engine.anomalies(period)
        if not f["items"]:
            return f, f"Nothing unusual {period_label(period, 'en')} — all charges look normal for you.", \
                f"لا يوجد شيء غير معتاد {period_label(period, 'ar')} — كل العمليات طبيعية بالنسبة لك.", [f"anomalies({period.key})"]
        en = "Unusual transactions: " + "; ".join(
            f"{a['merchant']} {money(a['amount'], 'en')} on {day_label(a['date'], 'en')} — {a['times_typical']:.1f}× your typical "
            f"{label(a['category']).lower()} charge of {money(a['typical_amount'], 'en')}" for a in f["items"]) + \
            ". If you don't recognise one, contact your bank."
        ar = "عمليات غير معتادة: " + "؛ ".join(
            f"{a['merchant']} {money(a['amount'], 'ar')} بتاريخ {day_label(a['date'], 'ar')} — {a['times_typical']:.1f} أضعاف المعتاد "
            f"لفئة {label(a['category'], 'ar')} ({money(a['typical_amount'], 'ar')})" for a in f["items"]) + \
            ". إذا لم تتعرف على أي منها تواصل مع البنك."
        return f, en, ar, [f"anomalies({period.key})"]

    def _a_forecast(self, p):
        f = self.engine.forecast_month_end()
        en = (f"So far this month you've spent {money(f['spent_so_far'], 'en')} (day {f['days_elapsed']} of {f['days_in_month']}). "
              f"With {money(f['upcoming_recurring'], 'en')} of recurring bills still due and your current pace, "
              f"I project about {money(f['projected_total'], 'en')} by month end.")
        ar = (f"صرفت حتى الآن هذا الشهر {money(f['spent_so_far'], 'ar')} (اليوم {f['days_elapsed']} من {f['days_in_month']}). "
              f"مع {money(f['upcoming_recurring'], 'ar')} التزامات متكررة متبقية ووتيرة صرفك الحالية، "
              f"أتوقع أن يصل المجموع إلى حوالي {money(f['projected_total'], 'ar')} بنهاية الشهر.")
        return f, en, ar, ["forecast_month_end()"]

    def _a_savings(self, p):
        period = self._period(p, default="last_month")
        f = self.engine.summary(period)
        if not f["income"]:
            return f, f"No income recorded {period_label(period, 'en')} yet.", \
                f"لا يوجد دخل مسجل {period_label(period, 'ar')} حتى الآن.", [f"summary({period.key})"]
        verb_en = "saved" if f["net"] >= 0 else "overspent by"
        verb_ar = "ادخرت" if f["net"] >= 0 else "تجاوزت دخلك بـ"
        en = (f"{period_label(period, 'en')[0].upper() + period_label(period, 'en')[1:]} your income was {money(f['income'], 'en')} and spending "
              f"{money(f['spending'], 'en')}, so you {verb_en} {money(abs(f['net']), 'en')} "
              f"(savings rate {f['savings_rate']:.0f}%).")
        ar = (f"{period_label(period, 'ar')} كان دخلك {money(f['income'], 'ar')} ومصروفاتك {money(f['spending'], 'ar')}، "
              f"أي أنك {verb_ar} {money(abs(f['net']), 'ar')} (نسبة الادخار {f['savings_rate']:.0f}%).")
        return f, en, ar, [f"summary({period.key})"]

    def _a_balance(self, p):
        if not self.balances:
            return {}, "No bank account connected yet — connect one from Settings to see balances.", \
                "لا يوجد حساب بنكي مرتبط بعد — اربط حسابك من الإعدادات لعرض الرصيد.", []
        en = "Balances: " + "; ".join(f"{b['nickname']} {b['masked']}: {money(b['balance'], 'en')}" for b in self.balances) + "."
        ar = "الأرصدة: " + "؛ ".join(f"{b.get('nickname_ar', b['nickname'])} {b['masked']}: {money(b['balance'], 'ar')}" for b in self.balances) + "."
        return {"accounts": self.balances}, en, ar, ["accounts (from last Open Banking sync)"]

    def _a_advice(self, p):
        tips = insights(self.engine, self.budgets)
        f = {"insights": tips}
        if not tips:
            return f, "You're in good shape — no warnings right now.", "وضعك ممتاز — لا توجد تنبيهات حالياً.", ["insights()"]
        en = "Here's what I'd focus on:\n" + "\n".join(f"• {t['en']}" for t in tips[:4])
        ar = "هذه أهم النقاط التي أنصحك بها:\n" + "\n".join(f"• {t['ar']}" for t in tips[:4])
        return f, en, ar, ["insights() → budgets, trends, recurring, anomalies, summary"]

    def _a_greeting(self, p):
        return {}, "Hi! I'm Hisbah. Ask me about your spending, budgets, subscriptions or savings.", \
            "أهلاً! أنا حِسبة. اسألني عن مصروفاتك أو ميزانيتك أو اشتراكاتك أو ادخارك.", []

    def _a_help(self, p):
        return {}, ("I answer questions using your on-device data, e.g. “How much did I spend on dining last month?”, "
                    "“Compare September vs August”, “What are my subscriptions?”, “Any unusual transactions?”"), \
            ("أجيب عن أسئلتك من بياناتك المحفوظة على جهازك، مثل: «كم صرفت على المطاعم الشهر الماضي؟»، "
             "«قارن سبتمبر بأغسطس»، «وش اشتراكاتي؟»، «هل فيه عمليات غريبة؟»"), []

    def _a_unknown(self, p):
        en, ar = self._a_help(p)[1:3]
        return {}, "I'm not sure I understood. " + en, "لم أفهم سؤالك تماماً. " + ar, []


# --------------------------------------------------------------------- insights

def insights(engine: FinanceEngine, budgets: dict[str, float]) -> list[dict]:
    out: list[dict] = []
    status = engine.budgets(budgets)
    days_left = max(status["days_in_month"] - status["days_elapsed"], 1)
    for b in status["items"]:
        lbl_en, lbl_ar = label(b["category"]), label(b["category"], "ar")
        if b["status"] == "over":
            out.append({"kind": "budget", "severity": "high", "category": b["category"],
                        "en": f"You're over your {lbl_en} budget: {money(b['spent'], 'en')} of {money(b['limit'], 'en')}.",
                        "ar": f"تجاوزت ميزانية {lbl_ar}: {money(b['spent'], 'ar')} من {money(b['limit'], 'ar')}."})
        elif b["status"] == "at_risk":
            per_day = max(b["remaining"], 0) / days_left
            out.append({"kind": "budget", "severity": "medium", "category": b["category"],
                        "en": f"At this pace {lbl_en} will reach {money(b['projected'], 'en')}, above your "
                              f"{money(b['limit'], 'en')} budget. Keep it under {money(per_day, 'en')}/day to stay on track.",
                        "ar": f"بهذه الوتيرة ستصل {lbl_ar} إلى {money(b['projected'], 'ar')}، أعلى من ميزانيتك "
                              f"{money(b['limit'], 'ar')}. حاول ألا تتجاوز {money(per_day, 'ar')} يومياً."})
    for a in engine.anomalies()["items"][:2]:
        out.append({"kind": "anomaly", "severity": "high", "category": a["category"],
                    "en": f"Unusual charge: {a['merchant']} {money(a['amount'], 'en')} ({a['times_typical']:.0f}× your typical {label(a['category']).lower()} purchase).",
                    "ar": f"عملية غير معتادة: {a['merchant']} {money(a['amount'], 'ar')} ({a['times_typical']:.0f} أضعاف مشترياتك المعتادة في {label(a['category'], 'ar')})."})
    rising = [t for t in engine.trends()["items"]
              if t["direction"] == "rising" and t["category"] not in {"bills", "housing", "transfers", "cash"}]
    for t in rising[:2]:
        out.append({"kind": "trend", "severity": "medium", "category": t["category"],
                    "en": f"{label(t['category'])} spending is rising — up {t['change_pct']:.0f}% over recent months "
                          f"(+{money(t['slope_per_month'], 'en')} per month).",
                    "ar": f"مصروفات {label(t['category'], 'ar')} في ازدياد — ارتفعت {t['change_pct']:.0f}% خلال الأشهر الأخيرة "
                          f"(+{money(t['slope_per_month'], 'ar')} شهرياً)."})
    rec = engine.recurring()
    if rec["subscriptions_count"]:
        yearly = rec["subscriptions_monthly_total"] * 12
        out.append({"kind": "subscriptions", "severity": "low", "category": "subscriptions",
                    "en": f"You pay {money(rec['subscriptions_monthly_total'], 'en')}/month for {rec['subscriptions_count']} subscriptions "
                          f"({money(yearly, 'en')}/year). Cancel any you no longer use.",
                    "ar": f"تدفع {money(rec['subscriptions_monthly_total'], 'ar')} شهرياً على {rec['subscriptions_count']} اشتراكات "
                          f"({money(yearly, 'ar')} سنوياً). ألغِ ما لا تستخدمه."})
    last = engine.summary(engine.period("last_month"))
    if last["savings_rate"] is not None:
        good = last["savings_rate"] >= 20
        out.append({"kind": "savings", "severity": "low" if good else "medium", "category": None,
                    "en": f"Last month you saved {last['savings_rate']:.0f}% of your income ({money(last['net'], 'en')})."
                          + ("" if good else " A common target is 20%."),
                    "ar": f"ادخرت الشهر الماضي {last['savings_rate']:.0f}% من دخلك ({money(last['net'], 'ar')})."
                          + ("" if good else " الهدف الشائع هو 20%.")})
    order = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda i: order[i["severity"]])
    return out


# --------------------------------------------------------------------- optional local LLM

def llm_settings() -> dict:
    url = os.getenv("HISBAH_LLM_URL", "").strip()
    host = urlparse(url).hostname if url else None
    local = host in {"localhost", "127.0.0.1", "::1"}
    return {"url": url or None, "enabled": bool(url) and (local or os.getenv("HISBAH_ALLOW_REMOTE_LLM") == "1"),
            "on_device": local, "model": os.getenv("HISBAH_LLM_MODEL", "local-gguf")}


_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _numbers(text: str) -> set[str]:
    return {n.replace(",", "").rstrip("0").rstrip(".") for n in _NUM.findall(normalize_digits(text))}


def llm_rephrase(question: str, draft: str, facts: dict, lang: str) -> str | None:
    """Ask a llama.cpp (OpenAI-compatible) server to phrase the verified draft more naturally.

    Returns None (keep the template answer) when no local model is configured, on any error,
    or if the model introduces a number that is not in the verified facts/draft.
    """
    cfg = llm_settings()
    if not cfg["enabled"]:
        return None
    system = ("You are Hisbah, a personal finance assistant. Rewrite the DRAFT answer to the user's question "
              f"in a friendly, concise way in {'Arabic' if lang == 'ar' else 'English'}. Use ONLY the numbers "
              "that appear in DRAFT or FACTS. Never calculate or invent numbers.")
    user = f"QUESTION: {question}\nFACTS: {json.dumps(facts, ensure_ascii=False)[:3000]}\nDRAFT: {draft}"
    try:
        resp = httpx.post(cfg["url"].rstrip("/") + "/v1/chat/completions", timeout=30, json={
            "model": cfg["model"], "temperature": 0.2, "max_tokens": 300,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        text = resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
    allowed = _numbers(draft) | _numbers(json.dumps(facts))
    if not text or not _numbers(text) <= allowed:
        return None
    return text
