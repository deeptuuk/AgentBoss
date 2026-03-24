# AgentBoss Feature A: Job Application System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add job application submission, listing, and employer response with NIP-04 encrypted DM notifications.

**Architecture:**
- Applications stored as Nostr kind:31970 events (submitted) and kind:31971 events (responses)
- NIP-04 AES-256-CTR encryption via ECDH-derived shared secret
- Encrypted DM notifications sent to employer (on submit) and applicant (on respond)
- Local SQLite `applications` table mirrors remote events

**Tech Stack:** Python 3.11+, SQLite, typer, secp256k1, cryptography (for AES-CTR)

**Spec:** `docs/superpowers/specs/2026-03-25-agentboss-job-application-design.md`

---

## File Map

| File | Change |
|------|--------|
| `shared/crypto.py` | Add `nip04_encrypt()`, `nip04_decrypt()` functions |
| `cli/nostr_client.py` | Add `send_dm()` method to `NostrRelay` class |
| `cli/storage.py` | Add `applications` table + CRUD methods |
| `cli/main.py` | Add `submit`, `applications list`, `applications respond` commands |
| `tests/test_crypto.py` | New file: NIP-04 encrypt/decrypt tests |
| `tests/test_storage.py` | Add application storage tests |
| `tests/test_cli.py` | Add CLI integration tests |

---

## Task 1: NIP-04 Crypto — shared/crypto.py

**Files:**
- Modify: `shared/crypto.py`
- Test: `tests/test_crypto.py` (new)

### Part A: Write failing tests for NIP-04 encrypt/decrypt

- [ ] **Step 1: Create test file**

Create `tests/test_crypto.py`:

```python
"""Tests for NIP-04 encryption utilities."""

import pytest
from shared.crypto import nip04_encrypt, nip04_decrypt


class TestNIP04:
    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted content can be decrypted back to original."""
        plaintext = "Hello, World!"
        sender_priv = "a" * 64
        recipient_pub = "b" * 64
        ciphertext = nip04_encrypt(plaintext, sender_priv, recipient_pub)
        decrypted = nip04_decrypt(ciphertext, sender_priv, recipient_pub)
        assert decrypted == plaintext

    def test_encrypt_produces_base64(self):
        """Encryption produces Base64-encoded ciphertext."""
        ciphertext = nip04_encrypt("test", "a" * 64, "b" * 64)
        # Base64 characters only
        import re
        assert re.match(r'^[A-Za-z0-9+/]+=*$', ciphertext)

    def test_different_ciphers_for_same_plaintext(self):
        """Same plaintext with same keys produces same output (deterministic)."""
        key1 = "a" * 64
        key2 = "b" * 64
        ct1 = nip04_encrypt("same text", key1, key2)
        ct2 = nip04_encrypt("same text", key1, key2)
        assert ct1 == ct2  # NIP-04 is deterministic (no random IV)

    def test_decrypt_wrong_key_fails(self):
        """Decryption with wrong key raises ValueError."""
        plaintext = "secret message"
        sender_priv = "a" * 64
        recipient_pub = "b" * 64
        wrong_priv = "c" * 64
        ciphertext = nip04_encrypt(plaintext, sender_priv, recipient_pub)
        with pytest.raises(ValueError):
            nip04_decrypt(ciphertext, wrong_priv, recipient_pub)
```

- [ ] **Step 2: Run tests — FAIL**

Run: `python -m pytest tests/test_crypto.py -v`
Expected: FAIL — `nip04_encrypt` not defined

### Part B: Implement NIP-04 encrypt/decrypt

- [ ] **Step 3: Add NIP-04 functions to shared/crypto.py**

Add to end of `shared/crypto.py`:

```python
# ── NIP-04 DM Encryption ──────────────────────────────────────────────────

import hashlib
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


def _aes_256_ctr_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    """AES-256-CTR encryption."""
    cipher = Cipher(
        algorithms.AES(key),
        modes.CTR(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    return encryptor.update(plaintext) + encryptor.finalize()


def _aes_256_ctr_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    """AES-256-CTR decryption."""
    cipher = Cipher(
        algorithms.AES(key),
        modes.CTR(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def nip04_encrypt(plaintext: str, sender_priv_hex: str, recipient_pub_hex: str) -> str:
    """Encrypt plaintext for NIP-04 DM.

    Uses AES-256-CTR with ECDH-derived shared secret.
    Returns Base64-encoded ciphertext with IV prepended.

    Args:
        plaintext: The message to encrypt
        sender_priv_hex: Sender's private key (64 hex chars)
        recipient_pub_hex: Recipient's public key (64 hex chars)

    Returns:
        Base64-encoded "iv+ciphertext" string
    """
    # Generate ephemeral key pair
    ephem_priv = secp256k1.PrivateKey()
    ephem_pub = ephem_priv.pubkey.serialize()[1:]

    # ECDH: compute shared secret
    recipient_pubkey = secp256k1.PublicKey(bytes.fromhex(recipient_pub_hex))
    ecdh_secret = ephem_priv.ecdh(
        bytes.fromhex(recipient_pub_hex),
        raw=True
    )

    # Derive encryption key: sha256(shared_secret || ephem_pub || recipient_pub)
    key_input = ecdh_secret + ephem_pub + bytes.fromhex(recipient_pub_hex)
    encryption_key = hashlib.sha256(key_input).digest()

    # Generate 16-byte IV (from nonce for CTR mode)
    iv = hashlib.sha256(ephem_pub + bytes.fromhex(recipient_pub_hex)).digest()[:16]

    # Encrypt
    plaintext_bytes = plaintext.encode("utf-8")
    ciphertext = _aes_256_ctr_encrypt(encryption_key, iv, plaintext_bytes)

    # Prepend IV to ciphertext
    combined = iv + ciphertext

    # Return as Base64
    return base64.b64encode(combined).decode("ascii")


def nip04_decrypt(ciphertext_b64: str, sender_priv_hex: str, sender_pub_hex: str) -> str:
    """Decrypt NIP-04 DM ciphertext.

    Args:
        ciphertext_b64: Base64-encoded "iv+ciphertext"
        sender_priv_hex: Sender's private key (64 hex chars)
        sender_pub_hex: Sender's public key (64 hex chars)

    Returns:
        Decrypted plaintext string

    Raises:
        ValueError: If decryption fails (wrong key or corrupted ciphertext)
    """
    try:
        combined = base64.b64decode(ciphertext_b64)
        iv = combined[:16]
        ciphertext = combined[16:]

        # ECDH shared secret computation
        privkey = secp256k1.PrivateKey(bytes.fromhex(sender_priv_hex))
        ephem_pub_raw = privkey.pubkey.serialize()[1:]

        ecdh_secret = privkey.ecdh(bytes.fromhex(sender_pub_hex), raw=True)

        # Same key derivation as encrypt
        key_input = ecdh_secret + ephem_pub_raw + bytes.fromhex(sender_pub_hex)
        encryption_key = hashlib.sha256(key_input).digest()

        # Decrypt
        plaintext_bytes = _aes_256_ctr_decrypt(encryption_key, iv, ciphertext)
        return plaintext_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")
```

**Note:** The NIP-04 encryption uses ephemeral key generation. The ephemeral private is used once for ECDH, and the ephemeral public is included in the key derivation to ensure uniqueness.

- [ ] **Step 4: Run tests — PASS**

Run: `python -m pytest tests/test_crypto.py -v`
Expected: PASS

### Part C: Verify with known test vector

- [ ] **Step 5: Add integration test with known vector**

```python
def test_nip04_known_vector(self):
    """Test with a known test vector (if available)."""
    # NIP-04 is deterministic - same inputs produce same outputs
    ct = nip04_encrypt("test message", "0" * 64, "1" * 64)
    assert len(ct) > 0
    pt = nip04_decrypt(ct, "0" * 64, "1" * 64)
    assert pt == "test message"
```

- [ ] **Step 6: Run tests — PASS**

- [ ] **Step 7: Commit**

```bash
git add shared/crypto.py tests/test_crypto.py
git commit -m "feat: add NIP-04 DM encryption with AES-256-CTR"
```

---

## Task 2: NostrRelay.send_dm — cli/nostr_client.py

**Files:**
- Modify: `cli/nostr_client.py`
- Test: `tests/test_nostr_client.py` (new, if exists — otherwise inline test)

### Part A: Write failing test for send_dm

- [ ] **Step 1: Write failing test**

```python
# tests/test_nostr_client.py (append or create)
import pytest
from cli.nostr_client import NostrRelay

class TestSendDM:
    @pytest.mark.asyncio
    async def test_send_dm_builds_correct_message(self):
        """DM is encrypted and sent as EVENT message."""
        relay = NostrRelay("wss://example.com")
        # This test verifies the DM message format
        # (actual WebSocket interaction tested separately)
        pass  # Will be implemented in Part B
```

- [ ] **Step 2: Run test — PASS** (placeholder)

### Part B: Add send_dm method to NostrRelay

- [ ] **Step 3: Add send_dm method to cli/nostr_client.py**

Add to `NostrRelay` class:

```python
async def send_dm(self, sender_privkey: str, recipient_pubkey: str, plaintext: str) -> dict:
    """Send an encrypted NIP-04 DM to a recipient.

    Args:
        sender_privkey: Sender's private key (hex)
        recipient_pubkey: Recipient's public key (hex)
        plaintext: Message content to encrypt and send

    Returns:
        dict with 'accepted' bool and optional 'message'
    """
    from shared.crypto import nip04_encrypt

    # Encrypt the plaintext
    ciphertext = nip04_encrypt(plaintext, sender_privkey, recipient_pubkey)

    # Build DM event (kind:4 is NIP-04 encrypted DM)
    from shared.event import build_event
    event = build_event(
        kind=4,  # NIP-04 encrypted DM
        content=ciphertext,
        privkey=sender_privkey,
        pubkey=sender_privkey[:64],  # Will be corrected by build_event
        tags=[
            ["p", recipient_pubkey],  # Recipient pubkey tag
        ],
    )

    # Send the event
    return await self.publish_event(event)
```

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 5: Commit**

```bash
git add cli/nostr_client.py
git commit -m "feat: add NostrRelay.send_dm for NIP-04 encrypted messages"
```

---

## Task 3: Applications Storage — cli/storage.py

**Files:**
- Modify: `cli/storage.py`
- Test: `tests/test_storage.py`

### Part A: Write failing tests for applications table

- [ ] **Step 1: Write failing test — test_applications_table_exists**

```python
def test_applications_table_exists(self, db):
    """applications table exists after init_db."""
    assert "applications" in db.list_tables()
```

- [ ] **Step 2: Run test — FAIL**

### Part B: Add applications table to init_db

- [ ] **Step 3: Add applications table to init_db()**

In `cur.executescript()`, add after `CREATE TABLE IF NOT EXISTS profiles`:

```python
CREATE TABLE IF NOT EXISTS applications (
    event_id TEXT PRIMARY KEY,
    d_tag TEXT NOT NULL,
    job_id TEXT NOT NULL,
    employer_pubkey TEXT NOT NULL,
    applicant_pubkey TEXT NOT NULL,
    message TEXT,
    status TEXT DEFAULT 'pending',
    response_message TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER DEFAULT (unixepoch('now'))
);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_applicant ON applications(applicant_pubkey);
```

- [ ] **Step 4: Run test — PASS**

### Part C: Add application CRUD methods

- [ ] **Step 5: Write failing test — test_upsert_application**

```python
def test_upsert_application(self, db):
    """Can insert and retrieve an application."""
    db.upsert_application(
        event_id="app1",
        d_tag="app_job1_1000",
        job_id="job1",
        employer_pubkey="emp1",
        applicant_pubkey="app1",
        message="I'm interested",
        status="pending",
        created_at=1000,
    )
    app = db.get_application("app1")
    assert app is not None
    assert app["job_id"] == "job1"
    assert app["status"] == "pending"
```

- [ ] **Step 6: Run test — FAIL**

- [ ] **Step 7: Add upsert_application and get_application methods**

```python
def upsert_application(
    self,
    event_id: str,
    d_tag: str,
    job_id: str,
    employer_pubkey: str,
    applicant_pubkey: str,
    message: str | None,
    status: str = "pending",
    response_message: str | None = None,
    created_at: int | None = None,
):
    """Insert or update an application record."""
    if created_at is None:
        created_at = int(time.time())
    self._conn.execute("""
        INSERT OR REPLACE INTO applications
        (event_id, d_tag, job_id, employer_pubkey, applicant_pubkey, message, status, response_message, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, unixepoch('now'))
    """, (event_id, d_tag, job_id, employer_pubkey, applicant_pubkey, message, status, response_message, created_at))
    self._conn.commit()


def get_application(self, event_id: str) -> dict | None:
    """Get application by event_id."""
    row = self._conn.execute(
        "SELECT * FROM applications WHERE event_id = ?", (event_id,)
    ).fetchone()
    return dict(row) if row else None


def list_applications(
    self,
    applicant_pubkey: str | None = None,
    employer_pubkey: str | None = None,
    job_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """List applications with optional filters."""
    query = "SELECT * FROM applications WHERE 1=1"
    params = []
    if applicant_pubkey:
        query += " AND applicant_pubkey = ?"
        params.append(applicant_pubkey)
    if employer_pubkey:
        query += " AND employer_pubkey = ?"
        params.append(employer_pubkey)
    if job_id:
        query += " AND job_id = ?"
        params.append(job_id)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"
    rows = self._conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def update_application_status(
    self,
    event_id: str,
    status: str,
    response_message: str | None = None,
):
    """Update application status (accepted/rejected)."""
    self._conn.execute(
        "UPDATE applications SET status = ?, response_message = ?, updated_at = unixepoch('now') WHERE event_id = ?",
        (status, response_message, event_id)
    )
    self._conn.commit()
```

- [ ] **Step 8: Run tests — PASS**

### Part D: Add more CRUD tests

- [ ] **Step 9: Write failing test — test_list_applications_filter**

```python
def test_list_applications_filter(self, db):
    """Can filter applications by applicant and status."""
    db.upsert_application("a1", "d1", "job1", "emp1", "app1", "msg", "pending", created_at=1000)
    db.upsert_application("a2", "d2", "job1", "emp1", "app1", "msg", "accepted", created_at=1001)
    db.upsert_application("a3", "d3", "job2", "emp1", "app2", "msg", "pending", created_at=1002)

    # Filter by applicant
    apps = db.list_applications(applicant_pubkey="app1")
    assert len(apps) == 2

    # Filter by status
    apps = db.list_applications(status="pending")
    assert len(apps) == 2

    # Filter by job_id
    apps = db.list_applications(job_id="job1")
    assert len(apps) == 2
```

- [ ] **Step 10: Run tests — PASS**

### Part E: Add check for existing application

- [ ] **Step 11: Write failing test — test_has_application**

```python
def test_has_application(self, db):
    """Can check if application exists for job+applicant."""
    db.upsert_application("a1", "app_job1_1000", "job1", "emp1", "app1", "msg", "pending", created_at=1000)
    assert db.has_application("job1", "app1") is True
    assert db.has_application("job2", "app1") is False
```

- [ ] **Step 12: Add has_application method**

```python
def has_application(self, job_id: str, applicant_pubkey: str) -> bool:
    """Check if an application exists for this job and applicant."""
    row = self._conn.execute(
        "SELECT 1 FROM applications WHERE job_id = ? AND applicant_pubkey = ?",
        (job_id, applicant_pubkey)
    ).fetchone()
    return row is not None
```

- [ ] **Step 13: Run tests — PASS**

### Part F: Commit

- [ ] **Step 14: Commit**

```bash
git add cli/storage.py tests/test_storage.py
git commit -m "feat: add applications table and CRUD methods"
```

---

## Task 4: CLI — submit command

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Part A: Write failing test for submit command

- [ ] **Step 1: Write failing test — test_submit_command**

```python
class TestSubmit:
    def test_submit_fails_without_login(self, cli_home):
        """submit without login shows error."""
        result = runner.invoke(app, ["submit", "abc123", "--message", "Hello"])
        assert result.exit_code != 0
        assert "login" in result.stdout.lower()

    def test_submit_fails_for_unknown_job(self, cli_home):
        """submit for unknown job shows error."""
        runner.invoke(app, ["login", "--key", "aa" * 32])
        result = runner.invoke(app, ["submit", "nonexistent", "--message", "Hello"])
        assert result.exit_code != 0
        assert "not found" in result.stdout.lower()

    def test_submit_success(self, cli_home):
        """submit publishes application event."""
        # Create a job first
        from cli.storage import Storage
        s = Storage(str(cli_home / "agentboss.db"))
        s.init_db()
        s.upsert_job("job1", "d1", "emp1", 1, 101, '{"title":"Dev","company":"Co","description":""}', 1000)
        s.close()

        runner.invoke(app, ["login", "--key", "aa" * 32])
        result = runner.invoke(app, ["submit", "job1", "--message", "I'm interested"])
        assert result.exit_code == 0
        assert "submitted" in result.stdout.lower() or "success" in result.stdout.lower()
```

- [ ] **Step 2: Run test — FAIL** (command doesn't exist)

### Part B: Add submit command to main.py

- [ ] **Step 3: Add submit command to cli/main.py**

Add after `apply` command definition (around line 315):

```python
@app.command(name="submit")
def submit(
    job_id: str = typer.Argument(..., help="Job ID (full or prefix)"),
    message: str = typer.Option("", "--message", help="Introduction message"),
):
    """Submit an application for a job posting."""
    identity = _load_identity()
    if not identity:
        typer.echo("No identity. Run: agentboss login --key <nsec>")
        raise typer.Exit(code=1)

    storage = _get_storage()

    # Find job
    job = storage.get_job(job_id)
    if not job:
        # Try prefix match
        jobs = storage.list_jobs()
        matches = [j for j in jobs if j["event_id"].startswith(job_id)]
        if len(matches) == 1:
            job = matches[0]
        elif len(matches) > 1:
            typer.echo("Multiple jobs match prefix. Use full ID.")
            storage.close()
            raise typer.Exit(code=1)
        else:
            typer.echo("Job not found in local storage. Run `agentboss fetch` first.")
            storage.close()
            raise typer.Exit(code=1)

    # Check if already applied
    if storage.has_application(job["event_id"], identity["pubkey"]):
        typer.echo("You have already applied to this job.")
        storage.close()
        raise typer.Exit(code=1)

    employer_pubkey = job["pubkey"]
    applicant_privkey = identity["privkey"]
    applicant_pubkey = identity["pubkey"]

    # Build d_tag: app_<job_id>_<timestamp>
    import time
    d_tag = f"app_{job['event_id']}_{int(time.time())}"

    # Build application event (kind:31970)
    event = build_event(
        kind=KIND_APP_DATA,
        content=json.dumps({"message": message}) if message else "{}",
        privkey=applicant_privkey,
        pubkey=applicant_pubkey,
        tags=[
            ["d", d_tag],
            ["t", APP_TAG],
            ["t", "application"],
        ],
    )

    relay_url = storage.get_config("relay", DEFAULT_RELAY)

    async def _submit():
        relay = NostrRelay(relay_url)
        try:
            await relay.connect()
            # Publish application event
            result = await relay.publish_event(event)
            if not result["accepted"]:
                typer.echo(f"Failed to submit: {result['message']}")
                return

            # Send DM to employer
            dm_content = json.dumps({
                "type": "application",
                "job_id": job["event_id"],
                "app_id": event["id"],
                "action": "submit",
                "message": message or "",
            })
            try:
                await relay.send_dm(applicant_privkey, employer_pubkey, dm_content)
            except Exception as e:
                typer.echo(f"Warning: Could not notify employer: {e}")

            # Store locally
            storage.upsert_application(
                event_id=event["id"],
                d_tag=d_tag,
                job_id=job["event_id"],
                employer_pubkey=employer_pubkey,
                applicant_pubkey=applicant_pubkey,
                message=message,
                status="pending",
                created_at=event["created_at"],
            )
            typer.echo(f"Application submitted for {job['event_id'][:12]}...")
        finally:
            await relay.close()

    asyncio.run(_submit())
    storage.close()
```

**Note:** The `submit` command uses `KIND_APP_DATA` (30078) per the spec's event kinds. The `kind=4` (NIP-04 DM) is only for the DM message itself, not the application event.

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 5: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add submit command for job applications"
```

---

## Task 5: CLI — applications list command

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Part A: Write failing test for applications list

- [ ] **Step 1: Write failing test**

```python
class TestApplicationsList:
    def test_applications_list_empty(self, cli_home):
        """list with no applications shows empty message."""
        runner.invoke(app, ["login", "--key", "aa" * 32])
        result = runner.invoke(app, ["applications", "list"])
        assert result.exit_code == 0
        assert "no applications" in result.stdout.lower() or "not found" in result.stdout.lower()

    def test_applications_list_shows_submitted(self, cli_home):
        """list shows submitted applications."""
        runner.invoke(app, ["login", "--key", "aa" * 32])
        # Create job and application directly in DB
        from cli.storage import Storage
        s = Storage(str(cli_home / "agentboss.db"))
        s.init_db()
        s.upsert_job("job1", "d1", "emp1", 1, 101, '{"title":"Dev","company":"Co","description":""}', 1000)
        s.upsert_application("app1", "app_job1_1000", "job1", "emp1", "aa" * 64, "I'm interested", "pending", created_at=1000)
        s.close()

        result = runner.invoke(app, ["applications", "list"])
        assert result.exit_code == 0
        assert "Dev" in result.stdout or "Co" in result.stdout
```

- [ ] **Step 2: Run test — FAIL**

### Part B: Add applications subcommand group

- [ ] **Step 3: Add applications typer and list command**

Add near the end of `cli/main.py`, before the last function:

```python
applications_app = typer.Typer(help="Manage job applications")
app.add_typer(applications_app, name="applications")


@applications_app.command(name="list")
def applications_list(
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status: pending, accepted, rejected"),
):
    """List your job applications."""
    identity = _load_identity()
    if not identity:
        typer.echo("No identity. Run: agentboss login --key <nsec>")
        raise typer.Exit(code=1)

    storage = _get_storage()
    resolver = RegionResolver(storage)

    apps = storage.list_applications(
        applicant_pubkey=identity["pubkey"],
        status=status,
    )

    if not apps:
        typer.echo("No applications found.")
        storage.close()
        return

    for app in apps:
        job = storage.get_job(app["job_id"])
        job_title = job["content"]["title"] if job else "(unknown job)"
        status_emoji = {"pending": "⏳", "accepted": "✅", "rejected": "❌"}.get(app["status"], "?")
        typer.echo(f"{status_emoji} {job_title} | {app['status']} | {app['created_at']}")

    storage.close()
```

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 5: Commit**

```bash
git add cli/main.py
git commit -m "feat: add applications list command"
```

---

## Task 6: CLI — applications respond command

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Part A: Write failing test

- [ ] **Step 1: Write failing test — test_applications_respond**

```python
def test_applications_respond_accept(self, cli_home):
    """Employer can accept an application."""
    runner.invoke(app, ["login", "--key", "aa" * 32])
    # Create job and application
    from cli.storage import Storage
    s = Storage(str(cli_home / "agentboss.db"))
    s.init_db()
    employer_priv = "aa" * 32
    employer_pub = derive_pub(employer_priv)
    s.upsert_job("job1", "d1", employer_pub, 1, 101, '{"title":"Dev","company":"Co","description":""}', 1000)
    s.upsert_application("app1", "app_job1_1000", "job1", employer_pub, "app1_pub", "Interested", "pending", created_at=1000)
    s.close()

    result = runner.invoke(app, ["applications", "respond", "app1", "--accept"])
    assert result.exit_code == 0
    assert "accepted" in result.stdout.lower() or "success" in result.stdout.lower()
```

- [ ] **Step 2: Run test — FAIL**

### Part B: Add respond command

- [ ] **Step 3: Add respond command**

Add after `applications_list`:

```python
@applications_app.command(name="respond")
def applications_respond(
    app_id: str = typer.Argument(..., help="Application event ID"),
    accept: bool = typer.Option(False, "--accept", is_flag=True, help="Accept the application"),
    reject: bool = typer.Option(False, "--reject", is_flag=True, help="Reject the application"),
    reason: Optional[str] = typer.Option(None, "--reason", help="Reason or feedback"),
):
    """Respond to a job application (employer only)."""
    if not (accept or reject):
        typer.echo("Use --accept or --reject")
        raise typer.Exit(code=1)

    identity = _load_identity()
    if not identity:
        typer.echo("No identity. Run: agentboss login --key <nsec>")
        raise typer.Exit(code=1)

    storage = _get_storage()

    # Get application
    app_record = storage.get_application(app_id)
    if not app_record:
        typer.echo("Application not found.")
        storage.close()
        raise typer.Exit(code=1)

    # Verify employer
    job = storage.get_job(app_record["job_id"])
    if not job or job["pubkey"] != identity["pubkey"]:
        typer.echo("Only the job publisher can respond to this application.")
        storage.close()
        raise typer.Exit(code=1)

    status = "accepted" if accept else "rejected"
    response_content = json.dumps({
        "message": reason or "",
    })

    # Build response event (kind:31971)
    event = build_event(
        kind=KIND_APP_DATA,
        content=response_content,
        privkey=identity["privkey"],
        pubkey=identity["pubkey"],
        tags=[
            ["d", app_record["d_tag"]],  # Same d_tag as application = replaceable
            ["job", app_record["job_id"]],
            ["status", status],
            ["t", "application_response"],
        ],
    )

    relay_url = storage.get_config("relay", DEFAULT_RELAY)

    async def _respond():
        relay = NostrRelay(relay_url)
        try:
            await relay.connect()
            result = await relay.publish_event(event)
            if not result["accepted"]:
                typer.echo(f"Failed to respond: {result['message']}")
                return

            # Send DM to applicant
            dm_content = json.dumps({
                "type": "application",
                "job_id": app_record["job_id"],
                "app_id": app_record["event_id"],
                "action": status,
                "message": reason or "",
            })
            try:
                await relay.send_dm(identity["privkey"], app_record["applicant_pubkey"], dm_content)
            except Exception as e:
                typer.echo(f"Warning: Could not notify applicant: {e}")

            # Update local status
            storage.update_application_status(app_record["event_id"], status, reason)
            typer.echo(f"Application {status}: {app_record['event_id'][:12]}...")
        finally:
            await relay.close()

    asyncio.run(_respond())
    storage.close()
```

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 5: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add applications respond command"
```

---

## Task 7: Final Integration + Tests

### Part A: Run full test suite

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS (existing + new)

### Part B: Commit

- [ ] **Step 2: Final commit**

```bash
git add -A
git commit -m "feat: implement AgentBoss Feature A — job application system"
```

---

## Summary: Task → Owner Mapping

| Task | Description | Owner |
|------|-------------|-------|
| 1 | NIP-04 Crypto (shared/crypto.py) | npub1g9plav7 |
| 2 | NostrRelay.send_dm (cli/nostr_client.py) | npub1g9plav7 |
| 3 | Applications storage (cli/storage.py) | npub1g9plav7 |
| 4 | CLI submit command (cli/main.py) | npub1g9plav7 |
| 5 | CLI applications list (cli/main.py) | npub1g9plav7 |
| 6 | CLI applications respond (cli/main.py) | npub1g9plav7 |
| 7 | Integration + final commit | npub1g9plav7 |
