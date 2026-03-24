#!/usr/bin/env python3
"""
strfry write policy plugin for AgentBoss.
Reads event from stdin, checks pubkey against whitelist, outputs accept/reject.

Environment:
    AGENTBOSS_WHITELIST: path to whitelist file (default: /etc/agentboss/whitelist.txt)
    AGENTBOSS_LOG_LEVEL: log level (DEBUG, INFO, WARNING, ERROR)
    AGENTBOSS_METRICS_FILE: path to metrics file (optional)
    AGENTBOSS_SYSLOG: syslog address (e.g., localhost:514) to enable syslog
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

WHITELIST_PATH = os.environ.get("AGENTBOSS_WHITELIST", "/etc/agentboss/whitelist.txt")
PROTECTED_KIND = 30078

# Metrics counters
_metrics = {"accept": 0, "reject": 0, "whitelist_reloads": 0}

# Whitelist cache
_whitelist_cache: dict[str, tuple[int, set[str]]] = {}  # path -> (mtime, whitelist_set)


def _setup_logging():
    """Setup structured logging based on AGENTBOSS_LOG_LEVEL."""
    log_level = os.environ.get("AGENTBOSS_LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    formatter = logging.Formatter(
        json.dumps({
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "module": "%(name)s",
            "message": "%(message)s"
        })
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    handler.setLevel(numeric_level)

    logger = logging.getLogger("agentboss_policy")
    logger.setLevel(numeric_level)
    logger.handlers = [handler]

    return logger


def _setup_syslog():
    """Setup syslog handler if AGENTBOSS_SYSLOG is set."""
    syslog_addr = os.environ.get("AGENTBOSS_SYSLOG")
    if not syslog_addr:
        return None

    try:
        import logging.handlers
        handler = logging.handlers.SysLogHandler(address=syslog_addr)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("agentboss: %(message)s")
        handler.setFormatter(formatter)

        logger = logging.getLogger("agentboss_syslog")
        logger.setLevel(logging.INFO)
        logger.handlers = [handler]
        return logger
    except Exception:
        return None


def load_whitelist(path: str) -> set[str]:
    """Load whitelist from file, using mtime-based caching."""
    whitelist_path = Path(path)
    cache_key = path

    try:
        current_mtime = whitelist_path.stat().st_mtime
    except (FileNotFoundError, OSError):
        current_mtime = 0

    # Check cache
    if cache_key in _whitelist_cache:
        cached_mtime, cached_whitelist = _whitelist_cache[cache_key]
        if cached_mtime == current_mtime:
            return cached_whitelist

    # Load fresh
    try:
        with open(path) as f:
            whitelist = {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        whitelist = set()

    # Update cache
    _whitelist_cache[cache_key] = (current_mtime, whitelist)
    _metrics["whitelist_reloads"] += 1

    return whitelist


def process(input_json: str) -> str:
    """Process a single event, returns JSON response."""
    msg = json.loads(input_json)
    event = msg.get("event", {})
    event_id = event.get("id", "")
    pubkey = event.get("pubkey", "")
    kind = event.get("kind", 0)

    logger = _setup_logging()
    syslog_logger = _setup_syslog()

    # Non-protected kinds pass through
    if kind != PROTECTED_KIND:
        _metrics["accept"] += 1
        logger.info(f"accept kind={kind} event_id={event_id[:8]} reason=kind_not_protected")
        return json.dumps({"id": event_id, "action": "accept"})

    whitelist = load_whitelist(WHITELIST_PATH)

    if pubkey in whitelist:
        _metrics["accept"] += 1
        log_msg = f"accept event_id={event_id[:8]} pubkey={pubkey[:8]} reason=whitelisted"
        logger.info(log_msg)
        if syslog_logger:
            syslog_logger.info(log_msg)
        return json.dumps({"id": event_id, "action": "accept"})
    else:
        _metrics["reject"] += 1
        log_msg = f"reject event_id={event_id[:8]} pubkey={pubkey[:8]} reason=not_whitelisted"
        logger.warning(log_msg)
        if syslog_logger:
            syslog_logger.warning(log_msg)
        return json.dumps({
            "id": event_id,
            "action": "reject",
            "msg": "blocked: pubkey not on whitelist",
        })


def get_metrics() -> dict:
    """Return current metrics."""
    return {
        "accept_count": _metrics["accept"],
        "reject_count": _metrics["reject"],
        "whitelist_reloads": _metrics["whitelist_reloads"],
    }


def reset_metrics():
    """Reset metrics counters."""
    _metrics["accept"] = 0
    _metrics["reject"] = 0


if __name__ == "__main__":
    input_data = sys.stdin.read().strip()

    if not input_data:
        print(json.dumps({"error": "empty input"}))
        sys.exit(1)

    # Handle metrics request
    if input_data == '{"type":"metrics"}' or '{"type":"metrics"}' in input_data:
        metrics_file = os.environ.get("AGENTBOSS_METRICS_FILE")
        if metrics_file:
            with open(metrics_file, "w") as f:
                json.dump(get_metrics(), f)
        print(json.dumps(get_metrics()))
        sys.exit(0)

    print(process(input_data))
