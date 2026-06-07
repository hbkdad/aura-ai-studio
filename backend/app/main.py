import json
import sqlite3
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator
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
from .memory_service import _purge_expired
from .routers.skills_router import router as skills_router
from .routers.agents_router import router as agents_router
from .routers.memory_router import router as memory_router

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

app.include_router(skills_router)
app.include_router(agents_router)
app.include_router(memory_router)


# ── Global error handlers ─────────────────────────────────────────────────────

@app.exception_handler(sqlite3.Error)
async def sqlite_error_handler(request: Request, exc: sqlite3.Error):
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error — please try again", "type": "database_error"},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "validation_error"},
    )


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()
    _purge_expired()


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
    source: str = Field(..., min_length=1, description="Revenue source (e.g. gumroad, stripe, consulting)")
    gross_amount: float = Field(..., description="Gross amount — must be greater than 0")
    description: Optional[str] = None
    currency: str = Field("CAD", description="Currency code, defaults to CAD")
    payment_method: str = "manual"
    reference_id: Optional[str] = None
    metadata: Optional[dict] = None

    @field_validator("gross_amount")
    @classmethod
    def gross_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("gross_amount must be greater than 0 — negative or zero revenue is not valid")
        return round(v, 2)

    @field_validator("source")
    @classmethod
    def source_must_not_be_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("source is required and cannot be blank")
        return v

    @field_validator("currency")
    @classmethod
    def currency_must_be_valid(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 3:
            raise ValueError("currency must be a 3-letter code (e.g. CAD, USD)")
        return v


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
    gross_amount: float = Field(..., description="Gross amount to calculate breakdown for")
    tax_reserve_pct: Optional[float] = Field(None, ge=0, le=100)
    btc_allocation_pct: Optional[float] = Field(None, ge=0, le=100)
    operating_cash_pct: Optional[float] = Field(None, ge=0, le=100)
    tool_budget_pct: Optional[float] = Field(None, ge=0, le=100)

    @field_validator("gross_amount")
    @classmethod
    def gross_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("gross_amount must be greater than 0")
        return round(v, 2)


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

    total_pct = (
        rules["tax_reserve_pct"] + rules["btc_allocation_pct"] +
        rules["operating_cash_pct"] + rules["tool_budget_pct"]
    )
    if abs(total_pct - 100.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Percentages must sum to 100 — current total is {total_pct:.1f}%",
        )

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


class TreasuryRulesRequest(BaseModel):
    tax_reserve_pct: float = Field(30.0, ge=0, le=100)
    btc_allocation_pct: float = Field(20.0, ge=0, le=100)
    operating_cash_pct: float = Field(40.0, ge=0, le=100)
    tool_budget_pct: float = Field(10.0, ge=0, le=100)

    @model_validator(mode="after")
    def percentages_must_sum_to_100(self) -> "TreasuryRulesRequest":
        total = self.tax_reserve_pct + self.btc_allocation_pct + self.operating_cash_pct + self.tool_budget_pct
        if abs(total - 100.0) > 0.01:
            raise ValueError(
                f"All percentages must sum to exactly 100% — current total is {total:.1f}%. "
                f"Default split: tax=30%, btc=20%, operating=40%, tools=10%"
            )
        return self


@app.put("/treasury/rules")
def update_treasury_rules(body: TreasuryRulesRequest):
    with get_db() as conn:
        conn.execute("""
            UPDATE treasury_rules
            SET tax_reserve_pct=?, btc_allocation_pct=?, operating_cash_pct=?,
                tool_budget_pct=?, updated_at=datetime('now')
            WHERE id=(SELECT MAX(id) FROM treasury_rules WHERE is_active=1)
        """, (
            body.tax_reserve_pct, body.btc_allocation_pct,
            body.operating_cash_pct, body.tool_budget_pct,
        ))
    return get_active_rules()


# ── BTC Allocations ───────────────────────────────────────────────────────────

@app.get("/btc/allocations")
def list_btc_allocations(limit: int = Query(100, ge=1, le=1000)):
    allocations = get_btc_allocations(limit=limit)
    summary = get_wallet_summary()
    return {"allocations": allocations, "summary": summary}


# ── Agents ────────────────────────────────────────────────────────────────────

class WebsiteAuditRequest(BaseModel):
    business_name: str = Field(..., min_length=1)
    website_url: str = Field(..., min_length=4)
    industry: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
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
    revenue_event_id: int = Field(..., gt=0)
    gross_amount: float = Field(..., gt=0)
    btc_allocation_usd: float = Field(..., gt=0)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def allocation_cannot_exceed_gross(self) -> "PaperAllocationRequest":
        if self.btc_allocation_usd > self.gross_amount:
            raise ValueError(
                f"BTC allocation (${self.btc_allocation_usd:.2f}) cannot exceed gross revenue "
                f"(${self.gross_amount:.2f})"
            )
        return self


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
def safety_settings_get():
    return get_safety_settings()


class SafetySettingsRequest(BaseModel):
    max_single_allocation_usd: Optional[float] = Field(None, gt=0)
    require_confirmation_above_usd: Optional[float] = Field(None, gt=0)

    @model_validator(mode="after")
    def confirm_threshold_below_max(self) -> "SafetySettingsRequest":
        if (self.max_single_allocation_usd is not None and
                self.require_confirmation_above_usd is not None):
            if self.require_confirmation_above_usd > self.max_single_allocation_usd:
                raise ValueError(
                    "require_confirmation_above_usd cannot exceed max_single_allocation_usd"
                )
        return self


@app.put("/safety/settings")
def update_safety_settings(body: SafetySettingsRequest):
    with get_db() as conn:
        if body.max_single_allocation_usd is not None:
            conn.execute(
                "UPDATE safety_settings SET max_single_allocation_usd=?, updated_at=datetime('now') "
                "WHERE id=(SELECT MAX(id) FROM safety_settings)",
                (body.max_single_allocation_usd,)
            )
        if body.require_confirmation_above_usd is not None:
            conn.execute(
                "UPDATE safety_settings SET require_confirmation_above_usd=?, updated_at=datetime('now') "
                "WHERE id=(SELECT MAX(id) FROM safety_settings)",
                (body.require_confirmation_above_usd,)
            )
    return get_safety_settings()


# ── Test endpoint ─────────────────────────────────────────────────────────────

@app.post("/test/fake-sale")
def test_fake_sale():
    """
    Creates a fake $100 CAD sale and verifies the treasury split is exactly:
      tax_reserve=30, btc_allocation=20, operating_cash=40, tool_budget=10
    Returns PASS/FAIL with the breakdown details.
    """
    from .revenue_agent import record_manual_revenue as _record

    result = _record(
        source="test",
        gross_amount=100.00,
        description="Automated test — fake $100 CAD sale",
        currency="CAD",
        payment_method="manual",
    )

    policy = result["policy_result"]
    checks = {
        "tax_reserve_eq_30": abs(policy["tax_reserve"] - 30.0) < 0.01,
        "btc_allocation_eq_20": abs(policy["btc_allocation"] - 20.0) < 0.01,
        "operating_cash_eq_40": abs(policy["operating_cash"] - 40.0) < 0.01,
        "tool_budget_eq_10": abs(policy["tool_budget"] - 10.0) < 0.01,
        "remainder_eq_0": abs(policy["remainder"] - 0.0) < 0.01,
    }
    passed = all(checks.values())

    return {
        "result": "PASS" if passed else "FAIL",
        "revenue_id": result["id"],
        "gross": 100.00,
        "currency": "CAD",
        "breakdown": {
            "tax_reserve": policy["tax_reserve"],
            "btc_allocation": policy["btc_allocation"],
            "operating_cash": policy["operating_cash"],
            "tool_budget": policy["tool_budget"],
            "remainder": policy["remainder"],
        },
        "checks": checks,
    }
