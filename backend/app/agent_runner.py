"""
Think → Act → Observe agent loop.

run_agent_loop(goal, session_id?, max_steps?) -> dict

Every step:
  1. Kill switch check — abort immediately if active
  2. Think — provider.think(system_prompt, messages) returns JSON decision
  3. Act — skill_call dispatches to skill_registry.run_skill()
  4. Observe — skill result appended to messages as "Observation: ..."
  5. Repeat until action=="done" or max_steps reached

All steps logged to agent_actions table.
"""
import json
import uuid
from datetime import datetime

from .ai_provider import get_provider
from .policy_engine import check_kill_switch, log_agent_action
from .skill_registry import list_skills, run_skill, SkillNotFoundError

MAX_STEPS = 10


def run_agent_loop(
    goal: str,
    session_id: str = None,
    max_steps: int = MAX_STEPS,
) -> dict:
    if not goal or not goal.strip():
        raise ValueError("goal is required and cannot be blank")

    if session_id is None:
        session_id = str(uuid.uuid4())

    max_steps = min(max_steps, MAX_STEPS)

    provider = get_provider()
    system_prompt = _build_system_prompt()
    messages = [{"role": "user", "content": goal}]
    steps = []
    loop_start = datetime.utcnow()

    for step_num in range(1, max_steps + 1):
        if check_kill_switch():
            result = {
                "session_id": session_id,
                "status": "blocked",
                "reason": "Kill switch is active — agent loop halted",
                "steps": steps,
                "steps_taken": step_num - 1,
            }
            log_agent_action(
                "agent_runner", "loop:killed",
                {"session_id": session_id, "step": step_num, "goal": goal[:200]},
                result,
                status="blocked",
            )
            return result

        # Think
        try:
            raw = provider.think(system_prompt=system_prompt, messages=messages)
            decision = json.loads(raw)
        except json.JSONDecodeError as exc:
            return _error_result(session_id, steps, step_num, loop_start,
                                  f"Provider returned non-JSON at step {step_num}: {exc}")
        except Exception as exc:
            return _error_result(session_id, steps, step_num, loop_start,
                                  f"Provider think() failed at step {step_num}: {exc}")

        action = decision.get("action")

        if action == "done":
            output = decision.get("output", "")
            duration_ms = _elapsed(loop_start)
            result = {
                "session_id": session_id,
                "status": "done",
                "output": output,
                "steps": steps,
                "steps_taken": len(steps),
                "duration_ms": duration_ms,
            }
            log_agent_action(
                "agent_runner", "loop:done",
                {"session_id": session_id, "goal": goal[:200], "steps_taken": len(steps)},
                {"output": output[:500]},
                duration_ms=duration_ms,
            )
            return result

        if action == "skill_call":
            skill_name = decision.get("skill", "")
            skill_input = decision.get("input") or {}

            step_start = datetime.utcnow()
            try:
                observation = run_skill(skill_name, skill_input)
                obs_str = json.dumps(observation)
                step_status = "ok"
            except SkillNotFoundError as exc:
                observation = {"error": str(exc)}
                obs_str = f"Error: {exc}"
                step_status = "error"
            except (ValueError, RuntimeError) as exc:
                observation = {"error": str(exc)}
                obs_str = f"Error: {exc}"
                step_status = "error"

            step_ms = _elapsed(step_start)
            steps.append({
                "step": step_num,
                "action": "skill_call",
                "skill": skill_name,
                "input": skill_input,
                "observation": observation,
                "status": step_status,
                "duration_ms": step_ms,
            })

            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"Observation: {obs_str[:1000]}"})
            continue

        # Unknown action
        return _error_result(
            session_id, steps, step_num, loop_start,
            f"Provider returned unknown action '{action}' at step {step_num}",
        )

    duration_ms = _elapsed(loop_start)
    result = {
        "session_id": session_id,
        "status": "max_steps_reached",
        "reason": f"Agent hit the {max_steps}-step ceiling without completing",
        "steps": steps,
        "steps_taken": max_steps,
        "duration_ms": duration_ms,
    }
    log_agent_action(
        "agent_runner", "loop:max_steps",
        {"session_id": session_id, "goal": goal[:200]},
        {"steps_taken": max_steps},
        status="error",
        duration_ms=duration_ms,
    )
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def _elapsed(since: datetime) -> int:
    return int((datetime.utcnow() - since).total_seconds() * 1000)


def _error_result(session_id, steps, step_num, loop_start, reason) -> dict:
    result = {
        "session_id": session_id,
        "status": "error",
        "reason": reason,
        "steps": steps,
        "steps_taken": step_num - 1,
        "duration_ms": _elapsed(loop_start),
    }
    log_agent_action(
        "agent_runner", "loop:error",
        {"session_id": session_id, "step": step_num},
        {"reason": reason},
        status="error",
        error=reason,
    )
    return result


def _build_system_prompt() -> str:
    skills = list_skills()
    skill_lines = "\n".join(
        f"- {s['name']}: {s['description']} | required_inputs: {s['required_inputs']}"
        for s in skills
    )
    return f"""You are AutoSats Agent, an AI assistant for a solo digital business owner.
You operate in a strict think-act-observe loop. Output ONLY valid JSON — nothing else.

To call a skill:
{{"action": "skill_call", "skill": "<name>", "input": {{...}}}}

To finish:
{{"action": "done", "output": "<final answer>"}}

Available skills:
{skill_lines}

Rules:
- Step 1 must always be check_kill_switch. Do not skip this.
- Never attempt real financial transactions. This is PAPER MODE only.
- If the kill switch is active or you cannot proceed safely, return done with an explanation.
- Be brief and direct. This is a solo business automation tool.
"""
