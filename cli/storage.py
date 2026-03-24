"""SQLite local storage for jobs, regions, and config."""

import sqlite3
import time


class Storage:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    def init_db(self):
        cur = self._conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                event_id TEXT PRIMARY KEY,
                d_tag TEXT UNIQUE,
                pubkey TEXT NOT NULL,
                province_code INTEGER,
                city_code INTEGER,
                content TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                received_at INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS regions (
                code INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                parent_code INTEGER
            );
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def close(self):
        self._conn.close()

    def list_tables(self) -> list[str]:
        cur = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        return [row["name"] for row in cur.fetchall()]

    # ── Config ──

    def set_config(self, key: str, value: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )
        self._conn.commit()

    def get_config(self, key: str, default: str | None = None) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    # ── Jobs ──

    def upsert_job(
        self,
        event_id: str,
        d_tag: str,
        pubkey: str,
        province_code: int,
        city_code: int,
        content: str,
        created_at: int,
    ):
        # Delete existing job with same d_tag (replaceable event)
        self._conn.execute("DELETE FROM jobs WHERE d_tag = ?", (d_tag,))
        self._conn.execute(
            """INSERT INTO jobs
               (event_id, d_tag, pubkey, province_code, city_code, content, created_at, received_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, d_tag, pubkey, province_code, city_code, content, created_at, int(time.time())),
        )
        self._conn.commit()

    def get_job(self, event_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE event_id = ?", (event_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_jobs(
        self,
        province_code: int | None = None,
        city_code: int | None = None,
    ) -> list[dict]:
        query = "SELECT * FROM jobs WHERE 1=1"
        params: list = []
        if province_code is not None:
            query += " AND province_code = ?"
            params.append(province_code)
        if city_code is not None:
            query += " AND city_code = ?"
            params.append(city_code)
        query += " ORDER BY created_at DESC"
        rows = self._conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def count_jobs(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as cnt FROM jobs").fetchone()
        return row["cnt"]

    def evict_oldest(self, max_count: int):
        count = self.count_jobs()
        if count <= max_count:
            return
        to_delete = count - max_count
        self._conn.execute(
            "DELETE FROM jobs WHERE event_id IN "
            "(SELECT event_id FROM jobs ORDER BY created_at ASC LIMIT ?)",
            (to_delete,),
        )
        self._conn.commit()

    # ── Regions ──

    def upsert_region(
        self,
        code: int,
        name: str,
        region_type: str,
        parent_code: int | None = None,
    ):
        self._conn.execute(
            "INSERT OR REPLACE INTO regions (code, name, type, parent_code) VALUES (?, ?, ?, ?)",
            (code, name, region_type, parent_code),
        )
        self._conn.commit()

    def get_region(self, code: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM regions WHERE code = ?", (code,)
        ).fetchone()
        return dict(row) if row else None

    def list_regions(self, region_type: str | None = None) -> list[dict]:
        if region_type:
            rows = self._conn.execute(
                "SELECT * FROM regions WHERE type = ? ORDER BY code", (region_type,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM regions ORDER BY code"
            ).fetchall()
        return [dict(r) for r in rows]
