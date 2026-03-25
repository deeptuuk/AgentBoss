# Relay Federation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable job postings to span multiple Nostr relays via federations identified by relay lists. Users join via invite codes and can publish/fetch jobs across all federation relays.

**Architecture:** Federation is a named group of relays identified by relay list metadata events (kind:31990) published by the federation owner. Clients join by importing invite codes, fetching the relay list from the owner's npub, and storing federation config locally. Job writes go to ALL federation relays simultaneously; job reads parallel-query all relays and merge-deduplicate.

**Tech Stack:** Python 3.11+, SQLite, typer, aiohttp, secp256k1

---

## File Structure

| File | Change | Responsibility |
|------|--------|----------------|
| `shared/constants.py` | Modify | Add `KIND_FEDERATION = 31990` |
| `cli/storage.py` | Modify | Add `federations` table + CRUD methods + `jobs.federation_id` column |
| `cli/nostr_client.py` | Modify | Add `fetch_events_from_relays()` parallel query + `_merge_events()` |
| `cli/main.py` | Modify | Add `federation` subcommand group + join/create/leave/list |
| `tests/test_storage.py` | Modify | Add federation storage tests |
| `tests/test_cli.py` | Modify | Add federation CLI tests |
| `tests/test_nostr_client.py` | Modify | Add multi-relay fetch + merge tests |

---

## Task 1: Constants + Storage Schema

**Files:**
- Modify: `shared/constants.py`
- Modify: `cli/storage.py`
- Test: `tests/test_storage.py`

### Part A: Add constant

- [ ] **Step 1: Modify shared/constants.py**

```python
# Add after KIND_APP_DATA = 30078
KIND_FEDERATION = 31990
```

### Part B: Add failing test for federations storage

- [ ] **Step 2: Add TestFederations class to tests/test_storage.py**

```python
class TestFederations:
    def test_federations_table_exists(self, db):
        """federations table exists after init_db."""
        assert "federations" in db.list_tables()

    def test_upsert_and_get_federation(self, db):
        """Can insert and retrieve a federation."""
        db.upsert_federation(
            federation_id="abc123",
            name="TechJobs",
            relay_urls=["wss://relay1.example.com", "wss://relay2.example.com"],
            created_at=1000,
        )
        fed = db.get_federation("abc123")
        assert fed is not None
        assert fed["name"] == "TechJobs"
        assert fed["relay_urls"] == ["wss://relay1.example.com", "wss://relay2.example.com"]

    def test_list_federations(self, db):
        """Can list multiple federations."""
        db.upsert_federation("id1", "Fed1", ["r1"], created_at=1000)
        db.upsert_federation("id2", "Fed2", ["r2"], created_at=1001)
        feds = db.list_federations()
        assert len(feds) == 2
        # Most recent first
        assert feds[0]["federation_id"] == "id2"

    def test_delete_federation(self, db):
        """Can delete a federation."""
        db.upsert_federation("id1", "Fed1", ["r1"], created_at=1000)
        db.delete_federation("id1")
        assert db.get_federation("id1") is None
```

- [ ] **Step 3: Run test — FAIL**

Run: `pytest tests/test_storage.py::TestFederations -v`
Expected: FAIL (AttributeError: 'Storage' object has no attribute 'upsert_federation')

### Part C: Add storage implementation

- [ ] **Step 4: Modify cli/storage.py — add federations table to init_db()**

In `cur.executescript()`, after the `applications` table creation:

```python
CREATE TABLE IF NOT EXISTS federations (
    federation_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    relay_urls TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER DEFAULT (unixepoch('now'))
);
CREATE INDEX IF NOT EXISTS idx_federations_name ON federations(name);
```

- [ ] **Step 5: Modify cli/storage.py — add federation_id to jobs table**

After the `CREATE INDEX IF NOT EXISTS idx_applications_applicant`:

```python
ALTER TABLE jobs ADD COLUMN federation_id TEXT;
CREATE INDEX IF NOT EXISTS idx_jobs_federation ON jobs(federation_id);
```

Note: `ALTER TABLE ADD COLUMN` with `IF NOT EXISTS` is safe — runs as no-op on existing columns.

- [ ] **Step 6: Modify cli/storage.py — add federation CRUD methods**

Add after `has_application()`:

```python
def upsert_federation(
    self,
    federation_id: str,
    name: str,
    relay_urls: list[str],
    created_at: int | None = None,
):
    """Insert or update a federation."""
    if created_at is None:
        created_at = int(time.time())
    relay_urls_json = json.dumps(relay_urls)
    self._conn.execute(
        """INSERT OR REPLACE INTO federations
           (federation_id, name, relay_urls, created_at, updated_at)
           VALUES (?, ?, ?, ?, unixepoch('now'))""",
        (federation_id, name, relay_urls_json, created_at),
    )
    self._conn.commit()

def get_federation(self, federation_id: str) -> dict | None:
    """Get federation by ID (npub hex)."""
    row = self._conn.execute(
        "SELECT * FROM federations WHERE federation_id = ?", (federation_id,)
    ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["relay_urls"] = json.loads(result["relay_urls"])
    return result

def list_federations(self) -> list[dict]:
    """List all joined federations."""
    rows = self._conn.execute(
        "SELECT * FROM federations ORDER BY created_at DESC"
    ).fetchall()
    results = []
    for row in rows:
        result = dict(row)
        result["relay_urls"] = json.loads(result["relay_urls"])
        results.append(result)
    return results

def delete_federation(self, federation_id: str):
    """Remove a federation."""
    self._conn.execute("DELETE FROM federations WHERE federation_id = ?", (federation_id,))
    self._conn.commit()
```

### Part D: Verify tests pass

- [ ] **Step 7: Run tests — PASS**

Run: `pytest tests/test_storage.py::TestFederations -v`
Expected: PASS

### Part E: Add jobs.federation_id column test

- [ ] **Step 8: Add test_job_has_federation_id to TestJobs**

```python
def test_job_has_federation_id(self, db):
    """jobs table has federation_id column."""
    db.upsert_job("id1", "d1", "pub1", 1, 101, "{}", 1000)
    job = db.get_job("id1")
    assert "federation_id" in job
```

- [ ] **Step 9: Run test — PASS**

Run: `pytest tests/test_storage.py::TestJobs::test_job_has_federation_id -v`
Expected: PASS

### Part F: Commit

- [ ] **Step 10: Commit**

```bash
git add shared/constants.py cli/storage.py tests/test_storage.py
git commit -m "feat: add KIND_FEDERATION constant and federations storage"
```

---

## Task 2: Multi-Relay Fetch

**Files:**
- Modify: `cli/nostr_client.py`
- Test: `tests/test_nostr_client.py`

### Part A: Write failing test for _merge_events

- [ ] **Step 1: Add TestMergeEvents class to tests/test_nostr_client.py**

```python
def test_merge_events_deduplicates_by_id(self):
    """_merge_events removes duplicates by event_id, later overrides earlier."""
    events1 = [
        {"id": "abc", "created_at": 1000, "content": "v1"},
        {"id": "def", "created_at": 1002, "content": "v2"},
    ]
    events2 = [
        {"id": "abc", "created_at": 1000, "content": "v1"},  # duplicate
        {"id": "ghi", "created_at": 1001, "content": "v3"},
    ]
    result = _merge_events([events1, events2])
    ids = [e["id"] for e in result]
    assert set(ids) == {"abc", "def", "ghi"}
    # Should be sorted by created_at desc
    assert result[0]["id"] == "def"  # created_at:1002
    assert result[1]["id"] == "ghi"   # created_at:1001
    assert result[2]["id"] == "abc"   # created_at:1000

def test_merge_events_empty_lists(self):
    """_merge_events handles empty input."""
    result = _merge_events([])
    assert result == []
    result = _merge_events([[]])
    assert result == []
```

Note: `_merge_events` is a module-level helper function in `nostr_client.py`. The test should import it explicitly.

- [ ] **Step 2: Run test — FAIL**

Run: `pytest tests/test_nostr_client.py::TestMergeEvents -v`
Expected: FAIL (ImportError or NameError: _merge_events not defined)

### Part B: Implement _merge_events and fetch_events_from_relays

- [ ] **Step 3: Modify cli/nostr_client.py — add _merge_events and fetch_events_from_relays**

Add at the top-level of the module (not inside a class):

```python
def _merge_events(event_lists: list[list[dict]]) -> list[dict]:
    """Merge events from multiple relays, deduplicate by event_id.

    Later duplicates (same id) override earlier ones.
    Result sorted by created_at descending (most recent first).
    """
    by_id: dict[str, dict] = {}
    for events in event_lists:
        for event in events:
            by_id[event["id"]] = event
    merged = list(by_id.values())
    merged.sort(key=lambda e: e.get("created_at", 0), reverse=True)
    return merged


async def fetch_events_from_relays(
    relay_urls: list[str],
    kinds: list[int],
    tags: dict | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Parallel query to multiple relays, merge and deduplicate results.

    Args:
        relay_urls: List of relay WebSocket URLs
        kinds: Event kinds to subscribe to
        tags: NIP-01 filter tags
        limit: Max events per relay (optional)

    Returns:
        Deduplicated list of events from all relays, sorted by created_at desc
    """
    async def fetch_from_relay(url: str) -> list[dict]:
        relay = NostrRelay(url)
        events = []
        try:
            await relay.connect()
            await relay.subscribe("_multi", kinds, tags, limit)
            async for event in relay.receive_events("_multi"):
                events.append(event)
            await relay.unsubscribe("_multi")
        finally:
            await relay.close()
        return events

    results = await asyncio.gather(*[fetch_from_relay(url) for url in relay_urls])
    return _merge_events(list(results))
```

Note: `asyncio` is already imported at the top of `nostr_client.py`.

- [ ] **Step 4: Run merge tests — PASS**

Run: `pytest tests/test_nostr_client.py::TestMergeEvents -v`
Expected: PASS

- [ ] **Step 5: Run all nostr_client tests — PASS**

Run: `pytest tests/test_nostr_client.py -v`
Expected: All existing tests still pass

### Part C: Commit

- [ ] **Step 6: Commit**

```bash
git add cli/nostr_client.py tests/test_nostr_client.py
git commit -m "feat: add multi-relay parallel fetch with merge-deduplicate"
```

---

## Task 3: Federation Join CLI

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Part A: Write failing tests for federation join/list/leave

- [ ] **Step 1: Add TestFederationJoin class to tests/test_cli.py**

```python
class TestFederationJoin:
    def test_federation_join_requires_login(self, cli_home):
        """join without identity shows error."""
        result = runner.invoke(app, ["federation", "join", "federation:abc123:myfed"])
        assert result.exit_code != 0
        assert "identity" in result.stdout.lower() or "login" in result.stdout.lower()

    def test_federation_join_invalid_format(self, cli_home):
        """join with malformed invite code shows error."""
        runner.invoke(app, ["login", "--key", "aa" * 32])
        result = runner.invoke(app, ["federation", "join", "badcode"])
        assert result.exit_code != 0
        assert "format" in result.stdout.lower()
        result = runner.invoke(app, ["federation", "join", "federation:abc:myfed"])  # npub too short
        assert result.exit_code != 0

    def test_federation_join_command_exists(self, cli_home):
        """join command is registered."""
        result = runner.invoke(app, ["federation", "join", "--help"])
        assert result.exit_code == 0
        assert "federation" in result.output.lower()
```

- [ ] **Step 2: Add TestFederationList class**

```python
class TestFederationList:
    def test_federation_list_requires_login(self, cli_home):
        """list without identity shows error."""
        result = runner.invoke(app, ["federation", "list"])
        assert result.exit_code != 0

    def test_federation_list_empty(self, cli_home):
        """list with no federations shows empty message."""
        runner.invoke(app, ["login", "--key", "aa" * 32])
        result = runner.invoke(app, ["federation", "list"])
        assert result.exit_code == 0
        assert "no federations" in result.stdout.lower()
```

- [ ] **Step 3: Add TestFederationLeave class**

```python
class TestFederationLeave:
    def test_federation_leave_requires_login(self, cli_home):
        """leave without identity shows error."""
        result = runner.invoke(app, ["federation", "leave", "abc123"])
        assert result.exit_code != 0

    def test_federation_leave_unknown_federation(self, cli_home):
        """leave for unknown federation shows error."""
        runner.invoke(app, ["login", "--key", "aa" * 32])
        result = runner.invoke(app, ["federation", "leave", "abc123"])
        assert result.exit_code != 0
        assert "not found" in result.stdout.lower()
```

- [ ] **Step 4: Run tests — FAIL**

Run: `pytest tests/test_cli.py::TestFederationJoin tests/test_cli.py::TestFederationList tests/test_cli.py::TestFederationLeave -v`
Expected: FAIL (command not found)

### Part B: Add federation_app Typer + subcommands

- [ ] **Step 5: Modify cli/main.py — add federation_app and join/list/leave**

Add in the Typer app setup section:

```python
federation_app = typer.Typer(help="Federation management")
app.add_typer(federation_app, name="federation")
```

Add after `applications_respond()`:

```python
# ── Federations ────────────────────────────────────────────────

@federation_app.command(name="join")
def federation_join(
    invite_code: str = typer.Argument(..., help="Federation invite code (federation:npub:name)"),
):
    """Join a federation by invite code.

    Fetches the relay list from the federation owner's npub and stores locally.
    """
    identity = _load_identity()
    if not identity:
        typer.echo("No identity. Run: agentboss login --key <nsec>")
        raise typer.Exit(code=1)

    # Parse invite code: federation:<npub_hex>:<name>
    if not invite_code.startswith("federation:"):
        typer.echo("Invalid invite code format. Must start with 'federation:'")
        raise typer.Exit(code=1)

    parts = invite_code.split(":", 2)
    if len(parts) != 3:
        typer.echo("Invalid invite code format. Use: federation:<npub_hex>:<name>")
        raise typer.Exit(code=1)
    _, federation_id, federation_name = parts

    # Validate npub hex (64 chars)
    if len(federation_id) != 64 or not all(c in "0123456789abcdef" for c in federation_id.lower()):
        typer.echo("Invalid federation npub. Must be 64 hex characters.")
        raise typer.Exit(code=1)

    storage = _get_storage()
    relay_url = storage.get_config("relay", DEFAULT_RELAY)

    async def _fetch_federation():
        relay = NostrRelay(relay_url)
        try:
            await relay.connect()
            await relay.subscribe(
                "fed_lookup",
                kinds=[KIND_FEDERATION],
                tags={"authors": [federation_id], "#d": [federation_name]},
            )
            events = []
            async for event in relay.receive_events("fed_lookup"):
                events.append(event)
            await relay.unsubscribe("fed_lookup")

            if not events:
                typer.echo(f"Federation '{federation_name}' not found for npub {federation_id[:16]}...")
                return

            latest = max(events, key=lambda e: e.get("created_at", 0))
            try:
                relay_urls = json.loads(latest["content"])
            except (json.JSONDecodeError, KeyError):
                typer.echo("Error: Invalid federation relay list in event content")
                return

            if not isinstance(relay_urls, list) or not all(isinstance(r, str) for r in relay_urls):
                typer.echo("Error: Federation relay list must be a JSON array of relay URLs")
                return

            storage.upsert_federation(
                federation_id=federation_id,
                name=federation_name,
                relay_urls=relay_urls,
                created_at=latest.get("created_at", int(time.time())),
            )
            typer.echo(f"Joined federation '{federation_name}' with {len(relay_urls)} relay(s)")
        finally:
            await relay.close()

    asyncio.run(_fetch_federation())
    storage.close()


@federation_app.command(name="list")
def federation_list():
    """List all joined federations."""
    identity = _load_identity()
    if not identity:
        typer.echo("No identity. Run: agentboss login --key <nsec>")
        raise typer.Exit(code=1)

    storage = _get_storage()
    feds = storage.list_federations()
    if not feds:
        typer.echo("No federations joined. Run: agentboss federation join <code>")
        storage.close()
        return

    for fed in feds:
        relay_count = len(fed["relay_urls"])
        typer.echo(f"- {fed['name']} ({fed['federation_id'][:16]}...) | {relay_count} relay(s)")
    storage.close()


@federation_app.command(name="leave")
def federation_leave(
    federation_id: str = typer.Argument(..., help="Federation ID (npub hex)"),
    confirm: bool = typer.Option(False, "--yes", help="Skip confirmation"),
):
    """Leave and delete a federation."""
    identity = _load_identity()
    if not identity:
        typer.echo("No identity. Run: agentboss login --key <nsec>")
        raise typer.Exit(code=1)

    storage = _get_storage()
    fed = storage.get_federation(federation_id)
    if not fed:
        typer.echo("Federation not found.")
        storage.close()
        raise typer.Exit(code=1)

    if not confirm:
        typer.echo(f"Leave federation '{fed['name']}'? Use --yes to confirm.")
        storage.close()
        raise typer.Exit(code=1)

    storage.delete_federation(federation_id)
    typer.echo(f"Left federation '{fed['name']}'.")
    storage.close()
```

- [ ] **Step 6: Run federation CLI tests — PASS**

Run: `pytest tests/test_cli.py::TestFederationJoin tests/test_cli.py::TestFederationList tests/test_cli.py::TestFederationLeave -v`
Expected: PASS

### Part C: Commit

- [ ] **Step 7: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add federation join/list/leave CLI commands"
```

---

## Task 4: Federation Create CLI

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Part A: Write failing test for federation create

- [ ] **Step 1: Add TestFederationCreate class**

```python
class TestFederationCreate:
    def test_federation_create_requires_login(self, cli_home):
        """create without identity shows error."""
        result = runner.invoke(app, ["federation", "create", "myfed", "wss://relay.example.com"])
        assert result.exit_code != 0
        assert "identity" in result.stdout.lower() or "login" in result.stdout.lower()

    def test_federation_create_command_exists(self, cli_home):
        """create command is registered."""
        result = runner.invoke(app, ["federation", "create", "--help"])
        assert result.exit_code == 0
```

- [ ] **Step 2: Run tests — FAIL** (command not registered)

Run: `pytest tests/test_cli.py::TestFederationCreate -v`
Expected: FAIL

### Part B: Add federation_create command

- [ ] **Step 3: Add federation_create to cli/main.py**

```python
@federation_app.command(name="create")
def federation_create(
    name: str = typer.Argument(..., help="Federation name"),
    relays: list[str] = typer.Argument(..., help="Relay URLs (at least one)"),
):
    """Create a new federation and publish its metadata.

    Publishes a federation metadata event (kind:31990) to all specified relays.
    The resulting invite code can be shared with others to join this federation.
    """
    identity = _load_identity()
    if not identity:
        typer.echo("No identity. Run: agentboss login --key <nsec>")
        raise typer.Exit(code=1)

    if len(relays) < 1:
        typer.echo("At least one relay URL is required.")
        raise typer.Exit(code=1)

    storage = _get_storage()
    federation_id = identity["pubkey"]
    relay_urls = relays

    content = json.dumps(relay_urls)
    event = build_event(
        kind=KIND_FEDERATION,
        content=content,
        privkey=identity["privkey"],
        pubkey=identity["pubkey"],
        tags=[
            ["d", name],
            ["t", "agentboss"],
            ["t", "federation"],
        ],
    )

    async def _create():
        failed = []
        for relay_url in relay_urls:
            relay = NostrRelay(relay_url)
            try:
                await relay.connect()
                result = await relay.publish_event(event)
                if not result["accepted"]:
                    failed.append(f"{relay_url}: {result['message']}")
            except Exception as e:
                failed.append(f"{relay_url}: {e}")
            finally:
                await relay.close()

        if failed:
            typer.echo(f"Federation created but failed to publish to {len(failed)} relay(s):")
            for f in failed:
                typer.echo(f"  - {f}")
        else:
            typer.echo(f"Federation '{name}' created and published to {len(relay_urls)} relay(s).")

        storage.upsert_federation(
            federation_id=federation_id,
            name=name,
            relay_urls=relay_urls,
            created_at=event["created_at"],
        )

        invite_code = f"federation:{federation_id}:{name}"
        typer.echo(f"\nYour invite code: {invite_code}")
        typer.echo("Share this code with others to join your federation.")

    asyncio.run(_create())
    storage.close()
```

- [ ] **Step 4: Run tests — PASS**

Run: `pytest tests/test_cli.py::TestFederationCreate -v`
Expected: PASS

### Part C: Commit

- [ ] **Step 5: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add federation create command with invite code generation"
```

---

## Task 5: Modified Fetch (Multi-Relay)

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Part A: Write failing test for fetch --federation

- [ ] **Step 1: Add test for fetch --federation option**

```python
class TestFederationFetch:
    def test_fetch_federation_option_exists(self, cli_home):
        """fetch --federation option is available."""
        result = runner.invoke(app, ["fetch", "--help"])
        assert result.exit_code == 0
        assert "--federation" in result.output
```

- [ ] **Step 2: Add test for fetch --federation stores results with federation_id**

```python
    def test_fetch_federation_stores_jobs_with_federation_id(self, cli_home):
        """fetch --federation stores jobs with federation_id set."""
        runner.invoke(app, ["login", "--key", "aa" * 32])
        from cli.storage import Storage
        from shared.crypto import derive_pub
        s = Storage(str(cli_home / "agentboss.db"))
        s.init_db()
        # Pre-populate a federation
        fed_id = derive_pub("aa" * 32)
        s.upsert_federation(fed_id, "TestFed", ["wss://fake-relay.example.com"], created_at=1000)
        s.close()
        # fetch --federation should use the federation's relay list
        # (will fail since relay is fake, but command should accept --federation flag)
        result = runner.invoke(app, ["fetch", "--federation", "TestFed"])
        # Should not crash on unknown federation
        assert "not found" in result.stdout.lower() or result.exit_code == 0
```

- [ ] **Step 3: Run tests — FAIL** (--federation option not implemented)

Run: `pytest tests/test_cli.py::TestFederationFetch -v`
Expected: FAIL

### Part B: Add --federation option to fetch command

- [ ] **Step 4: Modify fetch command in cli/main.py**

Find the existing `fetch` command definition. Add `federation: Optional[str] = None` parameter and logic to use `fetch_events_from_relays` when federation is specified:

```python
# Add import at top if not present:
from typing import Optional

# In fetch command definition, add parameter:
# Remove: limit: int = typer.Option(20, "--limit"...
# Add: federation: Optional[str] = typer.Option(None, "--federation"...

# Inside _fetch(), replace the relay selection logic:
if federation_name:
    fed = storage.get_federation_by_name(federation_name)  # Need helper or search
    if not fed:
        # Try by federation_id (npub)
        fed = storage.get_federation(federation_name)
    if not fed:
        typer.echo(f"Federation '{federation_name}' not found. Run: agentboss federation list")
        return
    relay_urls = fed["relay_urls"]
    # Use multi-relay fetch
    events = await fetch_events_from_relays(
        relay_urls=relay_urls,
        kinds=[KIND_APP_DATA],
        tags={"#t": [APP_TAG, JOB_TAG]},
        limit=limit,
    )
    # Process events same as single-relay case...
else:
    relay_url = storage.get_config("relay", DEFAULT_RELAY)
    # Existing single-relay logic unchanged
```

Note: `get_federation_by_name` doesn't exist yet. Add it as a helper in storage or do `next((f for f in list_federations() if f["name"] == name), None)`.

- [ ] **Step 5: Run tests — PASS**

Run: `pytest tests/test_cli.py::TestFederationFetch -v`
Expected: PASS

### Part C: Commit

- [ ] **Step 6: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add --federation option to fetch for multi-relay queries"
```

---

## Task 6: Modified Publish (Multi-Relay)

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Part A: Write failing test for publish --federation

- [ ] **Step 1: Add test for publish --federation option**

```python
class TestFederationPublish:
    def test_publish_federation_option_exists(self, cli_home):
        """publish --federation option is available."""
        result = runner.invoke(app, ["publish", "--help"])
        assert result.exit_code == 0
        assert "--federation" in result.output
```

- [ ] **Step 2: Run test — FAIL** (--federation not implemented for publish)

Run: `pytest tests/test_cli.py::TestFederationPublish -v`
Expected: FAIL

### Part B: Add --federation option to publish command

- [ ] **Step 3: Modify publish command in cli/main.py**

Add `federation: Optional[str] = None` parameter and multi-relay publish logic when federation is specified:

```python
# In publish command, after building the event:
if federation_name:
    fed = storage.get_federation(federation_name)
    if not fed:
        typer.echo(f"Federation '{federation_name}' not found.")
        return
    relay_urls = fed["relay_urls"]
    failed = []
    for relay_url in relay_urls:
        relay = NostrRelay(relay_url)
        try:
            await relay.connect()
            result = await relay.publish_event(event)
            if not result["accepted"]:
                failed.append(f"{relay_url}: {result['message']}")
        except Exception as e:
            failed.append(f"{relay_url}: {e}")
        finally:
            await relay.close()
    if failed:
        typer.echo(f"Published to {len(relay_urls) - len(failed)}/{len(relay_urls)} relays. Failures:")
        for f in failed:
            typer.echo(f"  - {f}")
    else:
        typer.echo(f"Published to all {len(relay_urls)} federation relays.")
else:
    # Existing single-relay publish logic
    relay = NostrRelay(relay_url)
    # ...
```

- [ ] **Step 4: Run test — PASS**

Run: `pytest tests/test_cli.py::TestFederationPublish -v`
Expected: PASS

### Part C: Commit

- [ ] **Step 5: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add --federation option to publish for multi-relay writes"
```

---

## Task 7: Integration + Final Tests

### Step 1: Run full test suite

- [ ] **Step 1: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS (all existing + new federation tests)

### Step 2: Final commit

- [ ] **Step 2: Final commit**

```bash
git add -A
git commit -m "feat: implement Relay Federation — multi-relay job posting federation"
```

---

## Summary: Task → Owner Mapping

| Task | Description | Owner |
|------|-------------|-------|
| 1 | Constants + Storage Schema | npub1g9plav7 |
| 2 | Multi-Relay Fetch | npub1g9plav7 |
| 3 | Federation Join/List/Leave CLI | npub1g9plav7 |
| 4 | Federation Create CLI | npub1g9plav7 |
| 5 | Modified Fetch (Multi-Relay) | npub1g9plav7 |
| 6 | Modified Publish (Multi-Relay) | npub1g9plav7 |
| 7 | Integration + Final Tests | npub1g9plav7 |

## Notes for Implementer

- **Kind number**: Use `KIND_FEDERATION = 31990` for federation metadata events
- **SQLite ALTER TABLE**: `ALTER TABLE jobs ADD COLUMN federation_id TEXT` is idempotent — safe on existing DBs
- **Invite code format**: `federation:<npub_hex>:<name>` (e.g., `federation:a1b2c3...:techjobs`)
- **Conflict resolution**: When same job (same event_id) appears from multiple relays, `_merge_events` keeps later one by `created_at` timestamp. Lexical tiebreak is N/A since duplicates have same timestamp.
- **`_merge_events`**: Module-level helper, must be importable for testing
- **Federation ID**: The owner's npub hex — uniquely identifies the federation
- **Federation lookup by name**: When `fetch --federation <name>` is used, search `list_federations()` for matching name
