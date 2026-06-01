"""
Central agent registry for AutoSats Engine.

Maps agent names to agent classes and provides a clean factory interface.
Also re-exports the skill registry so callers only need one import.

Usage:
    from app.agents.registry import get_agent, list_agents, get_skill, list_skills

    # Get an agent instance
    agent = get_agent("revenue")
    result = agent.record(source="gumroad", gross_amount=49.00)

    # List all agents
    for a in list_agents():
        print(a["name"], "—", a["description"])

    # Run a skill directly
    result = get_skill("treasury_split")({"gross_amount": 100.0})
"""
from .revenue_agent import RevenueAgent
from .website_audit_agent import WebsiteAuditAgent
from .sales_outreach_agent import SalesOutreachAgent
from .treasury_agent import TreasuryAgent
from .wallet_safety_agent import WalletSafetyAgent
from .compliance_log_agent import ComplianceLogAgent

# ── Agent registry ────────────────────────────────────────────────────────────

_AGENT_REGISTRY: dict[str, type] = {
    "revenue":          RevenueAgent,
    "website_audit":    WebsiteAuditAgent,
    "sales_outreach":   SalesOutreachAgent,
    "treasury":         TreasuryAgent,
    "wallet_safety":    WalletSafetyAgent,
    "compliance_log":   ComplianceLogAgent,
}


def get_agent(name: str):
    """Return a new instance of the named agent. Raises ValueError if not found."""
    cls = _AGENT_REGISTRY.get(name)
    if cls is None:
        available = list(_AGENT_REGISTRY)
        raise ValueError(f"Unknown agent '{name}'. Available: {available}")
    return cls()


def list_agents() -> list[dict]:
    """Return metadata for all registered agents."""
    return [
        {
            "name": name,
            "description": cls.description,
            "skills_used": cls.skills_used,
        }
        for name, cls in _AGENT_REGISTRY.items()
    ]


# ── Skill registry passthrough ─────────────────────────────────────────────

def get_skill(name: str):
    """Return the run() callable for a skill by name. Raises SkillNotFoundError if not found."""
    from ..skill_registry import _REGISTRY, SkillNotFoundError
    if name not in _REGISTRY:
        raise SkillNotFoundError(f"Skill '{name}' not found. Available: {list(_REGISTRY)}")
    return _REGISTRY[name].run


def list_skills() -> list[dict]:
    """Return metadata for all auto-discovered skills."""
    from ..skill_registry import list_skills as _list
    return _list()
