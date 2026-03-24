# AgentBoss Feature #5: Job Bookmark & Status

## Overview

Add local bookmark/status tracking for job postings. Users can mark jobs as `favorited` or `applied` to manage their job search workflow.

## Design Decisions

| Decision | Choice |
|----------|--------|
| Status types | `favorited` + `applied` (independent, can combine) |
| Storage | Separate `job_status` table (not extending jobs table) |
| Toggle behavior | Independent toggle — repeat command cancels |
| Extensibility | Index-ready for future states (archived, hidden) |

## Data Model

### job_status table

```sql
CREATE TABLE job_status (
    event_id TEXT PRIMARY KEY,
    favorited INTEGER DEFAULT 0,
    applied INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (unixepoch('now')),
    updated_at INTEGER DEFAULT (unixepoch('now'))
);
CREATE INDEX IF NOT EXISTS idx_job_status_event_id ON job_status(event_id);
```

- `event_id` references `jobs.event_id` (foreign key not enforced, MVP simplicity)
- `favorited`/`applied` are integers (0/1) for SQLite compatibility
- Timestamps in Unix epoch seconds

## CLI Commands

### New Commands

```
agentboss favorite <job_id>       # Toggle favorited (on↔off)
agentboss apply <job_id>          # Toggle applied (on↔off)
agentboss status <job_id>         # Show favorited/applied status
```

### Extended Existing Commands

```
agentboss list                        # Existing: all jobs
agentboss list --favorited            # Filter: favorited=1 only
agentboss list --applied             # Filter: applied=1 only
agentboss list --favorited --province 北京   # Combine filters (AND)
agentboss list --applied --city 北京市
agentboss list --favorited --applied  # AND: both true
```

### Toggle Behavior

- `favorite <id>`: if not favorited → set favorited=1; if favorited → set favorited=0
- `apply <id>`: if not applied → set applied=1; if applied → set applied=0

### Error Handling

| Scenario | Behavior |
|----------|----------|
| `favorite/apply <id>` — job not in local DB | Error: "Job not found in local storage. Run `fetch` first." |
| `favorite/apply <id>` — unknown prefix match | Error: "Multiple jobs match prefix. Use full ID." |
| `status <id>` — job not found | Error: "Job not found." |

## Implementation

### Changes to existing files

- `cli/storage.py`: add `job_status` table in `init_db()`, add CRUD methods
- `cli/main.py`: extend `list` command with `--favorited`/`--applied` options; add `favorite`, `apply`, `status` subcommands

### New files

- `tests/test_storage.py`: add tests for `job_status` CRUD
- `tests/test_cli.py`: add tests for new commands

### Storage API (cli/storage.py additions)

```python
def upsert_status(self, event_id: str, favorited: bool | None = None, applied: bool | None = None)
def get_status(self, event_id: str) -> dict | None
def list_status(self, favorited: bool | None = None, applied: bool | None = None) -> list[dict]
```

## Test Cases

1. `test_favorite_toggle_on` — first call sets favorited=1
2. `test_favorite_toggle_off` — second call sets favorited=0
3. `test_apply_toggle` — same for applied
4. `test_list_favorited_filter` — only favorited jobs returned
5. `test_list_applied_filter` — only applied jobs returned
6. `test_list_favorited_and_province` — AND filter works
7. `test_status_not_found` — error on missing job
8. `test_status_shows_both` — returns favorited+applied status

## TDD Order

1. `tests/test_storage.py` — test job_status CRUD
2. `cli/storage.py` — implement job_status methods
3. `tests/test_cli.py` — test favorite/apply/status/list filters
4. `cli/main.py` — implement new commands and extend list
