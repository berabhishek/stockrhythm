import time

from apps.backend.src.auth_store import AuthStore


def test_auth_store_roundtrip(tmp_path):
    db_path = tmp_path / "auth.db"
    store = AuthStore(db_path=str(db_path))

    store.save_upstox_token("token-123", expires_in=60)
    assert store.get_valid_upstox_token() == "token-123"


def test_auth_store_expires_token(tmp_path):
    db_path = tmp_path / "auth.db"
    store = AuthStore(db_path=str(db_path))

    store.save_upstox_token("token-123", expires_at=int(time.time()) - 1)
    assert store.get_valid_upstox_token() is None
