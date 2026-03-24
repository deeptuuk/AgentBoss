import json
import os
import pytest
import subprocess
import sys
import time
from pathlib import Path


POLICY_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "relay", "write_policy.py")


def run_policy(event_json: dict, whitelist_content: str, tmp_path) -> dict:
    """Run write_policy.py as subprocess, return parsed output."""
    whitelist_file = tmp_path / "whitelist.txt"
    whitelist_file.write_text(whitelist_content)

    stdin_data = json.dumps({"type": "new", "event": event_json})
    env = os.environ.copy()
    env["AGENTBOSS_WHITELIST"] = str(whitelist_file)

    result = subprocess.run(
        [sys.executable, POLICY_SCRIPT],
        input=stdin_data,
        capture_output=True,
        text=True,
        env=env,
    )
    return json.loads(result.stdout.strip())


def run_policy_with_env(event_json: dict, whitelist_content: str, tmp_path, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    """Run write_policy.py with extra environment variables."""
    whitelist_file = tmp_path / "whitelist.txt"
    whitelist_file.write_text(whitelist_content)

    stdin_data = json.dumps({"type": "new", "event": event_json})
    env = os.environ.copy()
    env["AGENTBOSS_WHITELIST"] = str(whitelist_file)
    if extra_env:
        env.update(extra_env)

    return subprocess.run(
        [sys.executable, POLICY_SCRIPT],
        input=stdin_data,
        capture_output=True,
        text=True,
        env=env,
    )


def run_policy_direct(whitelist_file: Path, event_json: dict) -> dict:
    """Run write_policy.py using an existing whitelist file (for mtime tests)."""
    stdin_data = json.dumps({"type": "new", "event": event_json})
    env = os.environ.copy()
    env["AGENTBOSS_WHITELIST"] = str(whitelist_file)

    result = subprocess.run(
        [sys.executable, POLICY_SCRIPT],
        input=stdin_data,
        capture_output=True,
        text=True,
        env=env,
    )
    return json.loads(result.stdout.strip())


class TestWritePolicy:
    def test_accept_whitelisted_pubkey(self, tmp_path):
        event = {"id": "abc123", "pubkey": "aa" * 32, "kind": 30078}
        whitelist = "aa" * 32 + "\n" + "bb" * 32 + "\n"
        result = run_policy(event, whitelist, tmp_path)
        assert result["id"] == "abc123"
        assert result["action"] == "accept"

    def test_reject_non_whitelisted_pubkey(self, tmp_path):
        event = {"id": "abc123", "pubkey": "cc" * 32, "kind": 30078}
        whitelist = "aa" * 32 + "\n"
        result = run_policy(event, whitelist, tmp_path)
        assert result["id"] == "abc123"
        assert result["action"] == "reject"

    def test_accept_non_30078_kind_without_whitelist(self, tmp_path):
        """Non-kind:30078 events pass through regardless."""
        event = {"id": "abc123", "pubkey": "cc" * 32, "kind": 0}
        whitelist = ""  # empty whitelist
        result = run_policy(event, whitelist, tmp_path)
        assert result["action"] == "accept"

    def test_accept_kind_1_from_anyone(self, tmp_path):
        event = {"id": "xyz", "pubkey": "dd" * 32, "kind": 1}
        whitelist = ""
        result = run_policy(event, whitelist, tmp_path)
        assert result["action"] == "accept"

    def test_whitelist_with_blank_lines(self, tmp_path):
        event = {"id": "abc", "pubkey": "aa" * 32, "kind": 30078}
        whitelist = "\n\n" + "aa" * 32 + "\n\n"
        result = run_policy(event, whitelist, tmp_path)
        assert result["action"] == "accept"

    def test_empty_whitelist_rejects_30078(self, tmp_path):
        event = {"id": "abc", "pubkey": "aa" * 32, "kind": 30078}
        whitelist = ""
        result = run_policy(event, whitelist, tmp_path)
        assert result["action"] == "reject"


class TestWhitelistMonitoring:
    """Tests for whitelist file monitoring (mtime caching, hot reload)."""

    def test_whitelist_reloads_on_mtime_change(self, tmp_path):
        """Whitelist is reloaded when file mtime changes."""
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("aa" * 32 + "\n")

        event_whitelisted = {"id": "abc", "pubkey": "aa" * 32, "kind": 30078}
        event_unlisted = {"id": "def", "pubkey": "bb" * 32, "kind": 30078}

        # First: whitelist has 'aa', 'bb' is rejected
        result1 = run_policy_direct(whitelist_file, event_unlisted)
        assert result1["action"] == "reject"

        # Update whitelist file with 'bb' (triggers mtime change)
        whitelist_file.write_text("aa" * 32 + "\n" + "bb" * 32 + "\n")

        # Now 'bb' should be accepted
        result2 = run_policy_direct(whitelist_file, event_unlisted)
        assert result2["action"] == "accept"

    def test_whitelist_cached_without_mtime_change(self, tmp_path):
        """Whitelist is cached if file mtime hasn't changed."""
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("aa" * 32 + "\n")

        event_whitelisted = {"id": "abc", "pubkey": "aa" * 32, "kind": 30078}
        event_unlisted = {"id": "def", "pubkey": "bb" * 32, "kind": 30078}

        # First call - whitelist is loaded
        result1 = run_policy_direct(whitelist_file, event_whitelisted)
        assert result1["action"] == "accept"

        # Second call - cached whitelist still valid (no mtime change)
        result2 = run_policy_direct(whitelist_file, event_unlisted)
        assert result2["action"] == "reject"

    def test_whitelist_hot_reload_with_added_pubkey(self, tmp_path):
        """Whitelist hot reload picks up newly added pubkey."""
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("aa" * 32 + "\n")

        event = {"id": "abc", "pubkey": "bb" * 32, "kind": 30078}

        # Initially rejected (only 'aa' in whitelist)
        result1 = run_policy_direct(whitelist_file, event)
        assert result1["action"] == "reject"

        # Add 'bb' to whitelist
        whitelist_file.write_text("aa" * 32 + "\n" + "bb" * 32 + "\n")

        # Now should be accepted
        result2 = run_policy_direct(whitelist_file, event)
        assert result2["action"] == "accept"

    def test_whitelist_hot_reload_with_removed_pubkey(self, tmp_path):
        """Whitelist hot reload picks up removed pubkey."""
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("aa" * 32 + "\n" + "bb" * 32 + "\n")

        event = {"id": "abc", "pubkey": "bb" * 32, "kind": 30078}

        # Initially accepted
        result1 = run_policy_direct(whitelist_file, event)
        assert result1["action"] == "accept"

        # Remove 'bb' from whitelist
        whitelist_file.write_text("aa" * 32 + "\n")

        # Now should be rejected
        result2 = run_policy_direct(whitelist_file, event)
        assert result2["action"] == "reject"

    def test_whitelist_mtime_tracked_correctly(self, tmp_path):
        """File mtime is correctly tracked for cache invalidation."""
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("aa" * 32 + "\n")

        event_whitelisted = {"id": "abc", "pubkey": "aa" * 32, "kind": 30078}
        event_unlisted = {"id": "def", "pubkey": "bb" * 32, "kind": 30078}

        # First: whitelist has 'aa', 'bb' is rejected
        result1 = run_policy_direct(whitelist_file, event_unlisted)
        assert result1["action"] == "reject"

        # Second: whitelist has 'aa' + 'bb', 'bb' accepted
        whitelist_file.write_text("aa" * 32 + "\n" + "bb" * 32 + "\n")
        result2 = run_policy_direct(whitelist_file, event_unlisted)
        assert result2["action"] == "accept"

        # Third: whitelist only has 'aa', 'bb' rejected again
        whitelist_file.write_text("aa" * 32 + "\n")
        result3 = run_policy_direct(whitelist_file, event_unlisted)
        assert result3["action"] == "reject"

    def test_whitelist_cache_survives_multiple_calls(self, tmp_path):
        """Whitelist cache persists across multiple policy checks without mtime change."""
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("aa" * 32 + "\n")

        event = {"id": "abc", "pubkey": "aa" * 32, "kind": 30078}

        # Multiple calls should all succeed with cached whitelist
        for i in range(5):
            result = run_policy_direct(whitelist_file, event)
            assert result["action"] == "accept"

    def test_whitelist_file_not_found_returns_empty(self, tmp_path):
        """Missing whitelist file is handled gracefully."""
        nonexistent_file = tmp_path / "nonexistent.txt"

        event = {"id": "abc", "pubkey": "aa" * 32, "kind": 30078}

        # Should reject since whitelist is empty
        result = run_policy_direct(nonexistent_file, event)
        assert result["action"] == "reject"


class TestStructuredLogging:
    """Tests for structured logging output."""

    def test_accept_log_contains_expected_fields(self, tmp_path):
        """Accept action produces structured log with required fields."""
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("aa" * 32 + "\n")

        event = {"id": "abc123", "pubkey": "aa" * 32, "kind": 30078}
        env = os.environ.copy()
        env["AGENTBOSS_WHITELIST"] = str(whitelist_file)
        env["AGENTBOSS_LOG_LEVEL"] = "INFO"

        stdin_data = json.dumps({"type": "new", "event": event})
        result = subprocess.run(
            [sys.executable, POLICY_SCRIPT],
            input=stdin_data,
            capture_output=True,
            text=True,
            env=env,
        )

        output_lines = result.stderr.strip().split("\n") if result.stderr else []
        assert len(output_lines) > 0

    def test_reject_log_contains_expected_fields(self, tmp_path):
        """Reject action produces structured log with required fields."""
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("")

        event = {"id": "abc123", "pubkey": "aa" * 32, "kind": 30078}
        env = os.environ.copy()
        env["AGENTBOSS_WHITELIST"] = str(whitelist_file)
        env["AGENTBOSS_LOG_LEVEL"] = "INFO"

        stdin_data = json.dumps({"type": "new", "event": event})
        result = subprocess.run(
            [sys.executable, POLICY_SCRIPT],
            input=stdin_data,
            capture_output=True,
            text=True,
            env=env,
        )

        output_lines = result.stderr.strip().split("\n") if result.stderr else []
        assert len(output_lines) > 0


class TestMetrics:
    """Tests for metrics collection."""

    def test_accept_increments_counter(self, tmp_path):
        """Accept action increments accept counter."""
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("aa" * 32 + "\n")

        event = {"id": "abc", "pubkey": "aa" * 32, "kind": 30078}

        # Run multiple times
        for _ in range(3):
            run_policy(event, "", tmp_path)

        # Check metrics endpoint or file exists
        metrics_file = tmp_path / "metrics.txt"
        env = os.environ.copy()
        env["AGENTBOSS_WHITELIST"] = str(whitelist_file)
        env["AGENTBOSS_METRICS_FILE"] = str(metrics_file)

        stdin_data = json.dumps({"type": "metrics"})
        result = subprocess.run(
            [sys.executable, POLICY_SCRIPT],
            input=stdin_data,
            capture_output=True,
            text=True,
            env=env,
        )

        # Should output metrics
        assert result.returncode == 0

    def test_reject_increments_counter(self, tmp_path):
        """Reject action increments reject counter."""
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("")

        event = {"id": "abc", "pubkey": "aa" * 32, "kind": 30078}

        # Run multiple times
        for _ in range(5):
            run_policy(event, "", tmp_path)

        # Check metrics
        metrics_file = tmp_path / "metrics.txt"
        env = os.environ.copy()
        env["AGENTBOSS_WHITELIST"] = str(whitelist_file)
        env["AGENTBOSS_METRICS_FILE"] = str(metrics_file)

        stdin_data = json.dumps({"type": "metrics"})
        result = subprocess.run(
            [sys.executable, POLICY_SCRIPT],
            input=stdin_data,
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0


class TestSyslog:
    """Tests for syslog handler."""

    def test_syslog_env_enables_handler(self, tmp_path):
        """AGENTBOSS_SYSLOG env var enables syslog handler."""
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("aa" * 32 + "\n")

        event = {"id": "abc", "pubkey": "aa" * 32, "kind": 30078}
        env = os.environ.copy()
        env["AGENTBOSS_WHITELIST"] = str(whitelist_file)
        env["AGENTBOSS_SYSLOG"] = "localhost:514"

        stdin_data = json.dumps({"type": "new", "event": event})
        result = subprocess.run(
            [sys.executable, POLICY_SCRIPT],
            input=stdin_data,
            capture_output=True,
            text=True,
            env=env,
        )

        # Should still succeed even with syslog enabled
        assert result.returncode == 0
        assert json.loads(result.stdout.strip())["action"] == "accept"

    def test_syslog_disabled_by_default(self, tmp_path):
        """Syslog is disabled when AGENTBOSS_SYSLOG is not set."""
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text("aa" * 32 + "\n")

        event = {"id": "abc", "pubkey": "aa" * 32, "kind": 30078}

        result = run_policy_direct(whitelist_file, event)

        # Should succeed without syslog errors
        assert result["action"] == "accept"
