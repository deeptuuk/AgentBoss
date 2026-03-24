#!/usr/bin/env python3
"""
strfry write policy plugin for AgentBoss.
Reads event from stdin, checks pubkey against whitelist, outputs accept/reject.

Environment:
    AGENTBOSS_WHITELIST: path to whitelist file (default: /etc/agentboss/whitelist.txt)
"""

import json
import os
import sys

WHITELIST_PATH = os.environ.get("AGENTBOSS_WHITELIST", "/etc/agentboss/whitelist.txt")
PROTECTED_KIND = 30078


def load_whitelist(path: str) -> set[str]:
    try:
        with open(path) as f:
            return {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        return set()


def process(input_json: str) -> str:
    msg = json.loads(input_json)
    event = msg.get("event", {})
    event_id = event.get("id", "")
    pubkey = event.get("pubkey", "")
    kind = event.get("kind", 0)

    # Non-protected kinds pass through
    if kind != PROTECTED_KIND:
        return json.dumps({"id": event_id, "action": "accept"})

    whitelist = load_whitelist(WHITELIST_PATH)

    if pubkey in whitelist:
        return json.dumps({"id": event_id, "action": "accept"})
    else:
        return json.dumps({
            "id": event_id,
            "action": "reject",
            "msg": "blocked: pubkey not on whitelist",
        })


if __name__ == "__main__":
    input_data = sys.stdin.read()
    print(process(input_data))
