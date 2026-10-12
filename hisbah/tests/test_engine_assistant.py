from datetime import date

import pytest

from app.assistant import Assistant, understand
from app.engine import FinanceEngine

TODAY = date(2026, 10, 12)


def txn(day, amount, merchant, category, direction="debit"):
    return {"id": f"{day}-{merchant}", "date": f"{day}T12:00:00", "amount": amount, "direction": direction,
            "merchant": merchant, "category": category, "description": merchant}


@pytest.fixture
def engine():
    rows = []
    for m in ("2026-06", "2026-07", "2026-08", "2026-09"):
        rows += [txn(f"{m}-05", 56.0, "Netflix", "subscriptions"), txn(f"{m}-27", 10000, "Salary", "income", "credit"),
                 txn(f"{m}-10", 300.0, "Panda", "groceries"), txn(f"{m}-20", 200.0, "Panda", "groceries"),
                 txn(f"{m}-03", 40.0, "Kudu", "dining"), txn(f"{m}-15", 60.0, "Kudu", "dining")]
    rows += [txn("2026-10-05", 56.0, "Netflix", "subscriptions"), txn("2026-10-06", 250.0, "Panda", "groceries"),
             txn("2026-10-07", 900.0, "Kudu", "dining")]
    return FinanceEngine(rows, TODAY)


def test_summary_and_savings(engine):
    s = engine.summary(engine.period("last_month"))
    assert s["income"] == 10000 and s["spending"] == 656.0 and s["savings_rate"] == 93.44


def test_recurring_detects_netflix_only(engine):
    items = engine.recurring()["items"]
    assert [i["merchant"] for i in items] == ["Netflix"]
    assert items[0]["next_date"] == "2026-11-04"


def test_anomaly_flags_unusual_dining(engine):
    flagged = engine.anomalies()["items"]
    assert [a["merchant"] for a in flagged] == ["Kudu"] and flagged[0]["amount"] == 900.0


def test_budget_status(engine):
    items = {b["category"]: b for b in engine.budgets({"dining": 500, "groceries": 1000})["items"]}
    assert items["dining"]["status"] == "over"
    assert items["groceries"]["status"] == "on_track"


@pytest.mark.parametrize("q,intent,category,periods", [
    ("How much did I spend on food last month?", "spend_total", "dining", ["last_month"]),
    ("كم صرفت على المطاعم هذا الشهر؟", "spend_total", "dining", ["this_month"]),
    ("قارن سبتمبر بأغسطس", "compare", None, ["2026-09", "2026-08"]),
    ("كيف وضع ميزانيتي؟", "budget", None, []),
    ("وش اشتراكاتي؟", "recurring", "subscriptions", []),
    ("هل فيه عمليات غريبة؟", "anomalies", None, []),
    ("Give me tips to save money", "advice", None, []),
    ("كم صرفت آخر ٣ شهور؟", "spend_total", None, ["last_3_months"]),
])
def test_understanding(q, intent, category, periods):
    u = understand(q, TODAY)
    assert (u["intent"], u["category"], u["periods"]) == (intent, category, periods)


def test_answers_are_grounded_in_engine_facts(engine):
    r = Assistant(engine, {}).ask("How much did I spend on dining last month?")
    assert r["facts"]["total"] == 100.0
    assert "SAR 100.00" in r["answer"]
    r_ar = Assistant(engine, {}).ask("كم صرفت على المطاعم الشهر الماضي؟")
    assert r_ar["language"] == "ar" and "100.00 ريال" in r_ar["answer"]
