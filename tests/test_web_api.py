import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTBOSS_WEB_DB", str(tmp_path / "users.db"))
    monkeypatch.setenv("AGENTBOSS_WHITELIST", str(tmp_path / "whitelist.txt"))
    monkeypatch.setenv("AGENTBOSS_SERVER_KEY", "test-key-12345")
    (tmp_path / "whitelist.txt").write_text("")

    from web.app import create_app
    app = create_app()
    return TestClient(app)


class TestRegister:
    def test_register_success(self, app_client):
        resp = app_client.post("/api/register", json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "npub" in data
        assert "nsec" in data

    def test_register_duplicate_username(self, app_client):
        app_client.post("/api/register", json={
            "username": "alice", "email": "a@b.com", "password": "pass",
        })
        resp = app_client.post("/api/register", json={
            "username": "alice", "email": "c@d.com", "password": "pass",
        })
        assert resp.status_code == 400

    def test_register_missing_fields(self, app_client):
        resp = app_client.post("/api/register", json={"username": "alice"})
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, app_client):
        app_client.post("/api/register", json={
            "username": "alice", "email": "a@b.com", "password": "mypass",
        })
        resp = app_client.post("/api/login", json={
            "username": "alice", "password": "mypass",
        })
        assert resp.status_code == 200
        assert "session" in resp.cookies or resp.json().get("ok")

    def test_login_wrong_password(self, app_client):
        app_client.post("/api/register", json={
            "username": "alice", "email": "a@b.com", "password": "mypass",
        })
        resp = app_client.post("/api/login", json={
            "username": "alice", "password": "wrong",
        })
        assert resp.status_code == 401


class TestMe:
    def test_me_without_login(self, app_client):
        resp = app_client.get("/api/me")
        assert resp.status_code == 401

    def test_me_with_session(self, app_client):
        app_client.post("/api/register", json={
            "username": "alice", "email": "a@b.com", "password": "mypass",
        })
        app_client.post("/api/login", json={
            "username": "alice", "password": "mypass",
        })
        resp = app_client.get("/api/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "alice"
        assert "npub" in data


class TestKey:
    def test_get_key_with_session(self, app_client):
        reg = app_client.post("/api/register", json={
            "username": "alice", "email": "a@b.com", "password": "mypass",
        })
        app_client.post("/api/login", json={
            "username": "alice", "password": "mypass",
        })
        resp = app_client.get("/api/key")
        assert resp.status_code == 200
        assert "nsec" in resp.json()
