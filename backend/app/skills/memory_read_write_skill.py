"""
MemoryReadWriteSkill — read or write a value in the agent memory store.

Supports both short-term memory (TTL-based expiry) and long-term memory (persistent).
Use operation="write" to store context, operation="read" to retrieve it.
"""
NAME = "memory_read_write"
DESCRIPTION = (
    "Reads or writes a value in the agent memory store. "
    "operation='read' returns the value; operation='write' stores it with optional TTL"
)
REQUIRED_INPUTS = ["operation", "key"]
INPUT_SCHEMA = {
    "operation": "str (required) — 'read' or 'write'",
    "key": "str (required) — memory key to read or write",
    "agent_name": "str (optional, default 'agent_runner') — which agent owns this memory",
    "memory_type": "str (optional, default 'short_term') — 'short_term' or 'long_term'",
    "value": "any (required for write) — value to store (dict or string)",
    "ttl_hours": "float (optional, for write) — hours until expiry; null = never expires",
}
OUTPUT_SCHEMA = {
    "operation": "str — 'read' or 'write'",
    "key": "str",
    "value": "any — the stored value (read) or the written value (write)",
    "found": "bool — for read: True if key exists and is not expired",
    "memory_type": "str",
    "agent_name": "str",
}


def run(input: dict) -> dict:
    """Read or write agent memory."""
    operation = input.get("operation", "").strip().lower()
    key = input.get("key", "").strip()
    agent_name = input.get("agent_name", "agent_runner").strip()
    memory_type = input.get("memory_type", "short_term").strip()

    if operation not in ("read", "write"):
        raise ValueError("operation must be 'read' or 'write'")
    if not key:
        raise ValueError("key is required")
    if memory_type not in ("short_term", "long_term"):
        raise ValueError("memory_type must be 'short_term' or 'long_term'")

    from ..memory_service import read_memory, write_memory

    if operation == "read":
        entry = read_memory(agent_name, memory_type, key)
        return {
            "operation": "read",
            "key": key,
            "value": entry["value"] if entry else None,
            "found": entry is not None,
            "memory_type": memory_type,
            "agent_name": agent_name,
        }

    # write
    value = input.get("value")
    if value is None:
        raise ValueError("value is required for operation='write'")
    ttl_hours = input.get("ttl_hours")

    entry = write_memory(agent_name, memory_type, key, value, ttl_hours=ttl_hours)
    return {
        "operation": "write",
        "key": key,
        "value": entry["value"],
        "found": True,
        "memory_type": memory_type,
        "agent_name": agent_name,
    }
