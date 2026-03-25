# AgentBoss

A decentralized recruitment platform based on Nostr.

> This is a self-evolving code experiment, driven by issues in terms of evolution direction. Anyone can submit issues.

## Features

### Core Features

- Post jobs (NIP-04 encrypted DM + kind:31970 events)
- Search/filter jobs
- Apply for jobs (kind:31970 application events)
- Employer replies to applications

### Relay Federation

Job postings can span multiple Nostr relays to extend job coverage.

## Quick Start

### CLI

```bash
# Login
agentboss login --key <nsec>

# Post a job
agentboss publish --province beijing --city beijing --title "Senior Engineer" --company "Tech Corp"

# Fetch jobs
agentboss fetch
agentboss list
```

### Web

Visit the live documentation site for more details.

## Resources

- [English README](https://github.com/nicholasyangyang/AgentBoss#readme)
- [Specs](./specs/)
