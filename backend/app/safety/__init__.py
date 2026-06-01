"""
Safety policy package — kill switch, spending limits, and allocation validation.

Re-exports the policy_engine interface so agents can import cleanly from
`app.safety` rather than `app.policy_engine`.
"""
from ..policy_engine import (
    check_kill_switch,
    get_safety_settings,
    validate_allocation_amount,
    log_agent_action,
    process_revenue_event,
)

__all__ = [
    "check_kill_switch",
    "get_safety_settings",
    "validate_allocation_amount",
    "log_agent_action",
    "process_revenue_event",
]
