from fastapi import APIRouter, Query
from typing import Optional

from ..memory_service import read_all_memory, clear_memory

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("")
def get_memory(
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    memory_type: Optional[str] = Query(None, description="Filter by type: short_term or long_term"),
):
    entries = read_all_memory(agent_name=agent_name, memory_type=memory_type)
    return {"entries": entries, "count": len(entries)}


@router.delete("")
def delete_memory(
    agent_name: Optional[str] = Query(None, description="Delete memory for this agent"),
    memory_type: Optional[str] = Query(None, description="Delete only this type"),
    key: Optional[str] = Query(None, description="Delete only this specific key"),
):
    deleted = clear_memory(agent_name=agent_name, memory_type=memory_type, key=key)
    return {"deleted": deleted}
