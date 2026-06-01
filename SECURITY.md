# Security Policy — AutoSats Engine V0.1

## Why V0.1 is PAPER MODE Only

AutoSats Engine V0.1 is intentionally restricted to **paper mode** — no real money moves,
no real Bitcoin transactions, and no private keys are ever stored or referenced.

### What this means

| Feature | V0.1 Status |
|---|---|
| Real BTC transactions | ❌ Disabled |
| Private key storage | ❌ Never implemented |
| Real wallet integration | ❌ Not present |
| Stripe live payments | ❌ Placeholder only |
| Gumroad live payments | ❌ Placeholder only |
| Paper BTC simulation | ✅ Enabled |
| Revenue tracking | ✅ Manual entry only |
| Kill switch | ✅ Present and functional |

### Principles

1. **No private keys in code** — the codebase contains zero references to private keys,
   seed phrases, or wallet credentials. There is no key generation code.

2. **No real transactions** — `wallet_service.py` creates simulated database records only.
   No network calls to any blockchain are made.

3. **Every financial event is logged** — all revenue events, allocations, and agent actions
   are written to the audit log in SQLite before any downstream processing occurs.

4. **Kill switch always present** — even in paper mode, the kill switch field exists in the
   database and is checked before every operation. This ensures the architecture is correct
   before real money is involved.

5. **Secrets never committed** — `.env` is in `.gitignore`. Only `.env.example` with
   placeholder values is tracked.

### Before enabling real money (future versions)

- [ ] Full security audit of all API endpoints
- [ ] Authentication and authorization layer added
- [ ] Rate limiting on all write endpoints
- [ ] Webhook signature verification for Stripe/Gumroad
- [ ] Hardware wallet integration review
- [ ] Penetration test of the full stack
- [ ] Legal/compliance review for jurisdiction-specific requirements

### Reporting a vulnerability

If you discover a security issue, please do not open a public GitHub issue.
Contact the maintainer privately with a description of the vulnerability.

---

*AutoSats Engine is a personal finance automation tool. V0.1 is a local-first MVP
intended for single-user use on a trusted machine. Do not expose the API server
to the public internet without adding authentication.*
