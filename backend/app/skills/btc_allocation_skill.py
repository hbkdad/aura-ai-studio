"""
BTCAllocationSkill — simulate a paper-mode BTC allocation for a revenue event.

PAPER MODE ONLY. No real BTC is moved. No private keys. No blockchain access.
Records a simulated allocation in the btc_allocations table at the current
mock BTC price ($65,000 USD).
"""
NAME = "btc_allocation"
DESCRIPTION = (
    "Simulates a paper-mode BTC allocation for a revenue event — "
    "records how much BTC would have been bought. No real transaction. PAPER MODE ONLY."
)
REQUIRED_INPUTS = ["revenue_event_id", "gross_amount", "btc_allocation_usd"]
INPUT_SCHEMA = {
    "revenue_event_id": "int (required) — ID of the related revenue event",
    "gross_amount": "float (required) — total gross amount of the revenue event",
    "btc_allocation_usd": "float (required) — USD amount to simulate allocating to BTC",
    "notes": "str (optional) — free-text notes for this allocation",
}
OUTPUT_SCHEMA = {
    "allocation_id": "int",
    "revenue_event_id": "int",
    "allocated_usd": "float",
    "btc_price_usd": "float — simulated price, not live",
    "simulated_btc": "float — how much BTC would have been purchased",
    "wallet_mode": "str — always 'paper' in V0.1",
    "status": "str — always 'simulated' in V0.1",
    "disclaimer": "str",
}


def run(input: dict) -> dict:
    """Simulate a paper BTC allocation. Calls wallet_service.simulate_paper_allocation."""
    revenue_event_id = input.get("revenue_event_id")
    gross_amount = input.get("gross_amount")
    btc_allocation_usd = input.get("btc_allocation_usd")
    notes = input.get("notes")

    if revenue_event_id is None:
        raise ValueError("revenue_event_id is required")
    if gross_amount is None or float(gross_amount) <= 0:
        raise ValueError("gross_amount must be greater than 0")
    if btc_allocation_usd is None or float(btc_allocation_usd) <= 0:
        raise ValueError("btc_allocation_usd must be greater than 0")
    if float(btc_allocation_usd) > float(gross_amount):
        raise ValueError("btc_allocation_usd cannot exceed gross_amount")

    from ..wallet_service import simulate_paper_allocation
    result = simulate_paper_allocation(
        revenue_event_id=int(revenue_event_id),
        gross_amount=float(gross_amount),
        btc_allocation_usd=float(btc_allocation_usd),
        notes=notes,
    )

    if result.get("status") in ("blocked", "rejected"):
        raise RuntimeError(result.get("reason", "Allocation blocked or rejected"))

    return result
