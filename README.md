> This is a self-evolving code experiment, driven by issues in terms of evolution direction. Anyone can submit issues.

[中文版](README_zh.md)

# AgentBoss

A decentralized recruitment platform based on Nostr.

## Features

### Core Features
- Post jobs (NIP-04 encrypted DM + kind:31970 events)
- Search/filter jobs
- Apply for jobs (kind:31970 application events)
- Employer replies to applications

### Relay Federation
Job postings can span multiple Nostr relays to extend job coverage.

#### Federation Commands
```bash
# Create a Federation
agentboss federation create <name> <relay1> [relay2...]

# Join a Federation
agentboss federation join federation:<npub_hex>:<name>

# List joined Federations
agentboss federation list

# Leave a Federation
agentboss federation leave <federation_id>
```

#### Multi-Relay Operations
```bash
# Fetch jobs from Federation
agentboss fetch --federation <name>

# Publish job to Federation
agentboss publish --federation <name> --province <province> --city <city> --title <title> --company <company>
```

## Installation
```bash
# Create virtual environment with uv
uv venv .env --python 3.12
source .env/bin/activate  # Linux/Mac
# .env\Scripts\activate   # Windows

# Install pip and project
uv pip install pip

# Option 1: pip install
pip install -e .

# Option 2: uv lock for dependency management
uv lock
uv sync
```

## Runtime Environment
Use `uv` to manage virtual environments for consistency:
```bash
# Activate environment (before each operation)
source .env/bin/activate

# Run tests
pytest tests/ -v

# Run CLI
agentboss <command>
```

## Quick Start
```bash
# 1. Login
agentboss login --key <nsec>

# 2. Create a Federation
agentboss federation create techjobs wss://relay1.example.com wss://relay2.example.com

# 3. Post a job
agentboss publish --province beijing --city beijing --title "Senior Engineer" --company "Tech Corp"

# 4. Fetch jobs
agentboss fetch
agentboss list
```

## Job Event (kind:31970)
```json
{
  "content": "{\"title\":\"...\",\"company\":\"...\",\"salary_range\":\"...\",\"description\":\"...\"}",
  "tags": [
    ["d", "<unique-id>"],
    ["t", "agentboss"],
    ["t", "job"],
    ["province", "<code>"],
    ["city", "<code>"]
  ]
}
```

## Federation Invite Code Format
```
federation:<npub_hex>:<name>
```

Federation event (kind:31990):
```json
{
  "content": "[\"wss://relay1.example.com\", \"wss://relay2.example.com\"]",
  "tags": [["d", "<federation_name>"], ["t", "agentboss"], ["t", "federation"]]
}
```
