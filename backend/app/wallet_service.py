import json
from datetime import datetime
from .db import get_db
from .policy_engine import log_agent_action, check_kill_switch, validate_allocation_amount

SIMULATED_BTC_PRICE_USD = 65000.0


def get_btc_price() -> float:
    return SIMULATED_BTC_PRICE_USD


def simulate_paper_allocation(
    revenue_event_id: int,
    gross_amount: float,
    btc_allocation_usd: float,
    notes: str = None,
) -> dict:
    start = datetime.utcnow()

    if check_kill_switch():
        result = {"status": "blocked", "reason": "Kill switch is active"}
        log_agent_action("wallet_service", "paper_allocation",
                         {"revenue_event_id": revenue_event_id, "amount_usd": btc_allocation_usd},
                         result, status="blocked")
        return result

    validation = validate_allocation_amount(btc_allocation_usd)
    if not validation["allowed"]:
        result = {"status": "rejected", "reason": validation["reason"]}
        log_agent_action("wallet_service", "paper_allocation",
                         {"revenue_event_id": revenue_event_id, "amount_usd": btc_allocation_usd},
                         result, status="rejected")
        return result

    btc_price = get_btc_price()
    simulated_btc = round(btc_allocation_usd / btc_price, 8)

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO btc_allocations
                (revenue_event_id, gross_amount, allocated_usd, btc_price_usd, simulated_btc, wallet_mode, status, notes)
            VALUES (?, ?, ?, ?, ?, 'paper', 'simulated', ?)
        """, (revenue_event_id, gross_amount, btc_allocation_usd, btc_price, simulated_btc, notes))
        allocation_id = cursor.lastrowid

        conn.execute("""
            INSERT INTO wallet_events
                (event_type, wallet_mode, amount_usd, simulated_btc, btc_price_usd, notes)
            VALUES ('allocation', 'paper', ?, ?, ?, ?)
        """, (btc_allocation_usd, simulated_btc, btc_price, f"Paper allocation for revenue #{revenue_event_id}"))

    result = {
        "allocation_id": allocation_id,
        "revenue_event_id": revenue_event_id,
        "gross_amount": gross_amount,
        "allocated_usd": btc_allocation_usd,
        "btc_price_usd": btc_price,
        "simulated_btc": simulated_btc,
        "wallet_mode": "paper",
        "status": "simulated",
        "disclaimer": "PAPER MODE ONLY — no real BTC was moved",
    }

    duration = int((datetime.utcnow() - start).total_seconds() * 1000)
    log_agent_action("wallet_service", "paper_allocation",
                     {"revenue_event_id": revenue_event_id, "amount_usd": btc_allocation_usd},
                     result, duration_ms=duration)
    return result


def get_btc_allocations(limit: int = 100) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM btc_allocations ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_wallet_summary() -> dict:
    with get_db() as conn:
        row = conn.execute("""
            SELECT
                COALESCE(SUM(allocated_usd), 0) as total_allocated_usd,
                COALESCE(SUM(simulated_btc), 0) as total_simulated_btc,
                COUNT(*) as total_allocations,
                wallet_mode
            FROM btc_allocations
            GROUP BY wallet_mode
        """).fetchone()

        if not row:
            return {
                "total_allocated_usd": 0.0,
                "total_simulated_btc": 0.0,
                "total_allocations": 0,
                "wallet_mode": "paper",
                "current_btc_price_usd": get_btc_price(),
            }

        return {
            "total_allocated_usd": row["total_allocated_usd"],
            "total_simulated_btc": row["total_simulated_btc"],
            "total_allocations": row["total_allocations"],
            "wallet_mode": row["wallet_mode"] or "paper",
            "current_btc_price_usd": get_btc_price(),
        }
