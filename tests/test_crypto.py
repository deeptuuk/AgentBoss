import pytest
from shared.crypto import (
    gen_keys, derive_pub, to_npub, to_nsec,
    npub_to_hex, nsec_to_hex, schnorr_sign,
)


class TestBech32:
    def test_to_npub_roundtrip(self):
        """hex -> npub -> hex should be identity"""
        hex_pub = "a" * 64
        npub = to_npub(hex_pub)
        assert npub.startswith("npub1")
        assert npub_to_hex(npub) == hex_pub

    def test_to_nsec_roundtrip(self):
        hex_sec = "b" * 64
        nsec = to_nsec(hex_sec)
        assert nsec.startswith("nsec1")
        assert nsec_to_hex(nsec) == hex_sec

    def test_npub_to_hex_invalid_prefix(self):
        nsec = to_nsec("cc" * 32)
        with pytest.raises(ValueError, match="not an npub"):
            npub_to_hex(nsec)

    def test_nsec_to_hex_invalid_prefix(self):
        npub = to_npub("dd" * 32)
        with pytest.raises(ValueError, match="not an nsec"):
            nsec_to_hex(npub)


class TestKeyGeneration:
    def test_gen_keys_returns_hex_pair(self):
        priv, pub = gen_keys()
        assert len(priv) == 64
        assert len(pub) == 64
        assert all(c in "0123456789abcdef" for c in priv)
        assert all(c in "0123456789abcdef" for c in pub)

    def test_gen_keys_unique(self):
        k1 = gen_keys()
        k2 = gen_keys()
        assert k1[0] != k2[0]

    def test_derive_pub_matches_gen(self):
        priv, pub = gen_keys()
        assert derive_pub(priv) == pub


class TestSchnorr:
    def test_schnorr_sign_produces_valid_hex(self):
        priv, pub = gen_keys()
        msg = "aa" * 32
        sig = schnorr_sign(msg, priv)
        assert len(sig) == 128
        assert all(c in "0123456789abcdef" for c in sig)

    def test_schnorr_sign_deterministic_for_same_input(self):
        priv, _ = gen_keys()
        msg = "bb" * 32
        sig1 = schnorr_sign(msg, priv)
        sig2 = schnorr_sign(msg, priv)
        # Schnorr with same aux_rand=None should be same
        assert sig1 == sig2
