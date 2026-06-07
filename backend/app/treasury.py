from dataclasses import dataclass
from .db import get_db


@dataclass
class TreasuryBreakdown:
    gross: float
    tax_reserve: float
    btc_allocation: float
    operating_cash: float
    tool_budget: float
    remainder: float
    tax_pct: float
    btc_pct: float
    operating_pct: float
    tool_pct: float


def get_active_rules() -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM treasury_rules WHERE is_active=1 ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            return {
                "name": "Default Policy",
                "tax_reserve_pct": 30.0,
                "btc_allocation_pct": 20.0,
                "operating_cash_pct": 40.0,
                "tool_budget_pct": 10.0,
            }
        return dict(row)


def calculate_breakdown(gross: float, rules: dict = None) -> TreasuryBreakdown:
    if rules is None:
        rules = get_active_rules()

    tax_pct = rules["tax_reserve_pct"] / 100
    btc_pct = rules["btc_allocation_pct"] / 100
    op_pct = rules["operating_cash_pct"] / 100
    tool_pct = rules["tool_budget_pct"] / 100

    tax = round(gross * tax_pct, 2)
    btc = round(gross * btc_pct, 2)
    operating = round(gross * op_pct, 2)
    tool = round(gross * tool_pct, 2)
    remainder = round(gross - tax - btc - operating - tool, 2)

    return TreasuryBreakdown(
        gross=gross,
        tax_reserve=tax,
        btc_allocation=btc,
        operating_cash=operating,
        tool_budget=tool,
        remainder=remainder,
        tax_pct=rules["tax_reserve_pct"],
        btc_pct=rules["btc_allocation_pct"],
        operating_pct=rules["operating_cash_pct"],
        tool_pct=rules["tool_budget_pct"],
    )


def get_summary() -> dict:
    with get_db() as conn:
        row = conn.execute("""
            SELECT
                COALESCE(SUM(gross_amount), 0) as total_gross,
                COUNT(*) as event_count
            FROM revenue_events
        """).fetchone()

        total_gross = row["total_gross"]
        breakdown = calculate_breakdown(total_gross)
        rules = get_active_rules()

        return {
            "total_gross": total_gross,
            "event_count": row["event_count"],
            "tax_reserve": breakdown.tax_reserve,
            "btc_allocation": breakdown.btc_allocation,
            "operating_cash": breakdown.operating_cash,
            "tool_budget": breakdown.tool_budget,
            "remainder": breakdown.remainder,
            "rules": rules,
        }
