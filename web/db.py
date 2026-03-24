"""User database for the registration website."""

import sqlite3
import time


class UserDB:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def init_db(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                npub TEXT UNIQUE NOT NULL,
                nsec_encrypted TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1
            );
        """)
        self._conn.commit()

    def close(self):
        self._conn.close()

    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        npub: str,
        nsec_encrypted: str,
    ) -> dict:
        cur = self._conn.execute(
            """INSERT INTO users (username, email, password_hash, npub, nsec_encrypted, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username, email, password_hash, npub, nsec_encrypted, int(time.time())),
        )
        self._conn.commit()
        return dict(self._conn.execute(
            "SELECT * FROM users WHERE id = ?", (cur.lastrowid,)
        ).fetchone())

    def get_user_by_username(self, username: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_active_npubs(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT npub FROM users WHERE is_active = 1"
        ).fetchall()
        return [row["npub"] for row in rows]
