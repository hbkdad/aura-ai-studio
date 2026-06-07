"""
WalletSafetyAgent — paper-mode BTC allocation simulation with safety enforcement.

Responsibilities:
- Simulate BTC allocation from revenue (paper mode only, never real)
- Validate amounts against kill switch and spending limits before simulating
- Return simulated BTC amounts at current mock BTC price
- Manage kill switch state (on/off)

Hard limits enforced at this layer (V0.1):
  - WALLET_MODE constant is "paper" — always
  - No private keys, no seed phrases, no transaction signing
  - No real BTC network communication
  - transfer_real_btc() and broadcast_transaction() raise RuntimeError immediately

Does NOT:
- Connect to any Bitcoin node or exchange
- Hold or custody real funds
- Execute trades or DeFi interactions
- Access or store wallet private keys or seed phrases
"""
from ..policy_engine import check_kill_switch, log_agent_action, get_safety_settings
from ..wallet_service import (
    simulate_paper_allocation,
    get_btc_allocations,
    get_wallet_summary,
    get_btc_price,
    WALLET_MODE,
)
from ..db import get_db

AGENT_NAME = "wallet_safety_agent"


class WalletSafetyAgent:
    name = AGENT_NAME
    description = "Paper-mode BTC allocation simulation — enforces kill switch and spending caps"
    skills_used = ["btc_allocation", "safety_policy", "check_kill_switch"]
    WALLET_MODE = WALLET_MODE  # always "paper" in V0.1

    def simulate_allocation(
        self,
        revenue_event_id: int,
        gross_amount: float,
        btc_allocation_usd: float,
        notes: str = None,
    ) -> dict:
        """Simulate allocating a portion of revenue to BTC. No real BTC moves."""
        if check_kill_switch():
            return {"status": "blocked", "reason": "Kill switch is active — no allocation"}
        if btc_allocation_usd > gross_amount:
            raise ValueError(
                f"BTC allocation (${btc_allocation_usd:.2f}) cannot exceed "
                f"gross revenue (${gross_amount:.2f})"
            )
        return simulate_paper_allocation(
            revenue_event_id=revenue_event_id,
            gross_amount=gross_amount,
            btc_allocation_usd=btc_allocation_usd,
            notes=notes,
        )

    def get_allocations(self, limit: int = 100) -> list:
        """Return paper BTC allocation history."""
        return get_btc_allocations(limit=limit)

    def wallet_summary(self) -> dict:
        """Return total simulated BTC and USD allocated, plus mock BTC price."""
        return get_wallet_summary()

    def btc_price(self) -> float:
        """Return the mock BTC price used for paper simulations (not a live feed in V0.1)."""
        return get_btc_price()

    def safety_settings(self) -> dict:
        """Return current kill switch state and spending limits."""
        return get_safety_settings()

    def set_kill_switch(self, active: bool, reason: str = None) -> dict:
        """Toggle the kill switch. When active, all write operations across the app are blocked."""
        with get_db() as conn:
            conn.execute(
                "UPDATE safety_settings SET kill_switch_active=?, updated_at=datetime('now') "
                "WHERE id=(SELECT MAX(id) FROM safety_settings)",
                (1 if active else 0,)
            )
        log_agent_action(
            AGENT_NAME, "kill_switch_toggle",
            {"active": active, "reason": reason},
            {"kill_switch_active": active},
        )
        return {
            "kill_switch_active": active,
            "message": "Kill switch ACTIVATED — all writes blocked" if active else "Kill switch DEACTIVATED",
            "reason": reason,
            "wallet_mode": self.WALLET_MODE,
        }
