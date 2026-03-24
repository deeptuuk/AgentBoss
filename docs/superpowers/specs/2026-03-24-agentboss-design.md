# AgentBoss: Decentralized Job Recruitment Platform — Design Spec

## Overview

AgentBoss is a decentralized job recruitment platform built on the Nostr network. Job postings are broadcast publicly via Nostr events, and every node subscribes to receive them. The system consists of three components:

1. **CLI Client** (typer + Python) — publish/fetch/browse job postings
2. **strfry Relay** (C++ with Python write policy) — event relay with whitelist authentication
3. **Registration Website** (FastAPI + Jinja2) — user registration, key generation, whitelist management

Development follows **TDD**: tests are written before implementation code for every module.

## Architecture

```
┌─────────────┐    Register   ┌─────────────┐   Write       ┌──────────────┐
│  Browser     │ ───────────→ │  Web App     │ ───────────→ │ whitelist.txt│
│             │  ← nsec      │  :8000       │              │              │
└─────────────┘              └─────────────┘              └──────┬───────┘
                                                                 │ Read
┌─────────────┐  publish     ┌─────────────┐  write policy  ┌───▼──────────┐
│  CLI Client  │ ───────────→│  strfry      │ ←───────────→ │write_policy  │
│  (typer)    │  ← jobs     │  Relay :7777 │              │  .py         │
└──────┬──────┘              └──────────────┘              └──────────────┘
       │
       │ Store/Query
       ▼
┌─────────────┐
│  SQLite     │
│  (local)    │
└─────────────┘
```

### Deployment (Local Development)

| Component | Address | Tech |
|-----------|---------|------|
| strfry Relay | ws://localhost:7777 | C++ binary + Python write policy |
| Registration Website | http://localhost:8000 | FastAPI + Jinja2 + SQLite |
| CLI Client | local process | typer + aiohttp + SQLite |

## Project Structure

```
AgentBoss/
├── cli/                        # CLI client
│   ├── __init__.py
│   ├── main.py                 # typer entry point
│   ├── nostr_client.py         # Nostr connection, publish, subscribe
│   ├── storage.py              # SQLite local storage
│   ├── regions.py              # Province/City mapping management
│   └── models.py               # Data models
├── relay/                      # strfry customization
│   ├── write_policy.py         # strfry write policy script
│   ├── setup.sh                # strfry installation and config
│   └── strfry.conf             # strfry config template
├── web/                        # Registration website
│   ├── __init__.py
│   ├── app.py                  # FastAPI app
│   ├── auth.py                 # Registration / Key generation
│   ├── db.py                   # User database (SQLite)
│   ├── templates/              # Jinja2 templates
│   │   ├── base.html
│   │   ├── register.html
│   │   └── dashboard.html
│   └── static/                 # CSS/JS
├── shared/                     # Shared code
│   ├── __init__.py
│   ├── crypto.py               # Nostr key generation, Bech32, Schnorr signing
│   ├── event.py                # Nostr Event build/verify
│   └── constants.py            # kind numbers, version, etc.
├── tests/                      # All tests (TDD)
│   ├── test_crypto.py
│   ├── test_event.py
│   ├── test_regions.py
│   ├── test_storage.py
│   ├── test_cli.py
│   ├── test_nostr_client.py
│   ├── test_web_auth.py
│   ├── test_web_api.py
│   └── test_write_policy.py
├── pyproject.toml
└── README.md
```

## Nostr Event Design

### Job Posting Event (kind:30078)

```json
{
  "kind": 30078,
  "pubkey": "<publisher hex pubkey>",
  "created_at": 1711234567,
  "tags": [
    ["d", "<unique identifier, e.g. uuid>"],
    ["t", "agentboss"],
    ["t", "job"],
    ["province", "1"],
    ["city", "101"]
  ],
  "content": "{\"title\":\"Python Developer\",\"company\":\"SomeTech\",\"salary_range\":\"15k-25k\",\"description\":\"...\",\"contact\":\"npub1xxx\",\"version\":1}",
  "id": "<sha256>",
  "sig": "<schnorr signature>"
}
```

**Design decisions:**
- `d` tag: Required by NIP-78, used for deduplication/update (newer event with same `d` value from same pubkey replaces older one)
- `province`/`city` tags: Numeric codes in tags for Relay-side REQ filtering
- `content`: Extensible JSON string with `version` field for schema evolution
- Clients ignore unknown fields for forward compatibility

### Region Mapping Event (kind:30078, different d prefix)

```json
{
  "kind": 30078,
  "tags": [
    ["d", "region_map_v1"],
    ["t", "agentboss"],
    ["t", "region"]
  ],
  "content": "{\"version\":2,\"provinces\":{\"1\":\"北京\",\"2\":\"上海\"},\"cities\":{\"101\":\"北京市\",\"201\":\"上海市\"},\"province_city\":{\"1\":[101],\"2\":[201]}}"
}
```

**Design decisions:**
- Same kind:30078, differentiated by `d` and `t` tags
- `version` increments; nodes only accept mapping with higher version than local
- Only registered users can publish mapping updates (enforced by Relay write policy)
- Incremental expansion: adding new provinces/cities only requires publishing a higher version

## CLI Client Design

### Commands

```bash
# Identity management
agentboss login --key <nsec>
agentboss whoami

# Publish job posting
agentboss publish \
  --province 北京 \
  --city 北京市 \
  --title "Python Developer" \
  --company "SomeTech" \
  --salary "15k-25k" \
  --description "Job description..." \
  --contact "npub1xxx"              # optional, defaults to own npub

# Fetch and browse
agentboss fetch \
  --province 北京 \                 # optional filter
  --city 北京市 \                   # optional filter
  --limit 50                        # max local storage, default 100

agentboss list \
  --province 北京 \                 # optional local filter
  --city 北京市

agentboss show <job_id>

# Region mapping
agentboss regions list
agentboss regions sync
agentboss regions publish

# Configuration
agentboss config set relay <url>
agentboss config set max-jobs 200
agentboss config show
```

### Local SQLite Schema

```sql
-- Job postings
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,            -- Nostr event id
    d_tag TEXT UNIQUE,              -- d tag for dedup/update
    pubkey TEXT NOT NULL,           -- publisher pubkey
    province_code INTEGER,
    city_code INTEGER,
    content TEXT NOT NULL,           -- raw JSON content
    created_at INTEGER NOT NULL,
    received_at INTEGER NOT NULL
);

-- Region mappings
CREATE TABLE regions (
    code INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,              -- 'province' | 'city'
    parent_code INTEGER              -- city's parent province code
);

-- Configuration
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

### Storage Limit Strategy

- `max-jobs` defaults to 100, configurable
- When limit is reached, oldest records by `created_at` are evicted
- `fetch` with `--province`/`--city` builds Relay REQ filter: `["REQ", sub_id, {"kinds":[30078], "#t":["job"], "#province":["1"]}]`

## Registration Website Design

### Pages

| Route | Function |
|-------|----------|
| `/` | Landing page + registration entry |
| `/register` | Registration form (username, email, password) |
| `/login` | Login |
| `/dashboard` | User panel: view npub/nsec, download key, status |

### API Endpoints

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/register` | Create user + generate Nostr keypair + add npub to whitelist |
| POST | `/api/login` | Verify password, return session |
| GET | `/api/me` | Current user info (npub, registration time, status) |
| GET | `/api/key` | Retrieve nsec (only accessible after login) |

### User Database Schema (SQLite)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,       -- bcrypt
    npub TEXT UNIQUE NOT NULL,
    nsec_encrypted TEXT NOT NULL,      -- encrypted with server-side key
    created_at INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1
);
```

### Registration Flow

```
User submits form → Backend validates
  → Generate Nostr keypair (shared/crypto.py)
  → bcrypt hash password, store in DB
  → Encrypt nsec, store in DB
  → Append npub hex to /etc/agentboss/whitelist.txt
  → Display nsec on page (prompt user to save, shown once)
```

## strfry Relay Customization

### Write Policy Script (write_policy.py)

```
stdin:  {"type":"new","event":{"id":"...","pubkey":"...","kind":30078,...}}
stdout: {"id":"...","action":"accept"} or {"id":"...","action":"reject","msg":"Unauthorized"}
```

**Logic:**
1. Load `/etc/agentboss/whitelist.txt` (npub hex list) into memory
2. Extract event `pubkey`
3. If pubkey in whitelist → accept
4. If pubkey not in whitelist → reject
5. Non-kind:30078 events pass through (preserve general Relay capability)
6. Whitelist reloaded periodically (every 60 seconds) to pick up new registrations

### strfry.conf Key Configuration

```
relay {
    info {
        name = "AgentBoss Relay"
        description = "Decentralized job recruitment relay"
    }
    writePolicy {
        plugin = "/opt/agentboss/write_policy.py"
    }
}
```

## Data Flow

### Publish Job Posting

```
CLI → regions.py: convert province/city name to code
    → event.py: build kind:30078 event
    → crypto.py: sign event
    → nostr_client.py: send to Relay
    → strfry: invoke write_policy.py, check whitelist
    → accept → event stored in Relay → broadcast to subscribers
```

### Fetch Job Postings

```
CLI fetch → nostr_client.py: send REQ (filter by province/city)
         → Relay returns matching events
         → models.py: parse and validate
         → storage.py: write to SQLite (dedup by d_tag)
         → evict oldest if over max-jobs limit
```

### Sync Region Mapping

```
CLI regions sync → subscribe to #t=region kind:30078
                → compare version, update only if higher than local
                → write to regions table
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| Relay connection failure | Retry 3 times with exponential backoff (2s→4s→8s), then prompt user |
| Whitelist rejection | CLI receives Relay OK with rejected, displays "Unauthorized, please register first" |
| Unknown province/city name | CLI prompts "Unknown region, run `regions sync` first" |
| SQLite storage full | Auto-evict oldest records, log notification |
| Event signature verification failure | Discard event, log warning |
| Duplicate username/email on registration | Return 400 with specific error message |

## Dependencies

### Python Packages

| Package | Purpose |
|---------|---------|
| typer | CLI framework |
| aiohttp | Async WebSocket for Nostr Relay |
| secp256k1 | Elliptic curve crypto for key generation & signing |
| cryptography | ChaCha20, HMAC, HKDF (NIP-44) |
| fastapi | Web framework |
| uvicorn | ASGI server |
| jinja2 | HTML templates |
| bcrypt | Password hashing |
| python-multipart | Form data parsing |
| aiosqlite | Async SQLite for CLI |
| pytest | Testing framework |
| pytest-asyncio | Async test support |

### External

| Component | Purpose |
|-----------|---------|
| strfry | Nostr Relay server |

## Development Approach

**TDD (Test-Driven Development):** For every module, tests are written BEFORE implementation code.

**Build order:**
1. `shared/` — crypto, event, constants (foundation)
2. `cli/` — storage, regions, models, nostr_client, main
3. `relay/` — write_policy, setup, config
4. `web/` — db, auth, app, templates
