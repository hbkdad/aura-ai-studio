"""
ComplianceLogAgent — CRA-ready CSV export and agent action audit trail.

Responsibilities:
- Export all revenue events with full treasury breakdown as a CRA-compatible CSV
- Retrieve the agent action log for transparency and debugging
- Provide a read-only view of what the system has done

Canadian CRA compliance context:
  - Every revenue event stores: date, source, gross amount, currency (CAD default)
  - Treasury split percentages are recorded per-event in the CSV
  - All agent actions are timestamped in agent_actions for audit trail purposes

Does NOT:
- Delete or modify any records
- File taxes or interact with CRA systems
- Process payroll or GST/HST calculations (manual verification required)
"""
from datetime import datetime
from ..policy_engine import log_agent_action
from ..tax_export import export_revenue_csv
from ..audit_agent import get_agent_actions as _get_actions

AGENT_NAME = "compliance_log_agent"


class ComplianceLogAgent:
    name = AGENT_NAME
    description = "CRA-compatible CSV export and full agent action audit trail"
    skills_used = ["csv_export"]

    def export_csv(self) -> dict:
        """Export all revenue events with treasury breakdown. Returns CSV string + row count."""
        start = datetime.utcnow()
        csv_data = export_revenue_csv()
        row_count = max(0, csv_data.count("\n") - 5)

        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        log_agent_action(
            AGENT_NAME, "export_csv",
            {},
            {"row_count": row_count},
            duration_ms=duration_ms,
        )
        return {
            "csv": csv_data,
            "row_count": row_count,
            "disclaimer": (
                "For CRA reporting purposes. Always verify totals with a qualified "
                "tax professional. Currency amounts are stored as entered (default: CAD)."
            ),
        }

    def action_log(self, limit: int = 100) -> list:
        """Return the most recent agent actions from the audit log, newest first."""
        return _get_actions(limit=limit)

    def summary(self) -> dict:
        """Return a high-level compliance summary."""
        from ..db import get_db
        with get_db() as conn:
            rev = conn.execute(
                "SELECT COUNT(*) as cnt, COALESCE(SUM(gross_amount),0) as total FROM revenue_events"
            ).fetchone()
            actions = conn.execute(
                "SELECT COUNT(*) as cnt FROM agent_actions"
            ).fetchone()
        return {
            "revenue_events_count": rev["cnt"],
            "revenue_total_gross": rev["total"],
            "agent_actions_count": actions["cnt"],
            "disclaimer": "All figures are gross amounts before tax. Not tax advice.",
        }
