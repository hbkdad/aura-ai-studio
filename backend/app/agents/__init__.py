"""
Agents package.

Each agent is a class that orchestrates one business domain.
Import agents via the registry for a consistent interface:

    from app.agents.registry import get_agent, list_agents
    agent = get_agent("revenue")
    result = agent.record(source="gumroad", gross_amount=49.00)
"""
