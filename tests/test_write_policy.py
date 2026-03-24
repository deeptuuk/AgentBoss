import json
import os
import pytest
import subprocess
import sys


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
