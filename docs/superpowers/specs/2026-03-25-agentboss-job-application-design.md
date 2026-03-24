# AgentBoss Feature A: Job Application System

## Overview

Enable job seekers to submit applications for job postings and allow employers to accept or reject applications with notification.

## Architecture

```
User submits application
  → Application event (kind:31970) published to relay
  → Encrypted NIP-04 DM sent to employer

Employer responds (accept/reject)
  → Response event (kind:31971) published to relay
  → Encrypted NIP-04 DM sent to applicant
```

**Note:** NIP-04 encryption (`shared/crypto.py`) and DM sending (`NostrRelay.send_dm`) must be implemented first. This is a prerequisite for this feature.

## Event Kinds

| Kind | Purpose | Tags |
|------|---------|------|
| 31970 | Application submission | `d`, `job`, `t=application` |
| 31971 | Application response | `d`, `job`, `status`, `t=application_response` |

## Application Event (kind:31970)

```json
{
  "content": "<applicant message>",
  "tags": [
    ["d", "app_<job_event_id>_<timestamp>"],
    ["job", "<job_event_id>"],
    ["t", "application"]
  ]
}
```

**`d` tag format:** `app_<job_event_id>_<unix_timestamp>` — ensures uniqueness per application per job, with timestamp for ordering.

## Response Event (kind:31971)

```json
{
  "content": "<response message or reason>",
  "tags": [
    ["d", "<application_d_tag>"],
    ["job", "<job_event_id>"],
    ["status", "accepted|rejected"],
    ["t", "application_response"]
  ]
}
```

**`d` tag:** Uses the same `d` tag as the application event (making the response a NIP-33 replaceable event — only the latest response per application is valid).

## CLI Commands

### submit (renamed from "apply" to avoid conflict with existing `apply` status command)

```bash
agentboss submit <job_id> --message "<text>"
```

Submit an application for a job posting.

- `<job_id>`: Job event ID (full or prefix)
- `--message`: Short introduction/cover letter

**Flow:**
1. Load identity (required)
2. Fetch job from storage by ID
3. Create application event (kind:31970) with `d` tag
4. Publish to relay (must succeed)
5. Send NIP-04 DM to job publisher (must succeed — if fails, rollback event)
6. Store application locally with status

### applications list

```bash
agentboss applications list [--status pending|accepted|rejected]
```

List all applications submitted by the user.

- `--status`: Filter by application status (default: all)

### applications respond

```bash
agentboss applications respond <app_id> --accept/--reject [--reason "<text>"]
```

Respond to an application (employer only).

- `<app_id>`: Application event ID
- `--accept`: Accept the application
- `--reject`: Reject the application
- `--reason`: Optional reason/feedback

**Flow:**
1. Load identity (required)
2. Verify user is the job publisher
3. Create response event (kind:31971)
4. Publish to relay
5. Send NIP-04 DM to applicant
6. Update local application status

## Data Flow

### Application Submission

```
CLI: agentboss submit <job_id> --message "Hello"
  → main.py: load identity, get job
  → build kind:31970 event with d="app_<job_id>_<timestamp>"
  → publish to relay (must succeed)
  → encrypt NIP-04 DM to job publisher pubkey
  → send via NostrRelay.send_dm (must succeed or rollback event)
  → store locally: applications table
```

### Application Response

```
CLI: agentboss applications respond <app_id> --accept
  → main.py: load identity, verify publisher
  → build kind:31971 event with d=<application_d_tag>, status=accepted
  → publish to relay (must succeed)
  → encrypt NIP-04 DM to applicant pubkey
  → send via NostrRelay.send_dm (must succeed or rollback event)
  → update local: application status
```

## Storage Schema

### New: applications table

```sql
CREATE TABLE applications (
    event_id TEXT PRIMARY KEY,
    d_tag TEXT NOT NULL,
    job_id TEXT NOT NULL,
    employer_pubkey TEXT NOT NULL,
    applicant_pubkey TEXT NOT NULL,
    message TEXT,
    status TEXT DEFAULT 'pending',
    response_message TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER DEFAULT (unixepoch('now'))
);
```

**Note:** The existing `job_status` table's `applied` boolean remains for local-only bookmarking. The new `applications` table tracks official submitted applications with employer responses. `applied=True` in `job_status` is set automatically when a successful application is submitted.

### Relationship between tables

- When `submit` succeeds: set `job_status.applied=True` for the job
- `applications list` shows entries from `applications` table (not `job_status`)

## NIP-04 DM Encryption

**Implementation prerequisite:** `NIP04.encrypt(plaintext, shared_secret)` and `NIP04.decrypt(ciphertext, shared_secret)` must be implemented in `shared/crypto.py`. `NostrRelay.send_dm(recipient_pubkey, plaintext)` must be added to `cli/nostr_client.py`.

NIP-04 uses AES-256-CTR encryption with a shared secret derived from ECDH key agreement (secp256k1). The shared secret is computed as `sha256(sender_priv || recipient_pub)` where `||` denotes concatenation.

DM content format:
```json
{
  "type": "application",
  "job_id": "<job_event_id>",
  "app_id": "<application_event_id>",
  "action": "submit|accept|reject",
  "message": "<text>"
}
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Not logged in | Error: "Run agentboss login first" |
| Job not found | Error: "Job not found" |
| Already applied | Error: "You have already applied to this job" |
| Not job publisher (respond) | Error: "Only the job publisher can respond" |
| DM send failure | Rollback: delete published event, error to user |
| Event publish failure | Error: "Failed to submit application" |

## Security Considerations

- NIP-04 AES-256-CTR encryption using ECDH-derived shared secret
- Application events are public (employer can verify on relay)
- Only employer can respond (verified by pubkey match)
- DM failure causes full rollback (no orphaned events)
- Applicant pubkey is the event author's pubkey (from event itself, not stored separately)

## Test Cases

1. `test_submit_submits_application` — submit application successfully
2. `test_submit_fails_without_identity` — error without login
3. `test_submit_fails_for_nonexistent_job` — error for invalid job
4. `test_submit_duplicate_rejected` — cannot apply twice
5. `test_applications_list_shows_user_applications` — list own applications
6. `test_applications_list_filters_by_status` — filter by pending/accepted/rejected
7. `test_respond_accepts_application` — employer accepts
8. `test_respond_rejects_with_reason` — employer rejects with reason
9. `test_respond_fails_if_not_employer` — only employer can respond
10. `test_dm_sent_to_employer_on_submit` — DM notification
11. `test_dm_sent_to_applicant_on_respond` — DM notification
12. `test_submit_sets_applied_flag` — job_status.applied=True after submit
13. `test_respond_idempotent` — second respond replaces first response

## Implementation Order

1. **NIP-04 Crypto** — `NIP04.encrypt/decrypt` in `shared/crypto.py` + `NostrRelay.send_dm`
2. **Storage** — `applications` table + CRUD
3. **CLI: submit** — submit application + DM
4. **CLI: applications list** — list own applications
5. **CLI: applications respond** — accept/reject + DM
6. **Integration tests** — full flow
