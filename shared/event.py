"""Nostr event construction and verification."""

import hashlib
import json
import time

import secp256k1

from shared.crypto import schnorr_sign


def compute_event_id(event: dict) -> str:
    serialized = json.dumps(
        [
            0,
            event["pubkey"],
            event["created_at"],
            event["kind"],
            event["tags"],
            event["content"],
        ],
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(serialized.encode()).hexdigest()


def verify_event_id(event: dict) -> bool:
    return compute_event_id(event) == event.get("id")


def verify_event_sig(event: dict) -> bool:
    try:
        x_coord = bytes.fromhex(event["pubkey"])
        msg = bytes.fromhex(event["id"])
        sig = bytes.fromhex(event["sig"])
        # Try both parity bytes (0x02 = even y, 0x03 = odd y)
        for parity in (0x02, 0x03):
            try:
                pub = secp256k1.PublicKey(bytes([parity]) + x_coord, raw=True)
                if pub.schnorr_verify(msg, sig, None, raw=True):
                    return True
            except Exception:
                continue
        return False
    except Exception:
        return False


def build_event(
    kind: int,
    content: str,
    privkey: str,
    pubkey: str,
    tags: list[list[str]] | None = None,
    created_at: int | None = None,
) -> dict:
    event = {
        "pubkey": pubkey,
        "created_at": created_at or int(time.time()),
        "kind": kind,
        "tags": tags or [],
        "content": content,
    }
    event["id"] = compute_event_id(event)
    event["sig"] = schnorr_sign(event["id"], privkey)
    return event
