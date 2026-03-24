import pytest
from web.db import UserDB


@pytest.fixture
def db(tmp_path):
    d = UserDB(str(tmp_path / "users.db"))
    d.init_db()
    yield d
    d.close()


class TestUserDB:
    def test_create_user(self, db):
        user = db.create_user(
            username="alice",
            email="alice@example.com",
            password_hash="hash123",
            npub="npub1abc",
            nsec_encrypted="enc_nsec",
        )
        assert user["username"] == "alice"
        assert user["id"] is not None

    def test_create_duplicate_username_raises(self, db):
        db.create_user("alice", "a@b.com", "hash", "npub1", "enc1")
        with pytest.raises(Exception):
            db.create_user("alice", "c@d.com", "hash", "npub2", "enc2")

    def test_create_duplicate_email_raises(self, db):
        db.create_user("alice", "a@b.com", "hash", "npub1", "enc1")
        with pytest.raises(Exception):
            db.create_user("bob", "a@b.com", "hash", "npub2", "enc2")

    def test_get_user_by_username(self, db):
        db.create_user("alice", "a@b.com", "hash", "npub1", "enc1")
        user = db.get_user_by_username("alice")
        assert user is not None
        assert user["email"] == "a@b.com"

    def test_get_user_by_username_not_found(self, db):
        assert db.get_user_by_username("ghost") is None

    def test_get_user_by_id(self, db):
        created = db.create_user("alice", "a@b.com", "hash", "npub1", "enc1")
        user = db.get_user_by_id(created["id"])
        assert user["username"] == "alice"

    def test_list_active_npubs(self, db):
        db.create_user("alice", "a@b.com", "h", "npub1", "e1")
        db.create_user("bob", "b@b.com", "h", "npub2", "e2")
        npubs = db.list_active_npubs()
        assert len(npubs) == 2
        assert "npub1" in npubs
