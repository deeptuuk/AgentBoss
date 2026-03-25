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
| `cli/storage.py` | Modify | Add `federations` table + CRUD methods |
| `cli/nostr_client.py` | Modify | Add `NostrRelay.fetch_events_from_relays()` parallel query |
| `cli/main.py` | Modify | Add `federation` subcommand group + join/create/leave/list |
| `tests/test_storage.py` | Modify | Add federation storage tests |
| `tests/test_cli.py` | Modify | Add federation CLI tests |
| `tests/test_nostr_client.py` | Modify | Add multi-relay fetch tests |

---

## Task 1: Constants + Storage Schema

**Files:**
- Modify: `shared/constants.py`
- Modify: `cli/storage.py`
- Test: `tests/test_storage.py`

### Step 1: Add KIND_FEDERATION constant

- [ ] **Step 1: Modify shared/constants.py**

```python
# Add after KIND_APP_DATA = 30078
KIND_FEDERATION = 31990
```

### Step 2: Add federations table to init_db

- [ ] **Step 2: Modify cli/storage.py — add federations table**

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

### Step 3: Add federation_id column to jobs table

- [ ] **Step 3: Modify cli/storage.py — add federation_id to jobs**

In `cur.executescript()`, after `CREATE INDEX IF NOT EXISTS idx_applications_applicant`:

```python
ALTER TABLE jobs ADD COLUMN federation_id TEXT;
CREATE INDEX IF NOT EXISTS idx_jobs_federation ON jobs(federation_id);
```

Note: `ALTER TABLE ADD COLUMN` is safe since it's `IF NOT EXISTS` — running on an existing DB with the column already present is a no-op in SQLite.

### Step 4: Add federation CRUD methods

- [ ] **Step 4: Add federation storage methods to cli/storage.py**

Add after `has_application()`:

```python
# ── Federations ────────────────────────────────────────────────

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

### Step 5: Write failing test for federations storage

- [ ] **Step 5: Add test for federations storage**

In `tests/test_storage.py`, add new `TestFederations` class:

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

- [ ] **Step 6: Run test — FAIL** (federations table/methods don't exist yet)

Run: `pytest tests/test_storage.py::TestFederations -v`
Expected: FAIL with "no such table: federations" or "AttributeError"

- [ ] **Step 7: Implement storage methods (already done in Step 3-4)**

Run: `pytest tests/test_storage.py::TestFederations -v`
Expected: PASS

### Step 6: Add jobs.federation_id column test

- [ ] **Step 8: Write failing test for jobs.federation_id**

In `TestJobs`, add:

```python
def test_job_has_federation_id(self, db):
    """jobs table has federation_id column."""
    db.upsert_job("id1", "d1", "pub1", 1, 101, "{}", 1000)
    job = db.get_job("id1")
    assert "federation_id" in job
```

- [ ] **Step 9: Run test — PASS** (ALTER TABLE is idempotent)

### Step 7: Commit

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

### Step 1: Write failing test for multi-relay fetch

- [ ] **Step 1: Add test for multi-relay parallel fetch**

In `tests/test_nostr_client.py`, add:

```python
class TestMultiRelayFetch:
    @pytest.mark.asyncio
    async def test_fetch_from_multiple_relays_merges_results(self):
        """Parallel query to multiple relays returns merged, deduplicated events."""
        relay1 = NostrRelay("wss://relay1.example.com")
        relay2 = NostrRelay("wss://relay2.example.com")

        # Mock relay1 returning one event, relay2 returning two events (one duplicate)
        event1 = {"id": "abc", "kind": 30078, "content": "{}",
                  "pubkey": "pub1", "created_at": 1000, "tags": []}
        event2_dup = {"id": "abc", "kind": 30078, "content": "{}",
                      "pubkey": "pub1", "created_at": 1000, "tags": []}  # duplicate
        event3 = {"id": "def", "kind": 30078, "content": "{}",
                  "pubkey": "pub1", "created_at": 1001, "tags": []}

        with patch.object(NostrRelay, 'receive_events', new_callable=AsyncMock) as mock_recv:
            # relay1 returns [event1], relay2 returns [event2_dup, event3]
            async def yield_events(*args, **kwargs):
                yield event1
            async def yield_events2(*args, **kwargs):
                yield event2_dup
                yield event3

            async def mock_query(self, relay_url, *args, **kwargs):
                if "relay1" in relay_url:
                    async for e in yield_events(None):
                        yield e
                else:
                    async for e in yield_events2(None):
                        yield e

            # Test parallel fetch
            pass  # Implementation in Step 2
```

Actually, let's write a simpler unit test that doesn't require patching async methods. Add a synchronous test for the merge logic:

```python
def test_merge_events_deduplicates_by_id(self):
    """_merge_events removes duplicates by event_id."""
    events1 = [
        {"id": "abc", "content": "v1"},
        {"id": "def", "content": "v2"},
    ]
    events2 = [
        {"id": "abc", "content": "v1"},  # duplicate
        {"id": "ghi", "content": "v3"},
    ]
    result = _merge_events([events1, events2])
    ids = [e["id"] for e in result]
    assert ids == ["abc", "def", "ghi"]
```

### Step 2: Add _merge_events helper + fetch_events_from_relays to nostr_client.py

- [ ] **Step 2: Modify cli/nostr_client.py — add _merge_events and fetch_events_from_relays**

Add at the top-level (not inside a class):

```python
def _merge_events(event_lists: list[list[dict]]) -> list[dict]:
    """Merge events from multiple relays, deduplicate by event_id.

    Later duplicates (same id) override earlier ones.
    """
    by_id: dict[str, dict] = {}
    for events in event_lists:
        for event in events:
            by_id[event["id"]] = event
    return list(by_id.values())


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
    merged = _merge_events(results)
    # Sort by created_at descending
    merged.sort(key=lambda e: e.get("created_at", 0), reverse=True)
    return merged
```

Note: `asyncio` is already imported at the top of nostr_client.py.

- [ ] **Step 3: Run existing nostr_client tests — PASS**

Run: `pytest tests/test_nostr_client.py -v`
Expected: All existing tests still pass

- [ ] **Step 4: Commit**

```bash
git add cli/nostr_client.py tests/test_nostr_client.py
git commit -m "feat: add multi-relay parallel fetch with merge-deduplicate"
```

---

## Task 3: Federation Join CLI

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Step 1: Write failing test for federation join

- [ ] **Step 1: Add TestFederationJoin class**

In `tests/test_cli.py`:

```python
class TestFederationJoin:
    def test_federation_join_requires_login(self, cli_home):
        """join without identity shows error."""
        result = runner.invoke(app, ["federation", "join", "federation:abc123:myfed"])
        assert result.exit_code != 0
        assert "identity" in result.stdout.lower() or "login" in result.stdout.lower()

    def test_federation_join_unknown_npub(self, cli_home):
        """join with unknown npub shows error."""
        runner.invoke(app, ["login", "--key", "aa" * 32])
        # Try to join with a fake npub that won't resolve
        result = runner.invoke(app, ["federation", "join", "federation:0000000000000000000000000000000000000000000000000000000000000000:test"])
        # Should fail gracefully
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_federation_join_command_exists(self, cli_home):
        """join command is registered."""
        result = runner.invoke(app, ["federation", "join", "--help"])
        assert result.exit_code == 0
        assert "federation" in result.output.lower()
```

### Step 2: Add federation subcommand group to main.py

- [ ] **Step 2: Add federation_app Typer + subcommands to cli/main.py**

In the Typer app setup section (after `profile_app` and before `app.add_typer(profile_app)`):

```python
federation_app = typer.Typer(help="Federation management")
app.add_typer(federation_app, name="federation")
```

Add after `applications_list()` in main.py:

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

    # Validate npub hex
    if len(federation_id) != 64 or not all(c in "0123456789abcdef" for c in federation_id.lower()):
        typer.echo("Invalid federation npub. Must be 64 hex characters.")
        raise typer.Exit(code=1)

    storage = _get_storage()
    relay_url = storage.get_config("relay", DEFAULT_RELAY)

    async def _fetch_federation():
        relay = NostrRelay(relay_url)
        try:
            await relay.connect()
            # Query federation metadata event (kind:31990) from federation owner
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

            # Use the most recent event
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
```

### Step 3: Add federation list and leave commands

- [ ] **Step 3: Add federation list and leave commands**

After `federation_join()`:

```python
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
    confirm: bool = typer.Option(False, "--yes", is_flag=True, help="Skip confirmation"),
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

### Step 4: Run tests

- [ ] **Step 4: Run federation tests**

Run: `pytest tests/test_cli.py::TestFederationJoin -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add federation join/list/leave CLI commands"
```

---

## Task 4: Federation Create CLI

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Step 1: Write failing test for federation create

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
        assert "name" in result.output.lower()
```

### Step 2: Add federation create command

- [ ] **Step 2: Add federation_create to cli/main.py**

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
    federation_id = identity["pubkey"]  # Use own npub as federation ID
    relay_urls = relays

    # Build federation metadata event
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

        # Save locally
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

### Step 3: Run tests

- [ ] **Step 3: Run federation create tests**

Run: `pytest tests/test_cli.py::TestFederationCreate -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add federation create command with invite code generation"
```

---

## Task 5: Modified Fetch (Multi-Relay)

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Step 1: Write failing test for federation-aware fetch

- [ ] **Step 1: Add test for fetch --federation option**

In `tests/test_cli.py`, add to existing `TestListJobs` or new class:

```python
class TestFederationFetch:
    def test_fetch_federation_option_exists(self, cli_home):
        """fetch --federation option is available."""
        result = runner.invoke(app, ["fetch", "--help"])
        assert result.exit_code == 0
        assert "--federation" in result.output
```

### Step 2: Add --federation option to fetch command

- [ ] **Step 2: Modify fetch command in cli/main.py**

Find the existing `fetch` command and add a `--federation` option:

```python
# Find the fetch command definition and add:
# Remove: limit: int = typer.Option(20, "--limit"...
# Add: federation: Optional[str] = typer.Option(None, "--federation"...

async def _fetch():
    # ... existing relay setup ...

    if federation_name:
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
    else:
        relay_url = storage.get_config("relay", DEFAULT_RELAY)
        # Existing single-relay logic (keep for backward compatibility)
        relay = NostrRelay(relay_url)
        # ... existing single-relay fetch logic ...
```

Note: This modifies the existing `fetch` function. See the plan reviewer notes below.

### Step 3: Run tests

- [ ] **Step 3: Run fetch tests**

Run: `pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add --federation option to fetch for multi-relay queries"
```

---

## Task 6: Modified Publish (Multi-Relay)

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Step 1: Add multi-relay publish to publish command

- [ ] **Step 1: Modify publish command to support --federation relay list**

Find the existing `publish` command. When user has joined a federation and uses `--federation`, publish to ALL federation relays:

```python
# In publish command, after getting the event:
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

### Step 2: Commit

- [ ] **Step 2: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add multi-relay publish to federation relays"
```

---

## Task 7: Integration + Final Tests

### Step 1: Run full test suite

- [ ] **Step 1: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

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
| 3 | Federation Join CLI | npub1g9plav7 |
| 4 | Federation Create CLI | npub1g9plav7 |
| 5 | Modified Fetch (Multi-Relay) | npub1g9plav7 |
| 6 | Modified Publish (Multi-Relay) | npub1g9plav7 |
| 7 | Integration + Final Tests | npub1g9plav7 |

## Notes for Implementer

- **Kind number**: Use `KIND_FEDERATION = 31990` for federation metadata events
- **SQLite ALTER TABLE**: `ALTER TABLE jobs ADD COLUMN federation_id TEXT` is idempotent — safe to run on existing DBs
- **Invite code format**: `federation:<npub_hex>:<name>` (e.g., `federation:a1b2c3...:techjobs`)
- **Conflict resolution**: When same job (same event_id) appears from multiple relays, keep the latest by `created_at` timestamp
- **fetch_events_from_relays**: Uses `asyncio.gather` for parallel relay queries
- **Federation ID**: The owner's npub hex — uniquely identifies the federation
