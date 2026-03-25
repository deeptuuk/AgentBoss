# Federation 职位持久化与筛选 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 `Storage.upsert_job` 缺少 `federation_id` 参数的 bug，使 `publish --federation` 和 `fetch --federation` 能正确持久化 federation 来源，并增加 `list --federation` 筛选命令。

**Architecture:**
- 存储层：在 `upsert_job` 增加 `federation_id` 参数（默认 None 保持兼容）；在 `list_jobs` 增加 `federation_name` 参数（通过 federations 表查 id 再过滤）
- CLI 层：在 `publish`、`fetch` 命令的 federation 分支传入 federation_id；在 `list` 命令增加 `--federation` 选项
- 测试层：存储层单元测试 + 集成测试覆盖所有变更点

**Tech Stack:** Python 3.11+, SQLite, pytest, Typer

---

## 文件变更概览

| 文件 | 变更类型 |
|------|---------|
| `cli/storage.py` | 修改：`upsert_job` 签名+实现、`list_jobs` 签名+实现 |
| `cli/main.py` | 修改：`publish`、`fetch`、`list` 命令 |
| `tests/test_storage.py` | 新增：federation 相关测试用例 |
| `tests/test_integration.py` | 新增：federation 集成测试 |

---

## Task 1: 存储层 — `upsert_job` 增加 `federation_id` 参数

**Files:**
- Modify: `cli/storage.py:109-127`（`upsert_job` 方法）
- Test: `tests/test_storage.py` 新增 2 个测试

- [ ] **Step 1: 写失败的测试 — `test_upsert_job_with_federation_id`**

在 `tests/test_storage.py` 的 `TestJobs` 类中新增：

```python
def test_upsert_job_with_federation_id(self, db):
    db.upsert_job(
        event_id="e1", d_tag="d1", pubkey="p1",
        province_code=110000, city_code=110100,
        content='{"title":"A"}', created_at=1000,
        federation_id="fed123",
    )
    job = db.get_job("e1")
    assert job["federation_id"] == "fed123"
```

- [ ] **Step 2: 写失败的测试 — `test_upsert_job_federation_id_none`**

```python
def test_upsert_job_federation_id_none(self, db):
    db.upsert_job(
        event_id="e2", d_tag="d2", pubkey="p2",
        province_code=110000, city_code=110100,
        content='{"title":"B"}', created_at=1000,
    )
    job = db.get_job("e2")
    assert job["federation_id"] is None
```

- [ ] **Step 3: 运行测试验证失败**

```bash
cd /home/deeptuuk/Code4/AgentBoss
source /home/deeptuuk/Code4/code_env/bin/activate
python -m pytest tests/test_storage.py::TestJobs::test_upsert_job_with_federation_id tests/test_storage.py::TestJobs::test_upsert_job_federation_id_none -v
```
预期：FAIL（`upsert_job` 暂无 `federation_id` 参数）

- [ ] **Step 4: 修改 `upsert_job` 签名和实现**

`cli/storage.py:109-127`，修改为：

```python
def upsert_job(
    self,
    event_id: str,
    d_tag: str,
    pubkey: str,
    province_code: int,
    city_code: int,
    content: str,
    created_at: int,
    federation_id: str | None = None,
):
    # Delete existing job with same d_tag (replaceable event)
    self._conn.execute("DELETE FROM jobs WHERE d_tag = ?", (d_tag,))
    self._conn.execute(
        """INSERT INTO jobs
           (event_id, d_tag, pubkey, province_code, city_code, content,
            created_at, received_at, federation_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (event_id, d_tag, pubkey, province_code, city_code,
         content, created_at, int(time.time()), federation_id),
    )
    self._conn.commit()
```

- [ ] **Step 5: 运行测试验证通过**

```bash
cd /home/deeptuuk/Code4/AgentBoss
source /home/deeptuuk/Code4/code_env/bin/activate
python -m pytest tests/test_storage.py::TestJobs::test_upsert_job_with_federation_id tests/test_storage.py::TestJobs::test_upsert_job_federation_id_none -v
```
预期：PASS

- [ ] **Step 6: 提交**

```bash
git add tests/test_storage.py cli/storage.py
git commit -m "feat(storage): add federation_id param to upsert_job"
```

---

## Task 2: 存储层 — `list_jobs` 增加 `federation_name` 筛选参数

**Files:**
- Modify: `cli/storage.py:245-279`（`list_jobs` 方法）
- Test: `tests/test_storage.py` 新增 1 个测试

- [ ] **Step 1: 写失败的测试 — `test_list_jobs_filter_federation`**

在 `tests/test_storage.py` 的 `TestJobSearch` 类中新增：

```python
def test_list_jobs_filter_federation(self, db):
    """list_jobs filters by federation via federation_name."""
    # Setup: create federations and jobs
    db.upsert_federation(
        federation_id="fed1",
        name="techjobs",
        relay_urls=["wss://r1.example.com"],
    )
    db.upsert_job(
        event_id="e1", d_tag="d1", pubkey="p1",
        province_code=110000, city_code=110100,
        content="{}", created_at=1000,
        federation_id="fed1",
    )
    db.upsert_job(
        event_id="e2", d_tag="d2", pubkey="p2",
        province_code=110000, city_code=110100,
        content="{}", created_at=999,
        federation_id="fed2",
    )
    # federation name 不存在返回空
    results = db.list_jobs(federation_name="nonexistent")
    assert results == []
    # 按 name 查询 — 返回 fed1 的职位
    results = db.list_jobs(federation_name="techjobs")
    assert len(results) == 1
    assert results[0]["event_id"] == "e1"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_storage.py::TestJobSearch::test_list_jobs_filter_federation -v
```
预期：FAIL（`list_jobs` 暂无 `federation_name` 参数）

- [ ] **Step 3: 修改 `list_jobs` 签名和实现**

在 `cli/storage.py:245-279`，`list_jobs` 方法：

```python
def list_jobs(
    self,
    province_code: int | None = None,
    city_code: int | None = None,
    favorited: bool | None = None,
    applied: bool | None = None,
    search_query: str | None = None,
    federation_name: str | None = None,
) -> list[dict]:
    query = "SELECT jobs.* FROM jobs LEFT JOIN job_status ON jobs.event_id = job_status.event_id WHERE 1=1"
    params: list = []
    # ... 现有 province/city/favorited/applied/search_query 逻辑不变 ...
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
    if search_query and search_query.strip():
        keywords = search_query.strip().split()
        for keyword in keywords:
            escaped = self._escape_like(keyword)
            pattern = f"%{escaped}%"
            query += (
                " AND (LOWER(json_extract(jobs.content, '$.title')) LIKE ? ESCAPE '\\' COLLATE NOCASE"
                " OR LOWER(json_extract(jobs.content, '$.company')) LIKE ? ESCAPE '\\' COLLATE NOCASE"
                " OR LOWER(json_extract(jobs.content, '$.description')) LIKE ? ESCAPE '\\' COLLATE NOCASE)"
            )
            params.extend([pattern, pattern, pattern])
    # 新增：federation_name 筛选
    if federation_name is not None:
        fed = next(
            (f for f in self.list_federations() if f["name"] == federation_name),
            None,
        )
        if fed is None:
            return []  # federation name 不存在返回空列表
        query += " AND jobs.federation_id = ?"
        params.append(fed["federation_id"])
    query += " ORDER BY jobs.created_at DESC"
    rows = self._conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_storage.py::TestJobSearch::test_list_jobs_filter_federation -v
```
预期：PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_storage.py cli/storage.py
git commit -m "feat(storage): add federation_name filter to list_jobs"
```

---

## Task 3: CLI — `publish --federation` 写入 federation_id

**Files:**
- Modify: `cli/main.py`（`publish` 命令 federation 分支）
- Test: `tests/test_integration.py` 新增 1 个测试

- [ ] **Step 1: 确认 publish 命令 federation 分支现有代码结构**

阅读 `cli/main.py` 第160-200行，确认 `d_tag` 提取位置和 `fed` 对象可用性。

- [ ] **Step 2: 写失败的集成测试**

在 `tests/test_integration.py` 中新增（mock NostrRelay，不发真实网络请求）：

```python
def test_publish_to_federation_persists_federation_id(db, monkeypatch):
    """publish --federation writes federation_id to local storage."""
    from cli.main import publish
    from cli.nostr_client import NostrRelay

    # Setup: create a federation
    db.upsert_federation(
        federation_id="fed_pub_test",
        name="testfed",
        relay_urls=["wss://fake.example.com"],
    )

    # Mock NostrRelay.publish_event to succeed without real network
    async def mock_publish(event):
        return {"event_id": event["id"], "accepted": True, "message": "ok"}

    async def mock_connect():
        pass

    async def mock_close():
        pass

    monkeypatch.setattr(NostrRelay, "connect", mock_connect)
    monkeypatch.setattr(NostrRelay, "close", mock_close)
    monkeypatch.setattr(NostrRelay, "publish_event", mock_publish)

    # Mock identity
    monkeypatch.setattr("cli.main._load_identity", lambda: {
        "privkey": "a" * 64,
        "pubkey": "b" * 64,
        "npub": "npub1test",
    })
    monkeypatch.setattr("cli.main._get_storage", lambda: db)

    # Run publish
    from cli.main import publish
    from typer.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(publish, [
        "--province", "beijing",
        "--city", "beijing",
        "--title", "Engineer",
        "--company", "Corp",
        "--federation", "testfed",
    ])
    assert result.exit_code == 0

    # Verify federation_id was written
    jobs = db.list_jobs()
    assert len(jobs) >= 1
    assert jobs[0]["federation_id"] == "fed_pub_test"
```

- [ ] **Step 3: 运行测试验证失败**

```bash
python -m pytest tests/test_integration.py::test_publish_to_federation_persists_federation_id -v
```
预期：FAIL（`publish` 暂未调用 `storage.upsert_job`）

- [ ] **Step 4: 修改 `publish` 命令 federation 分支**

在 `cli/main.py` 的 `publish` 函数中，找到 `if federation:` 分支，在发布成功后（`typer.echo` 打印前）添加：

```python
if federation:
    fed = next((f for f in storage.list_federations() if f["name"] == federation), None)
    if not fed:
        typer.echo(f"Federation '{federation}' not found. Run: agentboss federation list")
        raise typer.Exit(code=1)
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
        typer.echo(f"Published to {len(relay_urls) - len(failed)}/{len(relay_urls)} federation relays. Failures:")
        for f in failed:
            typer.echo(f"  - {f}")
    else:
        # 提取 d_tag
        d_tag = ""
        for tag in event.get("tags", []):
            if tag[0] == "d":
                d_tag = tag[1]
                break
        storage.upsert_job(
            event_id=event["id"],
            d_tag=d_tag,
            pubkey=event["pubkey"],
            province_code=prov_code,
            city_code=city_code,
            content=event["content"],
            created_at=event["created_at"],
            federation_id=fed["federation_id"],
        )
        typer.echo(f"Published to all {len(relay_urls)} federation relays.")
    return
```

- [ ] **Step 5: 运行测试验证通过**

```bash
python -m pytest tests/test_integration.py::test_publish_to_federation_persists_federation_id -v
```
预期：PASS

- [ ] **Step 6: 提交**

```bash
git add cli/main.py tests/test_integration.py
git commit -m "feat(cli): publish --federation persists federation_id to storage"
```

---

## Task 4: CLI — `fetch --federation` 写入 federation_id

**Files:**
- Modify: `cli/main.py`（`fetch` 命令 federation 分支）
- Test: `tests/test_integration.py` 新增 1 个测试

- [ ] **Step 1: 确认 fetch 命令 federation 分支现有代码结构**

阅读 `cli/main.py` 第232-273行，确认 federation 分支中 `upsert_job` 调用位置。

- [ ] **Step 2: 写失败的集成测试**

```python
def test_fetch_from_federation_persists_federation_id(db):
    """fetch --federation writes federation_id to local storage."""
    from cli.nostr_client import NostrRelay
    import asyncio

    db.upsert_federation(
        federation_id="fed_fetch_test",
        name="fetchfed",
        relay_urls=["wss://fake.example.com"],
    )

    async def mock_fetch_from_relay(url):
        return [{
            "id": "evt_fetch_1",
            "pubkey": "pk1",
            "created_at": 1000,
            "kind": 30078,
            "tags": [["d", "dtag1"], ["t", "agentboss"], ["t", "job"], ["province", "110000"]],
            "content": '{"title":"SRE","company":"Co"}',
        }]

    async def run():
        from cli.main import fetch
        # Patch fetch_events_from_relays
        import cli.main
        orig = cli.main.fetch_events_from_relays
        cli.main.fetch_events_from_relays = mock_fetch_from_relay
        try:
            from typer.testing import CliRunner
            runner = CliRunner()
            result = runner.invoke(fetch, ["--federation", "fetchfed", "--limit", "10"])
            assert result.exit_code == 0
            # Verify
            jobs = db.list_jobs()
            assert len(jobs) >= 1
            assert jobs[0]["federation_id"] == "fed_fetch_test"
        finally:
            cli.main.fetch_events_from_relays = orig

    asyncio.run(run())
```

- [ ] **Step 3: 运行测试验证失败**

```bash
python -m pytest tests/test_integration.py::test_fetch_from_federation_persists_federation_id -v
```
预期：FAIL

- [ ] **Step 4: 修改 `fetch` 命令 federation 分支**

在 `cli/main.py` 的 `fetch` 函数中，找到 federation 分支的 `storage.upsert_job` 调用，添加 `federation_id=fed["federation_id"]` 参数。确认 `fed` 变量在 federation 分支顶部已获取（与 publish 相同的 `fed = next(...)` 逻辑）。

- [ ] **Step 5: 运行测试验证通过**

```bash
python -m pytest tests/test_integration.py::test_fetch_from_federation_persists_federation_id -v
```
预期：PASS

- [ ] **Step 6: 提交**

```bash
git add cli/main.py tests/test_integration.py
git commit -m "feat(cli): fetch --federation persists federation_id to storage"
```

---

## Task 5: CLI — `list` 命令增加 `--federation` 筛选选项

**Files:**
- Modify: `cli/main.py:320`（`list_jobs` 函数签名和实现）
- Test: `tests/test_integration.py` 新增 2 个测试

- [ ] **Step 1: 写失败的集成测试 — `test_list_filter_by_federation`**

```python
def test_list_filter_by_federation(db):
    """list --federation filters jobs by federation."""
    from typer.testing import CliRunner
    from cli.main import list_jobs

    db.upsert_federation("fed_list_1", "listfed1", ["wss://r1"])
    db.upsert_federation("fed_list_2", "listfed2", ["wss://r2"])
    db.upsert_job("id1", "d1", "p", 1, 101, "{}", 1000, federation_id="fed_list_1")
    db.upsert_job("id2", "d2", "p", 1, 101, "{}", 999, federation_id="fed_list_2")

    runner = CliRunner()

    # All jobs
    result = runner.invoke(list_jobs, [])
    assert result.exit_code == 0

    # Filter by federation
    result = runner.invoke(list_jobs, ["--federation", "listfed1"])
    assert result.exit_code == 0
    assert "id1" in result.output
    assert "id2" not in result.output

    # Federation not found — friendly message, no crash
    result = runner.invoke(list_jobs, ["--federation", "nonexistent"])
    assert result.exit_code == 0
```

- [ ] **Step 2: 写失败的集成测试 — `test_list_federation_with_province`**

```python
def test_list_federation_with_province(db):
    """list --federation --province combines filters."""
    from typer.testing import CliRunner
    from cli.main import list_jobs

    db.upsert_federation("fed_comb", "combined", ["wss://r1"])
    db.upsert_job("cid1", "cd1", "p", 110000, 110100, "{}", 1000, federation_id="fed_comb")
    db.upsert_job("cid2", "cd2", "p", 310000, 310100, "{}", 999, federation_id="fed_comb")

    runner = CliRunner()
    result = runner.invoke(list_jobs, ["--federation", "combined", "--province", "beijing"])
    assert result.exit_code == 0
    assert "cid1" in result.output
    assert "cid2" not in result.output
```

- [ ] **Step 3: 运行测试验证失败**

```bash
python -m pytest tests/test_integration.py::test_list_filter_by_federation tests/test_integration.py::test_list_federation_with_province -v
```
预期：FAIL（`list` 命令暂无 `--federation` 选项）

- [ ] **Step 4: 修改 `list_jobs` 命令**

`cli/main.py:320-340` 区域，修改函数签名和实现：

```python
@app.command(name="list")
def list_jobs(
    province: Optional[str] = typer.Option(None, "--province"),
    city: Optional[str] = typer.Option(None, "--city"),
    favorited: bool = typer.Option(False, "--favorited", is_flag=True, help="Show only favorited jobs"),
    applied: bool = typer.Option(False, "--applied", is_flag=True, help="Show only applied jobs"),
    search: Optional[str] = typer.Option(None, "--search", help="Search in title, company, description"),
    federation: Optional[str] = typer.Option(None, "--federation", help="Filter by federation name"),
):
    storage = _get_storage()
    resolver = RegionResolver(storage)

    prov_code = resolver.province_code(province) if province else None
    city_code = resolver.city_code(city) if city else None

    if federation:
        fed = next((f for f in storage.list_federations() if f["name"] == federation), None)
        if not fed:
            typer.echo(f"Federation '{federation}' not found. Run: agentboss federation list")
            return

    # ... 现有 format 和打印逻辑不变 ...
    # 调用 storage.list_jobs 时传入 federation_name 参数
    jobs = storage.list_jobs(
        province_code=prov_code,
        city_code=city_code,
        favorited=favorited,
        applied=applied,
        search_query=search,
        federation_name=federation,
    )
    # ... 后续打印逻辑不变 ...
```

- [ ] **Step 5: 运行测试验证通过**

```bash
python -m pytest tests/test_integration.py::test_list_filter_by_federation tests/test_integration.py::test_list_federation_with_province -v
```
预期：PASS

- [ ] **Step 6: 提交**

```bash
git add cli/main.py tests/test_integration.py
git commit -m "feat(cli): add --federation filter to list command"
```

---

## Task 6: 全量测试验证

- [ ] **Step 1: 运行全部测试**

```bash
cd /home/deeptuuk/Code4/AgentBoss
source /home/deeptuuk/Code4/code_env/bin/activate
python -m pytest tests/ -v --tb=short
```
预期：全部 PASS

- [ ] **Step 2: 推送所有 commits 到远程**

```bash
git push
```

---

## 相关文件

- Spec: `docs/superpowers/specs/2026-03-25-agentboss-federation-job-persistence-design.md`
- Issue: https://github.com/nicholasyangyang/AgentBoss/issues/13
