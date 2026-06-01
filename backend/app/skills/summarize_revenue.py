NAME = "summarize_revenue"
DESCRIPTION = "Queries the database and returns a text summary of all revenue to date"
REQUIRED_INPUTS = []
INPUT_SCHEMA = {}
OUTPUT_SCHEMA = {
    "summary": "str — human-readable summary",
    "total_gross": "float",
    "total_events": "int",
    "avg_sale": "float",
    "max_sale": "float",
}


def run(input: dict) -> dict:
    from ..revenue_agent import get_revenue_stats
    stats = get_revenue_stats()
    gross = stats["total_gross"]
    count = stats["total_events"]
    avg = stats["avg_sale"]
    summary = (
        f"Total revenue: ${gross:,.2f} CAD across {count} event{'s' if count != 1 else ''}. "
        f"Average sale: ${avg:,.2f}. "
        f"Tax reserve (30%): ${gross * 0.3:,.2f}. "
        f"BTC allocation (20%): ${gross * 0.2:,.2f}. "
        f"Operating cash (40%): ${gross * 0.4:,.2f}. "
        f"Tool budget (10%): ${gross * 0.1:,.2f}."
    ) if count > 0 else "No revenue events recorded yet."
    return {
        "summary": summary,
        "total_gross": gross,
        "total_events": count,
        "avg_sale": avg,
        "max_sale": stats["max_sale"],
    }
