"""
RevenueAgent — records revenue events and reports treasury splits.

Responsibilities:
- Accept manual revenue entries from any source (consulting, product sales, etc.)
- Trigger treasury split calculation (30/20/40/10) on every recorded event
- Provide revenue stats for dashboard display
- All write operations are guarded by kill switch

Does NOT:
- Move money between accounts
- Access private keys
- Process payments directly (that's the future Stripe/Gumroad service layer)
- Change treasury split rules (that's TreasuryAgent)
"""
from datetime import datetime
from ..policy_engine import check_kill_switch
from .. import revenue_agent as _svc

AGENT_NAME = "revenue_agent"


class RevenueAgent:
    name = AGENT_NAME
    description = "Records revenue events and calculates per-event treasury splits"
    skills_used = ["treasury_split", "summarize_revenue", "check_kill_switch"]

    def record(
        self,
        source: str,
        gross_amount: float,
        description: str = None,
        currency: str = "CAD",
        payment_method: str = "manual",
        reference_id: str = None,
        metadata: dict = None,
    ) -> dict:
        """Record a revenue event. Returns the event ID and treasury split breakdown."""
        if check_kill_switch():
            return {"status": "blocked", "reason": "Kill switch is active"}
        return _svc.record_manual_revenue(
            source=source,
            gross_amount=gross_amount,
            description=description,
            currency=currency,
            payment_method=payment_method,
            reference_id=reference_id,
            metadata=metadata,
        )

    def stats(self) -> dict:
        """Return aggregate revenue stats: total, count, average, min, max."""
        return _svc.get_revenue_stats()

    def list_events(self, limit: int = 100, offset: int = 0) -> list:
        """Return paginated list of revenue events, newest first."""
        return _svc.get_all_revenue(limit=limit, offset=offset)

    def split_preview(self, gross_amount: float) -> dict:
        """Preview treasury split for a given amount without recording anything."""
        if gross_amount <= 0:
            raise ValueError("gross_amount must be greater than 0")
        from ..skills.treasury_split_skill import run as _split
        return _split({"gross_amount": gross_amount})
