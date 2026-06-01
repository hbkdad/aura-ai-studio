"""
CSVExportSkill — export all revenue events as a CRA-compatible CSV string.

Returns the full CSV content as a string. No file is written to disk.
The caller (route or agent) is responsible for streaming it to the client.
"""
NAME = "csv_export"
DESCRIPTION = (
    "Exports all revenue events with treasury breakdown columns as a "
    "CRA-compatible CSV string ready for download or tax reporting"
)
REQUIRED_INPUTS = []
INPUT_SCHEMA = {}
OUTPUT_SCHEMA = {
    "csv": "str — full CSV content",
    "row_count": "int — approximate number of revenue rows",
    "disclaimer": "str",
}


def run(input: dict) -> dict:
    """Export revenue events as a CRA-compatible CSV. Returns csv string + row count."""
    from ..tax_export import export_revenue_csv
    csv_data = export_revenue_csv()
    # Count data rows: total lines minus header, 2 blank + totals + 2 footer lines
    row_count = max(0, csv_data.count("\n") - 5)
    return {
        "csv": csv_data,
        "row_count": row_count,
        "disclaimer": (
            "For CRA reporting purposes. Always verify totals with a qualified tax professional. "
            "Currency: CAD by default."
        ),
    }
