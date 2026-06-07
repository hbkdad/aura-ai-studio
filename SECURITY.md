# Security Policy — AutoSats Engine V0.1

## Paper Mode Guarantee

AutoSats Engine V0.1 is hard-wired to **PAPER MODE**. This is not a configuration switch —
it is a code-level guarantee enforced on every wallet operation.

---

## 1. No Private Keys — Ever

- Zero private keys, seed phrases, xpubs, WIFs, or mnemonic phrases exist anywhere in the codebase.
- There is no key-generation code.
- There is no key-storage code.
- Searching the entire codebase for "private", "seed", "mnemonic", "xpub", or "wif" returns zero results.

---

## 2. Paper Mode Only — Real Transactions Are Impossible

`wallet_service.py` enforces this at the function level:

```python
WALLET_MODE = "paper"

def _assert_paper_mode(operation):
    if WALLET_MODE != "paper":
        raise RuntimeError("SAFETY VIOLATION: ...")

def transfer_real_btc(*args, **kwargs):
    _assert_paper_mode("transfer")
    raise RuntimeError("transfer_real_btc() is not implemented in V0.1 PAPER MODE.")

def broadcast_transaction(*args, **kwargs):
    _assert_paper_mode("broadcast")
    raise RuntimeError("broadcast_transaction() is not implemented in V0.1 PAPER MODE.")
```

Every wallet function calls `_assert_paper_mode()` before any logic runs. If `WALLET_MODE`
ever changes from `"paper"`, every function raises immediately.

---

## 3. No Real Crypto Transactions

When `POST /wallet/paper/simulate-allocation` is called:

1. A record is written to `btc_allocations` in SQLite — no network call is made.
2. A record is written to `wallet_events` — no network call is made.
3. The response contains `"wallet_mode": "paper"` and `"disclaimer": "PAPER MODE ONLY — no real BTC was moved"`.

The blockchain is never contacted. No RPC call, no REST call, no P2P message.

---

## 4. Kill Switch — Present on Every Write Operation

A kill switch exists in `safety_settings` (SQLite) and is checked before every:
- revenue recording
- treasury allocation
- wallet simulation
- agent action

Activating it via `POST /safety/kill-switch {"active": true}` halts all operations immediately.

---

## 5. Every Financial Event Is Logged

All of the following write to immutable audit tables before downstream processing:
- Revenue events → `revenue_events`
- BTC allocations → `btc_allocations` + `wallet_events`
- Policy decisions → `agent_actions`
- Kill switch toggles → `agent_actions`

---

## 6. Secrets Are Never Committed

`.env` is listed in `.gitignore`. Only `.env.example` with placeholder values is tracked.
The CI/CD rule: if `.env` ever appears in a commit diff, reject the commit.

---

## Upgrade Requirements Before Real Money

Real wallet support **must not** be implemented until all of the following are complete:

### Testnet First
- [ ] Full integration with Bitcoin testnet (not mainnet)
- [ ] End-to-end test of the complete fund flow on testnet
- [ ] Testnet stability verified over at least 30 days of simulated use

### Spending Caps — Non-Negotiable
- [ ] Per-transaction spending cap enforced in code (not just settings)
- [ ] Daily aggregate spending cap enforced in code
- [ ] Caps cannot be removed without a code change + review

### Key Management
- [ ] Hardware wallet integration reviewed by a Bitcoin security specialist
- [ ] No software key storage — all signing must happen on hardware
- [ ] Multi-sig required for any single transaction above a threshold
- [ ] Key derivation path documented and audited

### Infrastructure
- [ ] Authentication layer added to all API endpoints
- [ ] Rate limiting on all write endpoints
- [ ] Webhook signature verification for Stripe/Gumroad
- [ ] TLS enforced — no plaintext HTTP in production

### Audit
- [ ] Full penetration test of the complete stack
- [ ] Legal/compliance review for CRA/IRS digital asset reporting requirements
- [ ] Third-party security audit of wallet integration code
- [ ] All findings resolved before mainnet deployment

---

## Why These Requirements Exist

Bitcoin transactions are irreversible. A single bug in payment code can result in
permanent loss of funds with no recourse. The upgrade checklist above is the minimum
viable bar — not a gold standard. When in doubt, wait for testnet validation.

---

## Reporting a Vulnerability

Do not open a public GitHub issue for security vulnerabilities.
Contact the maintainer privately with a description of the issue and reproduction steps.

---

*AutoSats Engine is a personal finance automation tool. V0.1 is a local-first MVP
intended for single-user use on a trusted machine. Do not expose the API server
to the public internet without adding authentication.*
