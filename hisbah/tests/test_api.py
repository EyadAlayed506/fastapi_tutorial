from app.sandbox import generate_transactions
from tests.conftest import TODAY


def test_pin_setup_lock_unlock(client, auth):
    assert client.get("/api/dashboard").status_code == 401
    assert client.post("/api/auth/unlock", json={"pin": "0000"}).status_code == 401
    assert client.post("/api/auth/setup", json={"pin": "1111"}).status_code == 409
    token = client.post("/api/auth/unlock", json={"pin": "2468"}).json()["token"]
    assert client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    client.post("/api/auth/lock", headers=auth)
    assert client.get("/api/dashboard", headers=auth).status_code == 401


def test_lockout_after_repeated_wrong_pins(client, auth):
    codes = [client.post("/api/auth/unlock", json={"pin": "9999"}).status_code for _ in range(6)]
    assert codes[:5] == [401] * 5 and codes[5] == 429


def test_open_banking_consent_flow(client, auth):
    consent = client.post("/api/bank/consent", json={"bank_id": "nakheel"}, headers=auth).json()
    assert consent["status"] == "AwaitingAuthorisation"
    # The sandbox refuses data access before authorisation
    assert client.get("/sandbox/v1/accounts", headers={"Authorization": "Bearer nope"}).status_code == 401
    assert client.post("/api/bank/authorise", json={"consent_id": consent["consent_id"]}, headers=auth).json()["status"] == "Authorised"
    first = client.post("/api/bank/sync", headers=auth).json()
    assert first["accounts"] == 2 and first["new"] == first["fetched"] > 150
    assert first["categorized_pct"] > 95
    assert client.post("/api/bank/sync", headers=auth).json()["new"] == 0  # de-duplicated
    assert client.delete("/api/bank/nakheel", headers=auth).json()["revoked"] is True


def test_declined_consent_shares_nothing(client, auth):
    consent = client.post("/api/bank/consent", json={"bank_id": "sahara"}, headers=auth).json()
    r = client.post("/api/bank/authorise", json={"consent_id": consent["consent_id"], "approve": False}, headers=auth)
    assert r.json()["status"] == "Rejected"
    assert client.post("/api/bank/sync", headers=auth).status_code == 400


def test_database_contains_only_ciphertext(client, synced, tmp_path):
    raw = (tmp_path / "hisbah_local.db").read_bytes()
    for plaintext in (b"STARBUCKS", b"Starbucks", "هنقرستيشن".encode(), b"14500", b"SALARY"):
        assert plaintext not in raw


def test_dashboard_and_assistant(client, synced):
    d = client.get("/api/dashboard", headers=synced).json()
    assert d["has_data"] and d["this_month"]["spending"] > 0
    assert any(i["kind"] == "anomaly" for i in d["insights"])
    assert {r["merchant"] for r in d["recurring"]["items"]} >= {"Netflix", "Shahid", "Spotify"}
    r = client.post("/api/assistant", json={"question": "What are my subscriptions?"}, headers=synced).json()
    assert r["understanding"]["intent"] == "recurring" and "Netflix" in r["answer"]


def test_sms_ingest_and_recategorize(client, synced):
    sms = "Purchase\nCard: **8812 Visa\nAmount: SAR 1,250.00\nAt: JARIR BOOKSTORE\nOn: 2026-10-11 14:02"
    first = client.post("/api/ingest/sms", json={"text": sms}, headers=synced).json()
    assert first["saved"] and first["transaction"]["merchant"] == "Jarir Bookstore"
    assert client.post("/api/ingest/sms", json={"text": sms}, headers=synced).json()["duplicate"]
    # Mixed timestamp precisions (SMS vs bank feed) must not break the engine.
    assert client.get("/api/dashboard", headers=synced).status_code == 200
    r = client.patch(f"/api/transactions/{first['transaction']['id']}",
                     json={"category": "education", "apply_to_merchant": True}, headers=synced).json()
    assert r["updated"] > 1  # all Jarir purchases re-categorised
    txns = client.get("/api/transactions", params={"q": "jarir"}, headers=synced).json()["items"]
    assert {t["category"] for t in txns} == {"education"}


def test_statement_upload(client, auth):
    csv = "التاريخ,البيان,المبلغ\n05/10/2026,شراء عبر نقاط البيع البيك جدة,-32.00\n06/10/2026,إيداع راتب,9000\n"
    r = client.post("/api/ingest/statement", files={"file": ("s.csv", csv.encode(), "text/csv")}, headers=auth).json()
    assert r == {"rows": 2, "new": 2}
    items = client.get("/api/transactions", headers=auth).json()["items"]
    assert {(t["merchant"], t["category"]) for t in items} == {("AlBaik", "dining"), ("Salary", "income")}


def test_sandbox_feed_is_deterministic():
    assert generate_transactions("nakheel", "nakheel-cur-4523", TODAY) == generate_transactions("nakheel", "nakheel-cur-4523", TODAY)
