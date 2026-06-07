import json
from datetime import datetime, timedelta
from .db import get_db


def write_memory(
    agent_name: str,
    memory_type: str,
    key: str,
    value: dict | str,
    ttl_hours: float = None,
) -> dict:
    """Upsert a memory entry. value can be dict (auto-serialised) or plain string."""
    if not agent_name or not key:
        raise ValueError("agent_name and key are required")
    if memory_type not in ("short_term", "long_term"):
        raise ValueError("memory_type must be 'short_term' or 'long_term'")

    serialised = json.dumps(value) if isinstance(value, dict) else str(value)
    expires_at = None
    if ttl_hours is not None:
        expires_at = (datetime.utcnow() + timedelta(hours=ttl_hours)).strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        conn.execute("""
            INSERT INTO agent_memory (agent_name, memory_type, key, value, expires_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(agent_name, memory_type, key)
            DO UPDATE SET value=excluded.value,
                          updated_at=datetime('now'),
                          expires_at=excluded.expires_at
        """, (agent_name, memory_type, key, serialised, expires_at))

        row = conn.execute("""
            SELECT * FROM agent_memory WHERE agent_name=? AND memory_type=? AND key=?
        """, (agent_name, memory_type, key)).fetchone()
        return _parse_row(dict(row))


def read_memory(agent_name: str, memory_type: str, key: str) -> dict | None:
    """Read one memory entry. Returns None if not found or expired."""
    _purge_expired()
    with get_db() as conn:
        row = conn.execute("""
            SELECT * FROM agent_memory
            WHERE agent_name=? AND memory_type=? AND key=?
              AND (expires_at IS NULL OR expires_at > datetime('now'))
        """, (agent_name, memory_type, key)).fetchone()
        return _parse_row(dict(row)) if row else None


def read_all_memory(agent_name: str = None, memory_type: str = None) -> list[dict]:
    """Read all non-expired memory entries. Any agent can read any agent's memory."""
    _purge_expired()
    with get_db() as conn:
        conditions = ["(expires_at IS NULL OR expires_at > datetime('now'))"]
        params = []
        if agent_name:
            conditions.append("agent_name=?")
            params.append(agent_name)
        if memory_type:
            conditions.append("memory_type=?")
            params.append(memory_type)
        where = " AND ".join(conditions)
        rows = conn.execute(
            f"SELECT * FROM agent_memory WHERE {where} ORDER BY updated_at DESC",
            params,
        ).fetchall()
        return [_parse_row(dict(r)) for r in rows]


def clear_memory(
    agent_name: str = None,
    memory_type: str = None,
    key: str = None,
) -> int:
    """Delete memory entries. Returns count of deleted rows.
    Pass no args to wipe everything (use with care).
    """
    with get_db() as conn:
        conditions = []
        params = []
        if agent_name:
            conditions.append("agent_name=?")
            params.append(agent_name)
        if memory_type:
            conditions.append("memory_type=?")
            params.append(memory_type)
        if key:
            conditions.append("key=?")
            params.append(key)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        cursor = conn.execute(f"DELETE FROM agent_memory{where}", params)
        return cursor.rowcount


def _purge_expired() -> int:
    """Delete all expired entries. Called lazily before reads."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM agent_memory WHERE expires_at IS NOT NULL AND expires_at <= datetime('now')"
        )
        return cursor.rowcount


def _parse_row(row: dict) -> dict:
    """Deserialise the value field back to a dict if it was JSON."""
    try:
        row["value"] = json.loads(row["value"])
    except (json.JSONDecodeError, TypeError):
        pass
    return row
