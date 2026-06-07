from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..skill_registry import list_skills, run_skill, SkillNotFoundError

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("")
def get_skills():
    return {"skills": list_skills()}


class RunSkillRequest(BaseModel):
    input: Optional[dict] = {}


@router.post("/{skill_name}/run")
def run_skill_endpoint(skill_name: str, body: RunSkillRequest):
    try:
        result = run_skill(skill_name, body.input or {})
        return {"skill": skill_name, "result": result}
    except SkillNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
