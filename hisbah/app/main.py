"""Hisbah demo server.

Run:  uv run fastapi dev app/main.py     (then open http://127.0.0.1:8000)

One process hosts three logical parts of the architecture:
  * /sandbox/v1/*  – mock SAMA Open Banking provider (stands in for Lean / Tarabut sandboxes)
  * /api/*         – the Hisbah core that, in the Flutter app, runs on the phone:
                     encrypted local store, parser, categoriser, finance engine, assistant
  * /              – a mobile-style web client used for the demo
"""

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import ingest
from .assistant import Assistant, insights, llm_settings
from .categorizer import CATEGORIES, categorize, merchant_key
from .engine import FinanceEngine
from .parser import parse_message
from .sandbox import BANKS, PERMISSIONS, SandboxBank, build_router
from .vault import IDLE_TIMEOUT_SECONDS, Vault, VaultError

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_BUDGETS = {"dining": 1200.0, "groceries": 1800.0, "shopping": 1000.0, "transport": 300.0,
                   "fuel": 700.0, "entertainment": 250.0, "health": 300.0}


class PinBody(BaseModel):
    pin: str = Field(min_length=4, max_length=8)


class ConsentBody(BaseModel):
    bank_id: str


class AuthoriseBody(BaseModel):
    consent_id: str
    approve: bool = True


class TextBody(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class QuestionBody(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class RecategorizeBody(BaseModel):
    category: str
    apply_to_merchant: bool = True


@dataclass
class Ctx:
    token: str
    dek: bytes


def create_app(data_dir: Path | None = None, today: date | None = None) -> FastAPI:
    data_dir = data_dir or Path(os.getenv("HISBAH_DATA_DIR", BASE_DIR.parent / "data"))
    fixed_today = today or (date.fromisoformat(os.environ["HISBAH_TODAY"]) if os.getenv("HISBAH_TODAY") else None)

    def get_today() -> date:
        return fixed_today or date.today()

    vault = Vault(data_dir)
    bank = SandboxBank(today=get_today())

    app = FastAPI(title="Hisbah — Privacy-First AI Personal Finance Assistant (Demo)", version="0.1.0")
    app.include_router(build_router(bank))
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    @app.exception_handler(VaultError)
    async def vault_error(_: Request, exc: VaultError):
        return JSONResponse({"detail": str(exc)}, status_code=exc.status)

    def unlocked(authorization: Annotated[str | None, Header()] = None) -> Ctx:
        token = (authorization or "").removeprefix("Bearer ").strip()
        return Ctx(token, vault.dek(token))

    Auth = Annotated[Ctx, Depends(unlocked)]

    def overrides(ctx: Ctx) -> dict:
        return vault.get_setting(ctx.dek, "category_overrides", {})

    def budgets(ctx: Ctx) -> dict:
        return vault.get_setting(ctx.dek, "budgets", DEFAULT_BUDGETS)

    def engine(ctx: Ctx) -> FinanceEngine:
        bank.today = get_today()
        return FinanceEngine(vault.list_transactions(ctx.dek), get_today())

    # ------------------------------------------------------------------ pages
    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(BASE_DIR / "static" / "index.html")

    # ------------------------------------------------------------------ auth
    @app.get("/api/auth/status", tags=["auth"])
    def auth_status():
        return {"initialized": vault.is_initialized(), "idle_timeout_seconds": IDLE_TIMEOUT_SECONDS}

    @app.post("/api/auth/setup", tags=["auth"])
    def setup(body: PinBody):
        return {"token": vault.setup(body.pin)}

    @app.post("/api/auth/unlock", tags=["auth"])
    def unlock(body: PinBody):
        return {"token": vault.unlock(body.pin)}

    @app.post("/api/auth/lock", tags=["auth"])
    def lock(ctx: Auth):
        vault.lock(ctx.token)
        return {"locked": True}

    @app.post("/api/auth/change-pin", tags=["auth"])
    def change_pin(body: PinBody, ctx: Auth):
        vault.change_pin(ctx.token, body.pin)
        return {"changed": True}

    # ------------------------------------------------------------------ open banking
    @app.get("/api/banks", tags=["open banking"])
    def banks(ctx: Auth):
        links = vault.get_setting(ctx.dek, "bank_links", {})
        return [{**b, "connected": b["id"] in links, "permissions": PERMISSIONS} for b in BANKS.values()]

    @app.post("/api/bank/consent", tags=["open banking"])
    def create_consent(body: ConsentBody, ctx: Auth):
        consent = bank.create_consent(body.bank_id, PERMISSIONS)
        return {"consent_id": consent.id, "bank": BANKS[body.bank_id], "permissions": consent.permissions,
                "expires_at": consent.expires_at.isoformat(), "status": consent.status}

    @app.post("/api/bank/authorise", tags=["open banking"])
    def authorise(body: AuthoriseBody, ctx: Auth):
        consent = bank.authorise(body.consent_id, body.approve)
        if consent.status == "Authorised":
            links = vault.get_setting(ctx.dek, "bank_links", {})
            links[consent.bank_id] = {"consent_id": consent.id, "access_token": consent.access_token,
                                      "expires_at": consent.expires_at.isoformat()}
            vault.set_setting(ctx.dek, "bank_links", links)
        return {"status": consent.status}

    @app.post("/api/bank/sync", tags=["open banking"])
    def sync(ctx: Auth):
        links = vault.get_setting(ctx.dek, "bank_links", {})
        if not links:
            raise HTTPException(400, "No bank connected")
        bank.today = get_today()
        ov = overrides(ctx)
        records, accounts = [], []
        for bank_id, link in links.items():
            for account in bank.accounts(link["access_token"]):
                accounts.append({**account, "bank": bank_id})
                for txn in bank.transactions(link["access_token"], account["account_id"]):
                    records.append(ingest.from_bank_feed(txn, account, bank_id, ov))
        inserted = vault.add_transactions(ctx.dek, records)
        vault.set_setting(ctx.dek, "accounts", accounts)
        if vault.get_setting(ctx.dek, "budgets") is None:
            vault.set_setting(ctx.dek, "budgets", DEFAULT_BUDGETS)
        categorized = sum(1 for r in records if r["category"] != "other")
        return {"fetched": len(records), "new": len(inserted), "accounts": len(accounts),
                "categorized_pct": round(100 * categorized / len(records), 1) if records else 0.0}

    @app.delete("/api/bank/{bank_id}", tags=["open banking"])
    def disconnect(bank_id: str, ctx: Auth):
        links = vault.get_setting(ctx.dek, "bank_links", {})
        if link := links.pop(bank_id, None):
            bank.revoke(link["consent_id"])
        vault.set_setting(ctx.dek, "bank_links", links)
        vault.set_setting(ctx.dek, "accounts", [a for a in vault.get_setting(ctx.dek, "accounts", []) if a["bank"] != bank_id])
        return {"revoked": link is not None}

    # ------------------------------------------------------------------ ingestion
    @app.post("/api/parse", tags=["ingestion"])
    def parse_preview(body: TextBody, ctx: Auth):
        parsed = parse_message(body.text)
        category, reason = categorize(parsed.merchant, body.text, parsed.direction, parsed.channel, overrides(ctx))
        return {**parsed.to_dict(), "category": category, "category_reason": reason}

    @app.post("/api/ingest/sms", tags=["ingestion"])
    def ingest_sms(body: TextBody, ctx: Auth):
        try:
            record = ingest.from_parsed_message(parse_message(body.text), overrides(ctx), get_today())
        except ValueError as e:
            raise HTTPException(422, str(e))
        inserted = vault.add_transactions(ctx.dek, [record])
        return {"saved": bool(inserted), "duplicate": not inserted, "transaction": inserted[0] if inserted else record}

    @app.post("/api/ingest/statement", tags=["ingestion"])
    async def ingest_statement(ctx: Auth, file: UploadFile = File(...)):
        try:
            records = ingest.from_statement_csv(await file.read(), overrides(ctx))
        except (ValueError, UnicodeDecodeError) as e:
            raise HTTPException(422, f"Could not read statement: {e}")
        inserted = vault.add_transactions(ctx.dek, records)
        return {"rows": len(records), "new": len(inserted)}

    # ------------------------------------------------------------------ data
    @app.get("/api/categories", tags=["data"])
    def categories():
        return {k: {"en": v[0], "ar": v[1], "icon": v[2]} for k, v in CATEGORIES.items()}

    @app.get("/api/transactions", tags=["data"])
    def transactions(ctx: Auth, q: str = "", category: str | None = None, limit: int = 300):
        items = sorted(vault.list_transactions(ctx.dek), key=lambda t: t["date"], reverse=True)
        if category:
            items = [t for t in items if t["category"] == category]
        if q:
            ql = q.lower()
            items = [t for t in items if ql in t["merchant"].lower() or ql in t["description"].lower()]
        return {"total": len(items), "items": items[:limit]}

    @app.patch("/api/transactions/{txn_id}", tags=["data"])
    def recategorize(txn_id: str, body: RecategorizeBody, ctx: Auth):
        if body.category not in CATEGORIES:
            raise HTTPException(422, "Unknown category")
        updated = vault.update_transaction(ctx.dek, txn_id, {"category": body.category, "category_reason": "user"})
        changed = 1
        if body.apply_to_merchant:
            ov = overrides(ctx)
            ov[merchant_key(updated["merchant"])] = body.category
            vault.set_setting(ctx.dek, "category_overrides", ov)
            for t in vault.list_transactions(ctx.dek):
                if t["id"] != txn_id and t["merchant"] == updated["merchant"] and t["direction"] == "debit":
                    vault.update_transaction(ctx.dek, t["id"], {"category": body.category, "category_reason": "user_override"})
                    changed += 1
        return {"updated": changed, "transaction": updated}

    @app.get("/api/budgets", tags=["data"])
    def get_budgets(ctx: Auth):
        return budgets(ctx)

    @app.put("/api/budgets", tags=["data"])
    def put_budgets(body: dict[str, float], ctx: Auth):
        clean = {k: float(v) for k, v in body.items() if k in CATEGORIES and v and v > 0}
        vault.set_setting(ctx.dek, "budgets", clean)
        return clean

    @app.get("/api/dashboard", tags=["insights"])
    def dashboard(ctx: Auth):
        eng = engine(ctx)
        b = budgets(ctx)
        this_month, last_month = eng.period("this_month"), eng.period("last_month")
        return {
            "today": get_today().isoformat(),
            "has_data": not eng.df.empty,
            "accounts": vault.get_setting(ctx.dek, "accounts", []),
            "this_month": eng.summary(this_month),
            "last_month": eng.summary(last_month),
            "breakdown": eng.category_breakdown(this_month),
            "budgets": eng.budgets(b),
            "forecast": eng.forecast_month_end(),
            "vs_last_month": eng.month_to_date_vs_last(),
            "recurring": eng.recurring(),
            "trends": eng.trends(),
            "daily": eng.daily_cumulative(),
            "insights": insights(eng, b) if not eng.df.empty else [],
        }

    @app.post("/api/assistant", tags=["insights"])
    def ask(body: QuestionBody, ctx: Auth):
        eng = engine(ctx)
        return Assistant(eng, budgets(ctx), vault.get_setting(ctx.dek, "accounts", [])).ask(body.question)

    # ------------------------------------------------------------------ privacy
    @app.get("/api/privacy", tags=["privacy"])
    def privacy(ctx: Auth):
        llm = llm_settings()
        return {
            "storage": vault.stats(),
            "crypto": {"records": "AES-256-GCM (per-record nonce, record id as associated data)",
                       "key_derivation": "scrypt (N=2^14, r=8, p=1) from PIN → key-encryption key",
                       "data_key": "random 256-bit key, stored only wrapped by the PIN-derived key",
                       "dedup": "HMAC-SHA256 fingerprints (no plaintext on disk)",
                       "auto_lock_after_seconds": IDLE_TIMEOUT_SECONDS},
            "ai": {"computation": "deterministic finance engine (Pandas) on device",
                   "language": "local LLM via llama.cpp" if llm["enabled"] else "bilingual templates on device",
                   "llm_endpoint": llm["url"], "llm_on_device": llm["on_device"]},
            "network_log": bank.call_log[-20:],
            "financial_data_sent_to_cloud_ai": 0,
        }

    @app.post("/api/reset", tags=["privacy"])
    def reset(ctx: Auth):
        for link in vault.get_setting(ctx.dek, "bank_links", {}).values():
            bank.revoke(link["consent_id"])
        vault.wipe()
        return {"wiped": True}

    return app


app = create_app()
