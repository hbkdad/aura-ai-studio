"""
Gumroad integration — V0.1 STUB.

Not wired in paper mode. All functions raise NotImplementedError.
Wire in V0.2 when adding Gumroad sale webhook or polling.

Safety constraint: read-only access to sale data for logging — must never
modify products, prices, or customer records.
"""


def fetch_sales(access_token: str, after: str = None) -> list:
    """Fetch recent sales from the Gumroad API."""
    raise NotImplementedError(
        "Gumroad integration is not enabled in V0.1 paper mode. "
        "Add GUMROAD_ACCESS_TOKEN to .env and wire this in V0.2."
    )


def sale_to_revenue_event(sale: dict) -> dict:
    """Convert a Gumroad sale object to the AutoSats revenue event format."""
    raise NotImplementedError("Not enabled in V0.1 paper mode.")


def verify_ping(payload: dict, seller_id: str) -> bool:
    """Verify a Gumroad ping webhook matches expected seller_id."""
    raise NotImplementedError("Not enabled in V0.1 paper mode.")
