"""Registration, authentication, and key management."""

import base64
import hashlib
import os

import bcrypt

from shared.crypto import gen_keys, to_npub, to_nsec, npub_to_hex


# ── Password hashing ──

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


# ── nsec encryption using ChaCha20-Poly1305 (NIP-44 inspired) ──

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import secrets


def encrypt_nsec(nsec: str, server_key: str) -> str:
    """Encrypt nsec with server key using ChaCha20."""
    key_bytes = hashlib.sha256(server_key.encode()).digest()[:32]
    nonce = secrets.token_bytes(16)  # ChaCha20 requires 16-byte nonce
    cipher = Cipher(algorithms.ChaCha20(key_bytes, nonce), None, backend=default_backend())
    encryptor = cipher.encryptor()
    nsec_bytes = nsec.encode()
    encrypted = encryptor.update(nsec_bytes) + encryptor.finalize()
    # Prepend nonce for use in decryption
    return base64.b64encode(nonce + encrypted).decode()


def decrypt_nsec(encrypted_b64: str, server_key: str) -> str:
    """Decrypt nsec."""
    key_bytes = hashlib.sha256(server_key.encode()).digest()[:32]
    raw = base64.b64decode(encrypted_b64)
    nonce, ciphertext = raw[:16], raw[16:]  # ChaCha20 uses 16-byte nonce
    cipher = Cipher(algorithms.ChaCha20(key_bytes, nonce), None, backend=default_backend())
    decryptor = cipher.decryptor()
    return (decryptor.update(ciphertext) + decryptor.finalize()).decode()


# ── Registration ──

def register_user(
    db,
    username: str,
    email: str,
    password: str,
    whitelist_path: str,
    server_key: str = "agentboss-default-key-change-in-prod",
) -> dict:
    """Register a new user: generate keypair, hash password, update whitelist."""
    privkey, pubkey = gen_keys()
    npub = to_npub(pubkey)
    nsec = to_nsec(privkey)
    hex_pubkey = pubkey  # already hex from gen_keys

    pw_hash = hash_password(password)
    nsec_enc = encrypt_nsec(nsec, server_key)

    db.create_user(
        username=username,
        email=email,
        password_hash=pw_hash,
        npub=npub,
        nsec_encrypted=nsec_enc,
    )

    # Append hex pubkey to whitelist
    with open(whitelist_path, "a") as f:
        f.write(hex_pubkey + "\n")

    return {"npub": npub, "nsec": nsec, "pubkey": hex_pubkey}
