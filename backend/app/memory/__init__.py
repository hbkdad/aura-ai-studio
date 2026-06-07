"""
Agent memory package.

Two distinct memory systems:

1. agent_memory table — short-term (TTL) and long-term key-value store
   for agent runtime state. Imported from memory_service.

2. memory_events table — human-readable project decisions, audit notes,
   and rule changes. Managed by memory_store.

Project context (docs + live rules) lives in project_memory and
context_builder.
"""
# Agent runtime memory (memory_service → agent_memory table)
from ..memory_service import (
    write_memory,
    read_memory,
    read_all_memory,
    clear_memory,
    _purge_expired,
)

# Project memory events (memory_events table)
from .memory_store import (
    add_event,
    get_events,
    get_event,
    count_events,
    safety_filter,
    VALID_TYPES,
    VALID_SOURCES,
)

# Project context builders
from .project_memory import (
    read_project_memory_doc,
    read_agents_doc,
    get_product_rules,
    get_project_summary,
)

from .context_builder import (
    build_agent_context,
    build_system_context,
    get_safe_doc_excerpt,
)

__all__ = [
    # agent_memory
    "write_memory", "read_memory", "read_all_memory", "clear_memory", "_purge_expired",
    # memory_events
    "add_event", "get_events", "get_event", "count_events", "safety_filter",
    "VALID_TYPES", "VALID_SOURCES",
    # project context
    "read_project_memory_doc", "read_agents_doc", "get_product_rules", "get_project_summary",
    "build_agent_context", "build_system_context", "get_safe_doc_excerpt",
]
