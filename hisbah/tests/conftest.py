from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

TODAY = date(2026, 10, 12)


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path, today=TODAY))


@pytest.fixture
def auth(client):
    token = client.post("/api/auth/setup", json={"pin": "2468"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def synced(client, auth):
    consent = client.post("/api/bank/consent", json={"bank_id": "nakheel"}, headers=auth).json()
    client.post("/api/bank/authorise", json={"consent_id": consent["consent_id"]}, headers=auth)
    client.post("/api/bank/sync", headers=auth)
    return auth
