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
