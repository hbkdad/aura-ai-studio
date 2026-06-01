"""
SafetyPolicySkill — check whether an operation is allowed under current safety policy.

Checks: kill switch + max single allocation limit + confirmation threshold.
Use before any write that involves money amounts to get a clean allowed/blocked decision.
"""
NAME = "safety_policy"
DESCRIPTION = (
    "Checks whether a given amount is safe to allocate under the current kill switch "
    "and spending limit policy — returns allowed/blocked with reason"
)
REQUIRED_INPUTS = ["amount_usd"]
INPUT_SCHEMA = {
    "amount_usd": "float (required) — amount in USD to check against safety policy",
}
OUTPUT_SCHEMA = {
    "allowed": "bool — True if the operation is permitted",
    "requires_confirmation": "bool — True if amount exceeds confirmation threshold",
    "reason": "str | null — why it was blocked (null when allowed)",
    "kill_switch_active": "bool",
    "max_single_allocation_usd": "float",
    "require_confirmation_above_usd": "float",
}


def run(input: dict) -> dict:
    """Check if an amount passes the current safety policy."""
    amount_usd = input.get("amount_usd")
    if amount_usd is None:
        raise ValueError("amount_usd is required")

    amount = float(amount_usd)
    if amount < 0:
        raise ValueError("amount_usd cannot be negative")

    from ..policy_engine import check_kill_switch, validate_allocation_amount, get_safety_settings

    kill = check_kill_switch()
    if kill:
        return {
            "allowed": False,
            "requires_confirmation": False,
            "reason": "Kill switch is active — all operations halted",
            "kill_switch_active": True,
            "max_single_allocation_usd": None,
            "require_confirmation_above_usd": None,
        }

    validation = validate_allocation_amount(amount)
    settings = get_safety_settings()

    return {
        "allowed": validation["allowed"],
        "requires_confirmation": validation.get("requires_confirmation", False),
        "reason": validation.get("reason"),
        "kill_switch_active": False,
        "max_single_allocation_usd": settings.get("max_single_allocation_usd"),
        "require_confirmation_above_usd": settings.get("require_confirmation_above_usd"),
    }
