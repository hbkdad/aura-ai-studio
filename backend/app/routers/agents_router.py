from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ..agent_runner import run_agent_loop
from ..policy_engine import check_kill_switch

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentLoopRequest(BaseModel):
    goal: str = Field(..., min_length=1, description="What you want the agent to accomplish")
    session_id: Optional[str] = None
    max_steps: int = Field(10, ge=1, le=10)


@router.post("/run")
def run_agent(body: AgentLoopRequest):
    if check_kill_switch():
        raise HTTPException(status_code=503, detail="Kill switch is active — agent loop halted")
    result = run_agent_loop(
        goal=body.goal,
        session_id=body.session_id,
        max_steps=body.max_steps,
    )
    return result
