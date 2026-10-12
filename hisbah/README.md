# Hisbah (حِسبة): demo prototype

A working demo of **Hisbah: A Privacy-First AI Personal Finance Assistant** (CSC 496 Senior Capstone, King Saud University).
It covers the proposal's three core ideas: **automation**, **financial intelligence** and **local-first processing**.

## Run it

```bash
cd hisbah
uv sync
uv run uvicorn app.main:app --reload
# open http://127.0.0.1:8000   (API docs: http://127.0.0.1:8000/docs)
```

Optional environment variables:

| Variable | Purpose |
|---|---|
| `HISBAH_DATA_DIR` | Where the encrypted SQLite file lives (default `hisbah/data/`) |
| `HISBAH_TODAY` | Freeze "today" (e.g. `2026-10-12`) so a live demo always shows the same numbers |
| `HISBAH_LLM_URL` | A **local** llama.cpp server (`llama-server -m qwen2.5-1.5b-instruct-q4_k_m.gguf`, e.g. `http://127.0.0.1:8080`) used to rephrase answers. Off by default |

Tests: `uv run pytest` (42 tests).

## Demo script (about 5 minutes)

1. **Lock screen.** Create a 4‑digit PIN. It derives the key that unlocks the encrypted vault.
2. **Connect a bank.** Pick *Nakheel Bank (Sandbox)*, review the read-only consent, then approve on the "bank" page.
   About 240 transactions are fetched, parsed, categorised (100 % auto) and stored encrypted.
3. **Home.** Month-to-date spend vs. the same days last month, a projected month-end total, insights
   (an over-budget category, an **unusual 4,299 SAR eXtra purchase**, rising dining spend, and the yearly cost of subscriptions), a spending-pace chart,
   budgets with projections, and a category breakdown (toggle it to a table).
4. **Activity → + Add.** Tap *Arabic sample*. The bilingual parser pulls amount, merchant, date, card and balance
   out of an Arabic-digit SMS and shows which rules fired. Save it. Also try *Statement (CSV) → Use sample statement*.
   Tap any transaction to re-categorise it; Hisbah remembers that choice for the merchant.
5. **Assistant.** Ask in English or Arabic, for example "How much did I spend on dining this month?", «وش اشتراكاتي؟»,
   «قارن سبتمبر بأغسطس» or "Any unusual transactions?". Open **How I got this answer** to show the intent, the entities, the
   finance-engine call and the verified facts behind each number.
6. **Privacy.** Shows a real row from the database (ciphertext only), the crypto setup, the network log (sandbox calls
   only) and a count of *0* for financial data sent to cloud AI. Here you can also edit budgets, lock the app, or reset the demo.
7. Switch **عربي / English** at any time. The whole UI flips to RTL, and dark mode follows the OS.

## Architecture

```
┌──────────── Mock SAMA Open Banking sandbox  (/sandbox/v1) ─────────────┐
│ consents → authorise → access token → accounts / transactions          │
│ fictional banks, deterministic synthetic Saudi data (AR + EN text)      │
└───────────────────────────────┬────────────────────────────────────────┘
                                │ read-only, consent-scoped
┌──────────── Hisbah core (/api), on the phone in the Flutter app ───────┐
│ ingest.py        bank feed · bank SMS · CSV statement → records        │
│ parser.py        bilingual rule-based parser (amount, merchant, date…) │
│ categorizer.py   AR/EN keyword rules + merchant aliases + user overrides│
│ vault.py         PIN →scrypt→ KEK → wraps DEK → AES-256-GCM per record │
│ engine.py        deterministic Pandas finance engine (all numbers)     │
│ assistant.py     intent/entity extraction → engine → AR/EN answer      │
│                  (+ optional local llama.cpp rephrasing, number-checked)│
└───────────────────────────────┬────────────────────────────────────────┘
                     static/   mobile-style web client (stands in for Flutter)
```

**Computation is kept separate from language generation.** The assistant never does arithmetic.
It works out what you are asking, calls the finance engine, and phrases the verified result.
If a local LLM is configured and its rephrasing contains any number that is not in the verified facts, the
template answer is used instead.

### What maps to the proposal

| Proposal | In this demo |
|---|---|
| Consent-based Open Banking via Lean/Tarabut sandboxes | `app/sandbox.py`: same consent → authorise → token → data flow |
| Encrypted on-device SQLite (SQLCipher) + PIN/biometric gate | `app/vault.py`: AES-256-GCM per record, scrypt-wrapped key, lockout and auto-lock |
| Bilingual rule-based parser | `app/parser.py`: Arabic-Indic digits, `ر.س`/`SAR`, Saudi SMS formats |
| Categorisation layer | `app/categorizer.py`: AR/EN merchant rules and learning from user corrections |
| Deterministic finance engine (Pandas) | `app/engine.py`: totals, budgets and projection, recurring detection, anomalies (robust z-score), trends, month comparisons |
| On-device AI answers and insights | `app/assistant.py`: grounded bilingual answers, with an optional llama.cpp hook for Semester 2 |
| FastAPI backend | `app/main.py` |

### Limitations (honest scope)

- The web client stands in for the Flutter app, and the "device" core runs inside the FastAPI process.
- Banks and data are synthetic. No real banking APIs or credentials are used.
- Encryption is field-level (AES-GCM through `cryptography`) rather than SQLCipher. The key design is the same.
- Biometric unlock (`local_auth`) and on-device llama.cpp via FFI are Semester 2 items. The LLM hook here talks to a local llama.cpp server.
