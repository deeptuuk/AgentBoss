# AgentBoss Feature #1: Job Search Enhancement

## Overview

Add full-text search to the `list` command for filtering jobs by keywords in title, company, and description fields.

## Design Decisions

| Decision | Choice |
|----------|--------|
| Search scope | `title`, `company`, `description` fields (inside `jobs.content` JSON) |
| Matching | Multi-keyword AND — all keywords must appear (space-separated input) |
| Case sensitivity | Case-insensitive — "react" matches "React" |
| Interaction | Extend existing `list` command, `--search` option |
| Storage | Query via SQLite `json_extract` + `LIKE` on specific JSON fields |
| Combination | Combines with `--province`, `--city`, `--favorited`, `--applied` |

## CLI Interface

```
agentboss list --search "React TypeScript"           # AND: title/company/description contains both
agentboss list --search "React" --province 北京       # Combine with region filter
agentboss list --search "Python" --favorited          # Combine with status filter
agentboss list --search "前端" --applied                # Chinese keywords work too
```

### Keyword Parsing

- Input `"React TypeScript"` → keywords `["react", "typescript"]`
- Trim whitespace, ignore empty tokens
- All keywords must match (AND logic)
- Match against lowercase version of searchable fields

## Data Flow

```
CLI: list --search "React TypeScript"
  → main.py: parse keywords, call storage.list_jobs(search=["react", "typescript"])
  → storage.py: SELECT ... WHERE (json_extract(content,'$.title') LIKE ? OR ...)
                     AND (json_extract(content,'$.company') LIKE ? OR ...)
                     AND (json_extract(content,'$.description') LIKE ? OR ...)
  → jobs returned → formatted output with status indicators
```

## Implementation

### Changes to `cli/storage.py`

**Note:** The existing `storage.py` has two `list_jobs` methods — one basic (lines 98-113) and one extended with `favorited`/`applied` (lines 186-209). The second shadows the first. Consolidate into a single unified method.

Add `search: list[str] | None = None` parameter to the unified `list_jobs()`:

```python
import re

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

**Why `json_extract` instead of matching raw JSON:** Substring matching on raw JSON would cause false positives — searching `"act"` would match "React Developer" because "act" is a substring of "React". Using `json_extract` targets the actual field values only.

**Why `ESCAPE '\\'`:** SQLite LIKE treats `%` and `_` as wildcards. Keywords containing these characters (e.g. "C++/100% Remote") must be escaped to match literally. The `_escape_like` helper handles this.

**Why separate OR clauses per keyword:** Multi-keyword AND is achieved by AND-ing separate per-keyword blocks. Each keyword must appear in at least one of title/company/description.

### Changes to `cli/main.py`

Add `--search` option to the existing `list` command:

```python
@app.command(name="list")
def list_jobs(
    province: Optional[str] = typer.Option(None, "--province"),
    city: Optional[str] = typer.Option(None, "--city"),
    favorited: bool = typer.Option(False, "--favorited", is_flag=True),
    applied: bool = typer.Option(False, "--applied", is_flag=True),
    search: Optional[str] = typer.Option(None, "--search", help="Search keywords (space-separated, AND)"),
):
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
    # ... existing output formatting (unchanged) ...
```

### Error Handling

| Scenario | Behavior |
|----------|----------|
| `--search` with no keywords | Treated as no filter, returns all jobs |
| `--search` with empty string | Treated as no filter |
| No matching jobs | "No jobs found." (existing behavior) |

## Test Cases

1. `test_search_single_keyword_title` — single keyword matches title field
2. `test_search_multi_keyword_and` — both keywords must match at least one field
3. `test_search_case_insensitive` — "react" matches "React"
4. `test_search_no_results` — returns empty list
5. `test_search_in_description` — keyword only in description field
6. `test_search_in_company` — keyword only in company field
7. `test_search_combined_with_province` — AND with region filter
8. `test_search_combined_with_favorited` — AND with status filter
9. `test_search_chinese_keywords` — Chinese characters work
10. `test_search_empty_string` — treated as no filter
11. `test_search_substring_false_positive` — "act" does NOT match "React Developer"
12. `test_search_special_chars_escaped` — keywords with `%` or `_` match literally

## TDD Order

1. `tests/test_storage.py` — test `list_jobs(search=...)` with various keyword combinations
2. `cli/storage.py` — consolidate `list_jobs`, add search filter with `json_extract`
3. `tests/test_cli.py` — test `list --search` CLI integration
4. `cli/main.py` — add `--search` option to `list` command
