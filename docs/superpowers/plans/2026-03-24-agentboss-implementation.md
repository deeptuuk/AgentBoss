# AgentBoss Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a decentralized job recruitment platform (CLI + Relay + Registration Website) on the Nostr network.

**Architecture:** Three independent components — a Python CLI client (typer) that publishes/fetches job postings via Nostr events, a strfry Relay with a Python write-policy script for whitelist authentication, and a FastAPI+Jinja2 registration website that generates Nostr keypairs and manages the whitelist. All components share a common crypto library extracted from p2_node.

**Tech Stack:** Python 3.11+, typer, aiohttp, secp256k1, cryptography, FastAPI, Jinja2, SQLite, strfry, pytest

**Spec:** `docs/superpowers/specs/2026-03-24-agentboss-design.md`

**Reference:** `/home/deeptuuk/Code/cc_workdir/p2_node/main.py` (Nostr crypto stack to extract)

---

## File Map

| File | Responsibility |
|------|---------------|
| `shared/__init__.py` | Package init |
| `shared/constants.py` | Kind numbers, app tag, version |
| `shared/crypto.py` | Bech32, secp256k1 key gen, Schnorr sign, event ID hash |
| `shared/event.py` | Build/verify Nostr events, serialize for relay |
| `cli/__init__.py` | Package init |
| `cli/models.py` | Pydantic models for job content, region mapping |
| `cli/storage.py` | SQLite CRUD: jobs, regions, config tables |
| `cli/regions.py` | Province/City name↔code resolution, sync from relay |
| `cli/nostr_client.py` | WebSocket connect, publish EVENT, send REQ, receive events |
| `cli/main.py` | typer app: login, whoami, publish, fetch, list, show, regions, config |
| `relay/write_policy.py` | stdin/stdout strfry plugin: whitelist check |
| `relay/strfry.conf` | strfry config template |
| `relay/setup.sh` | Install/configure strfry + policy script |
| `web/__init__.py` | Package init |
| `web/db.py` | SQLite user table init, CRUD |
| `web/auth.py` | Register (keygen + bcrypt + whitelist), login, session |
| `web/app.py` | FastAPI app, routes, Jinja2 templates |
| `web/templates/base.html` | Base HTML layout |
| `web/templates/register.html` | Registration form |
| `web/templates/login.html` | Login form |
| `web/templates/dashboard.html` | User dashboard (show npub/nsec) |
| `web/static/style.css` | Minimal CSS |
| `tests/test_crypto.py` | Tests for shared/crypto.py |
| `tests/test_event.py` | Tests for shared/event.py |
| `tests/test_models.py` | Tests for cli/models.py |
| `tests/test_storage.py` | Tests for cli/storage.py |
| `tests/test_regions.py` | Tests for cli/regions.py |
| `tests/test_cli.py` | Tests for cli/main.py (typer CliRunner) |
| `tests/test_write_policy.py` | Tests for relay/write_policy.py |
| `tests/test_web_db.py` | Tests for web/db.py |
| `tests/test_web_auth.py` | Tests for web/auth.py |
| `tests/test_web_api.py` | Tests for web/app.py (TestClient) |
| `pyproject.toml` | Project config, dependencies, entry point |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`, `shared/__init__.py`, `shared/constants.py`, `cli/__init__.py`, `web/__init__.py`, `relay/`, `tests/`, `.gitignore`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agentboss"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.9.0",
    "aiohttp>=3.9.0",
    "secp256k1>=0.14.0",
    "cryptography>=41.0.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "jinja2>=3.1.0",
    "bcrypt>=4.0.0",
    "python-multipart>=0.0.6",
    "aiosqlite>=0.19.0",
    "itsdangerous>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
]

[project.scripts]
agentboss = "cli.main:app"
```

- [ ] **Step 2: Create .gitignore**

```
__pycache__/
*.pyc
.venv/
*.db
*.sqlite
.env
dist/
*.egg-info/
```

- [ ] **Step 3: Create package init files and constants**

`shared/__init__.py`: empty file
`cli/__init__.py`: empty file
`web/__init__.py`: empty file

`shared/constants.py`:
```python
APP_TAG = "agentboss"
JOB_TAG = "job"
REGION_TAG = "region"
KIND_APP_DATA = 30078
REGION_MAP_D_TAG = "region_map_v1"
DEFAULT_RELAY = "ws://localhost:7777"
DEFAULT_MAX_JOBS = 100
JOB_CONTENT_VERSION = 1
```

- [ ] **Step 4: Create directory stubs**

Create empty dirs: `relay/`, `tests/`, `web/templates/`, `web/static/`

- [ ] **Step 5: Install dev dependencies and verify**

Run: `cd /home/deeptuuk/Code/cc_workdir/AgentBoss && pip install -e ".[dev]"`
Expected: successful installation

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: scaffold project structure with dependencies"
```

---

## Task 2: shared/crypto.py — Bech32 & Key Generation

**Files:**
- Create: `tests/test_crypto.py`, `shared/crypto.py`
- Reference: `/home/deeptuuk/Code/cc_workdir/p2_node/main.py` lines 23-87

- [ ] **Step 1: Write failing tests**

`tests/test_crypto.py`:
```python
import pytest
from shared.crypto import (
    gen_keys, derive_pub, to_npub, to_nsec,
    npub_to_hex, nsec_to_hex, schnorr_sign,
)


class TestBech32:
    def test_to_npub_roundtrip(self):
        """hex -> npub -> hex should be identity"""
        hex_pub = "a" * 64
        npub = to_npub(hex_pub)
        assert npub.startswith("npub1")
        assert npub_to_hex(npub) == hex_pub

    def test_to_nsec_roundtrip(self):
        hex_sec = "b" * 64
        nsec = to_nsec(hex_sec)
        assert nsec.startswith("nsec1")
        assert nsec_to_hex(nsec) == hex_sec

    def test_npub_to_hex_invalid_prefix(self):
        nsec = to_nsec("cc" * 32)
        with pytest.raises(ValueError, match="not an npub"):
            npub_to_hex(nsec)

    def test_nsec_to_hex_invalid_prefix(self):
        npub = to_npub("dd" * 32)
        with pytest.raises(ValueError, match="not an nsec"):
            nsec_to_hex(npub)


class TestKeyGeneration:
    def test_gen_keys_returns_hex_pair(self):
        priv, pub = gen_keys()
        assert len(priv) == 64
        assert len(pub) == 64
        assert all(c in "0123456789abcdef" for c in priv)
        assert all(c in "0123456789abcdef" for c in pub)

    def test_gen_keys_unique(self):
        k1 = gen_keys()
        k2 = gen_keys()
        assert k1[0] != k2[0]

    def test_derive_pub_matches_gen(self):
        priv, pub = gen_keys()
        assert derive_pub(priv) == pub


class TestSchnorr:
    def test_schnorr_sign_produces_valid_hex(self):
        priv, pub = gen_keys()
        msg = "aa" * 32
        sig = schnorr_sign(msg, priv)
        assert len(sig) == 128
        assert all(c in "0123456789abcdef" for c in sig)

    def test_schnorr_sign_deterministic_for_same_input(self):
        priv, _ = gen_keys()
        msg = "bb" * 32
        sig1 = schnorr_sign(msg, priv)
        sig2 = schnorr_sign(msg, priv)
        # Schnorr with same aux_rand=None should be same
        assert sig1 == sig2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/deeptuuk/Code/cc_workdir/AgentBoss && python -m pytest tests/test_crypto.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.crypto'`

- [ ] **Step 3: Implement shared/crypto.py**

Extract from p2_node/main.py lines 23-87, clean up naming:

```python
"""Nostr cryptographic primitives: Bech32, secp256k1, Schnorr."""

import hashlib
import secrets

import secp256k1

# ── Bech32 encoding/decoding ──────────────────────────────────────────

_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_CHARSET_MAP = {c: i for i, c in enumerate(_CHARSET)}
_GENERATOR = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]


def _polymod(values: list[int]) -> int:
    chk = 1
    for val in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ val
        for i in range(5):
            chk ^= _GENERATOR[i] if (top >> i) & 1 else 0
    return chk


def _hrp_expand(hrp: str) -> list[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _convert_bits(data: bytes, from_bits: int, to_bits: int, pad: bool = True) -> list[int]:
    acc = 0
    bits = 0
    result: list[int] = []
    max_val = (1 << to_bits) - 1
    for val in data:
        acc = (acc << from_bits) | val
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            result.append((acc >> bits) & max_val)
    if pad and bits:
        result.append((acc << (to_bits - bits)) & max_val)
    return result


def _bech32_encode(hrp: str, data: bytes) -> str:
    values = _convert_bits(data, 8, 5)
    polymod = _polymod(_hrp_expand(hrp) + values + [0] * 6) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(_CHARSET[v] for v in values + checksum)


def _bech32_decode(bech: str) -> tuple[str, bytes]:
    bech = bech.lower()
    pos = bech.rfind("1")
    if pos < 1 or pos + 7 > len(bech):
        raise ValueError("invalid bech32 string")
    hrp = bech[:pos]
    try:
        data = [_CHARSET_MAP[c] for c in bech[pos + 1 :]]
    except KeyError:
        raise ValueError("invalid bech32 character")
    if _polymod(_hrp_expand(hrp) + data) != 1:
        raise ValueError("invalid bech32 checksum")
    return hrp, bytes(_convert_bits(data[:-6], 5, 8, pad=False))


def to_npub(hex_pubkey: str) -> str:
    return _bech32_encode("npub", bytes.fromhex(hex_pubkey))


def to_nsec(hex_privkey: str) -> str:
    return _bech32_encode("nsec", bytes.fromhex(hex_privkey))


def npub_to_hex(npub: str) -> str:
    hrp, data = _bech32_decode(npub)
    if hrp != "npub":
        raise ValueError("not an npub")
    return data.hex()


def nsec_to_hex(nsec: str) -> str:
    hrp, data = _bech32_decode(nsec)
    if hrp != "nsec":
        raise ValueError("not an nsec")
    return data.hex()


# ── secp256k1 key generation & signing ────────────────────────────────


def gen_keys() -> tuple[str, str]:
    priv_bytes = secrets.token_bytes(32)
    pub_bytes = secp256k1.PrivateKey(priv_bytes).pubkey.serialize()[1:]
    return priv_bytes.hex(), pub_bytes.hex()


def derive_pub(hex_privkey: str) -> str:
    return secp256k1.PrivateKey(bytes.fromhex(hex_privkey)).pubkey.serialize()[1:].hex()


def schnorr_sign(event_id_hex: str, hex_privkey: str) -> str:
    return secp256k1.PrivateKey(bytes.fromhex(hex_privkey)).schnorr_sign(
        bytes.fromhex(event_id_hex), None, raw=True
    ).hex()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/deeptuuk/Code/cc_workdir/AgentBoss && python -m pytest tests/test_crypto.py -v`
Expected: all 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shared/crypto.py tests/test_crypto.py
git commit -m "feat: add shared crypto module (Bech32, secp256k1, Schnorr)"
```

---

## Task 3: shared/event.py — Nostr Event Build & Verify

**Files:**
- Create: `tests/test_event.py`, `shared/event.py`
- Reference: `/home/deeptuuk/Code/cc_workdir/p2_node/main.py` lines 138-180

- [ ] **Step 1: Write failing tests**

`tests/test_event.py`:
```python
import json
import pytest
from shared.crypto import gen_keys
from shared.event import compute_event_id, build_event, verify_event_id, verify_event_sig


class TestEventId:
    def test_compute_event_id_deterministic(self):
        ev = {
            "pubkey": "aa" * 32,
            "created_at": 1700000000,
            "kind": 30078,
            "tags": [["d", "test"]],
            "content": '{"hello":"world"}',
        }
        id1 = compute_event_id(ev)
        id2 = compute_event_id(ev)
        assert id1 == id2
        assert len(id1) == 64

    def test_compute_event_id_changes_with_content(self):
        base = {
            "pubkey": "aa" * 32,
            "created_at": 1700000000,
            "kind": 30078,
            "tags": [],
        }
        ev1 = {**base, "content": "hello"}
        ev2 = {**base, "content": "world"}
        assert compute_event_id(ev1) != compute_event_id(ev2)

    def test_verify_event_id_correct(self):
        ev = {
            "pubkey": "bb" * 32,
            "created_at": 1700000000,
            "kind": 1,
            "tags": [],
            "content": "test",
        }
        ev["id"] = compute_event_id(ev)
        assert verify_event_id(ev) is True

    def test_verify_event_id_tampered(self):
        ev = {
            "pubkey": "bb" * 32,
            "created_at": 1700000000,
            "kind": 1,
            "tags": [],
            "content": "test",
        }
        ev["id"] = "00" * 32
        assert verify_event_id(ev) is False


class TestBuildEvent:
    def test_build_event_has_all_fields(self):
        priv, pub = gen_keys()
        ev = build_event(
            kind=30078,
            content='{"title":"test"}',
            privkey=priv,
            pubkey=pub,
            tags=[["d", "job1"], ["t", "agentboss"]],
        )
        assert ev["kind"] == 30078
        assert ev["pubkey"] == pub
        assert ev["content"] == '{"title":"test"}'
        assert ev["tags"] == [["d", "job1"], ["t", "agentboss"]]
        assert "id" in ev
        assert "sig" in ev
        assert "created_at" in ev

    def test_build_event_sig_is_valid(self):
        priv, pub = gen_keys()
        ev = build_event(kind=1, content="hello", privkey=priv, pubkey=pub)
        assert verify_event_id(ev) is True
        assert verify_event_sig(ev) is True


class TestVerifyEventSig:
    def test_verify_event_sig_tampered_content(self):
        priv, pub = gen_keys()
        ev = build_event(kind=1, content="original", privkey=priv, pubkey=pub)
        ev["content"] = "tampered"
        # id no longer matches, sig no longer valid
        assert verify_event_id(ev) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_event.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.event'`

- [ ] **Step 3: Implement shared/event.py**

```python
"""Nostr event construction and verification."""

import hashlib
import json
import time

import secp256k1

from shared.crypto import schnorr_sign


def compute_event_id(event: dict) -> str:
    serialized = json.dumps(
        [
            0,
            event["pubkey"],
            event["created_at"],
            event["kind"],
            event["tags"],
            event["content"],
        ],
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(serialized.encode()).hexdigest()


def verify_event_id(event: dict) -> bool:
    return compute_event_id(event) == event.get("id")


def verify_event_sig(event: dict) -> bool:
    try:
        # pubkey is raw 32-byte hex (from gen_keys / derive_pub)
        pub = secp256k1.PublicKey(bytes.fromhex(event["pubkey"]), raw=True)
        return pub.schnorr_verify(
            bytes.fromhex(event["id"]),
            bytes.fromhex(event["sig"]),
            None,
            raw=True,
        )
    except Exception:
        return False


def build_event(
    kind: int,
    content: str,
    privkey: str,
    pubkey: str,
    tags: list[list[str]] | None = None,
    created_at: int | None = None,
) -> dict:
    event = {
        "pubkey": pubkey,
        "created_at": created_at or int(time.time()),
        "kind": kind,
        "tags": tags or [],
        "content": content,
    }
    event["id"] = compute_event_id(event)
    event["sig"] = schnorr_sign(event["id"], privkey)
    return event
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_event.py -v`
Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shared/event.py tests/test_event.py
git commit -m "feat: add Nostr event build and verify module"
```

---

## Task 4: cli/models.py — Data Models

**Files:**
- Create: `tests/test_models.py`, `cli/models.py`

- [ ] **Step 1: Write failing tests**

`tests/test_models.py`:
```python
import json
import pytest
from cli.models import JobContent, RegionMapping, parse_job_content, parse_region_mapping


class TestJobContent:
    def test_parse_valid_job(self):
        raw = json.dumps({
            "title": "Python Developer",
            "company": "SomeTech",
            "salary_range": "15k-25k",
            "description": "Build things",
            "contact": "npub1xxx",
            "version": 1,
        })
        job = parse_job_content(raw)
        assert job.title == "Python Developer"
        assert job.company == "SomeTech"
        assert job.salary_range == "15k-25k"
        assert job.version == 1

    def test_parse_job_with_extra_fields(self):
        """Forward compatibility: unknown fields are preserved"""
        raw = json.dumps({
            "title": "Dev",
            "company": "Co",
            "version": 1,
            "future_field": "value",
        })
        job = parse_job_content(raw)
        assert job.title == "Dev"
        assert job.extra["future_field"] == "value"

    def test_parse_job_missing_title_raises(self):
        raw = json.dumps({"company": "Co", "version": 1})
        with pytest.raises(ValueError):
            parse_job_content(raw)

    def test_job_to_json_roundtrip(self):
        raw = json.dumps({
            "title": "Dev",
            "company": "Co",
            "version": 1,
        })
        job = parse_job_content(raw)
        restored = parse_job_content(job.to_json())
        assert restored.title == job.title
        assert restored.company == job.company


class TestRegionMapping:
    def test_parse_valid_mapping(self):
        raw = json.dumps({
            "version": 1,
            "provinces": {"1": "北京", "2": "上海"},
            "cities": {"101": "北京市", "201": "上海市"},
            "province_city": {"1": [101], "2": [201]},
        })
        mapping = parse_region_mapping(raw)
        assert mapping.version == 1
        assert mapping.provinces["1"] == "北京"
        assert mapping.cities["101"] == "北京市"
        assert mapping.province_city["1"] == [101]

    def test_name_to_code_province(self):
        raw = json.dumps({
            "version": 1,
            "provinces": {"1": "北京", "2": "上海"},
            "cities": {},
            "province_city": {},
        })
        mapping = parse_region_mapping(raw)
        assert mapping.province_name_to_code("北京") == "1"
        assert mapping.province_name_to_code("不存在") is None

    def test_name_to_code_city(self):
        raw = json.dumps({
            "version": 1,
            "provinces": {},
            "cities": {"101": "北京市", "201": "上海市"},
            "province_city": {},
        })
        mapping = parse_region_mapping(raw)
        assert mapping.city_name_to_code("北京市") == "101"
        assert mapping.city_name_to_code("不存在") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement cli/models.py**

```python
"""Data models for job content and region mapping."""

import json
from dataclasses import dataclass, field


_JOB_KNOWN_FIELDS = {"title", "company", "salary_range", "description", "contact", "version"}


@dataclass
class JobContent:
    title: str
    company: str
    version: int = 1
    salary_range: str = ""
    description: str = ""
    contact: str = ""
    extra: dict = field(default_factory=dict)

    def to_json(self) -> str:
        data = {
            "title": self.title,
            "company": self.company,
            "version": self.version,
        }
        if self.salary_range:
            data["salary_range"] = self.salary_range
        if self.description:
            data["description"] = self.description
        if self.contact:
            data["contact"] = self.contact
        data.update(self.extra)
        return json.dumps(data, ensure_ascii=False)


def parse_job_content(raw_json: str) -> JobContent:
    data = json.loads(raw_json)
    if "title" not in data:
        raise ValueError("missing required field: title")
    if "company" not in data:
        raise ValueError("missing required field: company")
    extra = {k: v for k, v in data.items() if k not in _JOB_KNOWN_FIELDS}
    return JobContent(
        title=data["title"],
        company=data["company"],
        version=data.get("version", 1),
        salary_range=data.get("salary_range", ""),
        description=data.get("description", ""),
        contact=data.get("contact", ""),
        extra=extra,
    )


@dataclass
class RegionMapping:
    version: int
    provinces: dict[str, str]  # code -> name
    cities: dict[str, str]  # code -> name
    province_city: dict[str, list[int]]  # province_code -> [city_codes]

    def province_name_to_code(self, name: str) -> str | None:
        for code, n in self.provinces.items():
            if n == name:
                return code
        return None

    def city_name_to_code(self, name: str) -> str | None:
        for code, n in self.cities.items():
            if n == name:
                return code
        return None


def parse_region_mapping(raw_json: str) -> RegionMapping:
    data = json.loads(raw_json)
    return RegionMapping(
        version=data["version"],
        provinces=data.get("provinces", {}),
        cities=data.get("cities", {}),
        province_city=data.get("province_city", {}),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_models.py -v`
Expected: all 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add cli/models.py tests/test_models.py
git commit -m "feat: add job content and region mapping data models"
```

---

## Task 5: cli/storage.py — SQLite Local Storage

**Files:**
- Create: `tests/test_storage.py`, `cli/storage.py`

- [ ] **Step 1: Write failing tests**

`tests/test_storage.py`:
```python
import os
import pytest
import sqlite3
from cli.storage import Storage


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    s = Storage(db_path)
    s.init_db()
    yield s
    s.close()


class TestStorageInit:
    def test_creates_tables(self, db):
        tables = db.list_tables()
        assert "jobs" in tables
        assert "regions" in tables
        assert "config" in tables


class TestConfig:
    def test_set_and_get(self, db):
        db.set_config("relay", "ws://localhost:7777")
        assert db.get_config("relay") == "ws://localhost:7777"

    def test_get_missing_returns_default(self, db):
        assert db.get_config("missing", "default") == "default"

    def test_set_overwrites(self, db):
        db.set_config("key", "v1")
        db.set_config("key", "v2")
        assert db.get_config("key") == "v2"


class TestJobs:
    def test_upsert_and_get(self, db):
        db.upsert_job(
            event_id="id1",
            d_tag="d1",
            pubkey="pub1",
            province_code=1,
            city_code=101,
            content='{"title":"Dev"}',
            created_at=1000,
        )
        job = db.get_job("id1")
        assert job is not None
        assert job["d_tag"] == "d1"
        assert job["province_code"] == 1

    def test_upsert_replaces_by_d_tag(self, db):
        db.upsert_job("id1", "d1", "pub1", 1, 101, '{"v":1}', 1000)
        db.upsert_job("id2", "d1", "pub1", 1, 101, '{"v":2}', 2000)
        # old id1 should be gone, id2 should exist
        assert db.get_job("id1") is None
        assert db.get_job("id2") is not None

    def test_list_jobs_filter_province(self, db):
        db.upsert_job("id1", "d1", "p", 1, 101, "{}", 1000)
        db.upsert_job("id2", "d2", "p", 2, 201, "{}", 1000)
        jobs = db.list_jobs(province_code=1)
        assert len(jobs) == 1
        assert jobs[0]["event_id"] == "id1"

    def test_list_jobs_filter_city(self, db):
        db.upsert_job("id1", "d1", "p", 1, 101, "{}", 1000)
        db.upsert_job("id2", "d2", "p", 1, 102, "{}", 1000)
        jobs = db.list_jobs(city_code=102)
        assert len(jobs) == 1
        assert jobs[0]["event_id"] == "id2"

    def test_evict_oldest_when_over_limit(self, db):
        for i in range(5):
            db.upsert_job(f"id{i}", f"d{i}", "p", 1, 101, "{}", created_at=i)
        db.evict_oldest(max_count=3)
        remaining = db.list_jobs()
        assert len(remaining) == 3
        # oldest (created_at=0,1) should be evicted
        ids = [j["event_id"] for j in remaining]
        assert "id0" not in ids
        assert "id1" not in ids

    def test_count_jobs(self, db):
        db.upsert_job("id1", "d1", "p", 1, 101, "{}", 1000)
        db.upsert_job("id2", "d2", "p", 1, 101, "{}", 1000)
        assert db.count_jobs() == 2


class TestRegions:
    def test_upsert_and_get_region(self, db):
        db.upsert_region(code=1, name="北京", region_type="province")
        r = db.get_region(1)
        assert r["name"] == "北京"
        assert r["type"] == "province"

    def test_upsert_city_with_parent(self, db):
        db.upsert_region(1, "北京", "province")
        db.upsert_region(101, "北京市", "city", parent_code=1)
        r = db.get_region(101)
        assert r["parent_code"] == 1

    def test_list_provinces(self, db):
        db.upsert_region(1, "北京", "province")
        db.upsert_region(2, "上海", "province")
        db.upsert_region(101, "北京市", "city", parent_code=1)
        provinces = db.list_regions(region_type="province")
        assert len(provinces) == 2

    def test_get_region_version(self, db):
        """Region version stored in config"""
        assert db.get_config("region_version", "0") == "0"
        db.set_config("region_version", "3")
        assert db.get_config("region_version") == "3"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_storage.py -v`
Expected: FAIL

- [ ] **Step 3: Implement cli/storage.py**

```python
"""SQLite local storage for jobs, regions, and config."""

import sqlite3
import time


class Storage:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    def init_db(self):
        cur = self._conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                event_id TEXT PRIMARY KEY,
                d_tag TEXT UNIQUE,
                pubkey TEXT NOT NULL,
                province_code INTEGER,
                city_code INTEGER,
                content TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                received_at INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS regions (
                code INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                parent_code INTEGER
            );
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def close(self):
        self._conn.close()

    def list_tables(self) -> list[str]:
        cur = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        return [row["name"] for row in cur.fetchall()]

    # ── Config ──

    def set_config(self, key: str, value: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )
        self._conn.commit()

    def get_config(self, key: str, default: str | None = None) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    # ── Jobs ──

    def upsert_job(
        self,
        event_id: str,
        d_tag: str,
        pubkey: str,
        province_code: int,
        city_code: int,
        content: str,
        created_at: int,
    ):
        # Delete existing job with same d_tag (replaceable event)
        self._conn.execute("DELETE FROM jobs WHERE d_tag = ?", (d_tag,))
        self._conn.execute(
            """INSERT INTO jobs
               (event_id, d_tag, pubkey, province_code, city_code, content, created_at, received_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, d_tag, pubkey, province_code, city_code, content, created_at, int(time.time())),
        )
        self._conn.commit()

    def get_job(self, event_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE event_id = ?", (event_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_jobs(
        self,
        province_code: int | None = None,
        city_code: int | None = None,
    ) -> list[dict]:
        query = "SELECT * FROM jobs WHERE 1=1"
        params: list = []
        if province_code is not None:
            query += " AND province_code = ?"
            params.append(province_code)
        if city_code is not None:
            query += " AND city_code = ?"
            params.append(city_code)
        query += " ORDER BY created_at DESC"
        rows = self._conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def count_jobs(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as cnt FROM jobs").fetchone()
        return row["cnt"]

    def evict_oldest(self, max_count: int):
        count = self.count_jobs()
        if count <= max_count:
            return
        to_delete = count - max_count
        self._conn.execute(
            "DELETE FROM jobs WHERE event_id IN "
            "(SELECT event_id FROM jobs ORDER BY created_at ASC LIMIT ?)",
            (to_delete,),
        )
        self._conn.commit()

    # ── Regions ──

    def upsert_region(
        self,
        code: int,
        name: str,
        region_type: str,
        parent_code: int | None = None,
    ):
        self._conn.execute(
            "INSERT OR REPLACE INTO regions (code, name, type, parent_code) VALUES (?, ?, ?, ?)",
            (code, name, region_type, parent_code),
        )
        self._conn.commit()

    def get_region(self, code: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM regions WHERE code = ?", (code,)
        ).fetchone()
        return dict(row) if row else None

    def list_regions(self, region_type: str | None = None) -> list[dict]:
        if region_type:
            rows = self._conn.execute(
                "SELECT * FROM regions WHERE type = ? ORDER BY code", (region_type,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM regions ORDER BY code"
            ).fetchall()
        return [dict(r) for r in rows]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_storage.py -v`
Expected: all 12 tests PASS

- [ ] **Step 5: Commit**

```bash
git add cli/storage.py tests/test_storage.py
git commit -m "feat: add SQLite storage for jobs, regions, and config"
```

---

## Task 6: cli/regions.py — Region Name/Code Resolution

**Files:**
- Create: `tests/test_regions.py`, `cli/regions.py`

- [ ] **Step 1: Write failing tests**

`tests/test_regions.py`:
```python
import json
import pytest
from cli.storage import Storage
from cli.regions import RegionResolver


@pytest.fixture
def db(tmp_path):
    s = Storage(str(tmp_path / "test.db"))
    s.init_db()
    yield s
    s.close()


@pytest.fixture
def resolver(db):
    return RegionResolver(db)


class TestRegionResolver:
    def test_apply_mapping_populates_db(self, resolver, db):
        mapping_json = json.dumps({
            "version": 1,
            "provinces": {"1": "北京", "2": "上海"},
            "cities": {"101": "北京市", "201": "上海市"},
            "province_city": {"1": [101], "2": [201]},
        })
        resolver.apply_mapping(mapping_json)
        assert db.get_region(1)["name"] == "北京"
        assert db.get_region(101)["name"] == "北京市"
        assert db.get_region(101)["parent_code"] == 1
        assert db.get_config("region_version") == "1"

    def test_apply_mapping_skips_older_version(self, resolver, db):
        v2 = json.dumps({
            "version": 2,
            "provinces": {"1": "北京"},
            "cities": {},
            "province_city": {},
        })
        v1 = json.dumps({
            "version": 1,
            "provinces": {"1": "旧北京"},
            "cities": {},
            "province_city": {},
        })
        resolver.apply_mapping(v2)
        resolver.apply_mapping(v1)  # should be ignored
        assert db.get_region(1)["name"] == "北京"

    def test_resolve_province_name_to_code(self, resolver):
        resolver.apply_mapping(json.dumps({
            "version": 1,
            "provinces": {"1": "北京"},
            "cities": {},
            "province_city": {},
        }))
        assert resolver.province_code("北京") == 1
        assert resolver.province_code("不存在") is None

    def test_resolve_city_name_to_code(self, resolver):
        resolver.apply_mapping(json.dumps({
            "version": 1,
            "provinces": {},
            "cities": {"101": "北京市"},
            "province_city": {},
        }))
        assert resolver.city_code("北京市") == 101
        assert resolver.city_code("不存在") is None

    def test_province_name_from_code(self, resolver):
        resolver.apply_mapping(json.dumps({
            "version": 1,
            "provinces": {"1": "北京"},
            "cities": {},
            "province_city": {},
        }))
        assert resolver.province_name(1) == "北京"
        assert resolver.province_name(999) is None

    def test_city_name_from_code(self, resolver):
        resolver.apply_mapping(json.dumps({
            "version": 1,
            "provinces": {},
            "cities": {"101": "北京市"},
            "province_city": {},
        }))
        assert resolver.city_name(101) == "北京市"
        assert resolver.city_name(999) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_regions.py -v`
Expected: FAIL

- [ ] **Step 3: Implement cli/regions.py**

```python
"""Province/City region resolution using local SQLite storage."""

import json
from cli.storage import Storage
from cli.models import parse_region_mapping


class RegionResolver:
    def __init__(self, storage: Storage):
        self._storage = storage

    def apply_mapping(self, mapping_json: str):
        mapping = parse_region_mapping(mapping_json)
        current_version = int(self._storage.get_config("region_version", "0"))
        if mapping.version <= current_version:
            return
        for code_str, name in mapping.provinces.items():
            self._storage.upsert_region(int(code_str), name, "province")
        for code_str, name in mapping.cities.items():
            parent = None
            for prov_code, city_codes in mapping.province_city.items():
                if int(code_str) in city_codes:
                    parent = int(prov_code)
                    break
            self._storage.upsert_region(int(code_str), name, "city", parent_code=parent)
        self._storage.set_config("region_version", str(mapping.version))

    def province_code(self, name: str) -> int | None:
        for r in self._storage.list_regions(region_type="province"):
            if r["name"] == name:
                return r["code"]
        return None

    def city_code(self, name: str) -> int | None:
        for r in self._storage.list_regions(region_type="city"):
            if r["name"] == name:
                return r["code"]
        return None

    def province_name(self, code: int) -> str | None:
        r = self._storage.get_region(code)
        return r["name"] if r and r["type"] == "province" else None

    def city_name(self, code: int) -> str | None:
        r = self._storage.get_region(code)
        return r["name"] if r and r["type"] == "city" else None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_regions.py -v`
Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add cli/regions.py tests/test_regions.py
git commit -m "feat: add region resolver for province/city name-code mapping"
```

---

## Task 7: cli/nostr_client.py — Nostr WebSocket Client

**Files:**
- Create: `tests/test_nostr_client.py`, `cli/nostr_client.py`

- [ ] **Step 1: Write failing tests**

`tests/test_nostr_client.py`:
```python
import json
import pytest
from cli.nostr_client import (
    build_req_filter,
    build_event_message,
    build_close_message,
    parse_relay_message,
)
from shared.crypto import gen_keys
from shared.event import build_event


class TestMessageBuilders:
    def test_build_req_filter_basic(self):
        req = build_req_filter(
            sub_id="sub1",
            kinds=[30078],
            tags={"#t": ["agentboss", "job"]},
        )
        parsed = json.loads(req)
        assert parsed[0] == "REQ"
        assert parsed[1] == "sub1"
        assert parsed[2]["kinds"] == [30078]
        assert parsed[2]["#t"] == ["agentboss", "job"]

    def test_build_req_filter_with_province(self):
        req = build_req_filter(
            sub_id="sub2",
            kinds=[30078],
            tags={"#t": ["agentboss", "job"], "#province": ["1"]},
        )
        parsed = json.loads(req)
        assert parsed[2]["#province"] == ["1"]

    def test_build_req_filter_with_limit(self):
        req = build_req_filter(sub_id="s", kinds=[30078], limit=50)
        parsed = json.loads(req)
        assert parsed[2]["limit"] == 50

    def test_build_event_message(self):
        priv, pub = gen_keys()
        ev = build_event(kind=1, content="hello", privkey=priv, pubkey=pub)
        msg = build_event_message(ev)
        parsed = json.loads(msg)
        assert parsed[0] == "EVENT"
        assert parsed[1]["id"] == ev["id"]

    def test_build_close_message(self):
        msg = build_close_message("sub1")
        parsed = json.loads(msg)
        assert parsed == ["CLOSE", "sub1"]


class TestParseRelayMessage:
    def test_parse_event_message(self):
        raw = json.dumps(["EVENT", "sub1", {"id": "abc", "kind": 30078}])
        msg_type, data = parse_relay_message(raw)
        assert msg_type == "EVENT"
        assert data["sub_id"] == "sub1"
        assert data["event"]["id"] == "abc"

    def test_parse_eose_message(self):
        raw = json.dumps(["EOSE", "sub1"])
        msg_type, data = parse_relay_message(raw)
        assert msg_type == "EOSE"
        assert data["sub_id"] == "sub1"

    def test_parse_ok_accepted(self):
        raw = json.dumps(["OK", "eventid1", True, ""])
        msg_type, data = parse_relay_message(raw)
        assert msg_type == "OK"
        assert data["event_id"] == "eventid1"
        assert data["accepted"] is True

    def test_parse_ok_rejected(self):
        raw = json.dumps(["OK", "eventid1", False, "blocked: not on whitelist"])
        msg_type, data = parse_relay_message(raw)
        assert msg_type == "OK"
        assert data["accepted"] is False
        assert "whitelist" in data["message"]

    def test_parse_notice(self):
        raw = json.dumps(["NOTICE", "some error"])
        msg_type, data = parse_relay_message(raw)
        assert msg_type == "NOTICE"
        assert data["message"] == "some error"

    def test_parse_unknown(self):
        raw = json.dumps(["UNKNOWN", "data"])
        msg_type, data = parse_relay_message(raw)
        assert msg_type == "UNKNOWN"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_nostr_client.py -v`
Expected: FAIL

- [ ] **Step 3: Implement cli/nostr_client.py**

```python
"""Nostr WebSocket client: message builders, parsers, and relay connection."""

import json
import asyncio
import aiohttp


def build_req_filter(
    sub_id: str,
    kinds: list[int],
    tags: dict[str, list[str]] | None = None,
    limit: int | None = None,
) -> str:
    filter_obj: dict = {"kinds": kinds}
    if tags:
        filter_obj.update(tags)
    if limit is not None:
        filter_obj["limit"] = limit
    return json.dumps(["REQ", sub_id, filter_obj])


def build_event_message(event: dict) -> str:
    return json.dumps(["EVENT", event])


def build_close_message(sub_id: str) -> str:
    return json.dumps(["CLOSE", sub_id])


def parse_relay_message(raw: str) -> tuple[str, dict]:
    msg = json.loads(raw)
    msg_type = msg[0]

    if msg_type == "EVENT":
        return "EVENT", {"sub_id": msg[1], "event": msg[2]}
    elif msg_type == "EOSE":
        return "EOSE", {"sub_id": msg[1]}
    elif msg_type == "OK":
        return "OK", {
            "event_id": msg[1],
            "accepted": msg[2],
            "message": msg[3] if len(msg) > 3 else "",
        }
    elif msg_type == "NOTICE":
        return "NOTICE", {"message": msg[1]}
    elif msg_type == "CLOSED":
        return "CLOSED", {"sub_id": msg[1], "message": msg[2] if len(msg) > 2 else ""}
    else:
        return "UNKNOWN", {"raw": msg}


class NostrRelay:
    """Single relay WebSocket connection."""

    def __init__(self, url: str):
        self.url = url
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._session: aiohttp.ClientSession | None = None

    async def connect(self):
        self._session = aiohttp.ClientSession()
        self._ws = await self._session.ws_connect(self.url)

    async def close(self):
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()

    async def send(self, message: str):
        if not self._ws:
            raise RuntimeError("not connected")
        await self._ws.send_str(message)

    async def publish_event(self, event: dict) -> dict:
        await self.send(build_event_message(event))
        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                msg_type, data = parse_relay_message(msg.data)
                if msg_type == "OK" and data["event_id"] == event["id"]:
                    return data
        return {"event_id": event["id"], "accepted": False, "message": "no response"}

    async def subscribe(self, sub_id: str, kinds: list[int], tags: dict | None = None, limit: int | None = None):
        req = build_req_filter(sub_id, kinds, tags, limit)
        await self.send(req)

    async def receive_events(self, sub_id: str):
        """Yield events until EOSE."""
        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                msg_type, data = parse_relay_message(msg.data)
                if msg_type == "EVENT" and data["sub_id"] == sub_id:
                    yield data["event"]
                elif msg_type == "EOSE" and data["sub_id"] == sub_id:
                    break

    async def unsubscribe(self, sub_id: str):
        await self.send(build_close_message(sub_id))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_nostr_client.py -v`
Expected: all 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add cli/nostr_client.py tests/test_nostr_client.py
git commit -m "feat: add Nostr WebSocket client with message builders and parser"
```

---

## Task 8: cli/main.py — CLI Entry Point (typer)

**Files:**
- Create: `tests/test_cli.py`, `cli/main.py`

- [ ] **Step 1: Write failing tests**

`tests/test_cli.py`:
```python
import json
import os
import pytest
from typer.testing import CliRunner
from cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def cli_home(tmp_path, monkeypatch):
    """Set CLI data directory to tmp for all tests."""
    monkeypatch.setenv("AGENTBOSS_HOME", str(tmp_path))
    return tmp_path


class TestLogin:
    def test_login_saves_key(self, cli_home):
        # Use a real-format nsec (but we'll mock validation)
        result = runner.invoke(app, ["login", "--key", "aa" * 32])
        assert result.exit_code == 0
        key_file = cli_home / "identity.json"
        assert key_file.exists()

    def test_login_invalid_key_rejected(self):
        result = runner.invoke(app, ["login", "--key", "tooshort"])
        assert result.exit_code != 0 or "Invalid" in result.stdout


class TestWhoami:
    def test_whoami_no_key(self):
        result = runner.invoke(app, ["whoami"])
        assert "No identity" in result.stdout or result.exit_code != 0

    def test_whoami_with_key(self, cli_home):
        runner.invoke(app, ["login", "--key", "aa" * 32])
        result = runner.invoke(app, ["whoami"])
        assert result.exit_code == 0
        assert "npub" in result.stdout


class TestConfig:
    def test_config_set_and_show(self, cli_home):
        runner.invoke(app, ["config", "set", "relay", "ws://localhost:7777"])
        result = runner.invoke(app, ["config", "show"])
        assert "ws://localhost:7777" in result.stdout

    def test_config_set_max_jobs(self, cli_home):
        runner.invoke(app, ["config", "set", "max-jobs", "50"])
        result = runner.invoke(app, ["config", "show"])
        assert "50" in result.stdout


class TestRegionsList:
    def test_regions_list_empty(self, cli_home):
        result = runner.invoke(app, ["regions", "list"])
        assert result.exit_code == 0


class TestListJobs:
    def test_list_empty(self, cli_home):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No jobs" in result.stdout or result.stdout.strip() == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL

- [ ] **Step 3: Implement cli/main.py**

```python
"""AgentBoss CLI — decentralized job recruitment on Nostr."""

import json
import os
import asyncio
from pathlib import Path
from typing import Optional

import typer

from shared.constants import (
    APP_TAG, JOB_TAG, REGION_TAG, KIND_APP_DATA,
    REGION_MAP_D_TAG, DEFAULT_RELAY, DEFAULT_MAX_JOBS, JOB_CONTENT_VERSION,
)
from shared.crypto import gen_keys, derive_pub, to_npub, nsec_to_hex, to_nsec
from shared.event import build_event
from cli.storage import Storage
from cli.regions import RegionResolver
from cli.models import parse_job_content
from cli.nostr_client import NostrRelay

app = typer.Typer(help="AgentBoss: Decentralized Job Recruitment CLI")
regions_app = typer.Typer(help="Region mapping management")
config_app = typer.Typer(help="Configuration management")
app.add_typer(regions_app, name="regions")
app.add_typer(config_app, name="config")


def _home() -> Path:
    return Path(os.environ.get("AGENTBOSS_HOME", Path.home() / ".agentboss"))


def _ensure_home() -> Path:
    home = _home()
    home.mkdir(parents=True, exist_ok=True)
    return home


def _get_storage() -> Storage:
    home = _ensure_home()
    s = Storage(str(home / "agentboss.db"))
    s.init_db()
    return s


def _load_identity() -> dict | None:
    path = _home() / "identity.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _save_identity(privkey: str, pubkey: str):
    path = _ensure_home() / "identity.json"
    path.write_text(json.dumps({
        "nsec": to_nsec(privkey),
        "npub": to_npub(pubkey),
        "privkey": privkey,
        "pubkey": pubkey,
    }))


# ── Identity ──

@app.command()
def login(key: str = typer.Option(..., "--key", help="Private key (nsec or 64-char hex)")):
    """Import identity from nsec or hex private key."""
    try:
        if key.startswith("nsec1"):
            privkey = nsec_to_hex(key)
        elif len(key) == 64 and all(c in "0123456789abcdef" for c in key.lower()):
            privkey = key.lower()
        else:
            typer.echo("Invalid key format. Use nsec1... or 64-char hex.")
            raise typer.Exit(code=1)
        pubkey = derive_pub(privkey)
        _save_identity(privkey, pubkey)
        typer.echo(f"Logged in as {to_npub(pubkey)}")
    except Exception as e:
        typer.echo(f"Invalid key: {e}")
        raise typer.Exit(code=1)


@app.command()
def whoami():
    """Show current identity."""
    identity = _load_identity()
    if not identity:
        typer.echo("No identity found. Run: agentboss login --key <nsec>")
        raise typer.Exit(code=1)
    typer.echo(f"npub: {identity['npub']}")
    typer.echo(f"hex:  {identity['pubkey']}")


# ── Publish ──

@app.command()
def publish(
    province: str = typer.Option(..., "--province"),
    city: str = typer.Option(..., "--city"),
    title: str = typer.Option(..., "--title"),
    company: str = typer.Option(..., "--company"),
    salary: str = typer.Option("", "--salary"),
    description: str = typer.Option("", "--description"),
    contact: str = typer.Option("", "--contact"),
):
    """Publish a job posting to the Nostr network."""
    identity = _load_identity()
    if not identity:
        typer.echo("No identity. Run: agentboss login --key <nsec>")
        raise typer.Exit(code=1)

    storage = _get_storage()
    resolver = RegionResolver(storage)

    prov_code = resolver.province_code(province)
    if prov_code is None:
        typer.echo(f"Unknown province '{province}'. Run: agentboss regions sync")
        raise typer.Exit(code=1)

    city_code = resolver.city_code(city)
    if city_code is None:
        typer.echo(f"Unknown city '{city}'. Run: agentboss regions sync")
        raise typer.Exit(code=1)

    import uuid
    content = json.dumps({
        "title": title,
        "company": company,
        "salary_range": salary,
        "description": description,
        "contact": contact or identity["npub"],
        "version": JOB_CONTENT_VERSION,
    }, ensure_ascii=False)

    tags = [
        ["d", str(uuid.uuid4())],
        ["t", APP_TAG],
        ["t", JOB_TAG],
        ["province", str(prov_code)],
        ["city", str(city_code)],
    ]

    event = build_event(
        kind=KIND_APP_DATA,
        content=content,
        privkey=identity["privkey"],
        pubkey=identity["pubkey"],
        tags=tags,
    )

    relay_url = storage.get_config("relay", DEFAULT_RELAY)

    async def _publish():
        relay = NostrRelay(relay_url)
        try:
            await relay.connect()
            result = await relay.publish_event(event)
            if result["accepted"]:
                typer.echo(f"Published: {event['id'][:16]}...")
            else:
                typer.echo(f"Rejected: {result['message']}")
        finally:
            await relay.close()

    asyncio.run(_publish())
    storage.close()


# ── Fetch ──

@app.command()
def fetch(
    province: Optional[str] = typer.Option(None, "--province"),
    city: Optional[str] = typer.Option(None, "--city"),
    limit: int = typer.Option(DEFAULT_MAX_JOBS, "--limit"),
):
    """Fetch job postings from Relay and store locally."""
    storage = _get_storage()
    resolver = RegionResolver(storage)
    relay_url = storage.get_config("relay", DEFAULT_RELAY)

    tags = {"#t": [APP_TAG, JOB_TAG]}
    if province:
        prov_code = resolver.province_code(province)
        if prov_code is None:
            typer.echo(f"Unknown province '{province}'. Run: agentboss regions sync")
            raise typer.Exit(code=1)
        tags["#province"] = [str(prov_code)]
    if city:
        city_code = resolver.city_code(city)
        if city_code is None:
            typer.echo(f"Unknown city '{city}'. Run: agentboss regions sync")
            raise typer.Exit(code=1)
        tags["#city"] = [str(city_code)]

    async def _fetch():
        relay = NostrRelay(relay_url)
        count = 0
        try:
            await relay.connect()
            await relay.subscribe("fetch", kinds=[KIND_APP_DATA], tags=tags, limit=limit)
            async for event in relay.receive_events("fetch"):
                # Extract province/city from tags
                pcode = ccode = 0
                for tag in event.get("tags", []):
                    if tag[0] == "province":
                        pcode = int(tag[1])
                    elif tag[0] == "city":
                        ccode = int(tag[1])
                d_tag = ""
                for tag in event.get("tags", []):
                    if tag[0] == "d":
                        d_tag = tag[1]
                # Only store job events (not region maps)
                has_job_tag = any(t[0] == "t" and t[1] == JOB_TAG for t in event.get("tags", []))
                if has_job_tag and d_tag:
                    storage.upsert_job(
                        event_id=event["id"],
                        d_tag=d_tag,
                        pubkey=event["pubkey"],
                        province_code=pcode,
                        city_code=ccode,
                        content=event["content"],
                        created_at=event["created_at"],
                    )
                    count += 1
            await relay.unsubscribe("fetch")
        finally:
            await relay.close()
        max_jobs = int(storage.get_config("max-jobs", str(DEFAULT_MAX_JOBS)))
        storage.evict_oldest(max_jobs)
        typer.echo(f"Fetched {count} jobs. Total stored: {storage.count_jobs()}")

    asyncio.run(_fetch())
    storage.close()


# ── List ──

@app.command(name="list")
def list_jobs(
    province: Optional[str] = typer.Option(None, "--province"),
    city: Optional[str] = typer.Option(None, "--city"),
):
    """List locally stored job postings."""
    storage = _get_storage()
    resolver = RegionResolver(storage)

    prov_code = None
    city_code_val = None
    if province:
        prov_code = resolver.province_code(province)
    if city:
        city_code_val = resolver.city_code(city)

    jobs = storage.list_jobs(province_code=prov_code, city_code=city_code_val)
    if not jobs:
        typer.echo("No jobs found.")
        storage.close()
        return

    for job in jobs:
        try:
            content = parse_job_content(job["content"])
            pname = resolver.province_name(job["province_code"]) or str(job["province_code"])
            cname = resolver.city_name(job["city_code"]) or str(job["city_code"])
            typer.echo(f"[{job['event_id'][:12]}] {content.title} @ {content.company} | {pname}/{cname} | {content.salary_range}")
        except Exception:
            typer.echo(f"[{job['event_id'][:12]}] (parse error)")
    storage.close()


# ── Show ──

@app.command()
def show(job_id: str = typer.Argument(..., help="Event ID (full or prefix)")):
    """Show details of a job posting."""
    storage = _get_storage()
    resolver = RegionResolver(storage)

    # Support prefix match
    job = storage.get_job(job_id)
    if not job:
        jobs = storage.list_jobs()
        for j in jobs:
            if j["event_id"].startswith(job_id):
                job = j
                break
    if not job:
        typer.echo("Job not found.")
        storage.close()
        raise typer.Exit(code=1)

    content = parse_job_content(job["content"])
    pname = resolver.province_name(job["province_code"]) or str(job["province_code"])
    cname = resolver.city_name(job["city_code"]) or str(job["city_code"])

    typer.echo(f"ID:          {job['event_id']}")
    typer.echo(f"Title:       {content.title}")
    typer.echo(f"Company:     {content.company}")
    typer.echo(f"Location:    {pname} / {cname}")
    typer.echo(f"Salary:      {content.salary_range}")
    typer.echo(f"Description: {content.description}")
    typer.echo(f"Contact:     {content.contact}")
    typer.echo(f"Publisher:   {job['pubkey']}")
    typer.echo(f"Posted:      {job['created_at']}")
    storage.close()


# ── Regions ──

@regions_app.command(name="list")
def regions_list():
    """List local region mappings."""
    storage = _get_storage()
    provinces = storage.list_regions(region_type="province")
    cities = storage.list_regions(region_type="city")
    if not provinces and not cities:
        typer.echo("No region mappings. Run: agentboss regions sync")
        storage.close()
        return
    typer.echo("Provinces:")
    for p in provinces:
        typer.echo(f"  {p['code']}: {p['name']}")
    typer.echo("Cities:")
    for c in cities:
        parent = f" (province: {c['parent_code']})" if c["parent_code"] else ""
        typer.echo(f"  {c['code']}: {c['name']}{parent}")
    storage.close()


@regions_app.command(name="sync")
def regions_sync():
    """Sync region mappings from Relay."""
    storage = _get_storage()
    resolver = RegionResolver(storage)
    relay_url = storage.get_config("relay", DEFAULT_RELAY)

    async def _sync():
        relay = NostrRelay(relay_url)
        try:
            await relay.connect()
            await relay.subscribe(
                "region_sync",
                kinds=[KIND_APP_DATA],
                tags={"#t": [APP_TAG, REGION_TAG]},
                limit=1,
            )
            async for event in relay.receive_events("region_sync"):
                resolver.apply_mapping(event["content"])
                typer.echo(f"Region mapping updated.")
            await relay.unsubscribe("region_sync")
        finally:
            await relay.close()

    asyncio.run(_sync())
    storage.close()


@regions_app.command(name="publish")
def regions_publish():
    """Publish region mapping to Relay (requires identity)."""
    identity = _load_identity()
    if not identity:
        typer.echo("No identity. Run: agentboss login --key <nsec>")
        raise typer.Exit(code=1)

    storage = _get_storage()
    relay_url = storage.get_config("relay", DEFAULT_RELAY)

    # Build mapping from local DB
    provinces = {str(r["code"]): r["name"] for r in storage.list_regions("province")}
    cities = {str(r["code"]): r["name"] for r in storage.list_regions("city")}
    province_city: dict[str, list[int]] = {}
    for c in storage.list_regions("city"):
        if c["parent_code"] is not None:
            key = str(c["parent_code"])
            province_city.setdefault(key, []).append(c["code"])

    current_version = int(storage.get_config("region_version", "0"))
    new_version = current_version + 1

    content = json.dumps({
        "version": new_version,
        "provinces": provinces,
        "cities": cities,
        "province_city": province_city,
    }, ensure_ascii=False)

    event = build_event(
        kind=KIND_APP_DATA,
        content=content,
        privkey=identity["privkey"],
        pubkey=identity["pubkey"],
        tags=[["d", REGION_MAP_D_TAG], ["t", APP_TAG], ["t", REGION_TAG]],
    )

    async def _publish():
        relay = NostrRelay(relay_url)
        try:
            await relay.connect()
            result = await relay.publish_event(event)
            if result["accepted"]:
                storage.set_config("region_version", str(new_version))
                typer.echo(f"Region mapping v{new_version} published.")
            else:
                typer.echo(f"Rejected: {result['message']}")
        finally:
            await relay.close()

    asyncio.run(_publish())
    storage.close()


# ── Config ──

@config_app.command(name="set")
def config_set(key: str = typer.Argument(...), value: str = typer.Argument(...)):
    """Set a config value."""
    storage = _get_storage()
    storage.set_config(key, value)
    typer.echo(f"Set {key} = {value}")
    storage.close()


@config_app.command(name="show")
def config_show():
    """Show all config."""
    storage = _get_storage()
    relay = storage.get_config("relay", DEFAULT_RELAY)
    max_jobs = storage.get_config("max-jobs", str(DEFAULT_MAX_JOBS))
    typer.echo(f"relay:    {relay}")
    typer.echo(f"max-jobs: {max_jobs}")
    storage.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_cli.py -v`
Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add cli/main.py tests/test_cli.py
git commit -m "feat: add CLI entry point with login, publish, fetch, list, show, regions, config"
```

---

## Task 9: relay/write_policy.py — strfry Write Policy

**Files:**
- Create: `tests/test_write_policy.py`, `relay/write_policy.py`

- [ ] **Step 1: Write failing tests**

`tests/test_write_policy.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_write_policy.py -v`
Expected: FAIL — script doesn't exist

- [ ] **Step 3: Implement relay/write_policy.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_write_policy.py -v`
Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add relay/write_policy.py tests/test_write_policy.py
git commit -m "feat: add strfry write policy script with whitelist auth"
```

---

## Task 10: relay/strfry.conf & relay/setup.sh

**Files:**
- Create: `relay/strfry.conf`, `relay/setup.sh`

- [ ] **Step 1: Create strfry.conf**

```
##
## AgentBoss strfry configuration
##

db = "./strfry-db/"

relay {
    info {
        name = "AgentBoss Relay"
        description = "Decentralized job recruitment relay"
        contact = ""
    }

    bind = "0.0.0.0"
    port = 7777
    nofiles = 1000

    writePolicy {
        plugin = "/opt/agentboss/write_policy.py"
    }
}
```

- [ ] **Step 2: Create setup.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== AgentBoss Relay Setup ==="

# Check if strfry is installed
if ! command -v strfry &> /dev/null; then
    echo "strfry not found. Please install strfry first:"
    echo "  git clone https://github.com/hoytech/strfry.git && cd strfry && git submodule update --init && make setup-golpe && make -j$(nproc)"
    exit 1
fi

# Create directories
sudo mkdir -p /etc/agentboss
sudo mkdir -p /opt/agentboss

# Install write policy
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
sudo cp "$SCRIPT_DIR/write_policy.py" /opt/agentboss/write_policy.py
sudo chmod +x /opt/agentboss/write_policy.py

# Initialize empty whitelist if not exists
if [ ! -f /etc/agentboss/whitelist.txt ]; then
    sudo touch /etc/agentboss/whitelist.txt
    sudo chmod 666 /etc/agentboss/whitelist.txt
fi

# Copy config
sudo cp "$SCRIPT_DIR/strfry.conf" /etc/strfry.conf

echo "Setup complete. Start relay with:"
echo "  strfry --config=/etc/strfry.conf relay"
```

- [ ] **Step 3: Smoke test write_policy.py**

Run: `python -c "import sys; sys.path.insert(0, 'relay'); import write_policy; print('OK')"`
Expected: prints "OK" with no traceback (module imports successfully)

- [ ] **Step 4: Commit**

```bash
chmod +x relay/setup.sh
git add relay/strfry.conf relay/setup.sh
git commit -m "feat: add strfry config and setup script"
```

---

## Task 11: web/db.py — User Database

**Files:**
- Create: `tests/test_web_db.py`, `web/db.py`

- [ ] **Step 1: Write failing tests**

`tests/test_web_db.py`:
```python
import pytest
from web.db import UserDB


@pytest.fixture
def db(tmp_path):
    d = UserDB(str(tmp_path / "users.db"))
    d.init_db()
    yield d
    d.close()


class TestUserDB:
    def test_create_user(self, db):
        user = db.create_user(
            username="alice",
            email="alice@example.com",
            password_hash="hash123",
            npub="npub1abc",
            nsec_encrypted="enc_nsec",
        )
        assert user["username"] == "alice"
        assert user["id"] is not None

    def test_create_duplicate_username_raises(self, db):
        db.create_user("alice", "a@b.com", "hash", "npub1", "enc1")
        with pytest.raises(Exception):
            db.create_user("alice", "c@d.com", "hash", "npub2", "enc2")

    def test_create_duplicate_email_raises(self, db):
        db.create_user("alice", "a@b.com", "hash", "npub1", "enc1")
        with pytest.raises(Exception):
            db.create_user("bob", "a@b.com", "hash", "npub2", "enc2")

    def test_get_user_by_username(self, db):
        db.create_user("alice", "a@b.com", "hash", "npub1", "enc1")
        user = db.get_user_by_username("alice")
        assert user is not None
        assert user["email"] == "a@b.com"

    def test_get_user_by_username_not_found(self, db):
        assert db.get_user_by_username("ghost") is None

    def test_get_user_by_id(self, db):
        created = db.create_user("alice", "a@b.com", "hash", "npub1", "enc1")
        user = db.get_user_by_id(created["id"])
        assert user["username"] == "alice"

    def test_list_active_npubs(self, db):
        db.create_user("alice", "a@b.com", "h", "npub1", "e1")
        db.create_user("bob", "b@b.com", "h", "npub2", "e2")
        npubs = db.list_active_npubs()
        assert len(npubs) == 2
        assert "npub1" in npubs
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_web_db.py -v`
Expected: FAIL

- [ ] **Step 3: Implement web/db.py**

```python
"""User database for the registration website."""

import sqlite3
import time


class UserDB:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    def init_db(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                npub TEXT UNIQUE NOT NULL,
                nsec_encrypted TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1
            );
        """)
        self._conn.commit()

    def close(self):
        self._conn.close()

    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        npub: str,
        nsec_encrypted: str,
    ) -> dict:
        cur = self._conn.execute(
            """INSERT INTO users (username, email, password_hash, npub, nsec_encrypted, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username, email, password_hash, npub, nsec_encrypted, int(time.time())),
        )
        self._conn.commit()
        return dict(self._conn.execute(
            "SELECT * FROM users WHERE id = ?", (cur.lastrowid,)
        ).fetchone())

    def get_user_by_username(self, username: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_active_npubs(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT npub FROM users WHERE is_active = 1"
        ).fetchall()
        return [row["npub"] for row in rows]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_web_db.py -v`
Expected: all 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add web/db.py tests/test_web_db.py
git commit -m "feat: add user database for registration website"
```

---

## Task 12: web/auth.py — Registration & Authentication Logic

**Files:**
- Create: `tests/test_web_auth.py`, `web/auth.py`

- [ ] **Step 1: Write failing tests**

`tests/test_web_auth.py`:
```python
import os
import pytest
from web.auth import register_user, verify_password, encrypt_nsec, decrypt_nsec
from web.db import UserDB


@pytest.fixture
def db(tmp_path):
    d = UserDB(str(tmp_path / "users.db"))
    d.init_db()
    yield d
    d.close()


@pytest.fixture
def whitelist_path(tmp_path):
    path = tmp_path / "whitelist.txt"
    path.write_text("")
    return str(path)


class TestRegisterUser:
    def test_register_creates_user_with_keypair(self, db, whitelist_path):
        result = register_user(
            db=db,
            username="alice",
            email="alice@example.com",
            password="securepass123",
            whitelist_path=whitelist_path,
        )
        assert "npub" in result
        assert "nsec" in result
        assert result["npub"].startswith("npub1")
        assert result["nsec"].startswith("nsec1")

    def test_register_adds_to_whitelist(self, db, whitelist_path):
        result = register_user(db, "alice", "a@b.com", "pass", whitelist_path)
        with open(whitelist_path) as f:
            content = f.read()
        # Whitelist should contain hex pubkey (not npub)
        from shared.crypto import npub_to_hex
        hex_pub = npub_to_hex(result["npub"])
        assert hex_pub in content

    def test_register_stores_encrypted_nsec(self, db, whitelist_path):
        result = register_user(db, "alice", "a@b.com", "pass", whitelist_path)
        user = db.get_user_by_username("alice")
        # nsec_encrypted should not be plaintext nsec
        assert user["nsec_encrypted"] != result["nsec"]

    def test_register_duplicate_username_raises(self, db, whitelist_path):
        register_user(db, "alice", "a@b.com", "pass", whitelist_path)
        with pytest.raises(Exception):
            register_user(db, "alice", "b@b.com", "pass", whitelist_path)


class TestPasswordVerify:
    def test_verify_correct_password(self, db, whitelist_path):
        register_user(db, "alice", "a@b.com", "mypassword", whitelist_path)
        user = db.get_user_by_username("alice")
        assert verify_password("mypassword", user["password_hash"]) is True

    def test_verify_wrong_password(self, db, whitelist_path):
        register_user(db, "alice", "a@b.com", "mypassword", whitelist_path)
        user = db.get_user_by_username("alice")
        assert verify_password("wrongpassword", user["password_hash"]) is False


class TestNsecEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        secret_key = "test-server-key-1234567890123456"
        nsec = "nsec1" + "a" * 58
        encrypted = encrypt_nsec(nsec, secret_key)
        assert encrypted != nsec
        decrypted = decrypt_nsec(encrypted, secret_key)
        assert decrypted == nsec
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_web_auth.py -v`
Expected: FAIL

- [ ] **Step 3: Implement web/auth.py**

```python
"""Registration, authentication, and key management."""

import base64
import hashlib
import os

import bcrypt

from shared.crypto import gen_keys, to_npub, to_nsec, npub_to_hex


# ── Password hashing ──

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


# ── nsec encryption using ChaCha20-Poly1305 (NIP-44 inspired) ──

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import secrets


def encrypt_nsec(nsec: str, server_key: str) -> str:
    """Encrypt nsec with server key using ChaCha20-Poly1305."""
    key_bytes = hashlib.sha256(server_key.encode()).digest()[:32]
    nonce = secrets.token_bytes(12)
    cipher = Cipher(algorithms.ChaCha20(key_bytes, nonce), None, backend=default_backend())
    encryptor = cipher.encryptor()
    nsec_bytes = nsec.encode()
    encrypted = encryptor.update(nsec_bytes) + encryptor.finalize()
    # Prepend nonce for use in decryption
    return base64.b64encode(nonce + encrypted).decode()


def decrypt_nsec(encrypted_b64: str, server_key: str) -> str:
    """Decrypt nsec."""
    key_bytes = hashlib.sha256(server_key.encode()).digest()[:32]
    raw = base64.b64decode(encrypted_b64)
    nonce, ciphertext = raw[:12], raw[12:]
    cipher = Cipher(algorithms.ChaCha20(key_bytes, nonce), None, backend=default_backend())
    decryptor = cipher.decryptor()
    return (decryptor.update(ciphertext) + decryptor.finalize()).decode()


# ── Registration ──

def register_user(
    db,
    username: str,
    email: str,
    password: str,
    whitelist_path: str,
    server_key: str = "agentboss-default-key-change-in-prod",
) -> dict:
    """Register a new user: generate keypair, hash password, update whitelist."""
    privkey, pubkey = gen_keys()
    npub = to_npub(pubkey)
    nsec = to_nsec(privkey)
    hex_pubkey = pubkey  # already hex from gen_keys

    pw_hash = hash_password(password)
    nsec_enc = encrypt_nsec(nsec, server_key)

    db.create_user(
        username=username,
        email=email,
        password_hash=pw_hash,
        npub=npub,
        nsec_encrypted=nsec_enc,
    )

    # Append hex pubkey to whitelist
    with open(whitelist_path, "a") as f:
        f.write(hex_pubkey + "\n")

    return {"npub": npub, "nsec": nsec, "pubkey": hex_pubkey}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_web_auth.py -v`
Expected: all 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add web/auth.py tests/test_web_auth.py
git commit -m "feat: add user registration, password hashing, and nsec encryption"
```

---

## Task 13: web/app.py — FastAPI Application & Templates

**Files:**
- Create: `tests/test_web_api.py`, `web/app.py`, `web/templates/*.html`, `web/static/style.css`

- [ ] **Step 1: Write failing tests — create `tests/test_web_api.py`**
```python
import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTBOSS_WEB_DB", str(tmp_path / "users.db"))
    monkeypatch.setenv("AGENTBOSS_WHITELIST", str(tmp_path / "whitelist.txt"))
    monkeypatch.setenv("AGENTBOSS_SERVER_KEY", "test-key-12345")
    (tmp_path / "whitelist.txt").write_text("")

    from web.app import create_app
    app = create_app()
    return TestClient(app)


class TestRegister:
    def test_register_success(self, app_client):
        resp = app_client.post("/api/register", json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "npub" in data
        assert "nsec" in data

    def test_register_duplicate_username(self, app_client):
        app_client.post("/api/register", json={
            "username": "alice", "email": "a@b.com", "password": "pass",
        })
        resp = app_client.post("/api/register", json={
            "username": "alice", "email": "c@d.com", "password": "pass",
        })
        assert resp.status_code == 400

    def test_register_missing_fields(self, app_client):
        resp = app_client.post("/api/register", json={"username": "alice"})
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, app_client):
        app_client.post("/api/register", json={
            "username": "alice", "email": "a@b.com", "password": "mypass",
        })
        resp = app_client.post("/api/login", json={
            "username": "alice", "password": "mypass",
        })
        assert resp.status_code == 200
        assert "session" in resp.cookies or resp.json().get("ok")

    def test_login_wrong_password(self, app_client):
        app_client.post("/api/register", json={
            "username": "alice", "email": "a@b.com", "password": "mypass",
        })
        resp = app_client.post("/api/login", json={
            "username": "alice", "password": "wrong",
        })
        assert resp.status_code == 401


class TestMe:
    def test_me_without_login(self, app_client):
        resp = app_client.get("/api/me")
        assert resp.status_code == 401

    def test_me_with_session(self, app_client):
        app_client.post("/api/register", json={
            "username": "alice", "email": "a@b.com", "password": "mypass",
        })
        app_client.post("/api/login", json={
            "username": "alice", "password": "mypass",
        })
        resp = app_client.get("/api/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "alice"
        assert "npub" in data


class TestKey:
    def test_get_key_with_session(self, app_client):
        reg = app_client.post("/api/register", json={
            "username": "alice", "email": "a@b.com", "password": "mypass",
        })
        app_client.post("/api/login", json={
            "username": "alice", "password": "mypass",
        })
        resp = app_client.get("/api/key")
        assert resp.status_code == 200
        assert "nsec" in resp.json()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_web_api.py -v`
Expected: FAIL

- [ ] **Step 3: Implement web/app.py**

```python
"""FastAPI registration website for AgentBoss."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from itsdangerous import URLSafeSerializer

from web.db import UserDB
from web.auth import register_user, verify_password, decrypt_nsec


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


def create_app() -> FastAPI:
    app = FastAPI(title="AgentBoss Registration")

    db_path = os.environ.get("AGENTBOSS_WEB_DB", "agentboss_users.db")
    whitelist_path = os.environ.get("AGENTBOSS_WHITELIST", "/etc/agentboss/whitelist.txt")
    server_key = os.environ.get("AGENTBOSS_SERVER_KEY", "agentboss-default-key-change-in-prod")

    db = UserDB(db_path)
    db.init_db()

    serializer = URLSafeSerializer(server_key)

    template_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"

    if template_dir.exists():
        templates = Jinja2Templates(directory=str(template_dir))
    else:
        templates = None

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    def _get_session_user(request: Request) -> dict | None:
        token = request.cookies.get("session")
        if not token:
            return None
        try:
            user_id = serializer.loads(token)
            return db.get_user_by_id(user_id)
        except Exception:
            return None

    # ── API routes ──

    @app.post("/api/register")
    def api_register(req: RegisterRequest):
        try:
            result = register_user(
                db=db,
                username=req.username,
                email=req.email,
                password=req.password,
                whitelist_path=whitelist_path,
                server_key=server_key,
            )
            return {"npub": result["npub"], "nsec": result["nsec"]}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/login")
    def api_login(req: LoginRequest, response: Response):
        user = db.get_user_by_username(req.username)
        if not user or not verify_password(req.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = serializer.dumps(user["id"])
        response.set_cookie("session", token, httponly=True)
        return {"ok": True, "npub": user["npub"]}

    @app.get("/api/me")
    def api_me(request: Request):
        user = _get_session_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not logged in")
        return {
            "username": user["username"],
            "email": user["email"],
            "npub": user["npub"],
            "created_at": user["created_at"],
        }

    @app.get("/api/key")
    def api_key(request: Request):
        user = _get_session_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not logged in")
        nsec = decrypt_nsec(user["nsec_encrypted"], server_key)
        return {"nsec": nsec, "npub": user["npub"]}

    # ── HTML routes ──

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        if templates:
            return templates.TemplateResponse("register.html", {"request": request})
        return HTMLResponse("<h1>AgentBoss</h1><p>Registration website</p>")

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard(request: Request):
        user = _get_session_user(request)
        if not user:
            return HTMLResponse("<p>Please login first</p>", status_code=401)
        if templates:
            return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
        return HTMLResponse(f"<p>Welcome {user['username']}</p>")

    return app
```

- [ ] **Step 4: Create templates**

`web/templates/base.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgentBoss - {% block title %}{% endblock %}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <nav><a href="/">AgentBoss</a> | <a href="/dashboard">Dashboard</a></nav>
    <main>{% block content %}{% endblock %}</main>
</body>
</html>
```

`web/templates/register.html`:
```html
{% extends "base.html" %}
{% block title %}Register{% endblock %}
{% block content %}
<h1>AgentBoss Registration</h1>
<form id="register-form">
    <label>Username: <input name="username" required></label><br>
    <label>Email: <input name="email" type="email" required></label><br>
    <label>Password: <input name="password" type="password" required></label><br>
    <button type="submit">Register</button>
</form>
<div id="result"></div>
<h2>Login</h2>
<form id="login-form">
    <label>Username: <input name="username" required></label><br>
    <label>Password: <input name="password" type="password" required></label><br>
    <button type="submit">Login</button>
</form>
<script>
document.getElementById('register-form').onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const resp = await fetch('/api/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(Object.fromEntries(fd))
    });
    const data = await resp.json();
    document.getElementById('result').innerText = resp.ok
        ? `Success! Your nsec: ${data.nsec}\nYour npub: ${data.npub}\nSave your nsec!`
        : `Error: ${data.detail}`;
};
document.getElementById('login-form').onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const resp = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(Object.fromEntries(fd))
    });
    if (resp.ok) window.location = '/dashboard';
    else document.getElementById('result').innerText = 'Login failed';
};
</script>
{% endblock %}
```

`web/templates/dashboard.html`:
```html
{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<h1>Welcome, {{ user.username }}</h1>
<p>npub: {{ user.npub }}</p>
<p>Registered: {{ user.created_at }}</p>
<button id="show-key">Show Private Key</button>
<pre id="key-display"></pre>
<h2>CLI Setup</h2>
<pre>agentboss login --key &lt;your nsec from above&gt;
agentboss regions sync
agentboss fetch --province 北京</pre>
<script>
document.getElementById('show-key').onclick = async () => {
    const resp = await fetch('/api/key');
    const data = await resp.json();
    document.getElementById('key-display').innerText = `nsec: ${data.nsec}\nnpub: ${data.npub}`;
};
</script>
{% endblock %}
```

`web/static/style.css`:
```css
body { font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }
nav { margin-bottom: 20px; padding: 10px 0; border-bottom: 1px solid #ccc; }
nav a { margin-right: 15px; text-decoration: none; color: #333; }
label { display: block; margin: 8px 0; }
input { padding: 6px; margin-left: 8px; }
button { margin-top: 10px; padding: 8px 16px; cursor: pointer; }
pre { background: #f4f4f4; padding: 12px; overflow-x: auto; }
#result { margin: 15px 0; padding: 10px; background: #e8f5e9; white-space: pre-wrap; }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_web_api.py -v`
Expected: all 7 tests PASS

- [ ] **Step 6: Commit**

```bash
git add web/app.py web/templates/ web/static/ tests/test_web_api.py
git commit -m "feat: add FastAPI registration website with templates"
```

---

## Task 14: Integration Test — Full Workflow

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

`tests/test_integration.py`:
```python
"""Integration tests for the full AgentBoss workflow (no real relay needed)."""

import json
import pytest
from typer.testing import CliRunner
from cli.main import app
from cli.storage import Storage
from cli.regions import RegionResolver
from cli.models import parse_job_content
from shared.crypto import gen_keys, to_nsec
from shared.event import build_event, verify_event_id, verify_event_sig
from shared.constants import KIND_APP_DATA, APP_TAG, JOB_TAG, REGION_TAG, REGION_MAP_D_TAG

runner = CliRunner()


@pytest.fixture
def cli_home(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTBOSS_HOME", str(tmp_path))
    return tmp_path


class TestIdentityWorkflow:
    def test_login_then_whoami(self, cli_home):
        priv, pub = gen_keys()
        nsec = to_nsec(priv)
        result = runner.invoke(app, ["login", "--key", nsec])
        assert result.exit_code == 0
        result = runner.invoke(app, ["whoami"])
        assert result.exit_code == 0
        assert "npub" in result.stdout


class TestEventBuildWorkflow:
    def test_build_job_event_is_valid(self):
        priv, pub = gen_keys()
        content = json.dumps({
            "title": "Python Dev",
            "company": "TestCo",
            "version": 1,
        })
        event = build_event(
            kind=KIND_APP_DATA,
            content=content,
            privkey=priv,
            pubkey=pub,
            tags=[
                ["d", "test-job-1"],
                ["t", APP_TAG],
                ["t", JOB_TAG],
                ["province", "1"],
                ["city", "101"],
            ],
        )
        assert verify_event_id(event)
        assert verify_event_sig(event)
        assert event["kind"] == KIND_APP_DATA
        parsed = parse_job_content(event["content"])
        assert parsed.title == "Python Dev"

    def test_build_region_event_is_valid(self):
        priv, pub = gen_keys()
        content = json.dumps({
            "version": 1,
            "provinces": {"1": "北京"},
            "cities": {"101": "北京市"},
            "province_city": {"1": [101]},
        })
        event = build_event(
            kind=KIND_APP_DATA,
            content=content,
            privkey=priv,
            pubkey=pub,
            tags=[["d", REGION_MAP_D_TAG], ["t", APP_TAG], ["t", REGION_TAG]],
        )
        assert verify_event_id(event)
        assert verify_event_sig(event)


class TestStorageWorkflow:
    def test_fetch_store_list_show(self, cli_home):
        """Simulate: region sync → store jobs → list → show."""
        storage = Storage(str(cli_home / "agentboss.db"))
        storage.init_db()
        resolver = RegionResolver(storage)

        # Sync regions
        resolver.apply_mapping(json.dumps({
            "version": 1,
            "provinces": {"1": "北京", "2": "上海"},
            "cities": {"101": "北京市", "201": "上海市"},
            "province_city": {"1": [101], "2": [201]},
        }))
        assert resolver.province_code("北京") == 1
        assert resolver.city_code("北京市") == 101

        # Store some jobs
        storage.upsert_job("ev1", "d1", "pub1", 1, 101, json.dumps({
            "title": "Python Dev", "company": "Co1", "version": 1,
        }), 1000)
        storage.upsert_job("ev2", "d2", "pub2", 2, 201, json.dumps({
            "title": "Go Dev", "company": "Co2", "version": 1,
        }), 2000)

        # List filtered
        beijing_jobs = storage.list_jobs(province_code=1)
        assert len(beijing_jobs) == 1
        assert beijing_jobs[0]["event_id"] == "ev1"

        # Show
        job = storage.get_job("ev1")
        content = parse_job_content(job["content"])
        assert content.title == "Python Dev"

        # Eviction
        for i in range(10):
            storage.upsert_job(f"evx{i}", f"dx{i}", "p", 1, 101, "{}", i)
        storage.evict_oldest(5)
        assert storage.count_jobs() == 5

        storage.close()


class TestWebRegistrationWorkflow:
    def test_register_and_login(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AGENTBOSS_WEB_DB", str(tmp_path / "users.db"))
        monkeypatch.setenv("AGENTBOSS_WHITELIST", str(tmp_path / "whitelist.txt"))
        monkeypatch.setenv("AGENTBOSS_SERVER_KEY", "test-key")
        (tmp_path / "whitelist.txt").write_text("")

        from fastapi.testclient import TestClient
        from web.app import create_app
        client = TestClient(create_app())

        # Register
        resp = client.post("/api/register", json={
            "username": "alice", "email": "a@b.com", "password": "pass123",
        })
        assert resp.status_code == 200
        nsec = resp.json()["nsec"]
        assert nsec.startswith("nsec1")

        # Whitelist populated
        wl = (tmp_path / "whitelist.txt").read_text()
        assert len(wl.strip()) == 64  # hex pubkey

        # Login
        resp = client.post("/api/login", json={
            "username": "alice", "password": "pass123",
        })
        assert resp.status_code == 200

        # Get key
        resp = client.get("/api/key")
        assert resp.status_code == 200
        assert resp.json()["nsec"] == nsec
```

- [ ] **Step 2: Run integration tests**

Run: `python -m pytest tests/test_integration.py -v`
Expected: all tests PASS

- [ ] **Step 3: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: all tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for full AgentBoss workflow"
```

---

## Task 15: Final Verification & Cleanup

- [ ] **Step 1: Run full test suite with coverage**

Run: `python -m pytest tests/ -v --tb=short`
Expected: all tests PASS

- [ ] **Step 2: Verify CLI entry point works**

Run: `cd /home/deeptuuk/Code/cc_workdir/AgentBoss && python -m cli.main --help`
Expected: shows help with all commands

- [ ] **Step 3: Verify web app starts**

Run: `cd /home/deeptuuk/Code/cc_workdir/AgentBoss && python -c "from web.app import create_app; print('OK')"`
Expected: prints "OK"

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final cleanup and verification"
```
