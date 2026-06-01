import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import io

from .db import init_db
from .revenue_agent import record_manual_revenue, get_all_revenue, get_revenue_stats
from .treasury import get_summary, get_active_rules, calculate_breakdown
from .audit_agent import run_website_audit, get_agent_actions
from .wallet_service import (
    simulate_paper_allocation, get_btc_allocations,
    get_wallet_summary, get_btc_price,
)
from .tax_export import export_revenue_csv
from .policy_engine import check_kill_switch, get_safety_settings, log_agent_action
from .db import get_db

app = FastAPI(
    title="AutoSats Engine",
    description="Local-first digital business automation — PAPER MODE V0.1",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    kill = check_kill_switch()
    settings = get_safety_settings()
    return {
        "status": "ok",
        "version": "0.1.0",
        "mode": "PAPER",
        "kill_switch_active": kill,
        "wallet_mode": settings.get("wallet_mode", "paper"),
    }


# ── Revenue ───────────────────────────────────────────────────────────────────

class ManualRevenueRequest(BaseModel):
    source: str = Field(..., description="Revenue source (e.g. gumroad, stripe, consulting)")
    gross_amount: float = Field(..., gt=0, description="Gross amount in USD")
    description: Optional[str] = None
    currency: str = "USD"
    payment_method: str = "manual"
    reference_id: Optional[str] = None
    metadata: Optional[dict] = None


@app.post("/revenue/manual")
def create_manual_revenue(body: ManualRevenueRequest):
    if check_kill_switch():
        raise HTTPException(status_code=503, detail="Kill switch is active — all operations halted")
    result = record_manual_revenue(
        source=body.source,
        gross_amount=body.gross_amount,
        description=body.description,
        currency=body.currency,
        payment_method=body.payment_method,
        reference_id=body.reference_id,
        metadata=body.metadata,
    )
    return result


@app.get("/revenue")
def list_revenue(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    events = get_all_revenue(limit=limit, offset=offset)
    stats = get_revenue_stats()
    return {"events": events, "stats": stats}


# ── Treasury ──────────────────────────────────────────────────────────────────

@app.get("/treasury/summary")
def treasury_summary():
    return get_summary()


class TreasuryCalculateRequest(BaseModel):
    gross_amount: float = Field(..., gt=0)
    tax_reserve_pct: Optional[float] = None
    btc_allocation_pct: Optional[float] = None
    operating_cash_pct: Optional[float] = None
    tool_budget_pct: Optional[float] = None


@app.post("/treasury/calculate")
def treasury_calculate(body: TreasuryCalculateRequest):
    rules = get_active_rules()
    if body.tax_reserve_pct is not None:
        rules["tax_reserve_pct"] = body.tax_reserve_pct
    if body.btc_allocation_pct is not None:
        rules["btc_allocation_pct"] = body.btc_allocation_pct
    if body.operating_cash_pct is not None:
        rules["operating_cash_pct"] = body.operating_cash_pct
    if body.tool_budget_pct is not None:
        rules["tool_budget_pct"] = body.tool_budget_pct

    breakdown = calculate_breakdown(body.gross_amount, rules)
    return {
        "gross": breakdown.gross,
        "tax_reserve": breakdown.tax_reserve,
        "btc_allocation": breakdown.btc_allocation,
        "operating_cash": breakdown.operating_cash,
        "tool_budget": breakdown.tool_budget,
        "remainder": breakdown.remainder,
        "percentages": {
            "tax": breakdown.tax_pct,
            "btc": breakdown.btc_pct,
            "operating": breakdown.operating_pct,
            "tools": breakdown.tool_pct,
        },
    }


# ── BTC Allocations ───────────────────────────────────────────────────────────

@app.get("/btc/allocations")
def list_btc_allocations(limit: int = Query(100, ge=1, le=1000)):
    allocations = get_btc_allocations(limit=limit)
    summary = get_wallet_summary()
    return {"allocations": allocations, "summary": summary}


# ── Agents ────────────────────────────────────────────────────────────────────

class WebsiteAuditRequest(BaseModel):
    business_name: str
    website_url: str
    industry: str
    city: str
    contact_email: Optional[str] = None


@app.post("/agents/website-audit")
def website_audit(body: WebsiteAuditRequest):
    if check_kill_switch():
        raise HTTPException(status_code=503, detail="Kill switch is active")
    result = run_website_audit(
        business_name=body.business_name,
        website_url=body.website_url,
        industry=body.industry,
        city=body.city,
        contact_email=body.contact_email,
    )
    return result


@app.get("/agents/actions")
def list_agent_actions(limit: int = Query(50, ge=1, le=500)):
    return {"actions": get_agent_actions(limit=limit)}


# ── Wallet ────────────────────────────────────────────────────────────────────

class PaperAllocationRequest(BaseModel):
    revenue_event_id: int
    gross_amount: float = Field(..., gt=0)
    btc_allocation_usd: float = Field(..., gt=0)
    notes: Optional[str] = None


@app.post("/wallet/paper/simulate-allocation")
def paper_simulate_allocation(body: PaperAllocationRequest):
    if check_kill_switch():
        raise HTTPException(status_code=503, detail="Kill switch is active")
    result = simulate_paper_allocation(
        revenue_event_id=body.revenue_event_id,
        gross_amount=body.gross_amount,
        btc_allocation_usd=body.btc_allocation_usd,
        notes=body.notes,
    )
    if result.get("status") in ("blocked", "rejected"):
        raise HTTPException(status_code=400, detail=result["reason"])
    return result


# ── Exports ───────────────────────────────────────────────────────────────────

@app.get("/exports/revenue-csv")
def revenue_csv_export():
    csv_content = export_revenue_csv()
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=autosats_revenue_export.csv"},
    )


# ── Safety ────────────────────────────────────────────────────────────────────

class KillSwitchRequest(BaseModel):
    active: bool
    reason: Optional[str] = None


@app.post("/safety/kill-switch")
def set_kill_switch(body: KillSwitchRequest):
    with get_db() as conn:
        conn.execute("""
            UPDATE safety_settings SET kill_switch_active=?, updated_at=datetime('now')
            WHERE id=(SELECT MAX(id) FROM safety_settings)
        """, (1 if body.active else 0,))

    log_agent_action(
        "safety_system", "kill_switch_toggle",
        {"active": body.active, "reason": body.reason},
        {"status": "applied", "kill_switch_active": body.active},
    )

    return {
        "kill_switch_active": body.active,
        "message": f"Kill switch {'ACTIVATED' if body.active else 'DEACTIVATED'}",
        "reason": body.reason,
    }


@app.get("/safety/settings")
def safety_settings():
    return get_safety_settings()


@app.put("/safety/settings")
def update_safety_settings(
    max_single_allocation_usd: Optional[float] = None,
    require_confirmation_above_usd: Optional[float] = None,
):
    with get_db() as conn:
        if max_single_allocation_usd is not None:
            conn.execute(
                "UPDATE safety_settings SET max_single_allocation_usd=?, updated_at=datetime('now') WHERE id=(SELECT MAX(id) FROM safety_settings)",
                (max_single_allocation_usd,)
            )
        if require_confirmation_above_usd is not None:
            conn.execute(
                "UPDATE safety_settings SET require_confirmation_above_usd=?, updated_at=datetime('now') WHERE id=(SELECT MAX(id) FROM safety_settings)",
                (require_confirmation_above_usd,)
            )
    return get_safety_settings()


@app.put("/treasury/rules")
def update_treasury_rules(
    tax_reserve_pct: Optional[float] = None,
    btc_allocation_pct: Optional[float] = None,
    operating_cash_pct: Optional[float] = None,
    tool_budget_pct: Optional[float] = None,
):
    with get_db() as conn:
        updates = []
        params = []
        if tax_reserve_pct is not None:
            updates.append("tax_reserve_pct=?")
            params.append(tax_reserve_pct)
        if btc_allocation_pct is not None:
            updates.append("btc_allocation_pct=?")
            params.append(btc_allocation_pct)
        if operating_cash_pct is not None:
            updates.append("operating_cash_pct=?")
            params.append(operating_cash_pct)
        if tool_budget_pct is not None:
            updates.append("tool_budget_pct=?")
            params.append(tool_budget_pct)

        if updates:
            updates.append("updated_at=datetime('now')")
            sql = f"UPDATE treasury_rules SET {', '.join(updates)} WHERE id=(SELECT MAX(id) FROM treasury_rules WHERE is_active=1)"
            conn.execute(sql, params)

    return get_active_rules()
