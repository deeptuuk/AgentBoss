"""Nostr cryptographic primitives: Bech32, secp256k1, Schnorr."""

import hashlib
import secrets

import secp256k1

# ── Bech32 encoding/decoding ──────────────────────────────────────────

_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_CHARSET_MAP = {c: i for i, c in enumerate(_CHARSET)}
_GENERATOR = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]


def _polymod(values: list[int]) -> int:
    chk = 1
    for val in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ val
        for i in range(5):
            chk ^= _GENERATOR[i] if (top >> i) & 1 else 0
    return chk


def _hrp_expand(hrp: str) -> list[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _convert_bits(data: bytes, from_bits: int, to_bits: int, pad: bool = True) -> list[int]:
    acc = 0
    bits = 0
    result: list[int] = []
    max_val = (1 << to_bits) - 1
    for val in data:
        acc = (acc << from_bits) | val
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            result.append((acc >> bits) & max_val)
    if pad and bits:
        result.append((acc << (to_bits - bits)) & max_val)
    return result


def _bech32_encode(hrp: str, data: bytes) -> str:
    values = _convert_bits(data, 8, 5)
    polymod = _polymod(_hrp_expand(hrp) + values + [0] * 6) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(_CHARSET[v] for v in values + checksum)


def _bech32_decode(bech: str) -> tuple[str, bytes]:
    bech = bech.lower()
    pos = bech.rfind("1")
    if pos < 1 or pos + 7 > len(bech):
        raise ValueError("invalid bech32 string")
    hrp = bech[:pos]
    try:
        data = [_CHARSET_MAP[c] for c in bech[pos + 1 :]]
    except KeyError:
        raise ValueError("invalid bech32 character")
    if _polymod(_hrp_expand(hrp) + data) != 1:
        raise ValueError("invalid bech32 checksum")
    return hrp, bytes(_convert_bits(data[:-6], 5, 8, pad=False))


def to_npub(hex_pubkey: str) -> str:
    return _bech32_encode("npub", bytes.fromhex(hex_pubkey))


def to_nsec(hex_privkey: str) -> str:
    return _bech32_encode("nsec", bytes.fromhex(hex_privkey))


def npub_to_hex(npub: str) -> str:
    hrp, data = _bech32_decode(npub)
    if hrp != "npub":
        raise ValueError("not an npub")
    return data.hex()


def nsec_to_hex(nsec: str) -> str:
    hrp, data = _bech32_decode(nsec)
    if hrp != "nsec":
        raise ValueError("not an nsec")
    return data.hex()


# ── secp256k1 key generation & signing ────────────────────────────────


def gen_keys() -> tuple[str, str]:
    priv_bytes = secrets.token_bytes(32)
    pub_bytes = secp256k1.PrivateKey(priv_bytes).pubkey.serialize()[1:]
    return priv_bytes.hex(), pub_bytes.hex()


def derive_pub(hex_privkey: str) -> str:
    return secp256k1.PrivateKey(bytes.fromhex(hex_privkey)).pubkey.serialize()[1:].hex()


def schnorr_sign(event_id_hex: str, hex_privkey: str) -> str:
    return secp256k1.PrivateKey(bytes.fromhex(hex_privkey)).schnorr_sign(
        bytes.fromhex(event_id_hex), None, raw=True
    ).hex()
