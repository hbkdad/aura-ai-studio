NAME = "fetch_btc_price"
DESCRIPTION = "Returns the current simulated BTC price in USD (paper mode only)"
REQUIRED_INPUTS = []
INPUT_SCHEMA = {}
OUTPUT_SCHEMA = {
    "price_usd": "float — simulated BTC/USD price",
    "mode": "str — always 'paper' in V0.1",
    "disclaimer": "str",
}


def run(input: dict) -> dict:
    from ..wallet_service import get_btc_price, WALLET_MODE
    return {
        "price_usd": get_btc_price(),
        "mode": WALLET_MODE,
        "disclaimer": "PAPER MODE — simulated price only, not a live market feed",
    }
