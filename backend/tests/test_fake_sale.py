"""
Standalone test script — run from backend/ directory:

    python -m tests.test_fake_sale

Verifies that a fake $100 CAD sale produces the exact treasury split:
  tax_reserve=30  btc_allocation=20  operating_cash=40  tool_budget=10
"""
import os
import sys
import tempfile

# Use a temp DB so the test never pollutes the real data
os.environ.setdefault("DB_PATH", tempfile.mktemp(suffix=".test.db"))

from app.db import init_db
from app.revenue_agent import record_manual_revenue
from app.treasury import calculate_breakdown, get_active_rules
from app.wallet_service import simulate_paper_allocation, transfer_real_btc, broadcast_transaction


def _check(label: str, actual: float, expected: float, tol: float = 0.01) -> bool:
    ok = abs(actual - expected) <= tol
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}: expected={expected}, got={actual}")
    return ok


def test_treasury_split():
    print("\n=== Test: Treasury split on $100 CAD sale ===")
    init_db()
    result = record_manual_revenue(
        source="gumroad",
        gross_amount=100.00,
        description="Automated test sale",
        currency="CAD",
        payment_method="manual",
    )
    p = result["policy_result"]
    checks = [
        _check("tax_reserve",    p["tax_reserve"],    30.0),
        _check("btc_allocation", p["btc_allocation"], 20.0),
        _check("operating_cash", p["operating_cash"], 40.0),
        _check("tool_budget",    p["tool_budget"],    10.0),
        _check("remainder",      p["remainder"],       0.0),
    ]
    return all(checks)


def test_currency_default():
    print("\n=== Test: Currency defaults to CAD ===")
    from app.revenue_agent import record_manual_revenue as _r
    result = _r(source="test", gross_amount=50.0)
    ok = result["currency"] == "CAD"
    print(f"  [{'PASS' if ok else 'FAIL'}] currency default is CAD: got '{result['currency']}'")
    return ok


def test_negative_amount_rejected():
    print("\n=== Test: Negative revenue amount is rejected ===")
    from app.main import ManualRevenueRequest
    from pydantic import ValidationError
    try:
        ManualRevenueRequest(source="test", gross_amount=-50.0)
        print("  [FAIL] Expected ValidationError but none raised")
        return False
    except ValidationError:
        print("  [PASS] ValidationError raised for negative amount")
        return True


def test_paper_mode_guard():
    print("\n=== Test: Real transfer methods raise RuntimeError ===")
    results = []
    for fn_name, fn in [("transfer_real_btc", transfer_real_btc),
                        ("broadcast_transaction", broadcast_transaction)]:
        try:
            fn()
            print(f"  [FAIL] {fn_name} did not raise")
            results.append(False)
        except RuntimeError as e:
            print(f"  [PASS] {fn_name} raised RuntimeError: {str(e)[:80]}...")
            results.append(True)
    return all(results)


def test_paper_allocation():
    print("\n=== Test: Paper BTC allocation simulation ===")
    result = simulate_paper_allocation(
        revenue_event_id=1,
        gross_amount=100.0,
        btc_allocation_usd=20.0,
    )
    checks = [
        _check("allocated_usd", result["allocated_usd"], 20.0),
        _check("simulated_btc", result["simulated_btc"], 20.0 / 65000.0, tol=1e-7),
    ]
    ok_mode = result.get("wallet_mode") == "paper"
    print(f"  [{'PASS' if ok_mode else 'FAIL'}] wallet_mode is 'paper': got '{result.get('wallet_mode')}'")
    ok_disc = "PAPER MODE" in result.get("disclaimer", "")
    print(f"  [{'PASS' if ok_disc else 'FAIL'}] disclaimer contains 'PAPER MODE'")
    return all(checks) and ok_mode and ok_disc


def test_calc_breakdown_direct():
    print("\n=== Test: calculate_breakdown() math ===")
    from app.treasury import calculate_breakdown
    bd = calculate_breakdown(250.0)
    checks = [
        _check("tax_reserve",    bd.tax_reserve,    75.0),
        _check("btc_allocation", bd.btc_allocation, 50.0),
        _check("operating_cash", bd.operating_cash, 100.0),
        _check("tool_budget",    bd.tool_budget,    25.0),
        _check("remainder",      bd.remainder,       0.0),
    ]
    return all(checks)


if __name__ == "__main__":
    init_db()
    results = {
        "treasury_split":       test_treasury_split(),
        "currency_default":     test_currency_default(),
        "negative_rejected":    test_negative_amount_rejected(),
        "paper_mode_guard":     test_paper_mode_guard(),
        "paper_allocation":     test_paper_allocation(),
        "calc_breakdown_direct": test_calc_breakdown_direct(),
    }

    print("\n" + "=" * 48)
    all_passed = all(results.values())
    for name, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print("=" * 48)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    sys.exit(0 if all_passed else 1)
