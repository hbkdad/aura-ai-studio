import json
from datetime import datetime
from .db import get_db
from .treasury import get_active_rules, calculate_breakdown


def log_agent_action(agent_name: str, action_type: str, input_data: dict, output_data: dict,
                     status: str = "completed", duration_ms: int = None, error: str = None):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO agent_actions (agent_name, action_type, input_data, output_data, status, duration_ms, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_name,
            action_type,
            json.dumps(input_data),
            json.dumps(output_data),
            status,
            duration_ms,
            error,
        ))


def check_kill_switch() -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT kill_switch_active FROM safety_settings ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return bool(row["kill_switch_active"]) if row else False


def get_safety_settings() -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM safety_settings ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else {}


def validate_allocation_amount(amount_usd: float) -> dict:
    settings = get_safety_settings()
    max_single = settings.get("max_single_allocation_usd", 1000.0)
    requires_confirm = settings.get("require_confirmation_above_usd", 500.0)

    if check_kill_switch():
        return {"allowed": False, "reason": "Kill switch is active — all operations halted"}

    if amount_usd > max_single:
        return {
            "allowed": False,
            "reason": f"Amount ${amount_usd:.2f} exceeds max single allocation of ${max_single:.2f}",
        }

    return {
        "allowed": True,
        "requires_confirmation": amount_usd > requires_confirm,
        "reason": None,
    }


def process_revenue_event(revenue_id: int, gross_amount: float) -> dict:
    start = datetime.utcnow()

    kill = check_kill_switch()
    if kill:
        result = {"status": "blocked", "reason": "Kill switch active"}
        log_agent_action("policy_engine", "revenue_process", {"revenue_id": revenue_id}, result, status="blocked")
        return result

    rules = get_active_rules()
    breakdown = calculate_breakdown(gross_amount, rules)

    result = {
        "revenue_id": revenue_id,
        "gross": gross_amount,
        "tax_reserve": breakdown.tax_reserve,
        "btc_allocation": breakdown.btc_allocation,
        "operating_cash": breakdown.operating_cash,
        "tool_budget": breakdown.tool_budget,
        "remainder": breakdown.remainder,
        "rules_applied": rules.get("name", "Default Policy"),
        "status": "processed",
    }

    duration = int((datetime.utcnow() - start).total_seconds() * 1000)
    log_agent_action("policy_engine", "revenue_process",
                     {"revenue_id": revenue_id, "gross": gross_amount},
                     result, duration_ms=duration)
    return result
