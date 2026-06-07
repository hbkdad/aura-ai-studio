NAME = "check_kill_switch"
DESCRIPTION = "Returns the current kill switch state and wallet mode"
REQUIRED_INPUTS = []
INPUT_SCHEMA = {}
OUTPUT_SCHEMA = {
    "kill_switch_active": "bool",
    "wallet_mode": "str — always 'paper' in V0.1",
    "safe_to_proceed": "bool — True when kill switch is off",
}


def run(input: dict) -> dict:
    from ..policy_engine import check_kill_switch, get_safety_settings
    active = check_kill_switch()
    settings = get_safety_settings()
    return {
        "kill_switch_active": active,
        "wallet_mode": settings.get("wallet_mode", "paper"),
        "safe_to_proceed": not active,
    }
