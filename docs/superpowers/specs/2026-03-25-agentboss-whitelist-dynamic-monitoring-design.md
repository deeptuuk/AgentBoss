# AgentBoss Feature #6: Whitelist Dynamic Monitoring

## Overview

Add logging and metrics to the existing whitelist dynamic reload behavior in `relay/write_policy.py`. The current implementation already reloads the whitelist file on every `process()` call (via `load_whitelist()`), but provides no observability. This feature adds structured logging and metrics for relay administrators.

## Design Decisions

| Decision | Choice |
|----------|--------|
| Log destination | stdout/stderr + syslog |
| Change detection | mtime comparison (file modification time) |
| Log format | Structured key=value: `timestamp event field=val...` |
| Metrics | 5指标: size, reload_count, check_total, last_reload_ts, reload_duration_seconds |
| Error strategy | Conservative — reject unknown pubkeys on any error |

## Log Format

### whitelist_reload event

```
2026-03-25T10:30:00Z whitelist_reload file_path=/etc/agentboss/whitelist.txt count=15
2026-03-25T10:30:00Z whitelist_reload_error file_path=/etc/agentboss/whitelist.txt error="file missing"
```

Fields: `timestamp`, `event=whitelist_reload`, `file_path`, `count`, `error?`

### whitelist_check event

```
2026-03-25T10:30:01Z whitelist_check pubkey=abc123... event_id=xyz789... action=accept
2026-03-25T10:30:02Z whitelist_check pubkey=def456... event_id=uvw321... action=reject
```

Fields: `timestamp`, `event=whitelist_check`, `pubkey`, `event_id`, `action`

## Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `whitelist_size` | gauge | Current number of pubkeys in whitelist |
| `whitelist_reload_count` | counter | Total number of reloads triggered by mtime change |
| `whitelist_reload_duration_seconds` | histogram | Time taken to reload whitelist file |
| `whitelist_check_total{action="accept\|reject"}` | counter | Total checks by result |
| `whitelist_last_reload_ts` | gauge | Unix timestamp of last successful reload |

Metrics are exposed via a `get_metrics()` function that returns a dict, and also logged to stdout/syslog on each reload.

## Change Detection

```
_cached_mtime: float | None = None
_cached_whitelist: set[str] = {}

def _should_reload(path: str) -> bool:
    if not os.path.exists(path):
        return _cached_mtime is not None  # trigger reload to return empty if file gone
    return os.path.getmtime(path) != _cached_mtime

def _reload_if_needed(path: str) -> set[str]:
    if not _should_reload(path):
        return _cached_whitelist
    new_whitelist = load_whitelist(path)
    # update cache and mtime...
    return _cached_whitelist
```

## Exception Handling

| Scenario | Behavior |
|----------|----------|
| File missing | Return reject, log ERROR + reload to empty whitelist |
| Permission denied | Return reject, log ERROR + reload to empty whitelist |
| Read timeout / OSError | Return reject, log ERROR + reload to empty whitelist |
| File deleted during reload | Use empty whitelist, log WARNING |
| Malformed line (non-hex) | Skip line, log WARNING |

## Implementation

### Changes to `relay/write_policy.py`

```python
import os
import sys
import json
import time
import logging
from datetime import datetime, UTC

WHITELIST_PATH = os.environ.get("AGENTBOSS_WHITELIST", "/etc/agentboss/whitelist.txt")
PROTECTED_KIND = 30078

# Cache
_cached_mtime: float | None = None
_cached_whitelist: set[str] = set()

_syslog_setup = False

def _setup_syslog_once():
    global _syslog_setup
    if _syslog_setup:
        return
    try:
        handler = logging.handlers.SysLogHandler(address="/dev/log")
        _logger.addHandler(handler)
        _syslog_setup = True
    except Exception:
        pass  # syslog unavailable — non-fatal


# Metrics
_metrics = {
    "whitelist_size": 0,
    "whitelist_reload_count": 0,
    "whitelist_check_total_accept": 0,
    "whitelist_check_total_reject": 0,
    "whitelist_last_reload_ts": 0,
    "whitelist_reload_duration_seconds": 0.0,
}

_logger = logging.getLogger("agentboss_whitelist")
_logger.setLevel(logging.DEBUG)
_logger.propagate = False


def _log(msg: str, level: str = "INFO"):
    """Log to stdout and syslog."""
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{timestamp} {msg}"
    print(line, file=sys.stderr if level in ("ERROR", "WARNING") else sys.stdout)
    # syslog fallback — non-fatal if unavailable
    try:
        import logging.handlers
        _setup_syslog_once()
        _logger.log(
            logging.ERROR if level == "ERROR" else (
                logging.WARNING if level == "WARNING" else logging.INFO
            ),
            msg,
        )
    except Exception:
        pass


def _should_reload(path: str) -> bool:
    if not os.path.exists(path):
        # File gone — if we have a cached whitelist, trigger reload to return empty
        return _cached_mtime is not None
    mtime = os.path.getmtime(path)
    return mtime != _cached_mtime


def _is_valid_hex_pubkey(key: str) -> bool:
    """Return True if key is a valid 64-char hex string."""
    return len(key) == 64 and all(c in "0123456789abcdefABCDEF" for c in key)


def load_whitelist(path: str) -> set[str]:
    try:
        with open(path) as f:
            lines = []
            for lineno, line in enumerate(f):
                stripped = line.strip()
                if not stripped:
                    continue
                if not _is_valid_hex_pubkey(stripped):
                    _log(f"whitelist_reload_skip file_path={path} lineno={lineno+1} content='{stripped[:20]}'", "WARNING")
                    continue
                lines.append(stripped)
            return set(lines)
    except FileNotFoundError:
        _log(f"whitelist_reload_error file_path={path} error='file missing'", "ERROR")
        return set()
    except PermissionError:
        _log(f"whitelist_reload_error file_path={path} error='permission denied'", "ERROR")
        return set()
    except OSError as e:
        _log(f"whitelist_reload_error file_path={path} error='{e}'", "ERROR")
        return set()


def _reload_if_needed(path: str) -> set[str]:
    global _cached_mtime, _cached_whitelist, _metrics
    if not _should_reload(path):
        return _cached_whitelist
    start = time.time()
    new_whitelist = load_whitelist(path)
    _cached_whitelist = new_whitelist
    try:
        _cached_mtime = os.path.getmtime(path)
    except OSError:
        _cached_mtime = None  # file deleted during reload
        _log(f"whitelist_reload file_path={path} count={len(new_whitelist)} warning='file deleted during reload'", "WARNING")
        return new_whitelist
    _metrics["whitelist_reload_count"] += 1
    _metrics["whitelist_size"] = len(new_whitelist)
    _metrics["whitelist_last_reload_ts"] = int(time.time())
    _metrics["whitelist_reload_duration_seconds"] = time.time() - start
    _log(f"whitelist_reload file_path={path} count={len(new_whitelist)}")
    return new_whitelist


def process(input_json: str) -> str:
    global _metrics
    msg = json.loads(input_json)
    event = msg.get("event", {})
    event_id = event.get("id", "")
    pubkey = event.get("pubkey", "")
    kind = event.get("kind", 0)

    if kind != PROTECTED_KIND:
        return json.dumps({"id": event_id, "action": "accept"})

    whitelist = _reload_if_needed(WHITELIST_PATH)

    if pubkey in whitelist:
        _metrics["whitelist_check_total_accept"] += 1
        _log(f"whitelist_check pubkey={pubkey} event_id={event_id} action=accept")
        return json.dumps({"id": event_id, "action": "accept"})
    else:
        _metrics["whitelist_check_total_reject"] += 1
        _log(f"whitelist_check pubkey={pubkey} event_id={event_id} action=reject")
        return json.dumps({
            "id": event_id,
            "action": "reject",
            "msg": "blocked: pubkey not on whitelist",
        })


def get_metrics() -> dict:
    """Return current metrics snapshot."""
    return dict(_metrics)
```

## Test Cases

1. `test_reload_on_mtime_change` — file mtime changes → whitelist reloaded
2. `test_no_reload_when_mtime_unchanged` — file unchanged → cached whitelist used
3. `test_reload_on_file_recreated` — file deleted and recreated → reloaded
4. `test_reload_with_15_pubkeys` — 15 pubkeys → count=15 in log and metrics
5. `test_check_accept_logged` — accepted pubkey → log line with action=accept
6. `test_check_reject_logged` — rejected pubkey → log line with action=reject
7. `test_malformed_line_skipped` — invalid hex line → skipped, warning logged
8. `test_missing_file_reject` — file gone → reject returned, error logged
9. `test_get_metrics_returns_all_keys` — get_metrics() has all 6 keys
10. `test_reload_duration_recorded` — duration > 0 after reload
11. `test_file_deleted_during_reload` — file deleted between check and mtime → empty whitelist, WARNING logged
12. `test_non_hex_pubkey_skipped` — line like "notahexkey" → skipped, WARNING logged

## TDD Order

1. `tests/test_write_policy.py` — add whitelist monitoring tests
2. `relay/write_policy.py` — implement logging, metrics, mtime caching
