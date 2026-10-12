"""Deterministic finance engine.

All numbers Hisbah shows or says come from here — computed with Pandas over the
structured, decrypted transaction records. The assistant layer only phrases
these verified results; it never does arithmetic of its own.
"""

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

SPENDING_EXCLUDED = {"income", "refunds"}


@dataclass(frozen=True)
class Period:
    start: date
    end: date  # inclusive
    key: str  # e.g. "this_month", "2026-09", "last_3_months"

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


def month_period(year: int, month: int, today: date) -> Period:
    last = date(year, month, calendar.monthrange(year, month)[1])
    return Period(date(year, month, 1), min(last, today), f"{year:04d}-{month:02d}")


def shift_month(d: date, n: int) -> date:
    m = d.month - 1 + n
    return date(d.year + m // 12, m % 12 + 1, 1)


def r2(x) -> float:
    return float(round(float(x), 2))


class FinanceEngine:
    def __init__(self, transactions: list[dict], today: date):
        self.today = today
        df = pd.DataFrame(transactions)
        if df.empty:
            df = pd.DataFrame(columns=["id", "date", "amount", "direction", "merchant", "category", "description"])
        df["date"] = pd.to_datetime(df["date"], format="ISO8601")
        df["amount"] = df["amount"].astype(float)
        df["day"] = df["date"].dt.date
        df["month"] = df["date"].dt.strftime("%Y-%m")
        self.df = df.sort_values("date").reset_index(drop=True)
        self.spend = self.df[(self.df["direction"] == "debit") & (~self.df["category"].isin(SPENDING_EXCLUDED))]

    # ------------------------------------------------------------ periods
    def period(self, key: str = "this_month") -> Period:
        t = self.today
        if key == "this_month":
            return Period(t.replace(day=1), t, key)
        if key == "last_month":
            p = shift_month(t, -1)
            return Period(p, date(p.year, p.month, calendar.monthrange(p.year, p.month)[1]), key)
        week_start = t - timedelta(days=(t.weekday() + 1) % 7)  # Saudi week starts on Sunday
        if key == "this_week":
            return Period(week_start, t, key)
        if key == "last_week":
            return Period(week_start - timedelta(days=7), week_start - timedelta(days=1), key)
        if key == "today":
            return Period(t, t, key)
        if key == "yesterday":
            return Period(t - timedelta(days=1), t - timedelta(days=1), key)
        if key == "this_year":
            return Period(date(t.year, 1, 1), t, key)
        if key.startswith("last_") and key.endswith("_months"):
            n = int(key.split("_")[1])
            return Period(shift_month(t, -n), t.replace(day=1) - timedelta(days=1), key)
        if len(key) == 7 and key[4] == "-":
            return month_period(int(key[:4]), int(key[5:]), t)
        raise ValueError(f"Unknown period {key}")

    def _slice(self, frame: pd.DataFrame, period: Period) -> pd.DataFrame:
        return frame[(frame["day"] >= period.start) & (frame["day"] <= period.end)]

    # ------------------------------------------------------------ queries
    def spending(self, period: Period, category: str | None = None, merchant: str | None = None) -> dict:
        frame = self._slice(self.spend, period)
        if category:
            frame = frame[frame["category"] == category]
        if merchant:
            frame = frame[frame["merchant"].str.lower() == merchant.lower()]
        top = frame.nlargest(3, "amount")
        return {
            "period": _p(period), "category": category, "merchant": merchant,
            "total": r2(frame["amount"].sum()), "count": int(len(frame)),
            "average": r2(frame["amount"].mean()) if len(frame) else 0.0,
            "daily_average": r2(frame["amount"].sum() / period.days),
            "largest": [_txn(row) for _, row in top.iterrows()],
        }

    def category_breakdown(self, period: Period) -> dict:
        frame = self._slice(self.spend, period)
        total = frame["amount"].sum()
        grouped = frame.groupby("category")["amount"].agg(["sum", "count"]).sort_values("sum", ascending=False)
        return {
            "period": _p(period), "total": r2(total),
            "categories": [
                {"category": cat, "total": r2(row["sum"]), "count": int(row["count"]),
                 "share": r2(100 * row["sum"] / total) if total else 0.0}
                for cat, row in grouped.iterrows()
            ],
        }

    def top_merchants(self, period: Period, n: int = 5, category: str | None = None) -> dict:
        frame = self._slice(self.spend, period)
        if category:
            frame = frame[frame["category"] == category]
        grouped = frame.groupby("merchant")["amount"].agg(["sum", "count"]).sort_values("sum", ascending=False).head(n)
        return {"period": _p(period), "category": category, "merchants": [
            {"merchant": m, "total": r2(row["sum"]), "count": int(row["count"])} for m, row in grouped.iterrows()]}

    def summary(self, period: Period) -> dict:
        frame = self._slice(self.df, period)
        income = frame[(frame["direction"] == "credit") & (frame["category"] == "income")]["amount"].sum()
        spending = self._slice(self.spend, period)["amount"].sum()
        return {
            "period": _p(period), "income": r2(income), "spending": r2(spending), "net": r2(income - spending),
            "savings_rate": r2(100 * (income - spending) / income) if income else None,
            "transactions": int(len(frame)),
        }

    def compare(self, a: Period, b: Period) -> dict:
        """Compare period a (usually current) against period b (usually previous)."""
        fa, fb = self._slice(self.spend, a), self._slice(self.spend, b)
        ca, cb = fa.groupby("category")["amount"].sum(), fb.groupby("category")["amount"].sum()
        rows = []
        for cat in sorted(set(ca.index) | set(cb.index)):
            va, vb = float(ca.get(cat, 0.0)), float(cb.get(cat, 0.0))
            rows.append({"category": cat, "a": r2(va), "b": r2(vb), "delta": r2(va - vb),
                         "pct": r2(100 * (va - vb) / vb) if vb else None})
        rows.sort(key=lambda r: abs(r["delta"]), reverse=True)
        ta, tb = fa["amount"].sum(), fb["amount"].sum()
        return {"a": _p(a), "b": _p(b), "total_a": r2(ta), "total_b": r2(tb), "delta": r2(ta - tb),
                "pct": r2(100 * (ta - tb) / tb) if tb else None, "by_category": rows}

    def month_to_date_vs_last(self) -> dict:
        """Fair comparison: this month so far vs the same number of days last month."""
        cur = self.period("this_month")
        prev_start = shift_month(self.today, -1)
        prev_days = calendar.monthrange(prev_start.year, prev_start.month)[1]
        prev = Period(prev_start, prev_start.replace(day=min(self.today.day, prev_days)), "last_month_same_days")
        return self.compare(cur, prev)

    def budgets(self, limits: dict[str, float]) -> dict:
        period = self.period("this_month")
        days_in_month = calendar.monthrange(self.today.year, self.today.month)[1]
        frame = self._slice(self.spend, period)
        spent_by_cat = frame.groupby("category")["amount"].sum()
        fixed = {r["category"] for r in self.recurring()["items"]}
        items = []
        for cat, limit in limits.items():
            spent = float(spent_by_cat.get(cat, 0.0))
            projected = spent if cat in fixed else spent / period.days * days_in_month
            pct = 100 * spent / limit if limit else 0.0
            status = "over" if spent > limit else "at_risk" if projected > limit else "on_track"
            items.append({"category": cat, "limit": r2(limit), "spent": r2(spent), "remaining": r2(limit - spent),
                          "pct": r2(pct), "projected": r2(projected), "status": status})
        items.sort(key=lambda i: i["pct"], reverse=True)
        return {"period": _p(period), "days_elapsed": period.days, "days_in_month": days_in_month, "items": items}

    def recurring(self) -> dict:
        """Detect subscriptions / fixed costs: ≥3 charges, regular gaps, stable amounts."""
        items = []
        for merchant, g in self.spend[~self.spend["category"].isin({"cash", "transfers"})].groupby("merchant"):
            if len(g) < 3:
                continue
            gaps = np.diff(sorted(g["date"].values)).astype("timedelta64[D]").astype(int)
            med_gap = float(np.median(gaps))
            amounts = g["amount"].values
            cv = float(np.std(amounts) / np.mean(amounts)) if np.mean(amounts) else 1.0
            if 26 <= med_gap <= 35 and float(np.std(gaps)) <= 5 and cv <= 0.15:
                cadence, per_month = "monthly", float(np.mean(amounts))
            elif 6 <= med_gap <= 8 and cv <= 0.15:
                cadence, per_month = "weekly", float(np.mean(amounts)) * 52 / 12
            else:
                continue
            last = g["date"].max().date()
            nxt = last + timedelta(days=int(round(med_gap)))
            items.append({"merchant": merchant, "category": g["category"].mode().iloc[0], "cadence": cadence,
                          "average_amount": r2(np.mean(amounts)), "monthly_cost": r2(per_month),
                          "occurrences": int(len(g)), "last_date": last.isoformat(), "next_date": nxt.isoformat()})
        items.sort(key=lambda i: i["monthly_cost"], reverse=True)
        subs = [i for i in items if i["category"] == "subscriptions"]
        return {"items": items, "monthly_total": r2(sum(i["monthly_cost"] for i in items)),
                "subscriptions_monthly_total": r2(sum(i["monthly_cost"] for i in subs)),
                "subscriptions_count": len(subs)}

    def anomalies(self, period: Period | None = None) -> dict:
        """Flag charges far above the user's normal spend in that category (robust z-score)."""
        period = period or self.period("this_month")
        found = []
        current = self._slice(self.spend, period)
        history = self.spend[self.spend["day"] < period.start]
        for _, row in current.iterrows():
            hist = history[history["category"] == row["category"]]["amount"]
            if len(hist) < 5:
                continue
            median = float(hist.median())
            mad = float((hist - median).abs().median()) or 1.0
            score = 0.6745 * (row["amount"] - median) / mad
            if score > 6 and row["amount"] > 3 * median and row["amount"] > 200:
                found.append({**_txn(row), "typical_amount": r2(median), "times_typical": r2(row["amount"] / median),
                              "score": r2(score)})
        found.sort(key=lambda f: f["score"], reverse=True)
        return {"period": _p(period), "items": found}

    def trends(self, months: int = 6) -> dict:
        """Linear trend of monthly spend per category over the last full months."""
        end = self.today.replace(day=1) - timedelta(days=1)
        start = shift_month(self.today, -months)
        frame = self.spend[(self.spend["day"] >= start) & (self.spend["day"] <= end)]
        first_month = self.spend["month"].min() if len(self.spend) else end.strftime("%Y-%m")
        month_keys = [k for k in (shift_month(self.today, -i).strftime("%Y-%m") for i in range(months, 0, -1))
                      if k >= first_month]
        if len(month_keys) < 3:
            return {"months": month_keys, "items": []}
        pivot = frame.pivot_table(index="month", columns="category", values="amount", aggfunc="sum").reindex(month_keys).fillna(0)
        out = []
        x = np.arange(len(month_keys))
        for cat in pivot.columns:
            y = pivot[cat].values
            if y.mean() < 100 or (y > 0).sum() < 3:
                continue
            slope = float(np.polyfit(x, y, 1)[0])
            first, last = float(y[: 2].mean()), float(y[-2:].mean())
            change = 100 * (last - first) / first if first else None
            direction = "rising" if slope > 0 and change and change > 15 else "falling" if slope < 0 and change and change < -15 else "stable"
            out.append({"category": cat, "slope_per_month": r2(slope), "change_pct": r2(change) if change is not None else None,
                        "direction": direction, "monthly": {m: r2(v) for m, v in zip(month_keys, y)}})
        out.sort(key=lambda t: t["slope_per_month"], reverse=True)
        return {"months": month_keys, "items": out}

    def forecast_month_end(self) -> dict:
        period = self.period("this_month")
        days_in_month = calendar.monthrange(self.today.year, self.today.month)[1]
        spent = float(self._slice(self.spend, period)["amount"].sum())
        recurring = self.recurring()["items"]
        seen = set(self._slice(self.spend, period)["merchant"])
        upcoming = sum(r["average_amount"] for r in recurring if r["cadence"] == "monthly" and r["merchant"] not in seen
                       and date.fromisoformat(r["next_date"]) <= date(self.today.year, self.today.month, days_in_month))
        fixed_spent = float(self._slice(self.spend, period)[self._slice(self.spend, period)["merchant"].isin(
            {r["merchant"] for r in recurring})]["amount"].sum())
        variable = spent - fixed_spent
        anomalies = sum(a["amount"] for a in self.anomalies(period)["items"])
        variable_pace = (variable - anomalies) / period.days * days_in_month + anomalies
        projected = fixed_spent + upcoming + variable_pace
        return {"spent_so_far": r2(spent), "upcoming_recurring": r2(upcoming), "projected_total": r2(projected),
                "days_elapsed": period.days, "days_in_month": days_in_month}

    def daily_cumulative(self) -> dict:
        cur = self.period("this_month")
        prev_start = shift_month(self.today, -1)
        prev = self.period(prev_start.strftime("%Y-%m"))

        def series(p: Period) -> list[float]:
            frame = self._slice(self.spend, p)
            daily = frame.groupby("day")["amount"].sum()
            values, running = [], 0.0
            for i in range(p.days):
                running += float(daily.get(p.start + timedelta(days=i), 0.0))
                values.append(r2(running))
            return values

        return {"this_month": series(cur), "last_month": series(prev)}


def _p(period: Period) -> dict:
    return {"key": period.key, "start": period.start.isoformat(), "end": period.end.isoformat()}


def _txn(row) -> dict:
    return {"id": row.get("id"), "date": row["date"].isoformat(timespec="minutes"), "merchant": row["merchant"],
            "amount": r2(row["amount"]), "category": row["category"]}
