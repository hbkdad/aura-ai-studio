"""
context_builder.py — assembles safe context payloads for agents and the AI loop.

build_agent_context() → structured dict for agent use
build_system_context() → text block ready for AI system prompts

Both functions are guaranteed to never include secrets, private keys,
seed phrases, or API credentials — they only surface project rules,
treasury settings, stats, and recent user decisions from memory_events.
"""
from .project_memory import get_product_rules, get_project_summary
from .memory_store import get_events


def build_agent_context(include_recent_events: int = 5) -> dict:
    """
    Build a structured context dict for agent use.

    Includes: project rules, current treasury split, safety state,
    revenue stats, and the most recent 'decision' memory events.

    Safe to serialise to JSON and pass to any agent or skill.
    """
    summary = get_project_summary()
    recent_decisions = get_events(limit=include_recent_events, memory_type="decision")
    recent_rules = get_events(limit=3, memory_type="rule")

    return {
        "project_name": summary["project"]["name"],
        "version": summary["project"]["version"],
        "mode": summary["project"]["mode"],
        "currency": summary["project"]["currency"],
        "treasury_split": summary["rules"]["treasury_split"],
        "safety": summary["rules"]["safety"],
        "invariants": summary["rules"]["invariants"],
        "stats": summary["stats"],
        "recent_decisions": [
            {
                "title": e["title"],
                "type": e["memory_type"],
                "source": e["source"],
                "created_at": e["created_at"],
                "summary": e["content"][:200],
            }
            for e in recent_decisions
        ],
        "recent_rule_changes": [
            {
                "title": e["title"],
                "created_at": e["created_at"],
                "summary": e["content"][:150],
            }
            for e in recent_rules
        ],
    }


def build_system_context() -> str:
    """
    Build a human-readable context block for AI system prompts.

    Returns a plain-text multi-line string. Safe to include verbatim
    in the system prompt sent to OpenAI or Ollama.
    """
    try:
        ctx = build_agent_context()
        rules = ctx["treasury_split"]
        safety = ctx["safety"]
        kill = "ACTIVE — all writes blocked" if safety["kill_switch_active"] else "inactive"

        lines = [
            f"Project: {ctx['project_name']} {ctx['version']} — {ctx['mode']}",
            f"Default currency: {ctx['currency']}",
            f"Treasury split: tax={rules['tax_reserve_pct']}% | "
            f"btc={rules['btc_allocation_pct']}% | "
            f"ops={rules['operating_cash_pct']}% | "
            f"tools={rules['tool_budget_pct']}%",
            f"Kill switch: {kill}",
            f"Wallet mode: {safety['wallet_mode']}",
            f"Revenue events logged: {ctx['stats']['revenue_events']}",
            f"Total gross (CAD): {ctx['stats']['total_gross_cad']}",
            "",
            "Hard rules:",
        ]
        for rule in ctx["invariants"]:
            lines.append(f"  - {rule}")

        if ctx["recent_decisions"]:
            lines.append("")
            lines.append("Recent decisions:")
            for d in ctx["recent_decisions"]:
                lines.append(f"  [{d['created_at'][:10]}] {d['title']}: {d['summary']}")

        if ctx["recent_rule_changes"]:
            lines.append("")
            lines.append("Recent rule changes:")
            for r in ctx["recent_rule_changes"]:
                lines.append(f"  [{r['created_at'][:10]}] {r['title']}: {r['summary']}")

        return "\n".join(lines)

    except Exception as exc:
        return f"[Context unavailable: {exc}]"


def get_safe_doc_excerpt(doc: str = "project_memory", max_chars: int = 2000) -> str:
    """
    Return a truncated excerpt from one of the project docs for use in prompts.

    doc: 'project_memory' | 'agents_and_skills'
    max_chars: truncate at this length to avoid bloating the context window.
    """
    from .project_memory import read_project_memory_doc, read_agents_doc

    if doc == "agents_and_skills":
        text = read_agents_doc()
    else:
        text = read_project_memory_doc()

    if len(text) > max_chars:
        return text[:max_chars] + f"\n\n[Truncated — {len(text) - max_chars} chars omitted]"
    return text
