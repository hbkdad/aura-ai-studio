"""
memory_store.py — CRUD for the memory_events table.

memory_events stores human-readable project decisions, audit notes, and rule
changes made over the lifetime of the project. It is separate from
agent_memory (which stores agent runtime state).

Safety filter: content and title are scanned for secrets before writing.
Any content that contains private keys, seed phrases, API credentials,
passwords, or similar sensitive patterns is rejected with a clear error.
"""
import json
import re
from ..db import get_db

# ── Safety filter ──────────────────────────────────────────────────────────────

_FORBIDDEN_KEYWORDS: list[str] = [
    "private key", "privatekey", "private_key",
    "seed phrase", "seedphrase", "seed_phrase",
    "mnemonic",
    "api key", "apikey", "api_key",
    "secret token", "secrettoken", "secret_token",
    "wallet backup", "walletbackup", "wallet_backup",
    "password",
    "passphrase",
    "secret key", "secretkey", "secret_key",
    "xpriv",
    "wif",        # Wallet Import Format (raw private key encoding)
    "bearer token",
]

_FORBIDDEN_PATTERNS: list[re.Pattern] = [
    re.compile(r'\bsk-[A-Za-z0-9]{20,}\b'),            # OpenAI / Anthropic API keys
    re.compile(r'\b0x[a-fA-F0-9]{64}\b'),               # Ethereum private key hex
    re.compile(r'\b[5KL][a-km-zA-HJ-NP-Z1-9]{51}\b'),  # Bitcoin WIF private key
    re.compile(r'-----BEGIN [A-Z ]+PRIVATE KEY-----'),   # PEM private key block
]


def safety_filter(title: str, content: str) -> None:
    """
    Raise ValueError if title or content contains forbidden terms or patterns.

    Called before every write. Protects against accidentally storing secrets
    in the project memory system.
    """
    combined = (title + " " + content).lower()

    for keyword in _FORBIDDEN_KEYWORDS:
        if keyword in combined:
            raise ValueError(
                f"Rejected: content contains forbidden term '{keyword}'. "
                "Never store secrets, private keys, seed phrases, API keys, "
                "or passwords in project memory."
            )

    full_text = title + " " + content  # preserve case for pattern matching
    for pattern in _FORBIDDEN_PATTERNS:
        if pattern.search(full_text):
            raise ValueError(
                "Rejected: content contains a pattern that looks like a private key, "
                "API credential, or secret token. "
                "Never store secrets or credentials in project memory."
            )


# ── Constants ──────────────────────────────────────────────────────────────────

VALID_TYPES = ("note", "decision", "audit", "rule", "action", "warning")
VALID_SOURCES = ("user", "agent", "system")


# ── CRUD ───────────────────────────────────────────────────────────────────────

def add_event(
    title: str,
    content: str,
    memory_type: str = "note",
    source: str = "user",
    tags: list[str] = None,
) -> dict:
    """Insert a memory event after safety-filtering content. Returns the created row."""
    title = title.strip()
    content = content.strip()

    if not title:
        raise ValueError("title is required")
    if len(title) > 200:
        raise ValueError("title must be 200 characters or fewer")
    if not content:
        raise ValueError("content is required")
    if memory_type not in VALID_TYPES:
        raise ValueError(f"memory_type must be one of: {list(VALID_TYPES)}")
    if source not in VALID_SOURCES:
        raise ValueError(f"source must be one of: {list(VALID_SOURCES)}")

    safety_filter(title, content)

    tags_json = json.dumps([t.strip() for t in (tags or []) if t.strip()])

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO memory_events (memory_type, title, content, source, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (memory_type, title, content, source, tags_json))
        row = conn.execute(
            "SELECT * FROM memory_events WHERE id=?", (cursor.lastrowid,)
        ).fetchone()
        return _parse_row(dict(row))


def get_events(
    limit: int = 50,
    offset: int = 0,
    memory_type: str = None,
    source: str = None,
) -> list[dict]:
    """Return memory events, newest first. Optionally filter by type or source."""
    conditions: list[str] = []
    params: list = []
    if memory_type:
        conditions.append("memory_type=?")
        params.append(memory_type)
    if source:
        conditions.append("source=?")
        params.append(source)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params += [limit, offset]

    with get_db() as conn:
        rows = conn.execute(
            f"SELECT * FROM memory_events {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params,
        ).fetchall()
        return [_parse_row(dict(r)) for r in rows]


def get_event(event_id: int) -> dict | None:
    """Return a single memory event by ID, or None if not found."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM memory_events WHERE id=?", (event_id,)
        ).fetchone()
        return _parse_row(dict(row)) if row else None


def count_events(memory_type: str = None) -> int:
    """Return the total count of memory events, optionally filtered by type."""
    with get_db() as conn:
        if memory_type:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM memory_events WHERE memory_type=?",
                (memory_type,)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM memory_events"
            ).fetchone()
        return row["cnt"] if row else 0


# ── Internal ───────────────────────────────────────────────────────────────────

def _parse_row(row: dict) -> dict:
    try:
        row["tags"] = json.loads(row.get("tags") or "[]")
    except (json.JSONDecodeError, TypeError):
        row["tags"] = []
    return row
