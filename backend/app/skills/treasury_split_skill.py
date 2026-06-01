"""
TreasurySplitSkill — calculate the treasury breakdown for a given gross amount.

Uses the active treasury rules from the database (default: 30/20/40/10).
Optional percentage overrides let you preview alternative splits without
changing the stored rules.
"""
NAME = "treasury_split"
DESCRIPTION = (
    "Calculates how a gross revenue amount splits into tax reserve, BTC allocation, "
    "operating cash, and tool budget using the current (or overridden) treasury rules"
)
REQUIRED_INPUTS = ["gross_amount"]
INPUT_SCHEMA = {
    "gross_amount": "float (required) — gross revenue amount to split",
    "tax_reserve_pct": "float (optional) — override tax % (all four must sum to 100 if provided)",
    "btc_allocation_pct": "float (optional) — override BTC %",
    "operating_cash_pct": "float (optional) — override operating cash %",
    "tool_budget_pct": "float (optional) — override tool budget %",
}
OUTPUT_SCHEMA = {
    "gross": "float",
    "tax_reserve": "float",
    "btc_allocation": "float",
    "operating_cash": "float",
    "tool_budget": "float",
    "remainder": "float — should be 0.00 or very close",
    "percentages": "dict — {tax, btc, operating, tools}",
}


def run(input: dict) -> dict:
    """Calculate treasury breakdown. Returns the split as a structured dict."""
    gross = float(input.get("gross_amount", 0))
    if gross <= 0:
        raise ValueError("gross_amount must be greater than 0")

    from ..treasury import get_active_rules, calculate_breakdown

    rules = dict(get_active_rules())

    # Apply optional overrides
    for key in ("tax_reserve_pct", "btc_allocation_pct", "operating_cash_pct", "tool_budget_pct"):
        if key in input and input[key] is not None:
            rules[key] = float(input[key])

    # Validate sum if any override was given
    total = rules["tax_reserve_pct"] + rules["btc_allocation_pct"] + rules["operating_cash_pct"] + rules["tool_budget_pct"]
    if abs(total - 100.0) > 0.01:
        raise ValueError(f"Override percentages must sum to 100 — got {total:.2f}")

    bd = calculate_breakdown(gross, rules)
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
