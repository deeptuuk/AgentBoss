# AgentBoss Relay Federation Design

> **Spec status:** Draft for review

## Overview

AgentBoss Relay Federation enables job postings to span multiple Nostr relays, expanding job coverage beyond a single relay's user base. Users join "federations" identified by relay lists, and can browse/search jobs from all relays in that federation.

## Architecture

### Core Concepts

- **Federation**: A named group of relays identified by a relay list event (kind:TBD) published by the federation owner
- **Federation ID**: The owner's npub (hex pubkey)
- **Join**: User imports a federation invite code → resolves to relay list → stores locally
- **Multi-write**: Job postings are published to ALL relays in the federation simultaneously
- **Hybrid cache**: Recent jobs cached locally; older jobs queried in real-time from relays

### Data Flow

```
User imports federation invite code
    │
    ▼
Resolve federation ID (npub) to relay list
    │
    ▼
Query relay list event (kind:TBD) from npub
    │
    ▼
Store federation config locally (relay URLs + name)
    │
    ▼
On job fetch:
    ├─ Recent (cached): serve from local SQLite
    └─ Historical (real-time): parallel query all relays, merge dedup
    │
    ▼
On job publish: publish to ALL federation relays simultaneously
```

## Decisions

| Decision | Choice | Rationale |
|----------|--------|----------|
| Sync strategy | Federation subscription (C) | Relay list as federation ID,符合 Nostr 去中心化 |
| Cache strategy | Hybrid (C) | Balance speed vs storage |
| Membership | Invite codes (B) | Shareable, user-friendly |
| Sync protocol | NIP-40 style (A) | Client-side aggregation, no relay changes needed |
| Write strategy | Client multi-write (B) | Immediate visibility, simple |
| Relay list resolution | Simple event (B) | Query npub's kind:TBD event |

## Federation Invite Code Format

```
federation:<npub_hex>:<name>
```

Example: `federation:a1b2c3d4...:techjobs`

### Resolved via:
1. Query relay: `["REQ", "resolve", {"kinds":[TBD], "authors":[<npub_hex>], "#d":["<name>"]}]`
2. Parse event content: JSON array of relay URLs
3. Store locally with federation name

## Event Kinds

| Kind | Name | Purpose |
|------|------|---------|
| TBD | Federation metadata | Relay list + federation name |

Federation metadata event (kind:TBD):
```json
{
  "content": "[\"wss://relay1.example.com\", \"wss://relay2.example.com\"]",
  "tags": [["d", "federation_name"], ["t", "agentboss"], ["t", "federation"]],
  "kind": TBD
}
```

## Storage Schema

### SQLite: federations table
```sql
CREATE TABLE federations (
    federation_id TEXT PRIMARY KEY,   -- npub_hex
    name TEXT NOT NULL,
    relay_urls TEXT NOT NULL,           -- JSON array
    created_at INTEGER NOT NULL,
    updated_at INTEGER DEFAULT (unixepoch('now'))
);
CREATE INDEX idx_federations_name ON federations(name);
```

### SQLite: jobs_cached table (extends existing jobs)
```sql
ALTER TABLE jobs ADD COLUMN federation_id TEXT;
CREATE INDEX idx_jobs_federation ON jobs(federation_id);
```

## CLI Commands

### `federation list`
List all joined federations.

### `federation join <invite_code>`
Join a federation by invite code.
1. Parse `federation:<npub>:<name>`
2. Fetch relay list event from npub
3. Store federation locally

### `federation create <name> <relay1> [relay2 ...]`
Create a new federation.
1. Generate kind:TBD event with relay list
2. Publish to specified relays
3. Store federation locally

### `federation leave <federation_id>`
Leave and delete a federation.

### Modified `fetch` command
- Accept `--federation <name>` to fetch from specific federation
- Parallel query all federation relays, merge + deduplicate by event_id

### Modified `publish` command
- When in a federation, publish to ALL federation relays
- Report per-relay success/failure

## Security Considerations

- Federation owner can update relay list (re-publish event) → clients should re-fetch on connect
- No authentication on federation events — anyone can create any federation
- Employer reputation travels with their npub, not relay

## Open Questions

1. What kind number to use for federation metadata? (propose 31990)
2. Should federations have a time-to-live (TTL) requiring re-sync?
3. How to handle conflicting edits to same job across relays?

## Implementation Priority

1. Storage schema (federations table)
2. Federation join CLI + relay list resolution
3. Federation create CLI
4. Modified fetch (multi-relay parallel query)
5. Modified publish (multi-relay write)
6. Federation leave + list commands
