"""
TreasuryAgent — manages treasury allocation rules and per-event splits.

Responsibilities:
- Read and update the active treasury split percentages (tax / BTC / ops / tools)
- Calculate the breakdown for any gross amount
- Return treasury summary across all recorded revenue events

The default split is 30/20/40/10 (tax/BTC/ops/tools). Percentages must always
sum to exactly 100%. All updates are guarded by the kill switch.

Does NOT:
- Move money between accounts
- Trigger BTC purchases or transfers
- Override the kill switch
- Handle foreign exchange conversion (all amounts stored in original currency)
"""
from datetime import datetime
from ..policy_engine import check_kill_switch, log_agent_action
from ..treasury import get_active_rules, calculate_breakdown, get_summary
from ..db import get_db

AGENT_NAME = "treasury_agent"


class TreasuryAgent:
    name = AGENT_NAME
    description = "Manages treasury allocation rules and calculates per-event splits (30/20/40/10 default)"
    skills_used = ["treasury_split", "check_kill_switch"]

    def summary(self) -> dict:
        """Return cumulative treasury totals across all recorded revenue events."""
        return get_summary()

    def active_rules(self) -> dict:
        """Return the currently active treasury split percentages."""
        return get_active_rules()

    def calculate(self, gross_amount: float, rules: dict = None) -> dict:
        """Calculate treasury breakdown for a given gross amount without recording anything."""
        if gross_amount <= 0:
            raise ValueError("gross_amount must be greater than 0")
        r = rules or get_active_rules()
        bd = calculate_breakdown(gross_amount, r)
        return {
            "gross": bd.gross,
            "tax_reserve": bd.tax_reserve,
            "btc_allocation": bd.btc_allocation,
            "operating_cash": bd.operating_cash,
            "tool_budget": bd.tool_budget,
            "remainder": bd.remainder,
            "percentages": {
                "tax": bd.tax_pct,
                "btc": bd.btc_pct,
                "operating": bd.operating_pct,
                "tools": bd.tool_pct,
            },
        }

    def update_rules(
        self,
        tax_reserve_pct: float,
        btc_allocation_pct: float,
        operating_cash_pct: float,
        tool_budget_pct: float,
    ) -> dict:
        """Update active treasury rules. All four percentages must sum to exactly 100."""
        if check_kill_switch():
            return {"status": "blocked", "reason": "Kill switch is active"}

        total = tax_reserve_pct + btc_allocation_pct + operating_cash_pct + tool_budget_pct
        if abs(total - 100.0) > 0.01:
            raise ValueError(
                f"Percentages must sum to 100, got {total:.2f}. "
                "Default: tax=30, btc=20, operating=40, tools=10."
            )

        start = datetime.utcnow()
        with get_db() as conn:
            conn.execute("""
                UPDATE treasury_rules
                SET tax_reserve_pct=?, btc_allocation_pct=?, operating_cash_pct=?,
                    tool_budget_pct=?, updated_at=datetime('now')
                WHERE id=(SELECT MAX(id) FROM treasury_rules WHERE is_active=1)
            """, (tax_reserve_pct, btc_allocation_pct, operating_cash_pct, tool_budget_pct))

        result = get_active_rules()
        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        log_agent_action(
            AGENT_NAME, "update_rules",
            {"tax": tax_reserve_pct, "btc": btc_allocation_pct,
             "operating": operating_cash_pct, "tools": tool_budget_pct},
            result,
            duration_ms=duration_ms,
        )
        return result
