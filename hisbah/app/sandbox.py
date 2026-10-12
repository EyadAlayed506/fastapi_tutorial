"""Mock SAMA Open Banking sandbox.

Simulates the consent-based flow offered by licensed providers' developer
sandboxes (e.g. Lean / Tarabut): create consent -> user authorises at the bank
-> app receives an access token -> read accounts & transactions.

Banks here are fictional; transaction descriptions mimic the raw, mixed
Arabic/English text Saudi banks put on feeds, so the parser has real work to do.
"""

import calendar
import random
import secrets
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

PERMISSIONS = ["ReadAccountsBasic", "ReadBalances", "ReadTransactionsDetail"]

BANKS = {
    "nakheel": {"id": "nakheel", "name": "Nakheel Bank (Sandbox)", "name_ar": "بنك النخيل (تجريبي)", "color": "#0f766e"},
    "sahara": {"id": "sahara", "name": "Sahara Bank (Sandbox)", "name_ar": "بنك الصحراء (تجريبي)", "color": "#9a3412"},
}

# (english, arabic) merchant names
GROCERY = [("PANDA", "بنده"), ("TAMIMI MARKETS", "أسواق التميمي"), ("DANUBE", "الدانوب"), ("OTHAIM MARKETS", "أسواق العثيمين"), ("LULU HYPERMARKET", "لولو")]
DINING = [("HUNGERSTATION", "هنقرستيشن"), ("JAHEZ", "جاهز"), ("ALBAIK", "البيك"), ("STARBUCKS", "ستاربكس"), ("BARN'S", "بارنز"), ("KUDU", "كودو"), ("HALF MILLION", "هاف مليون")]
FUEL = [("ALDREES", "الدريس"), ("SASCO", "ساسكو"), ("PETROMIN", "بترومين")]
RIDES = [("UBER", "أوبر"), ("CAREEM", "كريم")]
SHOPS = [("JARIR BOOKSTORE", "مكتبة جرير"), ("EXTRA STORES", "إكسترا"), ("NOON", "نون"), ("AMAZON.SA", "أمازون"), ("CENTREPOINT", "سنتربوينت")]
HEALTH = [("NAHDI PHARMACY", "صيدلية النهدي"), ("AL DAWAA PHARMACY", "صيدلية الدواء")]
FUN = [("VOX CINEMAS", "ڤوكس سينما"), ("MUVI CINEMAS", "موفي سينما")]
CITIES = [("RIYADH", "الرياض"), ("JEDDAH", "جدة"), ("DAMMAM", "الدمام")]


@dataclass
class Consent:
    id: str
    bank_id: str
    permissions: list[str]
    expires_at: datetime
    status: str = "AwaitingAuthorisation"
    access_token: str | None = None


@dataclass
class SandboxBank:
    today: date
    consents: dict[str, Consent] = field(default_factory=dict)
    call_log: list[dict] = field(default_factory=list)

    # ---------------------------------------------------------------- consent
    def create_consent(self, bank_id: str, permissions: list[str], days: int = 90) -> Consent:
        if bank_id not in BANKS:
            raise HTTPException(404, "Unknown bank")
        consent = Consent(id="cns_" + secrets.token_hex(6), bank_id=bank_id, permissions=permissions,
                          expires_at=datetime.now() + timedelta(days=days))
        self.consents[consent.id] = consent
        self._log("POST /consents", bank_id)
        return consent

    def authorise(self, consent_id: str, approve: bool) -> Consent:
        consent = self.consents.get(consent_id)
        if consent is None:
            raise HTTPException(404, "Consent not found")
        if consent.status != "AwaitingAuthorisation":
            raise HTTPException(409, f"Consent is {consent.status}")
        consent.status = "Authorised" if approve else "Rejected"
        if approve:
            consent.access_token = "sbx_" + secrets.token_urlsafe(24)
        self._log("POST /consents/{id}/authorise", consent.bank_id)
        return consent

    def revoke(self, consent_id: str) -> None:
        if consent := self.consents.get(consent_id):
            consent.status, consent.access_token = "Revoked", None
            self._log("DELETE /consents/{id}", consent.bank_id)

    def _consent_for(self, token: str | None, permission: str) -> Consent:
        for consent in self.consents.values():
            if token and consent.access_token == token and consent.status == "Authorised":
                if consent.expires_at < datetime.now():
                    raise HTTPException(401, "Consent expired")
                if permission not in consent.permissions:
                    raise HTTPException(403, f"Consent lacks {permission}")
                return consent
        raise HTTPException(401, "Invalid or revoked access token")

    # ---------------------------------------------------------------- data
    def accounts(self, token: str | None) -> list[dict]:
        consent = self._consent_for(token, "ReadAccountsBasic")
        self._log("GET /accounts", consent.bank_id)
        accounts = _accounts(consent.bank_id)
        if "ReadBalances" in consent.permissions:
            for acc in accounts:
                txns = generate_transactions(consent.bank_id, acc["account_id"], self.today)
                if acc["type"] == "CreditCard":  # previous statements were settled; show this cycle's outstanding
                    txns = [t for t in txns if t["booking_datetime"][:7] == self.today.strftime("%Y-%m")]
                acc["balance"] = round(acc["opening_balance"] + sum(
                    t["amount"] if t["credit_debit_indicator"] == "Credit" else -t["amount"] for t in txns), 2)
        for acc in accounts:
            acc.pop("opening_balance")
        return accounts

    def transactions(self, token: str | None, account_id: str) -> list[dict]:
        consent = self._consent_for(token, "ReadTransactionsDetail")
        if account_id not in {a["account_id"] for a in _accounts(consent.bank_id)}:
            raise HTTPException(404, "Account not found")
        self._log("GET /accounts/{id}/transactions", consent.bank_id)
        return generate_transactions(consent.bank_id, account_id, self.today)

    def _log(self, endpoint: str, bank_id: str) -> None:
        self.call_log.append({"at": datetime.now().isoformat(timespec="seconds"), "endpoint": endpoint,
                              "bank": bank_id, "direction": "device → bank (sandbox)",
                              "carries_user_financial_data": False})


def _accounts(bank_id: str) -> list[dict]:
    suffix = "4523" if bank_id == "nakheel" else "7710"
    return [
        {"account_id": f"{bank_id}-cur-{suffix}", "type": "CurrentAccount", "currency": "SAR",
         "nickname": "Current Account", "nickname_ar": "الحساب الجاري", "masked": f"•••• {suffix}",
         "opening_balance": 6200.0},
        {"account_id": f"{bank_id}-cc-8812", "type": "CreditCard", "currency": "SAR",
         "nickname": "Visa Signature", "nickname_ar": "بطاقة فيزا", "masked": "•••• 8812",
         "opening_balance": 0.0},
    ]


def _month_starts(today: date, months: int) -> list[date]:
    starts, y, m = [], today.year, today.month
    for _ in range(months):
        starts.append(date(y, m, 1))
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return list(reversed(starts))


def generate_transactions(bank_id: str, account_id: str, today: date, months: int = 6) -> list[dict]:
    """Deterministic synthetic feed for the last `months` months up to `today`."""
    rng = random.Random(f"{bank_id}:{account_id}")
    is_card = "-cc-" in account_id
    out: list[dict] = []

    def add(day: date, amount: float, indicator: str, desc: str, hour: int | None = None):
        if day > today:
            return
        ts = datetime(day.year, day.month, day.day, hour if hour is not None else rng.randint(8, 22), rng.randint(0, 59))
        out.append({"transaction_id": f"{account_id}-{len(out):04d}", "booking_datetime": ts.isoformat(),
                    "amount": round(amount, 2), "currency": "SAR", "credit_debit_indicator": indicator,
                    "description": desc, "status": "Booked"})

    def pos(name: tuple[str, str], arabic: bool | None = None) -> str:
        city = rng.choice(CITIES)
        if arabic if arabic is not None else rng.random() < 0.35:
            return rng.choice([f"شراء عبر نقاط البيع {name[1]} {city[1]}", f"شراء عبر أبل باي {name[1]}"])
        return rng.choice([f"POS PURCHASE MADA {name[0]} {city[0]}", f"APPLE PAY {name[0]} {city[0]} SA"])

    starts = _month_starts(today, months)
    for idx, start in enumerate(starts):
        days = calendar.monthrange(start.year, start.month)[1]

        def on(d: int) -> date:
            return start.replace(day=min(d, days))

        def anyday() -> date:
            return on(rng.randint(1, days))

        if is_card:
            add(on(5), 56.0, "Debit", "ONLINE PURCHASE NETFLIX.COM")
            add(on(12), 31.99, "Debit", "شراء إنترنت شاهد SHAHID")
            add(on(18), 21.99, "Debit", "ONLINE PURCHASE SPOTIFY")
            for _ in range(rng.randint(2, 4)):
                shop = rng.choice(SHOPS)
                add(anyday(), rng.uniform(60, 700), "Debit",
                    f"ONLINE PURCHASE {shop[0]}" if rng.random() < 0.6 else f"شراء إنترنت {shop[1]}")
            for _ in range(rng.randint(0, 2)):
                add(anyday(), rng.uniform(45, 160), "Debit", pos(rng.choice(FUN)))
            continue

        # Current account
        add(on(27), 14500.0, "Credit", rng.choice(["SALARY CREDIT - PAYROLL", "إيداع راتب شهري"]), hour=6)
        add(on(1), 3500.0, "Debit", "EJAR RENT PAYMENT - سداد إيجار", hour=9)
        add(on(2), 299.0, "Debit", "POS PURCHASE MADA FITNESS TIME RIYADH")
        add(on(10), rng.uniform(210, 250), "Debit", "SADAD BILL PAYMENT - STC")
        summer = start.month in (6, 7, 8, 9)
        add(on(15), rng.uniform(420, 610) if summer else rng.uniform(180, 260), "Debit",
            "سداد فاتورة - الشركة السعودية للكهرباء")
        add(on(rng.randint(8, 20)), 500.0, "Debit", f"ATM CASH WITHDRAWAL - {rng.choice(CITIES)[0]}")
        for _ in range(rng.randint(6, 8)):
            add(anyday(), rng.uniform(80, 420), "Debit", pos(rng.choice(GROCERY)))
        # Dining grows over time — gives the trend detector something to find.
        for _ in range(9 + int(idx * 1.5) + rng.randint(0, 2)):
            add(anyday(), rng.uniform(18, 140), "Debit", pos(rng.choice(DINING)))
        for _ in range(rng.randint(4, 5)):
            add(anyday(), rng.uniform(60, 130), "Debit", pos(rng.choice(FUEL)))
        for _ in range(rng.randint(3, 6)):
            ride = rng.choice(RIDES)
            add(anyday(), rng.uniform(15, 70), "Debit", f"{ride[0]} *TRIP" if rng.random() < 0.7 else f"شراء {ride[1]}")
        for _ in range(rng.randint(0, 2)):
            add(anyday(), rng.uniform(25, 220), "Debit", pos(rng.choice(HEALTH)))
        if rng.random() < 0.6:
            add(anyday(), rng.choice([200, 300, 500]), "Debit",
                rng.choice(["LOCAL TRANSFER - MOHAMMED A.", "حوالة صادرة إلى عبدالله"]))
        if rng.random() < 0.4:
            add(anyday(), rng.uniform(40, 250), "Credit", "REFUND - NOON")

    # One unusual purchase this month for anomaly detection.
    if not is_card:
        add(today.replace(day=max(1, min(today.day, 3))), 4299.0, "Debit", "POS PURCHASE MADA EXTRA STORES RIYADH")

    out.sort(key=lambda t: t["booking_datetime"])
    return out


# --------------------------------------------------------------------- HTTP

class ConsentRequest(BaseModel):
    bank_id: str
    permissions: list[str] = PERMISSIONS
    expires_in_days: int = 90


class AuthoriseRequest(BaseModel):
    approve: bool = True


def build_router(bank: SandboxBank) -> APIRouter:
    router = APIRouter(prefix="/sandbox/v1", tags=["Mock Open Banking sandbox"])

    def bearer(authorization: str | None) -> str | None:
        return authorization.removeprefix("Bearer ").strip() if authorization else None

    @router.get("/banks")
    def list_banks():
        return list(BANKS.values())

    @router.post("/consents", status_code=201)
    def create_consent(body: ConsentRequest):
        c = bank.create_consent(body.bank_id, body.permissions, body.expires_in_days)
        return {"consent_id": c.id, "status": c.status, "permissions": c.permissions,
                "expires_at": c.expires_at.isoformat(), "authorisation_url": f"/sandbox/v1/consents/{c.id}/authorise"}

    @router.post("/consents/{consent_id}/authorise")
    def authorise(consent_id: str, body: AuthoriseRequest):
        c = bank.authorise(consent_id, body.approve)
        return {"consent_id": c.id, "status": c.status, "access_token": c.access_token}

    @router.delete("/consents/{consent_id}", status_code=204)
    def revoke(consent_id: str):
        bank.revoke(consent_id)

    @router.get("/accounts")
    def accounts(authorization: str | None = Header(default=None)):
        return {"data": bank.accounts(bearer(authorization))}

    @router.get("/accounts/{account_id}/transactions")
    def transactions(account_id: str, authorization: str | None = Header(default=None)):
        return {"data": bank.transactions(bearer(authorization), account_id)}

    return router
