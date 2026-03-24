import os
import pytest
from web.auth import register_user, verify_password, encrypt_nsec, decrypt_nsec
from web.db import UserDB


@pytest.fixture
def db(tmp_path):
    d = UserDB(str(tmp_path / "users.db"))
    d.init_db()
    yield d
    d.close()


@pytest.fixture
def whitelist_path(tmp_path):
    path = tmp_path / "whitelist.txt"
    path.write_text("")
    return str(path)


class TestRegisterUser:
    def test_register_creates_user_with_keypair(self, db, whitelist_path):
        result = register_user(
            db=db,
            username="alice",
            email="alice@example.com",
            password="securepass123",
            whitelist_path=whitelist_path,
        )
        assert "npub" in result
        assert "nsec" in result
        assert result["npub"].startswith("npub1")
        assert result["nsec"].startswith("nsec1")

    def test_register_adds_to_whitelist(self, db, whitelist_path):
        result = register_user(db, "alice", "a@b.com", "pass", whitelist_path)
        with open(whitelist_path) as f:
            content = f.read()
        # Whitelist should contain hex pubkey (not npub)
        from shared.crypto import npub_to_hex
        hex_pub = npub_to_hex(result["npub"])
        assert hex_pub in content

    def test_register_stores_encrypted_nsec(self, db, whitelist_path):
        result = register_user(db, "alice", "a@b.com", "pass", whitelist_path)
        user = db.get_user_by_username("alice")
        # nsec_encrypted should not be plaintext nsec
        assert user["nsec_encrypted"] != result["nsec"]

    def test_register_duplicate_username_raises(self, db, whitelist_path):
        register_user(db, "alice", "a@b.com", "pass", whitelist_path)
        with pytest.raises(Exception):
            register_user(db, "alice", "b@b.com", "pass", whitelist_path)


class TestPasswordVerify:
    def test_verify_correct_password(self, db, whitelist_path):
        register_user(db, "alice", "a@b.com", "mypassword", whitelist_path)
        user = db.get_user_by_username("alice")
        assert verify_password("mypassword", user["password_hash"]) is True

    def test_verify_wrong_password(self, db, whitelist_path):
        register_user(db, "alice", "a@b.com", "mypassword", whitelist_path)
        user = db.get_user_by_username("alice")
        assert verify_password("wrongpassword", user["password_hash"]) is False


class TestNsecEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        secret_key = "test-server-key-1234567890123456"
        nsec = "nsec1" + "a" * 58
        encrypted = encrypt_nsec(nsec, secret_key)
        assert encrypted != nsec
        decrypted = decrypt_nsec(encrypted, secret_key)
        assert decrypted == nsec
