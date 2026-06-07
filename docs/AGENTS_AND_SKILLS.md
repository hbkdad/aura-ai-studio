# AutoSats Engine — Agents & Skills Reference

**Version:** V0.1.0 — PAPER MODE  
**Last updated:** 2026-06-01

---

## Architecture Overview

```
API Routes (main.py + routers/)
        │
        ▼
    Agents (app/agents/)          ← orchestrators, one per business domain
        │
        ├── calls ──► Skills (app/skills/)     ← atomic operations, AI-loop callable
        ├── calls ──► Services (app/services/) ← external integrations (stubs in V0.1)
        ├── reads ──► Memory (app/memory/)     ← short-term + long-term agent state
        └── checks ──► Safety (app/safety/)   ← kill switch, policy validation
```

**Agents** are class-based orchestrators. Each handles one business domain (revenue, treasury, wallet, etc.). They call skills or service functions, log every action to `agent_actions`, and never move real money.

**Skills** are pure callable modules. Each skill does one thing, has a defined input/output schema, and is auto-discovered by the skill registry for use in the AI think/act/observe loop.

**Registry** (`app/agents/registry.py`) is the single import point for all agents and skills.

---

## Agents

### 1. RevenueAgent

**File:** `backend/app/agents/revenue_agent.py`  
**Registry key:** `"revenue"`

Records revenue events from any source (manual, future Stripe/Gumroad) and calculates the per-event treasury split automatically.

| Method | Description |
|--------|-------------|
| `record(source, gross_amount, ...)` | Record a revenue event; returns event ID + treasury split |
| `stats()` | Aggregate stats: total, count, avg, min, max |
| `list_events(limit, offset)` | Paginated list of events, newest first |
| `split_preview(gross_amount)` | Preview treasury split without recording anything |

**Skills used:** `treasury_split`, `summarize_revenue`, `check_kill_switch`  
**Kill switch:** checked on `record()` — blocked when active

---

### 2. WebsiteAuditAgent

**File:** `backend/app/agents/website_audit_agent.py`  
**Registry key:** `"website_audit"`

Audits a business website and returns structured scores for SEO, design, mobile, and trust. Generates a ready-to-send outreach email.

Scan chain (tries each in order, falls back on failure):
1. `audit_report_skill` → calls `website_scan_skill` (HTTP scan via httpx)
2. `seo_audit_skill` (pyseoanalyzer full crawl, if installed)
3. Simulated scores (random but seeded on base score)

| Method | Description |
|--------|-------------|
| `run_audit(business_name, website_url, industry, city, contact_email?)` | Full audit; returns scores, issues, recommendations, outreach email |

**Skills used:** `website_scan`, `audit_report`, `outreach_email`, `check_kill_switch`  
**Kill switch:** checked on `run_audit()` — blocked when active

---

### 3. SalesOutreachAgent

**File:** `backend/app/agents/sales_outreach_agent.py`  
**Registry key:** `"sales_outreach"`

Generates personalised cold outreach emails for prospect businesses. Can incorporate SEO audit findings for higher personalisation.

| Method | Description |
|--------|-------------|
| `generate(business_name, industry, city, website_url?, issues?, scores?)` | Generate subject + body |
| `generate_from_audit(audit_result)` | Convenience: pass a WebsiteAuditAgent result directly |

**Skills used:** `outreach_email`, `draft_outreach`  
**Kill switch:** not applicable (read-only, no writes)

---

### 4. TreasuryAgent

**File:** `backend/app/agents/treasury_agent.py`  
**Registry key:** `"treasury"`

Manages the treasury split rules and calculates per-amount breakdowns. Default split: 30% tax / 20% BTC / 40% ops / 10% tools.

| Method | Description |
|--------|-------------|
| `summary()` | Cumulative treasury totals across all revenue |
| `active_rules()` | Currently active split percentages |
| `calculate(gross_amount, rules?)` | Breakdown preview for any amount |
| `update_rules(tax, btc, operating, tools)` | Update split rules (must sum to 100%) |

**Skills used:** `treasury_split`, `check_kill_switch`  
**Kill switch:** checked on `update_rules()` — blocked when active

---

### 5. WalletSafetyAgent

**File:** `backend/app/agents/wallet_safety_agent.py`  
**Registry key:** `"wallet_safety"`

Paper-mode BTC allocation simulation. **Never moves real money.** Validates all amounts against the kill switch and spending limits before simulating.

| Method | Description |
|--------|-------------|
| `simulate_allocation(revenue_event_id, gross_amount, btc_usd, notes?)` | Paper-simulate BTC allocation |
| `get_allocations(limit)` | Paper allocation history |
| `wallet_summary()` | Total simulated BTC + USD + mock price |
| `btc_price()` | Mock BTC price (static $65,000 in V0.1) |
| `safety_settings()` | Kill switch state + spending caps |
| `set_kill_switch(active, reason?)` | Toggle kill switch on/off |

**Skills used:** `btc_allocation`, `safety_policy`, `check_kill_switch`  
**Kill switch:** checked on `simulate_allocation()` — blocked when active  
**Hard limit:** `WALLET_MODE = "paper"` constant — `transfer_real_btc()` raises `RuntimeError` immediately

---

### 6. ComplianceLogAgent

**File:** `backend/app/agents/compliance_log_agent.py`  
**Registry key:** `"compliance_log"`

Read-only. Exports CRA-compatible CSV and surfaces the agent action audit trail.

| Method | Description |
|--------|-------------|
| `export_csv()` | Full revenue export with treasury breakdown columns |
| `action_log(limit)` | Agent action log, newest first |
| `summary()` | High-level counts: revenue events, total gross, action log entries |

**Skills used:** `csv_export`  
**Kill switch:** not applicable (read-only)

---

## Skills

Skills follow a strict contract. Every skill module must expose:
```python
NAME: str              # machine-readable identifier
DESCRIPTION: str       # one-line description for AI system prompt
REQUIRED_INPUTS: list  # keys that must be present in input dict
INPUT_SCHEMA: dict     # human-readable parameter descriptions
OUTPUT_SCHEMA: dict    # human-readable output field descriptions
run(input: dict) -> dict
```

Skills are auto-discovered by `skill_registry.py` at server startup via `pkgutil.iter_modules`. Bad files are skipped with a warning — the server never crashes on a broken skill.

---

### Original Skills (V0.1 launch)

| Skill | File | Required Inputs | Description |
|-------|------|----------------|-------------|
| `check_kill_switch` | `check_kill_switch.py` | none | Returns kill switch state and wallet mode |
| `fetch_btc_price` | `fetch_btc_price.py` | none | Returns simulated BTC price ($65k) |
| `summarize_revenue` | `summarize_revenue.py` | none | Returns aggregate revenue stats |
| `draft_outreach` | `draft_outreach.py` | business_name, industry, city | Basic cold email template |
| `seo_audit` | `seo_audit_skill.py` | url | Full pyseoanalyzer crawl with graceful fallback |

---

### New Skills (Architecture Refactor)

| Skill | File | Required Inputs | Description |
|-------|------|----------------|-------------|
| `website_scan` | `website_scan_skill.py` | url | Quick HTTP scan: title, meta, h1, SSL, basic issues |
| `audit_report` | `audit_report_skill.py` | business_name, url | Full business audit report using http_scan → pyseoanalyzer chain |
| `outreach_email` | `outreach_email_skill.py` | business_name, industry, city | Personalised email; accepts optional issues + scores |
| `treasury_split` | `treasury_split_skill.py` | gross_amount | Treasury breakdown with optional percentage overrides |
| `btc_allocation` | `btc_allocation_skill.py` | revenue_event_id, gross_amount, btc_allocation_usd | Paper-mode BTC allocation (no real transaction) |
| `csv_export` | `csv_export_skill.py` | none | CRA-compatible CSV string of all revenue events |
| `safety_policy` | `safety_policy_skill.py` | amount_usd | Kill switch + spending limit check for any amount |
| `memory_read_write` | `memory_read_write_skill.py` | operation, key | Read or write agent memory (short/long-term) |

---

## Agent → Skill Mapping

```
RevenueAgent
  └── treasury_split      (split preview)
  └── summarize_revenue   (stats)
  └── check_kill_switch   (safety gate)

WebsiteAuditAgent
  └── website_scan        (quick HTTP scan)
  └── audit_report        (full report with scores)
  └── outreach_email      (email generation)
  └── check_kill_switch   (safety gate)

SalesOutreachAgent
  └── outreach_email      (with audit context)
  └── draft_outreach      (plain email fallback)

TreasuryAgent
  └── treasury_split      (calculate breakdown)
  └── check_kill_switch   (safety gate)

WalletSafetyAgent
  └── btc_allocation      (paper simulation)
  └── safety_policy       (amount validation)
  └── check_kill_switch   (safety gate)

ComplianceLogAgent
  └── csv_export          (CRA CSV)
```

---

## Using the Registry

```python
from app.agents.registry import get_agent, list_agents, get_skill, list_skills

# Instantiate an agent
agent = get_agent("revenue")
result = agent.record(source="gumroad", gross_amount=49.00)

# Instantiate an audit agent and run it
audit = get_agent("website_audit")
report = audit.run_audit(
    business_name="Maple Digital Co",
    website_url="https://example.com",
    industry="Digital Marketing",
    city="Toronto",
)

# Get an outreach email from the audit result
outreach = get_agent("sales_outreach")
email = outreach.generate_from_audit(report)

# Run a skill directly (bypasses agent layer)
split_fn = get_skill("treasury_split")
breakdown = split_fn({"gross_amount": 500.00})

# List everything
for a in list_agents():
    print(a["name"], "—", a["description"])

for s in list_skills():
    print(s["name"], "| required:", s["required_inputs"])
```

---

## Current Limitations (V0.1)

| Area | Limitation |
|------|-----------|
| BTC Price | Static mock price ($65,000 USD). No live price feed. |
| Website Scan | `website_scan` uses httpx for basic HTML parsing, not a full browser. JavaScript-rendered content is not detected. |
| SEO Audit | `seo_audit` requires `pyseoanalyzer` to be installed. Fallback is simulated scores. |
| Outreach Email | Template-based. No AI generation (requires OpenAI/Ollama API key for AI personalisation). |
| Revenue Sources | Manual entry only. Stripe and Gumroad stubs exist but are not wired. |
| Memory | Agent memory is session-scoped with TTL. No cross-session learning without explicit `long_term` writes. |
| AI Loop | PlaceholderProvider uses keyword routing. Real AI decision-making requires `OPENAI_API_KEY` or `OLLAMA_BASE_URL`. |
| Currency | All amounts stored as entered. No FX conversion. Default is CAD. |

---

## Roadmap — Testnet & Real Wallet Support (V0.2+)

### V0.2 — Bitcoin Testnet

- Wire `btc_node_service.py` in `app/services/`
- Replace `SIMULATED_BTC_PRICE_USD` with live Testnet price feed (CoinGecko or mempool.space)
- Add testnet address generation (no mainnet keys, no real funds)
- Add `BTC_TESTNET_ADDRESS` to `.env.example`
- Hard cap: `MAX_REAL_BTC_ALLOCATION = 0` — still paper mode on mainnet
- All testnet actions still logged to `agent_actions`

### V0.2 — Revenue Webhooks

- Wire `stripe_service.py` — verify Stripe webhook + auto-record revenue events
- Wire `gumroad_service.py` — poll Gumroad sales API on a cron schedule
- Safety rule: webhooks can only *read* charge data and *create* revenue events — no payouts

### V0.3 — Real Wallet (Strictly Limited)

- Requires: hardware wallet review + testnet validation passing + explicit code changes
- Hard spending caps enforced at the `WalletSafetyAgent` layer
- `WALLET_MODE` constant changes from `"paper"` to `"mainnet"` only via a deliberate code commit
- Multi-step confirmation: safety_policy check → user confirmation → log → execute
- Maximum single allocation: user-configurable, default $50 CAD
- `transfer_real_btc()` and `broadcast_transaction()` stubs removed and replaced with tested implementations
- Full SECURITY.md checklist must pass before V0.3 ships

### Never (V0.1 Hard Limits That Do Not Change)

- No private keys or seed phrases in code, config, or database
- No pooled investment or custody of other users' funds
- No automated trading or DeFi interactions
- No exchange API keys (Binance, Coinbase, Kraken, etc.)
- Kill switch remains mandatory and enforced at code level
- Every financial event must be logged — no dark side effects
