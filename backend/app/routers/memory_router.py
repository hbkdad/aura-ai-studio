from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from ..memory_service import read_all_memory, clear_memory
from ..memory.memory_store import (
    add_event, get_events, VALID_TYPES, VALID_SOURCES,
)
from ..memory.project_memory import get_project_summary
from ..memory.context_builder import build_system_context

router = APIRouter(prefix="/memory", tags=["memory"])


# ── Agent memory (agent_memory table) ─────────────────────────────────────────

@router.get("")
def get_agent_memory(
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    memory_type: Optional[str] = Query(None, description="Filter: short_term or long_term"),
):
    """Return agent runtime memory entries (TTL key-value store)."""
    entries = read_all_memory(agent_name=agent_name, memory_type=memory_type)
    return {"entries": entries, "count": len(entries)}


@router.delete("")
def delete_agent_memory(
    agent_name: Optional[str] = Query(None),
    memory_type: Optional[str] = Query(None),
    key: Optional[str] = Query(None),
):
    """Delete agent memory entries. Pass no params to wipe all (use with care)."""
    deleted = clear_memory(agent_name=agent_name, memory_type=memory_type, key=key)
    return {"deleted": deleted}


# ── Project memory summary ─────────────────────────────────────────────────────

@router.get("/summary")
def get_memory_summary():
    """
    Return the full project memory summary: live rules, stats, and product config.
    Also includes a system-context string safe for AI system prompts.
    """
    summary = get_project_summary()
    system_context = build_system_context()
    return {
        **summary,
        "system_context": system_context,
    }


# ── Project memory events (memory_events table) ────────────────────────────────

@router.get("/events")
def list_memory_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    memory_type: Optional[str] = Query(None, description=f"Filter by type: {VALID_TYPES}"),
    source: Optional[str] = Query(None, description=f"Filter by source: {VALID_SOURCES}"),
):
    """Return project memory events (decisions, notes, audits, etc.), newest first."""
    if memory_type and memory_type not in VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid memory_type '{memory_type}'. Valid: {list(VALID_TYPES)}",
        )
    events = get_events(limit=limit, offset=offset, memory_type=memory_type, source=source)
    return {"events": events, "count": len(events)}


class CreateMemoryEventRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Short descriptive title")
    content: str = Field(..., min_length=1, description="Full content of the memory note")
    memory_type: str = Field("note", description="note|decision|audit|rule|action|warning")
    source: str = Field("user", description="user|agent|system")
    tags: list[str] = Field(default_factory=list, description="Optional list of tags")


@router.post("/events", status_code=201)
def create_memory_event(body: CreateMemoryEventRequest):
    """
    Add a project memory event.

    Safety filter: rejects content containing private keys, seed phrases,
    API keys, passwords, mnemonics, or any secret credentials.
    """
    try:
        event = add_event(
            title=body.title,
            content=body.content,
            memory_type=body.memory_type,
            source=body.source,
            tags=body.tags,
        )
        return event
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
