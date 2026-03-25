# AgentBoss Federation 职位持久化与筛选 — 设计文档

## 背景

`jobs` 表已添加 `federation_id` 列（kind:31970 职位来源追踪），但存储层 `Storage.upsert_job` 无法写入该字段，导致：
- `publish --federation` 发布的职位无法关联来源 federation
- `fetch --federation` 获取的职位无法关联来源 federation
- 用户无法按 federation 筛选本地职位记录

本设计修复该 bug，同时增加 `list --federation` 筛选命令，使 federation_id 字段有可见的使用价值。

---

## 变更 1：存储层修复

### 1.1 `Storage.upsert_job` 签名变更

```python
# cli/storage.py

def upsert_job(
    self,
    event_id: str,
    d_tag: str,
    pubkey: str,
    province_code: int,
    city_code: int,
    content: str,
    created_at: int,
    federation_id: str | None = None,  # 新增
):
```

新增 `federation_id: str | None = None` 参数，默认 `None` 保持向后兼容。

### 1.2 `init_db` 索引条件创建

```python
# cli/storage.py - init_db()

# 现有代码（第76-78行）已检查列存在性，保持不变
existing_cols = [col[1] for col in self._conn.execute("PRAGMA table_info(jobs)").fetchall()]
if "federation_id" not in existing_cols:
    self._conn.execute("ALTER TABLE jobs ADD COLUMN federation_id TEXT")
self._conn.execute(
    "CREATE INDEX IF NOT EXISTS idx_jobs_federation ON jobs(federation_id)"
)
```

`CREATE INDEX IF NOT EXISTS` 在 SQLite 中是幂等的，但如果列不存在会导致索引建立在 NULL 列上。上述代码先检查列存在再 ALTER，逻辑正确，无需修改。

### 1.3 `upsert_job` 实现更新

```python
def upsert_job(self, ..., federation_id: str | None = None):
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

`federation_id` 为 `None` 时写入 NULL，不影响原有行为。

---

## 变更 2：`publish --federation` 写入 federation_id

**文件：** `cli/main.py`

在 `if federation:` 分支中，获取 federation 对象后，将 `fed["federation_id"]` 传入 `storage.upsert_job`：

```python
# main.py publish 函数，if federation: 分支
if federation:
    fed = next((f for f in storage.list_federations() if f["name"] == federation), None)
    if not fed:
        typer.echo(f"Federation '{federation}' not found. Run: agentboss federation list")
        raise typer.Exit(code=1)
    relay_urls = fed["relay_urls"]
    # ... 现有发布逻辑 ...
    # 发布成功后写入，带 federation_id
    storage.upsert_job(
        event_id=event["id"],
        d_tag=d_tag,
        pubkey=event["pubkey"],
        province_code=prov_code,
        city_code=city_code,
        content=event["content"],
        created_at=event["created_at"],
        federation_id=fed["federation_id"],  # 新增
    )
    typer.echo(f"Published to all {len(relay_urls)} federation relays.")
```

注意：`d_tag` 需在 `tags` 中提前提取。

---

## 变更 3：`fetch --federation` 写入 federation_id

**文件：** `cli/main.py`

在 federation 分支的循环中，传入 federation_id：

```python
# main.py fetch 函数，if federation: 分支
if federation:
    fed = next((f for f in storage.list_federations() if f["name"] == federation), None)
    if not fed:
        typer.echo(f"Federation '{federation}' not found.")
        return
    # ... fetch 逻辑 ...
    for event in events:
        # ... 提取 pcode, ccode, d_tag ...
        if has_job_tag and d_tag:
            storage.upsert_job(
                ...,  # 现有参数
                federation_id=fed["federation_id"],  # 新增
            )
            count += 1
```

---

## 变更 4：`list --federation` 筛选命令

### 4.1 `Storage.list_jobs` 新增参数

```python
# cli/storage.py

def list_jobs(
    self,
    province_code: int | None = None,
    city_code: int | None = None,
    favorited: bool | None = None,
    applied: bool | None = None,
    search_query: str | None = None,
    federation_name: str | None = None,  # 新增
) -> list[dict]:
```

实现逻辑：

```python
if federation_name is not None:
    fed = next(
        (f for f in self.list_federations() if f["name"] == federation_name),
        None,
    )
    if fed is None:
        return []  # federation name 不存在返回空列表
    query += " AND jobs.federation_id = ?"
    params.append(fed["federation_id"])
```

### 4.2 CLI 选项

**文件：** `cli/main.py`

在 `list` 命令中添加 `--federation` 选项：

```python
@app.command()
def list(
    province: Optional[str] = typer.Option(None, "--province"),
    city: Optional[str] = typer.Option(None, "--city"),
    favorited: bool = typer.Option(False, "--favorited", "--starred"),
    applied: bool = typer.Option(False, "--applied"),
    search: Optional[str] = typer.Option(None, "--search"),
    federation: Optional[str] = typer.Option(None, "--federation"),
):
```

在 federation 查询为空时打印友好提示：

```python
if federation:
    fed = next((f for f in storage.list_federations() if f["name"] == federation), None)
    if not fed:
        typer.echo(f"Federation '{federation}' not found. Run: agentboss federation list")
        return
```

---

## 变更 5：测试

### 5.1 单元测试（`tests/test_storage.py`）

```python
def test_upsert_job_with_federation_id(self, storage):
    storage.upsert_job(event_id="e1", d_tag="d1", pubkey="p1",
                        province_code=110000, city_code=110100,
                        content='{"title":"A"}', created_at=1000,
                        federation_id="fed123")
    job = storage.get_job("e1")
    assert job["federation_id"] == "fed123"

def test_upsert_job_federation_id_none(self, storage):
    storage.upsert_job(event_id="e2", d_tag="d2", pubkey="p2",
                        province_code=110000, city_code=110100,
                        content='{"title":"B"}', created_at=1000)
    job = storage.get_job("e2")
    assert job["federation_id"] is None

def test_list_jobs_filter_federation(self, storage):
    storage.upsert_federation("fed1", "techjobs", ["wss://r1"])
    storage.upsert_job(event_id="e1", d_tag="d1", pubkey="p1",
                        province_code=110000, city_code=110100,
                        content='{}', created_at=1000, federation_id="fed1")
    storage.upsert_job(event_id="e2", d_tag="d2", pubkey="p2",
                        province_code=110000, city_code=110100,
                        content='{}', created_at=999, federation_id="fed2")
    #  federation name 不存在返回空
    assert storage.list_jobs(federation_name="nonexistent") == []
    # 按 name 查询
    results = storage.list_jobs(federation_name="techjobs")
    assert len(results) == 1
    assert results[0]["event_id"] == "e1"
```

### 5.2 集成测试（`tests/test_integration.py`）

- `test_publish_to_federation_persists_federation_id`：发布到 federation，验证本地存储含 federation_id
- `test_fetch_from_federation_persists_federation_id`：从 federation 获取，验证 federation_id 正确
- `test_list_filter_by_federation`：验证 list --federation 筛选正确
- `test_list_federation_with_province`：验证组合筛选

---

## 设计原则

- **向后兼容**：`federation_id` 参数默认为 `None`，现有调用链无需修改
- **幂等存储**：`upsert` 语义保证同一 `d_tag` 的职位被替换而非重复
- **友好错误**：`list --federation` federation 不存在时返回空列表 + 提示，不抛异常
- **测试覆盖**：存储层、CLI 层、集成层均有覆盖

---

## 相关文件

- `cli/storage.py` — Storage 类
- `cli/main.py` — CLI 命令
- `tests/test_storage.py` — 存储层测试
- `tests/test_integration.py` — 集成测试
