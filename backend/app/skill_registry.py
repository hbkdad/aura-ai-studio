"""
Skill registry — auto-discovers all modules in app/skills/ that expose
NAME, DESCRIPTION, REQUIRED_INPUTS, INPUT_SCHEMA, OUTPUT_SCHEMA, and run().

Discovery runs once at import time. Malformed skill files are skipped with
a warning so a bad skill never prevents the server from starting.
"""
import importlib
import pkgutil
import logging
from datetime import datetime
from . import skills as _skills_pkg
from .policy_engine import log_agent_action

logger = logging.getLogger(__name__)

# ── Discovery ─────────────────────────────────────────────────────────────────

def _discover() -> dict:
    registry = {}
    for finder, module_name, _ in pkgutil.iter_modules(_skills_pkg.__path__):
        full_name = f"{_skills_pkg.__name__}.{module_name}"
        try:
            mod = importlib.import_module(full_name)
            required = ("NAME", "DESCRIPTION", "REQUIRED_INPUTS", "INPUT_SCHEMA", "OUTPUT_SCHEMA", "run")
            missing = [attr for attr in required if not hasattr(mod, attr)]
            if missing:
                logger.warning("Skill %s skipped — missing attributes: %s", full_name, missing)
                continue
            registry[mod.NAME] = mod
            logger.info("Skill registered: %s", mod.NAME)
        except Exception as exc:
            logger.warning("Skill %s failed to load: %s", full_name, exc)
    return registry


_REGISTRY: dict = _discover()


# ── Public API ────────────────────────────────────────────────────────────────

class SkillNotFoundError(ValueError):
    pass


def list_skills() -> list[dict]:
    return [
        {
            "name": mod.NAME,
            "description": mod.DESCRIPTION,
            "required_inputs": mod.REQUIRED_INPUTS,
            "input_schema": mod.INPUT_SCHEMA,
            "output_schema": mod.OUTPUT_SCHEMA,
        }
        for mod in _REGISTRY.values()
    ]


def run_skill(name: str, input_data: dict) -> dict:
    if name not in _REGISTRY:
        available = list(_REGISTRY.keys())
        raise SkillNotFoundError(
            f"Skill '{name}' not found. Available skills: {available}"
        )

    skill = _REGISTRY[name]
    missing = [k for k in skill.REQUIRED_INPUTS if k not in input_data or input_data[k] == ""]
    if missing:
        raise ValueError(
            f"Skill '{name}' is missing required inputs: {missing}. "
            f"Schema: {skill.INPUT_SCHEMA}"
        )

    start = datetime.utcnow()
    try:
        result = skill.run(input_data)
        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        log_agent_action(
            agent_name="skill_registry",
            action_type=f"skill:{name}",
            input_data=input_data,
            output_data=result,
            status="completed",
            duration_ms=duration_ms,
        )
        return result
    except Exception as exc:
        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        log_agent_action(
            agent_name="skill_registry",
            action_type=f"skill:{name}",
            input_data=input_data,
            output_data={},
            status="error",
            duration_ms=duration_ms,
            error=str(exc),
        )
        raise RuntimeError(f"Skill '{name}' execution failed: {exc}") from exc
