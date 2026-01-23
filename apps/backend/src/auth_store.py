import sqlite3
import time
from pathlib import Path


class AuthStore:
    def __init__(self, db_path: str = "auth.db"):
        self.db_path = str(db_path)
        self._init_db()

    def _connect(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS upstox_tokens (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    expires_at INTEGER NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def save_upstox_token(
        self,
        access_token: str,
        *,
        expires_in: int | None = None,
        expires_at: int | None = None,
        refresh_token: str | None = None,
    ) -> None:
        now = int(time.time())
        if expires_at is None:
            lifetime = int(expires_in) if expires_in else 24 * 60 * 60
            expires_at = now + lifetime

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO upstox_tokens (id, access_token, refresh_token, expires_at, created_at)
                VALUES (1, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    access_token = excluded.access_token,
                    refresh_token = excluded.refresh_token,
                    expires_at = excluded.expires_at,
                    created_at = excluded.created_at
                """,
                (access_token, refresh_token, int(expires_at), now),
            )
            conn.commit()

    def get_valid_upstox_token(self) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT access_token, expires_at FROM upstox_tokens WHERE id = 1"
            ).fetchone()

        if not row:
            return None

        access_token, expires_at = row
        if int(expires_at) <= int(time.time()):
            return None
        return str(access_token)
