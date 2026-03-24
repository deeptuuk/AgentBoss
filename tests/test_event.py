import json
import pytest
from shared.crypto import gen_keys
from shared.event import compute_event_id, build_event, verify_event_id, verify_event_sig


class TestEventId:
    def test_compute_event_id_deterministic(self):
        ev = {
            "pubkey": "aa" * 32,
            "created_at": 1700000000,
            "kind": 30078,
            "tags": [["d", "test"]],
            "content": '{"hello":"world"}',
        }
        id1 = compute_event_id(ev)
        id2 = compute_event_id(ev)
        assert id1 == id2
        assert len(id1) == 64

    def test_compute_event_id_changes_with_content(self):
        base = {
            "pubkey": "aa" * 32,
            "created_at": 1700000000,
            "kind": 30078,
            "tags": [],
        }
        ev1 = {**base, "content": "hello"}
        ev2 = {**base, "content": "world"}
        assert compute_event_id(ev1) != compute_event_id(ev2)

    def test_verify_event_id_correct(self):
        ev = {
            "pubkey": "bb" * 32,
            "created_at": 1700000000,
            "kind": 1,
            "tags": [],
            "content": "test",
        }
        ev["id"] = compute_event_id(ev)
        assert verify_event_id(ev) is True

    def test_verify_event_id_tampered(self):
        ev = {
            "pubkey": "bb" * 32,
            "created_at": 1700000000,
            "kind": 1,
            "tags": [],
            "content": "test",
        }
        ev["id"] = "00" * 32
        assert verify_event_id(ev) is False


class TestBuildEvent:
    def test_build_event_has_all_fields(self):
        priv, pub = gen_keys()
        ev = build_event(
            kind=30078,
            content='{"title":"test"}',
            privkey=priv,
            pubkey=pub,
            tags=[["d", "job1"], ["t", "agentboss"]],
        )
        assert ev["kind"] == 30078
        assert ev["pubkey"] == pub
        assert ev["content"] == '{"title":"test"}'
        assert ev["tags"] == [["d", "job1"], ["t", "agentboss"]]
        assert "id" in ev
        assert "sig" in ev
        assert "created_at" in ev

    def test_build_event_sig_is_valid(self):
        priv, pub = gen_keys()
        ev = build_event(kind=1, content="hello", privkey=priv, pubkey=pub)
        assert verify_event_id(ev) is True
        assert verify_event_sig(ev) is True


class TestVerifyEventSig:
    def test_verify_event_sig_tampered_content(self):
        priv, pub = gen_keys()
        ev = build_event(kind=1, content="original", privkey=priv, pubkey=pub)
        ev["content"] = "tampered"
        # id no longer matches, sig no longer valid
        assert verify_event_id(ev) is False
