"""Pytest configuration for integration tests."""

import pytest
from cli.storage import Storage


@pytest.fixture
def cli_home(tmp_path, monkeypatch):
    """Provide a temp AGENTBOSS_HOME and return the path."""
    monkeypatch.setenv("AGENTBOSS_HOME", str(tmp_path))
    return tmp_path
