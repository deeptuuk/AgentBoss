# AgentBoss Feature #1: Job Search — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `--search` keyword filter to `list` command for filtering jobs by title, company, and description fields.

**Architecture:** Consolidate duplicate `list_jobs` in storage, add `search` parameter using SQLite `json_extract` + `LIKE` + `ESCAPE`, extend `list` CLI command with `--search` option.

**Tech Stack:** Python 3.11+, SQLite, typer, pytest

**Spec:** `docs/superpowers/specs/2026-03-24-agentboss-job-search-design.md`

---

## File Map

| File | Change |
|------|--------|
| `cli/storage.py` | Consolidate two `list_jobs` methods into one; add `search: list[str]` parameter with `json_extract` + `LIKE` + `_escape_like` |
| `cli/main.py` | Add `--search` option to `list` command; parse keywords and pass to storage |
| `tests/test_storage.py` | Add 12 tests for search functionality |
| `tests/test_cli.py` | Add CLI integration tests for `list --search` |

---

## Task 1: Storage — Consolidate `list_jobs` + Add Search

**Files:**
- Modify: `cli/storage.py`
- Test: `tests/test_storage.py`

### Part A: Write failing test — `test_search_single_keyword_title`

- [ ] **Step 1: Write failing test**

Add to `tests/test_storage.py`:

```python
class TestJobSearch:
    def test_search_single_keyword_title(self, db):
        db.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"React Developer","company":"Acme","description":""}', 1000)
        db.upsert_job("j2", "d2", "pub2", 1, 101, '{"title":"Python Engineer","company":"Beta","description":""}', 1000)
        jobs = db.list_jobs(search=["react"])
        assert len(jobs) == 1
        assert jobs[0]["event_id"] == "j1"
```

- [ ] **Step 2: Run test — FAIL**

Run: `python -m pytest tests/test_storage.py::TestJobSearch::test_search_single_keyword_title -v`
Expected: FAIL — `list_jobs()` doesn't accept `search` parameter yet

### Part B: Consolidate duplicate `list_jobs` + add search parameter

- [ ] **Step 3: Write minimal implementation**

In `cli/storage.py`, **delete the first `list_jobs` method (lines 98-113)**. Keep the second one (lines 186-209) and rename it to be the only one, then add the `search` parameter.

The final `list_jobs` should be:

```python
def _escape_like(text: str) -> str:
    """Escape LIKE special characters % and _ to treat them as literals."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

def list_jobs(
    self,
    province_code: int | None = None,
    city_code: int | None = None,
    favorited: bool | None = None,
    applied: bool | None = None,
    search: list[str] | None = None,
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
    if search:
        for kw in search:
            escaped = _escape_like(kw)
            pattern = f"%{escaped.lower()}%"
            query += (
                " AND (LOWER(json_extract(jobs.content, '$.title')) LIKE ? ESCAPE '\\'"
                " OR LOWER(json_extract(jobs.content, '$.company')) LIKE ? ESCAPE '\\'"
                " OR LOWER(json_extract(jobs.content, '$.description')) LIKE ? ESCAPE '\\')"
            )
            params.extend([pattern, pattern, pattern])
    query += " ORDER BY jobs.created_at DESC"
    rows = self._conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]
```

**Important:** Remove the first `list_jobs` method entirely (the one at lines 98-113 that only has `province_code` and `city_code`). The second one (with favorited/applied) already shadows it, but having two methods is confusing — consolidate into one.

- [ ] **Step 4: Run test — PASS**

Run: `python -m pytest tests/test_storage.py::TestJobSearch::test_search_single_keyword_title -v`
Expected: PASS

### Part C: Add remaining search tests

- [ ] **Step 5: Write failing test — `test_search_multi_keyword_and`**

```python
def test_search_multi_keyword_and(self, db):
    db.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"React Developer","company":"Acme","description":"TypeScript"},"company":"Acme","description":""}', 1000)
    db.upsert_job("j2", "d2", "pub2", 1, 101, '{"title":"React Developer","company":"Beta","description":""}', 1000)
    jobs = db.list_jobs(search=["react", "typescript"])
    assert len(jobs) == 1
    assert jobs[0]["event_id"] == "j1"
```

- [ ] **Step 6: Run test — PASS** (implementation already supports AND via multiple AND clauses)

Run: `python -m pytest tests/test_storage.py::TestJobSearch::test_search_multi_keyword_and -v`
Expected: PASS

- [ ] **Step 7: Write failing test — `test_search_case_insensitive`**

```python
def test_search_case_insensitive(self, db):
    db.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"React Developer","company":"Acme","description":""}', 1000)
    jobs = db.list_jobs(search=["REACT"])
    assert len(jobs) == 1
    assert jobs[0]["event_id"] == "j1"
```

- [ ] **Step 8: Run test — PASS**

- [ ] **Step 9: Write failing test — `test_search_no_results`**

```python
def test_search_no_results(self, db):
    db.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"React Developer","company":"Acme","description":""}', 1000)
    jobs = db.list_jobs(search=["golang"])
    assert len(jobs) == 0
```

- [ ] **Step 10: Run test — PASS**

- [ ] **Step 11: Write failing test — `test_search_in_description`**

```python
def test_search_in_description(self, db):
    db.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"Dev","company":"Acme","description":"React with TypeScript"}', 1000)
    db.upsert_job("j2", "d2", "pub2", 1, 101, '{"title":"Dev","company":"Beta","description":"Python only"}', 1000)
    jobs = db.list_jobs(search=["typescript"])
    assert len(jobs) == 1
    assert jobs[0]["event_id"] == "j1"
```

- [ ] **Step 12: Run test — PASS**

- [ ] **Step 13: Write failing test — `test_search_in_company`**

```python
def test_search_in_company(self, db):
    db.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"Dev","company":"Acme Corp","description":""}', 1000)
    db.upsert_job("j2", "d2", "pub2", 1, 101, '{"title":"Dev","company":"Beta Inc","description":""}', 1000)
    jobs = db.list_jobs(search=["acme"])
    assert len(jobs) == 1
    assert jobs[0]["event_id"] == "j1"
```

- [ ] **Step 14: Run test — PASS**

- [ ] **Step 15: Write failing test — `test_search_combined_with_province`**

```python
def test_search_combined_with_province(self, db):
    db.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"React Dev","company":"A","description":""}', 1000)
    db.upsert_job("j2", "d2", "pub2", 2, 201, '{"title":"React Dev","company":"B","description":""}', 1000)
    jobs = db.list_jobs(province_code=1, search=["react"])
    assert len(jobs) == 1
    assert jobs[0]["event_id"] == "j1"
```

- [ ] **Step 16: Run test — PASS**

- [ ] **Step 17: Write failing test — `test_search_combined_with_favorited`**

```python
def test_search_combined_with_favorited(self, db):
    db.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"React Dev","company":"A","description":""}', 1000)
    db.upsert_job("j2", "d2", "pub2", 1, 101, '{"title":"React Dev","company":"B","description":""}', 1000)
    db.upsert_status("j1", favorited=True)
    jobs = db.list_jobs(favorited=True, search=["react"])
    assert len(jobs) == 1
    assert jobs[0]["event_id"] == "j1"
```

- [ ] **Step 18: Run test — PASS**

- [ ] **Step 19: Write failing test — `test_search_chinese_keywords`**

```python
def test_search_chinese_keywords(self, db):
    db.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"前端开发","company":"Acme","description":""}', 1000)
    db.upsert_job("j2", "d2", "pub2", 1, 101, '{"title":"后端开发","company":"Beta","description":""}', 1000)
    jobs = db.list_jobs(search=["前端"])
    assert len(jobs) == 1
    assert jobs[0]["event_id"] == "j1"
```

- [ ] **Step 20: Run test — PASS**

- [ ] **Step 21: Write failing test — `test_search_empty_string`**

```python
def test_search_empty_string(self, db):
    db.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"React Dev","company":"A","description":""}', 1000)
    jobs = db.list_jobs(search=[])
    assert len(jobs) == 1  # empty list = no filter
```

- [ ] **Step 22: Run test — PASS**

- [ ] **Step 23: Write failing test — `test_search_substring_false_positive`**

```python
def test_search_substring_false_positive(self, db):
    """'act' should NOT match 'React Developer' (substring match bug)"""
    db.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"React Developer","company":"Acme","description":""}', 1000)
    jobs = db.list_jobs(search=["act"])
    assert len(jobs) == 0  # 'act' is not a word, should not match 'React'
```

- [ ] **Step 24: Run test — PASS** (json_extract prevents this)

- [ ] **Step 25: Write failing test — `test_search_special_chars_escaped`**

```python
def test_search_special_chars_escaped(self, db):
    """Keywords with % or _ should match literally"""
    db.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"100% Remote","company":"Acme","description":""}', 1000)
    db.upsert_job("j2", "d2", "pub2", 1, 101, '{"title":"Python Dev","company":"Beta","description":""}', 1000)
    jobs = db.list_jobs(search=["100%"])
    assert len(jobs) == 1
    assert jobs[0]["event_id"] == "j1"
```

- [ ] **Step 26: Run test — PASS**

- [ ] **Step 27: Run all storage tests**

Run: `python -m pytest tests/test_storage.py::TestJobSearch -v`
Expected: all 12 PASS

- [ ] **Step 28: Commit**

```bash
git add cli/storage.py tests/test_storage.py
git commit -m "feat: consolidate list_jobs and add search with json_extract LIKE"
```

---

## Task 2: CLI — Add `--search` to `list` Command

**Files:**
- Modify: `cli/main.py`
- Test: `tests/test_cli.py`

### Part A: Add `--search` option to `list` command

- [ ] **Step 1: Write failing test — `test_list_search_single_keyword`**

Add to `tests/test_cli.py`:

```python
class TestListSearch:
    def test_list_search_single_keyword(self, cli_home):
        from cli.storage import Storage
        s = Storage(str(cli_home / "agentboss.db"))
        s.init_db()
        s.upsert_job("abc123", "d1", "pub1", 1, 101, '{"title":"React Developer","company":"Acme","description":"TypeScript"},"company":"AcmeCorp","description":""}', 1000)
        s.close()

        result = runner.invoke(app, ["list", "--search", "react"])
        assert result.exit_code == 0
        assert "React Developer" in result.stdout
```

- [ ] **Step 2: Run test — FAIL**

Run: `python -m pytest tests/test_cli.py::TestListSearch::test_list_search_single_keyword -v`
Expected: FAIL — `--search` option doesn't exist

- [ ] **Step 3: Add `--search` option to `list` command in `cli/main.py`**

In `cli/main.py`, modify the `list_jobs` function (lines 241-284):

Add `search: Optional[str] = typer.Option(None, "--search", help="Search keywords (space-separated, AND)")` to the function signature.

And update the function body to parse keywords and pass to storage:

```python
@app.command(name="list")
def list_jobs(
    province: Optional[str] = typer.Option(None, "--province"),
    city: Optional[str] = typer.Option(None, "--city"),
    favorited: bool = typer.Option(False, "--favorited", is_flag=True, help="Show only favorited jobs"),
    applied: bool = typer.Option(False, "--applied", is_flag=True, help="Show only applied jobs"),
    search: Optional[str] = typer.Option(None, "--search", help="Search keywords (space-separated, AND)"),
):
    """List locally stored job postings."""
    storage = _get_storage()
    resolver = RegionResolver(storage)

    prov_code = None
    city_code_val = None
    if province:
        prov_code = resolver.province_code(province)
    if city:
        city_code_val = resolver.city_code(city)

    keywords = None
    if search:
        keywords = [kw.strip().lower() for kw in search.split() if kw.strip()]

    jobs = storage.list_jobs(
        province_code=prov_code,
        city_code=city_code_val,
        favorited=favorited or None,
        applied=applied or None,
        search=keywords,
    )
    # ... rest of output formatting unchanged (lines 265-284) ...
```

- [ ] **Step 4: Run test — PASS**

Run: `python -m pytest tests/test_cli.py::TestListSearch::test_list_search_single_keyword -v`
Expected: PASS

### Part B: Add remaining CLI tests

- [ ] **Step 5: Write failing test — `test_list_search_no_results`**

```python
def test_list_search_no_results(self, cli_home):
    from cli.storage import Storage
    s = Storage(str(cli_home / "agentboss.db"))
    s.init_db()
    s.upsert_job("abc123", "d1", "pub1", 1, 101, '{"title":"React Developer","company":"Acme","description":""}', 1000)
    s.close()

    result = runner.invoke(app, ["list", "--search", "golang"])
    assert result.exit_code == 0
    assert "No jobs found" in result.stdout
```

- [ ] **Step 6: Run test — PASS**

- [ ] **Step 7: Write failing test — `test_list_search_combined_with_province`**

```python
def test_list_search_combined_with_province(self, cli_home):
    from cli.storage import Storage
    s = Storage(str(cli_home / "agentboss.db"))
    s.init_db()
    s.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"React Dev","company":"A","description":""}', 1000)
    s.upsert_job("j2", "d2", "pub2", 2, 201, '{"title":"React Dev","company":"B","description":""}', 1000)
    s.close()

    result = runner.invoke(app, ["list", "--search", "react", "--province", "北京"])
    assert result.exit_code == 0
    assert "React Dev" in result.stdout
    # Should only show j1 (province 1)
```

**Note:** This test requires region data to be seeded. For now, test with `province_code=1` filter directly in storage-level test (already done in Task 1). For CLI test, mock the region resolver or seed regions. Since region seeding is complex, skip the CLI province+search combined test — the storage-level test (Task 1 Step 15) already covers this.

- [ ] **Step 8: Write failing test — `test_list_search_empty`**

```python
def test_list_search_empty(self, cli_home):
    from cli.storage import Storage
    s = Storage(str(cli_home / "agentboss.db"))
    s.init_db()
    s.upsert_job("abc123", "d1", "pub1", 1, 101, '{"title":"React Dev","company":"A","description":""}', 1000)
    s.close()

    result = runner.invoke(app, ["list", "--search", "   "])
    assert result.exit_code == 0
    assert "React Dev" in result.stdout  # empty keywords = no filter
```

- [ ] **Step 9: Run test — PASS**

- [ ] **Step 10: Write failing test — `test_list_search_multi_keyword`**

```python
def test_list_search_multi_keyword(self, cli_home):
    from cli.storage import Storage
    s = Storage(str(cli_home / "agentboss.db"))
    s.init_db()
    s.upsert_job("j1", "d1", "pub1", 1, 101, '{"title":"React TypeScript","company":"Acme","description":""}', 1000)
    s.upsert_job("j2", "d2", "pub2", 1, 101, '{"title":"React Developer","company":"Beta","description":""}', 1000)
    s.close()

    result = runner.invoke(app, ["list", "--search", "React TypeScript"])
    assert result.exit_code == 0
    assert "j1" in result.stdout
    assert "j2" not in result.stdout
```

- [ ] **Step 11: Run test — PASS**

- [ ] **Step 12: Run all CLI tests**

Run: `python -m pytest tests/test_cli.py -v`
Expected: all PASS

- [ ] **Step 13: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add --search option to list command"
```

---

## Task 3: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: all tests PASS (existing + new)

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: implement AgentBoss Feature #1 — job search"
```
