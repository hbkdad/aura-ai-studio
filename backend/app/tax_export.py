import csv
import io
from datetime import datetime
from .db import get_db
from .treasury import get_active_rules, calculate_breakdown


def export_revenue_csv() -> str:
    rules = get_active_rules()

    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM revenue_events ORDER BY created_at ASC
        """).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Date", "Source", "Description", "Gross Amount", "Currency",
        "Payment Method", "Reference ID",
        "Tax Reserve (30%)", "BTC Allocation (20%)",
        "Operating Cash (40%)", "Tool Budget (10%)", "Remainder",
    ])

    total_gross = 0.0
    total_tax = 0.0
    total_btc = 0.0
    total_op = 0.0
    total_tool = 0.0

    for row in rows:
        gross = row["gross_amount"]
        breakdown = calculate_breakdown(gross, rules)

        writer.writerow([
            row["id"],
            row["created_at"],
            row["source"],
            row["description"] or "",
            f"{gross:.2f}",
            row["currency"],
            row["payment_method"] or "manual",
            row["reference_id"] or "",
            f"{breakdown.tax_reserve:.2f}",
            f"{breakdown.btc_allocation:.2f}",
            f"{breakdown.operating_cash:.2f}",
            f"{breakdown.tool_budget:.2f}",
            f"{breakdown.remainder:.2f}",
        ])

        total_gross += gross
        total_tax += breakdown.tax_reserve
        total_btc += breakdown.btc_allocation
        total_op += breakdown.operating_cash
        total_tool += breakdown.tool_budget

    writer.writerow([])
    writer.writerow([
        "TOTALS", "", "", "",
        f"{total_gross:.2f}", "", "", "",
        f"{total_tax:.2f}",
        f"{total_btc:.2f}",
        f"{total_op:.2f}",
        f"{total_tool:.2f}",
        f"{total_gross - total_tax - total_btc - total_op - total_tool:.2f}",
    ])

    writer.writerow([])
    writer.writerow([f"Export generated: {datetime.utcnow().isoformat()} UTC"])
    writer.writerow(["Tax rates applied:", f"Tax={rules['tax_reserve_pct']}%",
                     f"BTC={rules['btc_allocation_pct']}%",
                     f"Operating={rules['operating_cash_pct']}%",
                     f"Tools={rules['tool_budget_pct']}%"])

    return output.getvalue()
