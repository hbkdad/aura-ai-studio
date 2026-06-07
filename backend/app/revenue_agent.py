import json
from datetime import datetime
from .db import get_db
from .policy_engine import process_revenue_event, log_agent_action


def record_manual_revenue(
    source: str,
    gross_amount: float,
    description: str = None,
    currency: str = "CAD",
    payment_method: str = "manual",
    reference_id: str = None,
    metadata: dict = None,
) -> dict:
    start = datetime.utcnow()

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO revenue_events (source, description, gross_amount, currency, payment_method, reference_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            source,
            description,
            gross_amount,
            currency,
            payment_method,
            reference_id,
            json.dumps(metadata) if metadata else None,
        ))
        revenue_id = cursor.lastrowid

    policy_result = process_revenue_event(revenue_id, gross_amount)

    duration = int((datetime.utcnow() - start).total_seconds() * 1000)
    log_agent_action(
        "revenue_agent", "record_manual",
        {"source": source, "gross": gross_amount},
        {"revenue_id": revenue_id, "policy": policy_result},
        duration_ms=duration,
    )

    return {
        "id": revenue_id,
        "source": source,
        "gross_amount": gross_amount,
        "currency": currency,
        "policy_result": policy_result,
    }


def get_all_revenue(limit: int = 100, offset: int = 0) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM revenue_events ORDER BY created_at DESC LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()
        return [dict(r) for r in rows]


def get_revenue_stats() -> dict:
    with get_db() as conn:
        row = conn.execute("""
            SELECT
                COALESCE(SUM(gross_amount), 0) as total_gross,
                COUNT(*) as total_events,
                COALESCE(AVG(gross_amount), 0) as avg_sale,
                COALESCE(MAX(gross_amount), 0) as max_sale,
                COALESCE(MIN(gross_amount), 0) as min_sale
            FROM revenue_events
        """).fetchone()
        return dict(row)
