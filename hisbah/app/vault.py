"""Encrypted on-device storage.

Key hierarchy (mirrors what the Flutter app does with SQLCipher + the OS keystore):

    PIN --scrypt(salt)--> KEK --AES-256-GCM--> wraps random 256-bit DEK
    DEK --AES-256-GCM--> every transaction record / setting stored in SQLite

The SQLite file therefore only ever contains ciphertext. The DEK lives in memory
only while the vault is unlocked and is dropped on lock / idle timeout.
"""

import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from sqlalchemy import func
from sqlmodel import Field, Session, SQLModel, create_engine, delete, select

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 30
IDLE_TIMEOUT_SECONDS = 10 * 60


class VaultMeta(SQLModel, table=True):
    __tablename__ = "vault_meta"
    id: int = Field(default=1, primary_key=True)
    salt: bytes
    wrapped_dek: bytes
    created_at: datetime
    failed_attempts: int = 0
    locked_until: float = 0.0


class EncryptedTransaction(SQLModel, table=True):
    __tablename__ = "transactions"
    id: str = Field(primary_key=True)
    fingerprint: str = Field(index=True, unique=True)  # keyed HMAC, used for de-duplication
    source: str
    ciphertext: bytes


class EncryptedSetting(SQLModel, table=True):
    __tablename__ = "settings"
    key: str = Field(primary_key=True)
    ciphertext: bytes


class VaultError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _derive_kek(pin: str, salt: bytes) -> bytes:
    return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(pin.encode())


def _seal(key: bytes, plaintext: bytes, aad: bytes) -> bytes:
    nonce = os.urandom(12)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)


def _open(key: bytes, blob: bytes, aad: bytes) -> bytes:
    return AESGCM(key).decrypt(blob[:12], blob[12:], aad)


@dataclass
class _Unlocked:
    dek: bytes
    last_seen: float


class Vault:
    def __init__(self, data_dir: Path):
        data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = data_dir / "hisbah_local.db"
        self.engine = create_engine(f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(self.engine)
        self._sessions: dict[str, _Unlocked] = {}

    # ---------------------------------------------------------------- auth
    def is_initialized(self) -> bool:
        with Session(self.engine) as s:
            return s.get(VaultMeta, 1) is not None

    def setup(self, pin: str) -> str:
        _validate_pin(pin)
        if self.is_initialized():
            raise VaultError("Vault already initialised", 409)
        salt, dek = os.urandom(16), AESGCM.generate_key(bit_length=256)
        wrapped = _seal(_derive_kek(pin, salt), dek, b"hisbah-dek")
        with Session(self.engine) as s:
            s.add(VaultMeta(salt=salt, wrapped_dek=wrapped, created_at=datetime.now(UTC)))
            s.commit()
        return self._open_session(dek)

    def unlock(self, pin: str) -> str:
        with Session(self.engine) as s:
            meta = s.get(VaultMeta, 1)
            if meta is None:
                raise VaultError("Vault not initialised", 404)
            now = time.time()
            if meta.locked_until > now:
                raise VaultError(f"Too many attempts. Try again in {int(meta.locked_until - now) + 1}s", 429)
            try:
                dek = _open(_derive_kek(pin, meta.salt), meta.wrapped_dek, b"hisbah-dek")
            except InvalidTag:
                meta.failed_attempts += 1
                if meta.failed_attempts >= MAX_ATTEMPTS:
                    meta.failed_attempts = 0
                    meta.locked_until = now + LOCKOUT_SECONDS
                s.add(meta)
                s.commit()
                raise VaultError("Incorrect PIN", 401)
            meta.failed_attempts = 0
            s.add(meta)
            s.commit()
        return self._open_session(dek)

    def change_pin(self, token: str, new_pin: str) -> None:
        _validate_pin(new_pin)
        dek = self.dek(token)
        salt = os.urandom(16)
        with Session(self.engine) as s:
            meta = s.get(VaultMeta, 1)
            meta.salt, meta.wrapped_dek = salt, _seal(_derive_kek(new_pin, salt), dek, b"hisbah-dek")
            s.add(meta)
            s.commit()

    def _open_session(self, dek: bytes) -> str:
        token = secrets.token_urlsafe(32)
        self._sessions[token] = _Unlocked(dek=dek, last_seen=time.time())
        return token

    def lock(self, token: str | None = None) -> None:
        if token is None:
            self._sessions.clear()
        else:
            self._sessions.pop(token, None)

    def dek(self, token: str) -> bytes:
        session = self._sessions.get(token)
        if session is None:
            raise VaultError("Vault is locked", 401)
        if time.time() - session.last_seen > IDLE_TIMEOUT_SECONDS:
            self._sessions.pop(token, None)
            raise VaultError("Session timed out — vault locked", 401)
        session.last_seen = time.time()
        return session.dek

    # ---------------------------------------------------------------- data
    def add_transactions(self, dek: bytes, records: list[dict]) -> list[dict]:
        """Encrypt and store records; returns only the newly-inserted ones (dedup by fingerprint)."""
        inserted = []
        with Session(self.engine) as s:
            existing = set(s.exec(select(EncryptedTransaction.fingerprint)).all())
            for record in records:
                fp = _fingerprint(dek, record)
                if fp in existing:
                    continue
                existing.add(fp)
                record = {**record, "id": record.get("id") or uuid.uuid4().hex}
                s.add(EncryptedTransaction(
                    id=record["id"], fingerprint=fp, source=record.get("source", "manual"),
                    ciphertext=_seal(dek, json.dumps(record, ensure_ascii=False).encode(), record["id"].encode()),
                ))
                inserted.append(record)
            s.commit()
        return inserted

    def list_transactions(self, dek: bytes) -> list[dict]:
        with Session(self.engine) as s:
            rows = s.exec(select(EncryptedTransaction)).all()
        return [json.loads(_open(dek, r.ciphertext, r.id.encode())) for r in rows]

    def update_transaction(self, dek: bytes, txn_id: str, changes: dict) -> dict:
        with Session(self.engine) as s:
            row = s.get(EncryptedTransaction, txn_id)
            if row is None:
                raise VaultError("Transaction not found", 404)
            record = {**json.loads(_open(dek, row.ciphertext, row.id.encode())), **changes}
            row.ciphertext = _seal(dek, json.dumps(record, ensure_ascii=False).encode(), row.id.encode())
            s.add(row)
            s.commit()
        return record

    def get_setting(self, dek: bytes, key: str, default=None):
        with Session(self.engine) as s:
            row = s.get(EncryptedSetting, key)
        return default if row is None else json.loads(_open(dek, row.ciphertext, key.encode()))

    def set_setting(self, dek: bytes, key: str, value) -> None:
        blob = _seal(dek, json.dumps(value, ensure_ascii=False).encode(), key.encode())
        with Session(self.engine) as s:
            row = s.get(EncryptedSetting, key) or EncryptedSetting(key=key, ciphertext=blob)
            row.ciphertext = blob
            s.add(row)
            s.commit()

    def stats(self) -> dict:
        with Session(self.engine) as s:
            count = s.exec(select(func.count()).select_from(EncryptedTransaction)).one()
            sample = s.exec(select(EncryptedTransaction).limit(1)).first()
        return {
            "db_file": self.db_path.name,
            "db_size_bytes": self.db_path.stat().st_size if self.db_path.exists() else 0,
            "encrypted_records": count,
            "sample_row_on_disk": None if sample is None else {
                "id": sample.id,
                "source": sample.source,
                "fingerprint": sample.fingerprint[:24] + "…",
                "ciphertext_hex": sample.ciphertext[:48].hex() + "…",
                "ciphertext_bytes": len(sample.ciphertext),
            },
        }

    def wipe(self) -> None:
        with Session(self.engine) as s:
            for table in (EncryptedTransaction, EncryptedSetting, VaultMeta):
                s.exec(delete(table))
            s.commit()
        self.lock()


def _validate_pin(pin: str) -> None:
    if not (pin.isdigit() and 4 <= len(pin) <= 8):
        raise VaultError("PIN must be 4–8 digits", 422)


def _fingerprint(dek: bytes, record: dict) -> str:
    key = hashlib.sha256(dek + b"fingerprint").digest()
    ref = record.get("external_ref") or (
        f"{record.get('date')}|{record.get('amount')}|{record.get('direction')}|{record.get('description')}"
    )
    return hmac.new(key, ref.encode(), hashlib.sha256).hexdigest()
