# AgentBoss Feature #3: User Profile System

## Overview

Add user profile management to AgentBoss CLI. Users can create, update, and publish their profile to the Nostr network as kind:30078 events. Profiles enable job seekers to present themselves to employers in a decentralized, self-sovereign way.

## Design Decisions

| Decision | Choice |
|----------|--------|
| Profile content | Basic: display name, skills tags, bio, work experience summary |
| Storage | Nostr event (kind:30078, `d=profile_<npub>`) |
| Content format | Free-form JSON (extensible) |
| Editing interface | CLI-first with JSON file support (`--json file.json`) |
| Publishing | Signed and published to relay (decentralized, discoverable) |
| Local cache | SQLite `profiles` table mirrors relay data |

## Profile Event Structure

### Nostr Event (kind:30078)

```json
{
  "kind": 30078,
  "pubkey": "<user hex pubkey>",
  "created_at": 1743000000,
  "tags": [
    ["d", "profile_<npub_hex>"],
    ["t", "agentboss"],
    ["t", "profile"]
  ],
  "content": "{\"name\":\"张三\",\"skills\":[\"Python\",\"Rust\",\"Nostr\"],\"bio\":\"5年全栈开发经验\",\"experience\":\"曾任XX公司高级工程师\"}",
  "id": "<sha256>",
  "sig": "<schnorr sig>"
}
```

### Profile JSON Content (example)

```json
{
  "name": "张三",
  "skills": ["Python", "Rust", "Nostr", "SQLite"],
  "bio": "5年全栈开发，专注于分布式系统和去中心化应用",
  "experience": "2020-2024: 某科技公司高级工程师\n2018-2020: 创业公司全栈工程师",
  "contact": "npub1xxx... or email@example.com"
}
```

## CLI Commands

### `profile set`

Create or update local profile (saves to local DB, optionally publishes):

```bash
# Set individual fields
agentboss profile set --name "张三" --skills "Python,Rust" --bio "5年开发经验"

# Set from JSON file
agentboss profile set --json profile.json

# Set and publish immediately
agentboss profile set --name "张三" --publish

# Set and publish to specific relay
agentboss profile set --name "张三" --relay wss://relay.example.com
```

### `profile show`

Display current user's profile:

```bash
agentboss profile show
# Output:
# Name:     张三
# Skills:   Python, Rust, Nostr
# Bio:      5年全栈开发
# Experience: 2020-2024: 某科技公司...
```

### `profile publish`

Publish current local profile to relay(s):

```bash
agentboss profile publish
agentboss profile publish --relay wss://custom-relay.com
```

### `profile fetch`

Fetch a specific user's profile from relay:

```bash
# By npub
agentboss profile fetch npub1xxx...

# By prefix (show all matching)
agentboss profile fetch npub1xxx --relay wss://relay.example.com
```

## Local Storage

### profiles table

```sql
CREATE TABLE profiles (
    pubkey TEXT PRIMARY KEY,
    content TEXT NOT NULL,        -- raw JSON
    name TEXT,                    -- cached for display
    skills TEXT,                  -- comma-separated
    bio TEXT,
    experience TEXT,
    last_updated INTEGER,
    relay_url TEXT                -- last published relay
);
```

## Data Flow

### Publish Profile

```
CLI: profile set --name 张三 --skills Python,Rust --publish
  → main.py: parse args, build profile dict
  → build kind:30078 event with d=profile_<pubkey>
  → sign with local identity private key
  → nostr_client.py: publish to relay
  → storage.py: save to profiles table
```

### Fetch Profile

```
CLI: profile fetch npub1xxx...
  → nostr_client.py: subscribe to relay for kind:30078, d=profile_<target_pubkey>
  → parse event content as JSON
  → storage.py: upsert into profiles table
  → display formatted profile
```

## Implementation

### Changes to `cli/storage.py`

Add `profiles` table and methods:

```python
def upsert_profile(self, pubkey: str, content: str, relay_url: str | None = None):
    data = json.loads(content)
    self._conn.execute("""
        INSERT OR REPLACE INTO profiles
        (pubkey, content, name, skills, bio, experience, last_updated, relay_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pubkey, content,
        data.get("name", ""),
        ",".join(data.get("skills", [])),
        data.get("bio", ""),
        data.get("experience", ""),
        int(time.time()),
        relay_url,
    ))
    self._conn.commit()

def get_profile(self, pubkey: str) -> dict | None:
    row = self._conn.execute(
        "SELECT * FROM profiles WHERE pubkey = ?", (pubkey,)
    ).fetchone()
    return dict(row) if row else None

def get_my_profile(self) -> dict | None:
    # Get current logged-in user's profile from identity.json
    ...
```

### Changes to `cli/main.py`

Add `profile_app` typer subcommand:

```python
profile_app = typer.Typer(help="Profile management")
app.add_typer(profile_app, name="profile")

@profile_app.command(name="set")
def profile_set(
    name: Optional[str] = typer.Option(None, "--name"),
    skills: Optional[str] = typer.Option(None, "--skills"),
    bio: Optional[str] = typer.Option(None, "--bio"),
    experience: Optional[str] = typer.Option(None, "--experience"),
    json_file: Optional[typer.FileText] = typer.Option(None, "--json"),
    publish: bool = typer.Option(False, "--publish"),
    relay: Optional[str] = typer.Option(None, "--relay"),
):
    # Build profile dict from args or JSON file
    # Save to local storage
    # If --publish, sign and publish to relay
    ...

@profile_app.command(name="show")
def profile_show():
    # Load identity, get profile from storage, display
    ...

@profile_app.command(name="publish")
def profile_publish(relay: Optional[str] = None):
    # Load identity, get profile, sign event, publish
    ...

@profile_app.command(name="fetch")
def profile_fetch(target: str, relay: Optional[str] = None):
    # Resolve npub, subscribe to relay, fetch profile event
    ...
```

### Changes to `cli/nostr_client.py`

Add profile-specific methods:

```python
def publish_profile(self, pubkey: str, content: str, privkey: str) -> dict:
    # Build kind:30078 event with d=profile_<pubkey>
    # Sign and publish
    ...

def fetch_profile(self, target_pubkey: str) -> dict | None:
    # Subscribe to relay with filter for kind:30078, d=profile_<target_pubkey>
    # Return first matching event
    ...
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No identity (not logged in) | Error: "Run agentboss login first" |
| Profile not found locally | "No profile found. Run agentboss profile fetch <npub>" |
| Relay publish fails | Retry 3x, then error with partial result |
| Invalid JSON in --json file | Error: "Invalid JSON in file" |
| Target pubkey not found on relay | "Profile not found on relay" |

## Test Cases

1. `test_profile_set_and_get` — set profile via CLI, retrieve from storage
2. `test_profile_set_from_json_file` — set profile from JSON file
3. `test_profile_publish_signed_event` — published event has valid signature
4. `test_profile_show_displays_fields` — all fields formatted correctly
5. `test_profile_fetch_from_relay` — fetches and caches remote profile
6. `test_profile_update_overwrites` — second set replaces first
7. `test_profile_skills_parsed` — skills comma-string parsed into list
8. `test_profile_login_required` — error if not logged in
9. `test_profile_fetch_caches_locally` — fetched profile saved to DB
10. `test_profile_nostr_event_structure` — event has correct kind, tags, content

## TDD Order

1. `tests/test_storage.py` — test profiles table CRUD
2. `cli/storage.py` — add profiles table and methods
3. `tests/test_cli.py` — test profile CLI commands
4. `cli/main.py` — add profile subcommands
5. `cli/nostr_client.py` — add publish_profile, fetch_profile
6. Integration test: publish + fetch round-trip
