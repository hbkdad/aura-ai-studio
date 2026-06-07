"""
project_memory.py — reads project docs and summarises current product rules.

Provides structured access to the two canonical docs (PROJECT_MEMORY.md and
AGENTS_AND_SKILLS.md) plus the live DB state (treasury rules, safety settings,
revenue stats). Used by context_builder and the /memory/summary API route.

Path resolution: docs/ is always found relative to this file, so the module
works regardless of the current working directory.
"""
from pathlib import Path

# backend/app/memory/project_memory.py → parents[3] = repo root
_DOCS_DIR = Path(__file__).parents[3] / "docs"


# ── Doc readers ────────────────────────────────────────────────────────────────

def read_project_memory_doc() -> str:
    """Return the full text of docs/PROJECT_MEMORY.md."""
    return _read_doc("PROJECT_MEMORY.md")


def read_agents_doc() -> str:
    """Return the full text of docs/AGENTS_AND_SKILLS.md."""
    return _read_doc("AGENTS_AND_SKILLS.md")


def _read_doc(filename: str) -> str:
    path = _DOCS_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"[{filename} not found — expected at {path}]"
    except Exception as exc:
        return f"[Error reading {filename}: {exc}]"


# ── Live rules from DB ─────────────────────────────────────────────────────────

def get_product_rules() -> dict:
    """
    Return the current active product rules from the database.

    Never includes secrets, private keys, or credentials.
    Safe to pass to agents and display in the UI.
    """
    from ..treasury import get_active_rules
    from ..policy_engine import get_safety_settings, check_kill_switch

    rules = get_active_rules()
    safety = get_safety_settings()

    return {
        "treasury_split": {
            "tax_reserve_pct": rules.get("tax_reserve_pct", 30.0),
            "btc_allocation_pct": rules.get("btc_allocation_pct", 20.0),
            "operating_cash_pct": rules.get("operating_cash_pct", 40.0),
            "tool_budget_pct": rules.get("tool_budget_pct", 10.0),
        },
        "safety": {
            "kill_switch_active": check_kill_switch(),
            "wallet_mode": safety.get("wallet_mode", "paper"),
            "max_single_allocation_usd": safety.get("max_single_allocation_usd", 1000.0),
            "require_confirmation_above_usd": safety.get("require_confirmation_above_usd", 500.0),
        },
        "invariants": [
            "Paper mode only in V0.1 — no real BTC transactions",
            "Kill switch enforced on every write operation",
            "Default currency: CAD",
            "Treasury percentages must always sum to exactly 100%",
            "Every financial event and agent action is logged to SQLite",
            "No private keys, seed phrases, or exchange API keys stored anywhere",
            "All agent memory events safety-filtered before writing",
        ],
    }


def get_project_summary() -> dict:
    """
    Return a full project summary combining live DB stats and current rules.

    Safe to display in the UI and pass to the AI agent loop.
    """
    from ..db import get_db
    from ..revenue_agent import get_revenue_stats

    rules = get_product_rules()
    stats = get_revenue_stats()

    with get_db() as conn:
        actions_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM agent_actions"
        ).fetchone()["cnt"]

        btc_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM btc_allocations"
        ).fetchone()["cnt"]

        # memory_events table — safe to fail if table not yet migrated
        try:
            mem_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM memory_events"
            ).fetchone()["cnt"]
        except Exception:
            mem_count = 0

    return {
        "project": {
            "name": "AutoSats Engine",
            "version": "V0.1.0",
            "mode": "PAPER MODE",
            "currency": "CAD",
        },
        "rules": rules,
        "stats": {
            "revenue_events": stats.get("total_events", 0),
            "total_gross_cad": round(stats.get("total_gross", 0.0), 2),
            "btc_allocations": btc_count,
            "agent_actions_logged": actions_count,
            "memory_events": mem_count,
        },
        "docs_available": [
            "docs/PROJECT_MEMORY.md",
            "docs/AGENTS_AND_SKILLS.md",
        ],
    }
