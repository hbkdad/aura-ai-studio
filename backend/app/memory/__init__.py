"""
Agent memory package — short-term (TTL) and long-term persistent key-value store.

Re-exports the memory_service interface so agents can import from here
instead of the top-level module.
"""
from ..memory_service import (
    write_memory,
    read_memory,
    read_all_memory,
    clear_memory,
    _purge_expired,
)

__all__ = [
    "write_memory",
    "read_memory",
    "read_all_memory",
    "clear_memory",
    "_purge_expired",
]
