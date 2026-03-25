"""Integration tests for the full AgentBoss workflow (no real relay needed)."""

import json
import pytest
from typer.testing import CliRunner
from cli.main import app
from cli.storage import Storage
from cli.regions import RegionResolver
from cli.models import parse_job_content
from shared.crypto import gen_keys, to_nsec
from shared.event import build_event, verify_event_id, verify_event_sig
from shared.constants import KIND_APP_DATA, APP_TAG, JOB_TAG, REGION_TAG, REGION_MAP_D_TAG

runner = CliRunner()


@pytest.fixture
def cli_home(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTBOSS_HOME", str(tmp_path))
    return tmp_path


class TestIdentityWorkflow:
    def test_login_then_whoami(self, cli_home):
        priv, pub = gen_keys()
        nsec = to_nsec(priv)
        result = runner.invoke(app, ["login", "--key", nsec])
        assert result.exit_code == 0
        result = runner.invoke(app, ["whoami"])
        assert result.exit_code == 0
        assert "npub" in result.stdout


class TestEventBuildWorkflow:
    def test_build_job_event_is_valid(self):
        priv, pub = gen_keys()
        content = json.dumps({
            "title": "Python Dev",
            "company": "TestCo",
            "version": 1,
        })
        event = build_event(
            kind=KIND_APP_DATA,
            content=content,
            privkey=priv,
            pubkey=pub,
            tags=[
                ["d", "test-job-1"],
                ["t", APP_TAG],
                ["t", JOB_TAG],
                ["province", "1"],
                ["city", "101"],
            ],
        )
        assert verify_event_id(event)
        assert verify_event_sig(event)
        assert event["kind"] == KIND_APP_DATA
        parsed = parse_job_content(event["content"])
        assert parsed.title == "Python Dev"

    def test_build_region_event_is_valid(self):
        priv, pub = gen_keys()
        content = json.dumps({
            "version": 1,
            "provinces": {"1": "北京"},
            "cities": {"101": "北京市"},
            "province_city": {"1": [101]},
        })
        event = build_event(
            kind=KIND_APP_DATA,
            content=content,
            privkey=priv,
            pubkey=pub,
            tags=[["d", REGION_MAP_D_TAG], ["t", APP_TAG], ["t", REGION_TAG]],
        )
        assert verify_event_id(event)
        assert verify_event_sig(event)


class TestStorageWorkflow:
    def test_fetch_store_list_show(self, cli_home):
        """Simulate: region sync -> store jobs -> list -> show."""
        storage = Storage(str(cli_home / "agentboss.db"))
        storage.init_db()
        resolver = RegionResolver(storage)

        # Sync regions
        resolver.apply_mapping(json.dumps({
            "version": 1,
            "provinces": {"1": "北京", "2": "上海"},
            "cities": {"101": "北京市", "201": "上海市"},
            "province_city": {"1": [101], "2": [201]},
        }))
        assert resolver.province_code("北京") == 1
        assert resolver.city_code("北京市") == 101

        # Store some jobs
        storage.upsert_job("ev1", "d1", "pub1", 1, 101, json.dumps({
            "title": "Python Dev", "company": "Co1", "version": 1,
        }), 1000)
        storage.upsert_job("ev2", "d2", "pub2", 2, 201, json.dumps({
            "title": "Go Dev", "company": "Co2", "version": 1,
        }), 2000)

        # List filtered
        beijing_jobs = storage.list_jobs(province_code=1)
        assert len(beijing_jobs) == 1
        assert beijing_jobs[0]["event_id"] == "ev1"

        # Show
        job = storage.get_job("ev1")
        content = parse_job_content(job["content"])
        assert content.title == "Python Dev"

        # Eviction
        for i in range(10):
            storage.upsert_job(f"evx{i}", f"dx{i}", "p", 1, 101, "{}", i)
        storage.evict_oldest(5)
        assert storage.count_jobs() == 5

        storage.close()


class TestFederationPublishWorkflow:
    def test_publish_to_federation_persists_federation_id(self, cli_home):
        """publish --federation writes federation_id to local storage."""
        from cli.main import app
        from cli.nostr_client import NostrRelay
        from cli.storage import Storage

        db_path = str(cli_home / "agentboss.db")

        # Create a fresh storage for the mock to use (separate from test's db_read)
        db = Storage(db_path)
        db.init_db()
        db.upsert_region(1, "beijing", "province")
        db.upsert_region(101, "beijing", "city", parent_code=1)
        db.upsert_federation(
            federation_id="fed_pub_test",
            name="testfed",
            relay_urls=["wss://fake.example.com"],
        )

        # Mock identity and NostrRelay
        import unittest.mock as mock
        mock_publish = mock.AsyncMock(return_value={"event_id": "fake-id", "accepted": True, "message": "ok"})
        mock_connect = mock.AsyncMock()
        mock_close = mock.AsyncMock()

        def make_storage():
            s = Storage(db_path)
            s.init_db()
            s.upsert_region(1, "beijing", "province")
            s.upsert_region(101, "beijing", "city", parent_code=1)
            s.upsert_federation(federation_id="fed_pub_test", name="testfed",
                                relay_urls=["wss://fake.example.com"])
            return s

        with mock.patch("cli.main._load_identity", return_value={
            "privkey": "a" * 64,
            "pubkey": "b" * 64,
            "npub": "npub1test",
        }), mock.patch("cli.main._get_storage", side_effect=make_storage), \
             mock.patch.object(NostrRelay, "connect", mock_connect), \
             mock.patch.object(NostrRelay, "close", mock_close), \
             mock.patch.object(NostrRelay, "publish_event", mock_publish):
            result = runner.invoke(app, ["publish",
                "--province", "beijing",
                "--city", "beijing",
                "--title", "Engineer",
                "--company", "Corp",
                "--federation", "testfed",
            ])
            assert result.exit_code == 0, f"Exit code: {result.exit_code}, output: {result.output}"

        # Verify federation_id was written (fresh connection; db was closed by publish)
        db2 = Storage(db_path)
        db2.init_db()
        jobs = db2.list_jobs()
        assert len(jobs) >= 1
        assert jobs[0]["federation_id"] == "fed_pub_test"
        db2.close()

    def test_fetch_from_federation_persists_federation_id(self, cli_home):
        """fetch --federation writes federation_id to local storage."""
        from cli.main import app
        from cli.storage import Storage
        import cli.main

        db_path = str(cli_home / "agentboss.db")
        db = Storage(db_path)
        db.init_db()
        db.upsert_region(110000, "beijing", "province")
        db.upsert_region(110100, "beijing", "city", parent_code=110000)
        db.upsert_federation(
            federation_id="fed_fetch_test",
            name="fetchfed",
            relay_urls=["wss://fake.example.com"],
        )

        def make_storage():
            s = Storage(db_path)
            s.init_db()
            s.upsert_region(110000, "beijing", "province")
            s.upsert_region(110100, "beijing", "city", parent_code=110000)
            s.upsert_federation(
                federation_id="fed_fetch_test",
                name="fetchfed",
                relay_urls=["wss://fake.example.com"],
            )
            return s

        async def mock_fetch_from_relays(relay_urls, kinds, tags, limit):
            return [{
                "id": "evt_fetch_1",
                "pubkey": "pk1",
                "created_at": 1000,
                "kind": 30078,
                "tags": [["d", "dtag1"], ["t", "agentboss"], ["t", "job"], ["province", "110000"]],
                "content": '{"title":"SRE","company":"Co","version":1}',
            }]

        import unittest.mock as mock
        with mock.patch("cli.main._get_storage", side_effect=make_storage), \
             mock.patch.object(cli.main, "fetch_events_from_relays", mock_fetch_from_relays):
            result = runner.invoke(app, ["fetch", "--federation", "fetchfed", "--limit", "10"])
            assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Verify federation_id was written
        db2 = Storage(db_path)
        db2.init_db()
        jobs = db2.list_jobs()
        assert len(jobs) >= 1
        assert jobs[0]["federation_id"] == "fed_fetch_test"
        db2.close()


class TestWebRegistrationWorkflow:
    def test_register_and_login(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AGENTBOSS_WEB_DB", str(tmp_path / "users.db"))
        monkeypatch.setenv("AGENTBOSS_WHITELIST", str(tmp_path / "whitelist.txt"))
        monkeypatch.setenv("AGENTBOSS_SERVER_KEY", "test-key")
        (tmp_path / "whitelist.txt").write_text("")

        from fastapi.testclient import TestClient
        from web.app import create_app
        client = TestClient(create_app())

        # Register
        resp = client.post("/api/register", json={
            "username": "alice", "email": "a@b.com", "password": "pass123",
        })
        assert resp.status_code == 200
        nsec = resp.json()["nsec"]
        assert nsec.startswith("nsec1")

        # Whitelist populated
        wl = (tmp_path / "whitelist.txt").read_text()
        assert len(wl.strip()) == 64  # hex pubkey

        # Login
        resp = client.post("/api/login", json={
            "username": "alice", "password": "pass123",
        })
        assert resp.status_code == 200

        # Get key
        resp = client.get("/api/key")
        assert resp.status_code == 200
        assert resp.json()["nsec"] == nsec
