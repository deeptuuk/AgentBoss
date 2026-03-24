import os
import pytest
import sqlite3
from cli.storage import Storage


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    s = Storage(db_path)
    s.init_db()
    yield s
    s.close()


class TestStorageInit:
    def test_creates_tables(self, db):
        tables = db.list_tables()
        assert "jobs" in tables
        assert "regions" in tables
        assert "config" in tables


class TestConfig:
    def test_set_and_get(self, db):
        db.set_config("relay", "ws://localhost:7777")
        assert db.get_config("relay") == "ws://localhost:7777"

    def test_get_missing_returns_default(self, db):
        assert db.get_config("missing", "default") == "default"

    def test_set_overwrites(self, db):
        db.set_config("key", "v1")
        db.set_config("key", "v2")
        assert db.get_config("key") == "v2"


class TestJobs:
    def test_upsert_and_get(self, db):
        db.upsert_job(
            event_id="id1",
            d_tag="d1",
            pubkey="pub1",
            province_code=1,
            city_code=101,
            content='{"title":"Dev"}',
            created_at=1000,
        )
        job = db.get_job("id1")
        assert job is not None
        assert job["d_tag"] == "d1"
        assert job["province_code"] == 1

    def test_upsert_replaces_by_d_tag(self, db):
        db.upsert_job("id1", "d1", "pub1", 1, 101, '{"v":1}', 1000)
        db.upsert_job("id2", "d1", "pub1", 1, 101, '{"v":2}', 2000)
        # old id1 should be gone, id2 should exist
        assert db.get_job("id1") is None
        assert db.get_job("id2") is not None

    def test_list_jobs_filter_province(self, db):
        db.upsert_job("id1", "d1", "p", 1, 101, "{}", 1000)
        db.upsert_job("id2", "d2", "p", 2, 201, "{}", 1000)
        jobs = db.list_jobs(province_code=1)
        assert len(jobs) == 1
        assert jobs[0]["event_id"] == "id1"

    def test_list_jobs_filter_city(self, db):
        db.upsert_job("id1", "d1", "p", 1, 101, "{}", 1000)
        db.upsert_job("id2", "d2", "p", 1, 102, "{}", 1000)
        jobs = db.list_jobs(city_code=102)
        assert len(jobs) == 1
        assert jobs[0]["event_id"] == "id2"

    def test_evict_oldest_when_over_limit(self, db):
        for i in range(5):
            db.upsert_job(f"id{i}", f"d{i}", "p", 1, 101, "{}", created_at=i)
        db.evict_oldest(max_count=3)
        remaining = db.list_jobs()
        assert len(remaining) == 3
        # oldest (created_at=0,1) should be evicted
        ids = [j["event_id"] for j in remaining]
        assert "id0" not in ids
        assert "id1" not in ids

    def test_count_jobs(self, db):
        db.upsert_job("id1", "d1", "p", 1, 101, "{}", 1000)
        db.upsert_job("id2", "d2", "p", 1, 101, "{}", 1000)
        assert db.count_jobs() == 2


class TestRegions:
    def test_upsert_and_get_region(self, db):
        db.upsert_region(code=1, name="北京", region_type="province")
        r = db.get_region(1)
        assert r["name"] == "北京"
        assert r["type"] == "province"

    def test_upsert_city_with_parent(self, db):
        db.upsert_region(1, "北京", "province")
        db.upsert_region(101, "北京市", "city", parent_code=1)
        r = db.get_region(101)
        assert r["parent_code"] == 1

    def test_list_provinces(self, db):
        db.upsert_region(1, "北京", "province")
        db.upsert_region(2, "上海", "province")
        db.upsert_region(101, "北京市", "city", parent_code=1)
        provinces = db.list_regions(region_type="province")
        assert len(provinces) == 2

    def test_get_region_version(self, db):
        """Region version stored in config"""
        assert db.get_config("region_version", "0") == "0"
        db.set_config("region_version", "3")
        assert db.get_config("region_version") == "3"
