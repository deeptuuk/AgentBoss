# AgentBoss Feature #6: Whitelist Dynamic Monitoring — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add logging and metrics to whitelist dynamic reload in `relay/write_policy.py`.

**Architecture:** Add mtime caching, structured logging to stdout/syslog, and metrics collection. No new files, no breaking changes.

**Tech Stack:** Python 3, stdlib `logging`, `logging.handlers.SysLogHandler`

**Spec:** `docs/superpowers/specs/2026-03-25-agentboss-whitelist-dynamic-monitoring-design.md`

---

## File Map

| File | Change |
|------|--------|
| `relay/write_policy.py` | Add mtime cache, structured logging, metrics, syslog handler |
| `tests/test_write_policy.py` | Add 12 tests for monitoring behavior |

---

## Task 1: Add Tests for Whitelist Monitoring

**Files:**
- Test: `tests/test_write_policy.py`

### Step 1: Write failing tests

Add to `tests/test_write_policy.py`:

```python
import os
import time
import tempfile
from unittest.mock import patch

class TestWhitelistMonitoring:
    def test_reload_on_mtime_change(self, tmp_path):
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("abc123\n")

        # Initialize
        write_policy._cached_mtime = None
        write_policy._cached_whitelist = set()
        result = write_policy.process(json.dumps({
            "event": {"id": "x", "pubkey": "abc123", "kind": 30078}
        }))
        assert result["action"] == "accept"

        # Touch file (update mtime)
        time.sleep(0.01)
        whitelist_file.write_text("abc123\ndef456\n")

        # Should reload — def456 is new
        result2 = write_policy.process(json.dumps({
            "event": {"id": "y", "pubkey": "def456", "kind": 30078}
        }))
        assert result2["action"] == "accept"

    def test_no_reload_when_mtime_unchanged(self, tmp_path):
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("abc123\n")

        write_policy._cached_mtime = None
        write_policy._cached_whitelist = set()

        # First call — caches
        write_policy.process(json.dumps({
            "event": {"id": "x", "pubkey": "abc123", "kind": 30078}
        }))

        # Second call with same mtime — should use cache
        cached = write_policy._cached_whitelist
        result = write_policy.process(json.dumps({
            "event": {"id": "y", "pubkey": "abc123", "kind": 30078}
        }))
        assert result["action"] == "accept"

    def test_check_accept_logged(self, tmp_path, capsys):
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("abc123\n")
        write_policy._cached_mtime = None
        write_policy._cached_whitelist = set()

        result = write_policy.process(json.dumps({
            "event": {"id": "event1", "pubkey": "abc123", "kind": 30078}
        }))
        assert result["action"] == "accept"
        captured = capsys.readouterr().out
        assert "action=accept" in captured

    def test_check_reject_logged(self, tmp_path, capsys):
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("abc123\n")
        write_policy._cached_mtime = None
        write_policy._cached_whitelist = set()

        result = write_policy.process(json.dumps({
            "event": {"id": "event2", "pubkey": "unknown", "kind": 30078}
        }))
        assert result["action"] == "reject"
        captured = capsys.readouterr().out
        assert "action=reject" in captured

    def test_malformed_line_skipped(self, tmp_path, capsys):
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("abc123\nnotahex\ndef456\n")
        write_policy._cached_mtime = None
        write_policy._cached_whitelist = set()

        result = write_policy.process(json.dumps({
            "event": {"id": "x", "pubkey": "abc123", "kind": 30078}
        }))
        assert result["action"] == "accept"
        # notahex is skipped
        result2 = write_policy.process(json.dumps({
            "event": {"id": "y", "pubkey": "notahex", "kind": 30078}
        }))
        assert result2["action"] == "reject"  # not in whitelist

    def test_missing_file_reject(self, tmp_path):
        missing_file = tmp_path / "nonexistent.txt"
        write_policy.WHITELIST_PATH = str(missing_file)
        write_policy._cached_mtime = None
        write_policy._cached_whitelist = set()

        result = write_policy.process(json.dumps({
            "event": {"id": "x", "pubkey": "abc123", "kind": 30078}
        }))
        assert result["action"] == "reject"

    def test_get_metrics_returns_all_keys(self, tmp_path):
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("abc123\n")
        write_policy._cached_mtime = None
        write_policy._cached_whitelist = set()

        write_policy.process(json.dumps({
            "event": {"id": "x", "pubkey": "abc123", "kind": 30078}
        }))
        metrics = write_policy.get_metrics()
        assert "whitelist_size" in metrics
        assert "whitelist_reload_count" in metrics
        assert "whitelist_check_total_accept" in metrics
        assert "whitelist_check_total_reject" in metrics
        assert "whitelist_last_reload_ts" in metrics
        assert "whitelist_reload_duration_seconds" in metrics

    def test_reload_duration_recorded(self, tmp_path):
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("abc123\n")
        write_policy._cached_mtime = None
        write_policy._cached_whitelist = set()

        write_policy.process(json.dumps({
            "event": {"id": "x", "pubkey": "abc123", "kind": 30078}
        }))
        metrics = write_policy.get_metrics()
        assert metrics["whitelist_reload_duration_seconds"] >= 0

    def test_file_deleted_during_reload(self, tmp_path, capsys):
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("abc123\n")
        write_policy._cached_mtime = None
        write_policy._cached_whitelist = set()

        # Cache the file
        write_policy.process(json.dumps({
            "event": {"id": "x", "pubkey": "abc123", "kind": 30078}
        }))

        # Delete the file
        whitelist_file.unlink()
        time.sleep(0.01)

        # Next check — should handle gracefully
        result = write_policy.process(json.dumps({
            "event": {"id": "y", "pubkey": "abc123", "kind": 30078}
        }))
        assert result["action"] == "reject"  # whitelist empty
```

### Step 2: Run tests — FAIL

Run: `python -m pytest tests/test_write_policy.py::TestWhitelistMonitoring -v`
Expected: FAIL — functions don't exist yet

---

## Task 2: Implement Monitoring in write_policy.py

**Files:**
- Modify: `relay/write_policy.py`

### Step 1: Read current write_policy.py

### Step 2: Add imports and module-level state

Add after existing imports:
```python
import os
import sys
import json
import time
import logging
import logging.handlers
from datetime import datetime, UTC

# Module state
_cached_mtime: float | None = None
_cached_whitelist: set[str] = set()
_syslog_setup = False

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
```

### Step 3: Add syslog setup and _log function

```python
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


def _log(msg: str, level: str = "INFO"):
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{timestamp} {msg}"
    print(line, file=sys.stderr if level in ("ERROR", "WARNING") else sys.stdout)
    try:
        _setup_syslog_once()
        _logger.log(
            logging.ERROR if level == "ERROR" else (
                logging.WARNING if level == "WARNING" else logging.INFO
            ),
            msg,
        )
    except Exception:
        pass
```

### Step 4: Add helper functions

```python
def _is_valid_hex_pubkey(key: str) -> bool:
    return len(key) == 64 and all(c in "0123456789abcdefABCDEF" for c in key)


def _should_reload(path: str) -> bool:
    if not os.path.exists(path):
        return _cached_mtime is not None
    return os.path.getmtime(path) != _cached_mtime
```

### Step 5: Update load_whitelist

```python
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
```

### Step 6: Add _reload_if_needed

```python
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
        _cached_mtime = None
        _log(f"whitelist_reload file_path={path} count={len(new_whitelist)} warning='file deleted during reload'", "WARNING")
        return new_whitelist
    _metrics["whitelist_reload_count"] += 1
    _metrics["whitelist_size"] = len(new_whitelist)
    _metrics["whitelist_last_reload_ts"] = int(time.time())
    _metrics["whitelist_reload_duration_seconds"] = time.time() - start
    _log(f"whitelist_reload file_path={path} count={len(new_whitelist)}")
    return new_whitelist
```

### Step 7: Update process() function

In `process()`, replace the direct `load_whitelist()` call with `_reload_if_needed()` and add metrics/logging:
- Call `_reload_if_needed(WHITELIST_PATH)` instead of `load_whitelist(WHITELIST_PATH)`
- On accept: increment `_metrics["whitelist_check_total_accept"]`, log `whitelist_check ... action=accept`
- On reject: increment `_metrics["whitelist_check_total_reject"]`, log `whitelist_check ... action=reject`

### Step 8: Add get_metrics() function

```python
def get_metrics() -> dict:
    return dict(_metrics)
```

### Step 9: Run tests — PASS

Run: `python -m pytest tests/test_write_policy.py::TestWhitelistMonitoring -v`
Expected: all 12 PASS

### Step 10: Run full test suite

Run: `python -m pytest tests/ -v`
Expected: all PASS

### Step 11: Commit

```bash
git add relay/write_policy.py tests/test_write_policy.py
git commit -m "feat: add whitelist dynamic monitoring with logging and metrics"
```
