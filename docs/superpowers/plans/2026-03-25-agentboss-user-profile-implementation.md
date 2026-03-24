# AgentBoss Feature #3: User Profile System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add user profile management (create, publish, fetch) via Nostr kind:30078 events.

**Architecture:** Profile stored as kind:30078 with `d=profile_<pubkey>`. CLI commands manage profile locally and publish to relay.

**Tech Stack:** Python 3.11+, SQLite, typer, nostr-python (reuse existing nostr_client patterns)

**Spec:** `docs/superpowers/specs/2026-03-25-agentboss-user-profile-design.md`

---

## File Map

| File | Change |
|------|--------|
| `cli/storage.py` | Add `profiles` table + CRUD methods |
| `cli/main.py` | Add `profile` subcommand with set/show/publish/fetch |
| `cli/nostr_client.py` | Add `publish_profile()`, `fetch_profile()` |
| `tests/test_storage.py` | Add profile storage tests |
| `tests/test_cli.py` | Add profile CLI tests |

---

## Task 1: Storage — profiles Table

**Files:**
- Modify: `cli/storage.py`
- Test: `tests/test_storage.py`

### Part A: Add profiles table

- [ ] **Step 1: Write failing test — `test_profiles_table_exists`**

```python
class TestProfiles:
    def test_profiles_table_exists(self, db):
        tables = db.list_tables()
        assert "profiles" in tables
```

- [ ] **Step 2: Run test — FAIL**

Run: `python -m pytest tests/test_storage.py::TestProfiles::test_profiles_table_exists -v`
Expected: FAIL

- [ ] **Step 3: Add profiles table to storage.py init_db()**

```python
cur.executescript("""
    CREATE TABLE IF NOT EXISTS profiles (
        pubkey TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        name TEXT,
        skills TEXT,
        bio TEXT,
        experience TEXT,
        last_updated INTEGER,
        relay_url TEXT
    );
""")
```

- [ ] **Step 4: Run test — PASS**

### Part B: upsert_profile

- [ ] **Step 5: Write failing test — `test_upsert_profile`**

```python
def test_upsert_profile(self, db):
    content = '{"name":"张三","skills":["Python"],"bio":"test","experience":""}'
    db.upsert_profile("abc123", content)
    profile = db.get_profile("abc123")
    assert profile is not None
    assert profile["name"] == "张三"
    assert profile["skills"] == "Python"
```

- [ ] **Step 6: Run test — FAIL**

- [ ] **Step 7: Implement upsert_profile**

```python
def upsert_profile(self, pubkey: str, content: str, relay_url: str | None = None):
    import json, time
    data = json.loads(content)
    self._conn.execute("""
        INSERT OR REPLACE INTO profiles
        (pubkey, content, name, skills, bio, experience, last_updated, relay_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pubkey, content,
        data.get("name", ""),
        ",".join(data.get("skills", [])),
        data.get("bio", ""),
        data.get("experience", ""),
        int(time.time()),
        relay_url,
    ))
    self._conn.commit()
```

- [ ] **Step 8: Run test — PASS**

### Part C: get_profile and get_my_profile

- [ ] **Step 9: Write failing tests — `test_get_profile` and `test_get_profile_not_found`**

```python
def test_get_profile(self, db):
    db.upsert_profile("abc123", '{"name":"李四","skills":["Rust"],"bio":"","experience":""}')
    profile = db.get_profile("abc123")
    assert profile["name"] == "李四"
    assert profile["skills"] == "Rust"

def test_get_profile_not_found(self, db):
    assert db.get_profile("nonexistent") is None
```

- [ ] **Step 10: Run tests — FAIL**

- [ ] **Step 11: Implement get_profile**

```python
def get_profile(self, pubkey: str) -> dict | None:
    row = self._conn.execute(
        "SELECT * FROM profiles WHERE pubkey = ?", (pubkey,)
    ).fetchone()
    return dict(row) if row else None
```

- [ ] **Step 12: Run tests — PASS**

### Part D: profile update (overwrite)

- [ ] **Step 13: Write failing test — `test_profile_update_overwrites`**

```python
def test_profile_update_overwrites(self, db):
    db.upsert_profile("abc123", '{"name":"旧名","skills":[],"bio":"","experience":""}')
    db.upsert_profile("abc123", '{"name":"新名","skills":["Go"],"bio":"","experience":""}')
    profile = db.get_profile("abc123")
    assert profile["name"] == "新名"
    assert profile["skills"] == "Go"
```

- [ ] **Step 14: Run test — PASS** (upsert already handles this)

- [ ] **Step 15: Commit**

```bash
git add cli/storage.py tests/test_storage.py
git commit -m "feat: add profiles table and CRUD methods"
```

---

## Task 2: CLI — profile subcommand

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Part A: profile set

- [ ] **Step 1: Write failing test — `test_profile_set`**

```python
class TestProfile:
    def test_profile_set(self, cli_home):
        runner.invoke(app, ["login", "--key", "aa" * 32])
        result = runner.invoke(app, ["profile", "set", "--name", "张三", "--skills", "Python,Rust"])
        assert result.exit_code == 0
        assert "张三" in result.stdout
```

- [ ] **Step 2: Run test — FAIL** (profile command doesn't exist)

- [ ] **Step 3: Add profile_app to main.py**

```python
profile_app = typer.Typer(help="Profile management")
app.add_typer(profile_app, name="profile")

@profile_app.command(name="set")
def profile_set(
    name: Optional[str] = typer.Option(None, "--name"),
    skills: Optional[str] = typer.Option(None, "--skills"),
    bio: Optional[str] = typer.Option(None, "--bio"),
    experience: Optional[str] = typer.Option(None, "--experience"),
    json_file: Optional[str] = typer.Option(None, "--json"),
    publish: bool = typer.Option(False, "--publish", is_flag=True),
    relay: Optional[str] = typer.Option(None, "--relay"),
):
    """Set your profile locally. Use --publish to publish to relay."""
    identity = _load_identity()
    if not identity:
        typer.echo("Not logged in. Run: agentboss login --key <nsec>")
        raise typer.Exit(code=1)

    storage = _get_storage()

    # Build profile dict
    if json_file:
        import json
        data = json.loads(Path(json_file).read_text())
    else:
        data = {}
        if name:
            data["name"] = name
        if skills:
            data["skills"] = [s.strip() for s in skills.split(",")]
        if bio:
            data["bio"] = bio
        if experience:
            data["experience"] = experience

    content = json.dumps(data, ensure_ascii=False)
    storage.upsert_profile(identity["pubkey"], content, relay_url=relay)

    if publish:
        relay_url = relay or storage.get_config("relay", DEFAULT_RELAY)
        # Publish to relay via nostr_client
        # (See Task 3)

    typer.echo(f"Profile saved.")
    storage.close()
```

- [ ] **Step 4: Run test — FAIL/PASS**

### Part B: profile show

- [ ] **Step 5: Write failing test — `test_profile_show`**

```python
def test_profile_show(self, cli_home):
    runner.invoke(app, ["login", "--key", "aa" * 32])
    runner.invoke(app, ["profile", "set", "--name", "张三", "--skills", "Python"])
    result = runner.invoke(app, ["profile", "show"])
    assert result.exit_code == 0
    assert "张三" in result.stdout
    assert "Python" in result.stdout
```

- [ ] **Step 6: Add profile_show command**

```python
@profile_app.command(name="show")
def profile_show():
    """Show your profile."""
    identity = _load_identity()
    if not identity:
        typer.echo("Not logged in. Run: agentboss login --key <nsec>")
        raise typer.Exit(code=1)

    storage = _get_storage()
    profile = storage.get_profile(identity["pubkey"])

    if not profile:
        typer.echo("No profile found. Run: agentboss profile set ...")
        storage.close()
        return

    skills = profile["skills"] or ""
    typer.echo(f"Name:       {profile['name'] or '(not set)'}")
    typer.echo(f"Skills:     {skills}")
    typer.echo(f"Bio:        {profile['bio'] or '(not set)'}")
    typer.echo(f"Experience: {profile['experience'] or '(not set)'}")
    storage.close()
```

- [ ] **Step 7: Run test — PASS**

### Part C: profile publish

- [ ] **Step 8: Write failing test — `test_profile_publish`**

```python
def test_profile_publish(self, cli_home):
    runner.invoke(app, ["login", "--key", "aa" * 32])
    runner.invoke(app, ["profile", "set", "--name", "张三"])
    result = runner.invoke(app, ["profile", "publish"])
    assert result.exit_code == 0
    assert "published" in result.stdout.lower()
```

- [ ] **Step 9: Add profile_publish command** (needs nostr_client publish_profile — Task 3)

### Part D: profile fetch

- [ ] **Step 10: Write failing test — `test_profile_fetch`**

```python
def test_profile_fetch(self, cli_home):
    # Fetch another user's profile by npub
    result = runner.invoke(app, ["profile", "fetch", "aa" * 64])
    assert result.exit_code == 0
```

- [ ] **Step 11: Add profile_fetch command**

### Part E: Commit

- [ ] **Step 12: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add profile CLI commands (set/show/publish/fetch)"
```

---

## Task 3: Nostr Client — profile publish/fetch

**Files:**
- Modify: `cli/nostr_client.py`

### Part A: publish_profile

- [ ] **Step 1: Write failing test**

```python
def test_publish_profile_signs_event(self):
    # Mock relay, verify signed event structure
    ...
```

- [ ] **Step 2: Add publish_profile method to NostrRelay**

```python
def publish_profile(self, pubkey: str, content: str, privkey: str) -> dict:
    from shared.event import build_event
    event = build_event(
        kind=KIND_APP_DATA,
        content=content,
        privkey=privkey,
        pubkey=pubkey,
        tags=[
            ["d", f"profile_{pubkey}"],
            ["t", APP_TAG],
            ["t", "profile"],
        ],
    )
    result = await self.publish_event(event)
    return result
```

### Part B: fetch_profile

- [ ] **Step 3: Add fetch_profile method**

```python
async def fetch_profile(self, target_pubkey: str, timeout: float = 5.0) -> dict | None:
    tag_filter = f"profile_{target_pubkey}"
    await self.subscribe(
        "profile_fetch",
        kinds=[KIND_APP_DATA],
        tags={"#d": [tag_filter]},
        limit=1,
    )
    async for event in self.receive_events("profile_fetch"):
        if event.get("pubkey") == target_pubkey:
            return event
    await self.unsubscribe("profile_fetch")
    return None
```

---

## Task 4: Integration + Final

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: all PASS

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: implement AgentBoss Feature #3 — user profile system"
```
