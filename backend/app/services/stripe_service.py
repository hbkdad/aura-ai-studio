"""
Stripe integration — V0.1 STUB.

Not wired in paper mode. All functions raise NotImplementedError.
Wire in V0.2 when adding Stripe webhook revenue tracking.

Safety constraint: even when wired, this must ONLY read charge data for
logging — it must never initiate payouts or access customer payment details.
"""


def verify_webhook(payload: bytes, signature: str, secret: str) -> dict:
    """Verify a Stripe webhook signature and return the parsed event."""
    raise NotImplementedError(
        "Stripe webhooks are not enabled in V0.1 paper mode. "
        "Add STRIPE_WEBHOOK_SECRET to .env and wire this in V0.2."
    )


def fetch_recent_charges(api_key: str, limit: int = 100) -> list:
    """Fetch recent successful charges from Stripe for revenue reconciliation."""
    raise NotImplementedError(
        "Stripe charge fetching is not enabled in V0.1 paper mode. "
        "Add STRIPE_SECRET_KEY to .env and wire this in V0.2."
    )


def charge_to_revenue_event(charge: dict) -> dict:
    """Convert a Stripe charge object to the AutoSats revenue event format."""
    raise NotImplementedError("Not enabled in V0.1 paper mode.")
