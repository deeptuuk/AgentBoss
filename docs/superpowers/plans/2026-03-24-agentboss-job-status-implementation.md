# AgentBoss Feature #5: Job Bookmark & Status — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local bookmark/status tracking (`favorited` + `applied`) for job postings with TDD.

**Architecture:** Add `job_status` SQLite table alongside existing `jobs` table. Extend `list` command with status filters. Add `favorite`, `apply`, `status` commands.

**Tech Stack:** Python 3.11+, SQLite, typer, pytest

**Spec:** `docs/superpowers/specs/2026-03-24-agentboss-job-status-design.md`

---

## File Map

| File | Change |
|------|--------|
| `cli/storage.py` | Add `job_status` table in `init_db()`, add CRUD methods |
| `cli/main.py` | Extend `list` with `--favorited`/`--applied`; add `favorite`, `apply`, `status` |
| `tests/test_storage.py` | Add 10 tests for job_status CRUD |
| `tests/test_cli.py` | Add tests for new commands and extended `list` |

---

## Task 1: Storage — job_status CRUD

**Files:**
- Modify: `cli/storage.py` (add table + methods)
- Test: `tests/test_storage.py`

### Part A: Add table to init_db()

- [ ] **Step 1: Write failing test — `test_job_status_table_exists`**

`tests/test_storage.py` (add to existing file):
```python
class TestJobStatus:
    def test_job_status_table_exists(self, db):
        tables = db.list_tables()
        assert "job_status" in tables
```

- [ ] **Step 2: Run test — FAIL**

Run: `python -m pytest tests/test_storage.py::TestJobStatus::test_job_status_table_exists -v`
Expected: FAIL — "job_status not in tables"

- [ ] **Step 3: Add job_status table to init_db()**

In `cli/storage.py`, add to `init_db()`:

```python
cur.executescript("""
    CREATE TABLE IF NOT EXISTS job_status (
        event_id TEXT PRIMARY KEY,
        favorited INTEGER DEFAULT 0,
        applied INTEGER DEFAULT 0,
        created_at INTEGER DEFAULT (unixepoch('now')),
        updated_at INTEGER DEFAULT (unixepoch('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_job_status_event_id ON job_status(event_id);
""")
```

- [ ] **Step 4: Run test — PASS**

Run: `python -m pytest tests/test_storage.py::TestJobStatus::test_job_status_table_exists -v`
Expected: PASS

### Part B: upsert_status

- [ ] **Step 5: Write failing test — `test_upsert_status_favorited`**

```python
def test_upsert_status_favorited(self, db):
    db.upsert_status("ev1", favorited=True)
    status = db.get_status("ev1")
    assert status is not None
    assert status["favorited"] == 1
    assert status["applied"] == 0
```

- [ ] **Step 6: Run test — FAIL**

Expected: FAIL — `upsert_status` not defined

- [ ] **Step 7: Write minimal implementation**

In `cli/storage.py`, add:

```python
def upsert_status(self, event_id: str, favorited: bool | None = None, applied: bool | None = None):
    existing = self.get_status(event_id)
    fav = 1 if favorited else (existing["favorited"] if existing else 0)
    app = 1 if applied else (existing["applied"] if existing else 0)
    self._conn.execute(
        """INSERT OR REPLACE INTO job_status (event_id, favorited, applied, updated_at)
           VALUES (?, ?, ?, unixepoch('now'))""",
        (event_id, fav, app),
    )
    self._conn.commit()
```

- [ ] **Step 8: Run test — FAIL**

Expected: FAIL — `get_status` not defined yet

### Part C: get_status

- [ ] **Step 9: Write failing test — `test_get_status_returns_status`**

```python
def test_get_status_returns_status(self, db):
    db.upsert_status("ev1", favorited=True, applied=False)
    status = db.get_status("ev1")
    assert status["favorited"] == 1
    assert status["applied"] == 0
    assert status["event_id"] == "ev1"

def test_get_status_not_found(self, db):
    assert db.get_status("nonexistent") is None
```

- [ ] **Step 10: Run test — FAIL**

Expected: FAIL — `get_status` not defined

- [ ] **Step 11: Write minimal implementation**

```python
def get_status(self, event_id: str) -> dict | None:
    row = self._conn.execute(
        "SELECT * FROM job_status WHERE event_id = ?", (event_id,)
    ).fetchone()
    return dict(row) if row else None
```

- [ ] **Step 12: Run tests — PASS**

Run: `python -m pytest tests/test_storage.py::TestJobStatus -v`
Expected: all 3 PASS

### Part D: Toggle behavior

- [ ] **Step 13: Write failing test — `test_toggle_favorited`**

```python
def test_toggle_favorited(self, db):
    # First call: set favorited=1
    db.upsert_status("ev1", favorited=True)
    assert db.get_status("ev1")["favorited"] == 1
    # Second call: toggle to 0
    db.upsert_status("ev1", favorited=True)  # already True, toggles off
    assert db.get_status("ev1")["favorited"] == 0

def test_toggle_applied(self, db):
    db.upsert_status("ev1", applied=True)
    assert db.get_status("ev1")["applied"] == 1
    db.upsert_status("ev1", applied=True)
    assert db.get_status("ev1")["applied"] == 0
```

- [ ] **Step 14: Run test — FAIL**

Expected: FAIL — toggle logic incorrect

- [ ] **Step 15: Fix upsert_status toggle logic**

Update `upsert_status`:
```python
def upsert_status(self, event_id: str, favorited: bool | None = None, applied: bool | None = None):
    existing = self.get_status(event_id)
    fav = 1 if favorited else (0 if existing is None else existing["favorited"])
    app = 1 if applied else (0 if existing is None else existing["applied"])
    self._conn.execute(
        """INSERT OR REPLACE INTO job_status (event_id, favorited, applied, updated_at)
           VALUES (?, ?, ?, unixepoch('now'))""",
        (event_id, fav, app),
    )
    self._conn.commit()
```

Wait — toggle means: if favorited=True passed, flip the current state. Fix logic:
```python
def upsert_status(self, event_id: str, favorited: bool | None = None, applied: bool | None = None):
    existing = self.get_status(event_id)
    current_fav = existing["favorited"] if existing else 0
    current_app = existing["applied"] if existing else 0
    new_fav = 1 - current_fav if favorited is not None else current_fav
    new_app = 1 - current_app if applied is not None else current_app
    self._conn.execute(
        """INSERT OR REPLACE INTO job_status (event_id, favorited, applied, updated_at)
           VALUES (?, ?, ?, unixepoch('now'))""",
        (event_id, new_fav, new_app),
    )
    self._conn.commit()
```

- [ ] **Step 16: Run tests — PASS**

Run: `python -m pytest tests/test_storage.py::TestJobStatus -v`
Expected: all PASS

### Part E: list_status + list_jobs with status filter

- [ ] **Step 17: Write failing test — `test_list_jobs_favorited`**

First add jobs to db, then test filtering:
```python
def test_list_jobs_favorited(self, db):
    db.upsert_job("j1", "d1", "pub1", 1, 101, "{}", 1000)
    db.upsert_job("j2", "d2", "pub2", 1, 101, "{}", 1000)
    db.upsert_status("j1", favorited=True)
    jobs = db.list_jobs(favorited=True)
    assert len(jobs) == 1
    assert jobs[0]["event_id"] == "j1"
```

- [ ] **Step 18: Run test — FAIL**

Expected: FAIL — `list_jobs` doesn't accept `favorited` yet

- [ ] **Step 19: Write failing test — `test_list_jobs_applied`**

```python
def test_list_jobs_applied(self, db):
    db.upsert_job("j1", "d1", "pub1", 1, 101, "{}", 1000)
    db.upsert_job("j2", "d2", "pub2", 2, 201, "{}", 1000)
    db.upsert_status("j2", applied=True)
    jobs = db.list_jobs(applied=True)
    assert len(jobs) == 1
    assert jobs[0]["event_id"] == "j2"
```

- [ ] **Step 20: Run test — FAIL**

- [ ] **Step 21: Write failing test — `test_list_jobs_favorited_and_province`**

```python
def test_list_jobs_favorited_and_province(self, db):
    db.upsert_job("j1", "d1", "pub1", 1, 101, "{}", 1000)
    db.upsert_job("j2", "d2", "pub2", 2, 201, "{}", 1000)
    db.upsert_status("j1", favorited=True)
    db.upsert_status("j2", favorited=True)
    jobs = db.list_jobs(province_code=1, favorited=True)
    assert len(jobs) == 1
    assert jobs[0]["event_id"] == "j1"
```

- [ ] **Step 22: Run test — FAIL**

- [ ] **Step 23: Update list_jobs signature and implementation**

Add `favorited: bool | None = None, applied: bool | None = None` parameters to `list_jobs` in `cli/storage.py`:

```python
def list_jobs(
    self,
    province_code: int | None = None,
    city_code: int | None = None,
    favorited: bool | None = None,
    applied: bool | None = None,
) -> list[dict]:
    query = "SELECT jobs.* FROM jobs LEFT JOIN job_status ON jobs.event_id = job_status.event_id WHERE 1=1"
    params: list = []
    if province_code is not None:
        query += " AND jobs.province_code = ?"
        params.append(province_code)
    if city_code is not None:
        query += " AND jobs.city_code = ?"
        params.append(city_code)
    if favorited is not None:
        query += " AND job_status.favorited = ?"
        params.append(1 if favorited else 0)
    if applied is not None:
        query += " AND job_status.applied = ?"
        params.append(1 if applied else 0)
    query += " ORDER BY jobs.created_at DESC"
    rows = self._conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]
```

- [ ] **Step 24: Run storage tests — PASS**

Run: `python -m pytest tests/test_storage.py::TestJobStatus -v`
Expected: all PASS

- [ ] **Step 25: Commit**

```bash
git add cli/storage.py tests/test_storage.py
git commit -m "feat: add job_status table and CRUD methods with toggle logic"
```

---

## Task 2: CLI Commands

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Part A: favorite command

- [ ] **Step 1: Write failing test — `test_favorite_command`**

```python
def test_favorite_command(self, cli_home):
    # First insert a job directly into storage for testing
    from cli.storage import Storage
    s = Storage(str(cli_home / "agentboss.db"))
    s.init_db()
    s.upsert_job("abc123", "d1", "pub1", 1, 101, "{}", 1000)
    s.close()

    result = runner.invoke(app, ["favorite", "abc123"])
    assert result.exit_code == 0
    assert "favorited" in result.stdout.lower() or "收藏" in result.stdout
```

- [ ] **Step 2: Run test — FAIL**

Expected: FAIL — `favorite` command not defined

- [ ] **Step 3: Add favorite command to cli/main.py**

In `cli/main.py`, add:

```python
@app.command()
def favorite(job_id: str = typer.Argument(..., help="Job ID (full or prefix)")):
    """Toggle favorited status of a job."""
    storage = _get_storage()
    job = storage.get_job(job_id)
    if not job:
        # Try prefix match
        jobs = storage.list_jobs()
        matches = [j for j in jobs if j["event_id"].startswith(job_id)]
        if len(matches) == 1:
            job = matches[0]
        elif len(matches) > 1:
            typer.echo("Multiple jobs match prefix. Use full ID.")
            raise typer.Exit(code=1)
        else:
            typer.echo("Job not found in local storage. Run `fetch` first.")
            raise typer.Exit(code=1)
    storage.upsert_status(job["event_id"], favorited=True)
    status = storage.get_status(job["event_id"])
    new_state = "收藏" if status["favorited"] else "取消收藏"
    typer.echo(f"Job {job['event_id'][:12]}... — {new_state}")
    storage.close()
```

- [ ] **Step 4: Run test — FAIL/PASS**

### Part B: apply command

- [ ] **Step 5: Write failing test — `test_apply_command`**

```python
def test_apply_command(self, cli_home):
    from cli.storage import Storage
    s = Storage(str(cli_home / "agentboss.db"))
    s.init_db()
    s.upsert_job("abc123", "d1", "pub1", 1, 101, "{}", 1000)
    s.close()

    result = runner.invoke(app, ["apply", "abc123"])
    assert result.exit_code == 0
```

- [ ] **Step 6: Add apply command**

```python
@app.command()
def apply(job_id: str = typer.Argument(..., help="Job ID (full or prefix)")):
    """Toggle applied status of a job."""
    storage = _get_storage()
    job = storage.get_job(job_id)
    if not job:
        jobs = storage.list_jobs()
        matches = [j for j in jobs if j["event_id"].startswith(job_id)]
        if len(matches) == 1:
            job = matches[0]
        elif len(matches) > 1:
            typer.echo("Multiple jobs match prefix. Use full ID.")
            raise typer.Exit(code=1)
        else:
            typer.echo("Job not found in local storage. Run `fetch` first.")
            raise typer.Exit(code=1)
    storage.upsert_status(job["event_id"], applied=True)
    status = storage.get_status(job["event_id"])
    new_state = "已投递" if status["applied"] else "取消投递"
    typer.echo(f"Job {job['event_id'][:12]}... — {new_state}")
    storage.close()
```

- [ ] **Step 7: Run tests — PASS**

### Part C: status command

- [ ] **Step 8: Write failing test — `test_status_command`**

```python
def test_status_command(self, cli_home):
    from cli.storage import Storage
    s = Storage(str(cli_home / "agentboss.db"))
    s.init_db()
    s.upsert_job("abc123", "d1", "pub1", 1, 101, "{}", 1000)
    s.upsert_status("abc123", favorited=True, applied=False)
    s.close()

    result = runner.invoke(app, ["status", "abc123"])
    assert result.exit_code == 0
    assert "favorited" in result.stdout.lower()
    assert "applied" in result.stdout.lower()
```

- [ ] **Step 9: Add status command**

```python
@app.command()
def status(job_id: str = typer.Argument(..., help="Job ID (full or prefix)")):
    """Show favorited/applied status of a job."""
    storage = _get_storage()
    job = storage.get_job(job_id)
    if not job:
        jobs = storage.list_jobs()
        matches = [j for j in jobs if j["event_id"].startswith(job_id)]
        if len(matches) == 1:
            job = matches[0]
        elif len(matches) > 1:
            typer.echo("Multiple jobs match prefix. Use full ID.")
            raise typer.Exit(code=1)
        else:
            typer.echo("Job not found.")
            raise typer.Exit(code=1)
    st = storage.get_status(job["event_id"])
    fav = "★ 收藏" if (st and st["favorited"]) else "☆ 未收藏"
    app = "✓ 已投递" if (st and st["applied"]) else "○ 未投递"
    typer.echo(f"Job {job['event_id'][:12]}... | {fav} | {app}")
    storage.close()
```

- [ ] **Step 10: Run tests — PASS**

### Part D: list with status filters

- [ ] **Step 11: Write failing test — `test_list_favorited_filter`**

```python
def test_list_favorited_filter(self, cli_home):
    from cli.storage import Storage
    s = Storage(str(cli_home / "agentboss.db"))
    s.init_db()
    s.upsert_job("j1", "d1", "pub1", 1, 101, "{}", 1000)
    s.upsert_job("j2", "d2", "pub2", 1, 101, "{}", 1000)
    s.upsert_status("j1", favorited=True)
    s.close()

    result = runner.invoke(app, ["list", "--favorited"])
    assert result.exit_code == 0
    assert "j1" in result.stdout
    assert "j2" not in result.stdout
```

- [ ] **Step 12: Update list_jobs command with filter options**

In `cli/main.py`, modify the `list_jobs` function signature and body:

```python
@app.command(name="list")
def list_jobs(
    province: Optional[str] = typer.Option(None, "--province"),
    city: Optional[str] = typer.Option(None, "--city"),
    favorited: bool = typer.Option(False, "--favorited", is_flag=True),
    applied: bool = typer.Option(False, "--applied", is_flag=True),
):
    storage = _get_storage()
    resolver = RegionResolver(storage)

    prov_code = None
    city_code_val = None
    if province:
        prov_code = resolver.province_code(province)
    if city:
        city_code_val = resolver.city_code(city)

    jobs = storage.list_jobs(
        province_code=prov_code,
        city_code=city_code_val,
        favorited=favorited or None,
        applied=applied or None,
    )
    if not jobs:
        typer.echo("No jobs found.")
        storage.close()
        return

    for job in jobs:
        try:
            content = parse_job_content(job["content"])
            pname = resolver.province_name(job["province_code"]) or str(job["province_code"])
            cname = resolver.city_name(job["city_code"]) or str(job["city_code"])
            # Show status indicators
            st = storage.get_status(job["event_id"])
            indicators = ""
            if st:
                indicators += " ★" if st["favorited"] else ""
                indicators += " ✓" if st["applied"] else ""
            typer.echo(f"[{job['event_id'][:12]}] {content.title} @ {content.company} | {pname}/{cname} | {content.salary_range}{indicators}")
        except Exception:
            typer.echo(f"[{job['event_id'][:12]}] (parse error)")
    storage.close()
```

- [ ] **Step 13: Run tests — PASS**

Run: `python -m pytest tests/test_cli.py -v`
Expected: all PASS

- [ ] **Step 14: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add favorite, apply, status commands and list filters"
```

---

## Task 3: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: all tests PASS (existing + new)

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: implement AgentBoss Feature #5 — job bookmark & status"
```
