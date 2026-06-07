# AutoSats Engine — Project Memory

**Last updated:** 2026-06-07  
**Version:** V0.1.0 — PAPER MODE  
**Branch:** `claude/autosats-engine-mvp-Dm6Pt`

---

## 1. Product Vision

AutoSats Engine is a **local-first digital business automation tool** for a solo Canadian founder.

**Core loop:**
1. Log revenue from any source (manual entry; future: Stripe/Gumroad webhooks)
2. Auto-split every dollar into four buckets (tax reserve, BTC savings, ops, tools)
3. Simulate BTC allocation at market price — paper mode only, no real keys
4. Run AI-powered website audits on prospect businesses and generate outreach emails
5. Export CRA-compatible revenue/tax CSV at any time
6. Store project decisions, rules, and audit history in a local memory system

**Target user:** Solo digital product seller / freelancer in Canada. Zero-budget. Windows 11 friendly. No crypto custody, no DeFi, no investment speculation.

**Progression path:** Paper mode (V0.1) → Bitcoin testnet (V0.2) → tiny real hot-wallet with spending caps (V0.3)

---

## 2. Hard Safety Rules (Must Never Be Violated)

These rules are **permanent for V0.1** and enforced at the code level:

| Rule | Where enforced |
|------|---------------|
| No private keys in any file | Code review, SECURITY.md |
| No seed phrases anywhere | Code review, SECURITY.md |
| No real wallet transfers | `wallet_service.py` — `transfer_real_btc()` raises immediately |
| No transaction broadcasting | `wallet_service.py` — `broadcast_transaction()` raises immediately |
| No crypto trading | Not implemented; no API integrations |
| No DeFi | Not implemented; no protocol integrations |
| No customer fund custody | No multi-user accounts; no pooled funds |
| No pooled investment logic | Single-user only; no shared treasury |
| Paper mode only in V0.1 | `WALLET_MODE = "paper"` constant; `_assert_paper_mode()` called on every wallet op |
| Kill switch on every write | `check_kill_switch()` called before every POST/PUT that creates data |
| Every financial event logged | `agent_actions` table; `log_agent_action()` called on every revenue/allocation op |
| Every agent action logged | `skill_registry.run_skill()` logs to `agent_actions`; `policy_engine.log_agent_action()` is the shared logger |
| Memory safety filter active | `memory_store.safety_filter()` rejects any content with private keys, seed phrases, API keys, or passwords |

**What must never be added in V0.1:**
- Real BTC/crypto wallet integration
- Exchange API keys (Binance, Coinbase, Kraken, etc.)
- Automatic payment processing (Stripe webhooks that trigger real payouts)
- Multi-user auth / user accounts
- External fund custody of any kind
- AI agent autonomy over real financial actions (agent loop is read-only in V0.1)

---

## 3. Technical Stack

### Backend
| Component | Choice | Notes |
|-----------|--------|-------|
| Framework | FastAPI 0.111.0 | Async-capable; Pydantic v2 built-in |
| Runtime | Python 3.11+ | Type unions `X \| Y` used throughout |
| Database | SQLite (WAL mode) | Local file: `backend/autosats.db` |
| Validation | Pydantic v2 | `@field_validator`, `@model_validator` |
| HTTP client | httpx | Used inside OpenAI/Ollama providers and website_scan skill |
| SEO crawling | pyseoanalyzer | In requirements.txt; graceful ImportError fallback in skill |
| Tests | stdlib unittest | `backend/tests/test_fake_sale.py` |

### Frontend
| Component | Choice | Notes |
|-----------|--------|-------|
| Framework | React 18 + Vite | Dark dashboard theme |
| HTTP | Axios | Interceptor converts Pydantic errors to `err.friendlyMessage` |
| Routing | React Router v6 | 7 pages |
| Styling | Custom CSS vars | `--accent` (orange), `--green`, `--red`, `--yellow`, `--muted` |

### Deployment
- Local only. Backend: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Frontend dev: `npm run dev` (Vite proxies `/api` → port 8000)
- No Docker yet. No cloud hosting.

---

## 4. Database Schema (SQLite)

File: `backend/app/db.py`

| Table | Purpose |
|-------|---------|
| `revenue_events` | Every logged sale — source, gross amount, currency (default **CAD**), metadata |
| `treasury_rules` | Active split percentages — default 30/20/40/10 |
| `btc_allocations` | Paper-mode BTC simulation records linked to revenue events |
| `agent_actions` | Audit log for every agent call, skill execution, and policy engine decision |
| `wallet_events` | Low-level wallet event stream (allocation, type, paper amounts) |
| `safety_settings` | Kill switch state, wallet mode, spending caps |
| `agent_memory` | Short-term (TTL) and long-term (persistent) key-value store for agent state |
| `memory_events` | Human-readable project decisions, rules, notes, and audit history |

`agent_memory` has a `UNIQUE(agent_name, memory_type, key)` constraint and uses `ON CONFLICT DO UPDATE SET` upsert semantics.

`memory_events` has an index on `memory_type` for filtered queries.

Seeds on first run: Default treasury rule (30/20/40/10) + safety settings (kill_switch=0, mode=paper).

---

## 5. API Routes

Base: `http://localhost:8000`  
Frontend proxy: `/api` → `http://localhost:8000`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Kill switch state, version, wallet mode |
| POST | `/revenue/manual` | Record revenue; triggers treasury split |
| GET | `/revenue` | List events + stats |
| GET | `/treasury/summary` | Totals across all revenue |
| POST | `/treasury/calculate` | One-off breakdown preview |
| PUT | `/treasury/rules` | Update split percentages (must sum to 100%) |
| GET | `/btc/allocations` | Paper BTC allocation history + wallet summary |
| POST | `/agents/website-audit` | Website audit (real HTTP scan via website_scan skill, fallback to simulated scores) |
| GET | `/agents/actions` | Agent action log |
| POST | `/agents/run` | Run the AI agent loop (goal → think/act/observe, max 10 steps) |
| POST | `/wallet/paper/simulate-allocation` | Log paper BTC allocation |
| GET | `/exports/revenue-csv` | CRA-compatible CSV download |
| POST | `/safety/kill-switch` | Toggle kill switch |
| GET | `/safety/settings` | Read safety config |
| PUT | `/safety/settings` | Update spending caps |
| POST | `/test/fake-sale` | Integration test — $100 CAD fake sale, returns PASS/FAIL |
| GET | `/skills` | List all registered skills with schemas |
| POST | `/skills/{name}/run` | Run a skill by name with input dict |
| GET | `/memory` | List agent runtime memory entries (TTL key-value) |
| DELETE | `/memory` | Clear agent memory entries |
| GET | `/memory/summary` | Full project summary — rules, stats, product config, system context |
| GET | `/memory/events` | List project memory events (filter: memory_type, source, limit) |
| POST | `/memory/events` | Add a project memory event (safety filter active) |

---

## 6. Frontend Pages

| Route | File | Status |
|-------|------|--------|
| `/` | `Dashboard.jsx` | Working |
| `/revenue` | `Revenue.jsx` | Working — uses live API rule pcts, CAD default |
| `/treasury` | `Treasury.jsx` | Working |
| `/agents` | `AgentTasks.jsx` | Working — website audit + AgentLoopPanel + SkillsListPanel |
| `/wallet` | `WalletSafety.jsx` | Working |
| `/memory` | `Memory.jsx` | Working — summary cards, rules, events table, add note form |
| `/settings` | `Settings.jsx` | Working — PUT body, not query params |

---

## 7. Agent + Skills Architecture

### Class-Based Agents (`backend/app/agents/`)

| Agent | File | Skills used |
|-------|------|------------|
| `RevenueAgent` | `revenue_agent.py` | treasury_split, summarize_revenue, check_kill_switch |
| `WebsiteAuditAgent` | `website_audit_agent.py` | website_scan, audit_report, outreach_email, check_kill_switch |
| `SalesOutreachAgent` | `sales_outreach_agent.py` | outreach_email, draft_outreach |
| `TreasuryAgent` | `treasury_agent.py` | treasury_split, check_kill_switch |
| `WalletSafetyAgent` | `wallet_safety_agent.py` | btc_allocation, safety_policy, check_kill_switch |
| `ComplianceLogAgent` | `compliance_log_agent.py` | csv_export |

Central registry: `backend/app/agents/registry.py` — `get_agent(name)`, `list_agents()`, `get_skill(name)`, `list_skills()`

### Skills (`backend/app/skills/`)

**Original 5:**
| Skill name | File | Required inputs |
|-----------|------|----------------|
| `check_kill_switch` | `check_kill_switch.py` | none |
| `fetch_btc_price` | `fetch_btc_price.py` | none |
| `summarize_revenue` | `summarize_revenue.py` | none |
| `draft_outreach` | `draft_outreach.py` | business_name, industry, city |
| `seo_audit` | `seo_audit_skill.py` | url |

**8 new skills (Task 3):**
| Skill name | File | Required inputs |
|-----------|------|----------------|
| `website_scan` | `website_scan_skill.py` | url |
| `audit_report` | `audit_report_skill.py` | business_name, url |
| `outreach_email` | `outreach_email_skill.py` | business_name, industry, city |
| `treasury_split` | `treasury_split_skill.py` | gross_amount |
| `btc_allocation` | `btc_allocation_skill.py` | revenue_event_id, gross_amount, btc_allocation_usd |
| `csv_export` | `csv_export_skill.py` | none |
| `safety_policy` | `safety_policy_skill.py` | amount_usd |
| `memory_read_write` | `memory_read_write_skill.py` | operation, key |

### Agent Runner (`backend/app/agent_runner.py`)

Think → Act → Observe loop:
- `run_agent_loop(goal, session_id, max_steps=10) -> dict`
- Kill switch checked every step
- UUID session IDs
- All steps logged to `agent_actions`
- Returns: `{status, session_id, steps, goal, result, reason}`

### AI Provider (`backend/app/ai_provider.py`)

- `PlaceholderProvider` — keyword routing, zero API keys, deterministic
- `OpenAIProvider` — httpx POST to OpenAI (gpt-4o-mini, JSON mode)
- `OllamaProvider` — httpx POST to `OLLAMA_BASE_URL/api/chat`
- `get_provider()` — picks based on `OPENAI_API_KEY` / `OLLAMA_BASE_URL` env vars

### Memory Service

Two separate systems:
1. **Agent runtime memory** (`memory_service.py` → `agent_memory` table): TTL + persistent key-value store for agent state
2. **Project memory** (`backend/app/memory/` package → `memory_events` table): Human-readable decisions, notes, audit history

Project memory package:
- `memory_store.py` — CRUD with safety filter
- `project_memory.py` — reads docs/*.md, returns live rules from DB
- `context_builder.py` — assembles safe context string for AI system prompts

---

## 8. What Is Working (Verified)

- [x] Backend starts with `uvicorn app.main:app --reload`
- [x] `GET /health` returns kill switch state + paper mode status
- [x] `POST /revenue/manual` records a sale and returns treasury split
- [x] `POST /test/fake-sale` returns `PASS` for correct 30/20/40/10 split
- [x] Revenue validation: negative amounts rejected, blank source rejected, 3-letter currency required
- [x] Treasury percentages must sum to exactly 100% (Pydantic `@model_validator`)
- [x] BTC allocation cannot exceed gross revenue (Pydantic `@model_validator`)
- [x] Kill switch blocks all write operations
- [x] `WALLET_MODE = "paper"` — real transfer stubs raise immediately
- [x] `agent_actions` table captures every revenue event, skill call, policy decision
- [x] `agent_memory` table with TTL and upsert semantics
- [x] 13 skills auto-discovered and registered
- [x] 3 AI providers implemented; `PlaceholderProvider` works with zero API keys
- [x] `agent_runner.py` think/act/observe loop with max 10 steps
- [x] Skills router (`GET /skills`, `POST /skills/{name}/run`)
- [x] Agents router (`POST /agents/run`)
- [x] Memory router (5 routes including project summary + events)
- [x] `memory_events` table with safety filter rejecting secrets/keys
- [x] Frontend 7-page dark dashboard — all pages functional including Memory
- [x] AgentLoopPanel.jsx + SkillsListPanel.jsx wired into AgentTasks
- [x] Memory.jsx with summary cards, rules panel, events table, add note form
- [x] Settings page saves treasury rules + safety limits via PUT body
- [x] Revenue page uses live API percentages (not hardcoded)
- [x] Axios interceptor converts Pydantic v2 error arrays to `err.friendlyMessage`
- [x] CRA-compatible CSV export at `GET /exports/revenue-csv`
- [x] Windows PowerShell setup instructions in README.md
- [x] SECURITY.md with code-level paper mode proof + testnet upgrade checklist
- [x] `docs/AGENTS_AND_SKILLS.md` reference document
- [x] Project memory system with `GET /memory/summary` providing system context for AI prompts

---

## 9. Known Gaps / V0.2 Candidates

| Item | Notes |
|------|-------|
| Stripe / Gumroad webhooks | Stubs exist in `services/`; raise NotImplementedError |
| python-dotenv not loaded | `DB_PATH` env var in `.env` has no effect without `load_dotenv()` call |
| `audit_agent.py` uses random scores | The new `website_scan` + `audit_report` skills are the real path; old route still uses random |
| No `MemoryViewerPanel.jsx` | Agent runtime memory (TTL key-value) has no UI; only project memory events do |
| No real pyseoanalyzer integration test | `seo_audit` skill has graceful fallback but no integration test |

---

## 10. Decisions Already Made

| Decision | Rationale |
|----------|-----------|
| SQLite not Postgres | Local-first, zero infra, single user |
| CAD as default currency | Canadian founder, CRA compliance |
| Paper mode hardcoded | Safety first; testnet/mainnet require explicit V0.2/V0.3 code changes |
| `WALLET_MODE` constant (not env var) | Prevents accidental real-money mode from a misconfigured .env |
| Pydantic v2 (not v1) | `@field_validator`/`@model_validator` syntax |
| Kill switch checked server-side | Client-side is UI only; server must enforce |
| Skills as plain Python files (not classes) | Simpler for solo dev; discovery via `pkgutil` needs no registration step |
| PlaceholderProvider as default | App works out of the box with zero API keys |
| Treasury must sum to 100% | Accounting correctness; remainder must always be zero |
| All agent actions logged to SQLite | CRA audit trail; no external logging dep |
| Two separate memory systems | Agent runtime memory (TTL KV) vs project memory events (human-readable) serve different purposes |
| Memory safety filter in Python | Regex + keyword matching in `memory_store.safety_filter()` — no DB trigger needed |
| `Path(__file__).parents[3] / "docs"` | Reliable repo-root path resolution regardless of cwd |

---

## 11. Current File Tree

```
aura-ai-studio/
├── README.md                          # Setup instructions (Mac + Windows + memory docs)
├── SECURITY.md                        # Paper mode proof + upgrade checklist
├── docs/
│   ├── PROJECT_MEMORY.md              # This file
│   └── AGENTS_AND_SKILLS.md           # Architecture reference for all agents + skills
├── backend/
│   ├── requirements.txt               # fastapi, pydantic, httpx, pyseoanalyzer, uvicorn
│   ├── .env.example                   # OPENAI_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL
│   ├── autosats.db                    # SQLite database (gitignored in production)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app, all routes, Pydantic models
│   │   ├── db.py                      # Schema (8 tables), get_db(), init_db()
│   │   ├── policy_engine.py           # Kill switch, log_agent_action, treasury validation
│   │   ├── revenue_agent.py           # record_manual_revenue, get_revenue_stats (service layer)
│   │   ├── treasury.py                # calculate_breakdown, get_active_rules
│   │   ├── wallet_service.py          # Paper allocation, real-transfer stubs
│   │   ├── audit_agent.py             # Legacy simulated website audit (random scores)
│   │   ├── tax_export.py              # CSV export with treasury breakdown
│   │   ├── memory_service.py          # Agent memory write/read/clear (TTL + persistent)
│   │   ├── skill_registry.py          # Auto-discover + run skills, log to agent_actions
│   │   ├── ai_provider.py             # Placeholder / OpenAI / Ollama providers
│   │   ├── agent_runner.py            # Think→Act→Observe loop, kill switch, max 10 steps
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── registry.py            # Agent + skill factory/listing
│   │   │   ├── revenue_agent.py       # RevenueAgent class
│   │   │   ├── website_audit_agent.py # WebsiteAuditAgent class
│   │   │   ├── sales_outreach_agent.py
│   │   │   ├── treasury_agent.py
│   │   │   ├── wallet_safety_agent.py
│   │   │   └── compliance_log_agent.py
│   │   ├── memory/
│   │   │   ├── __init__.py            # Re-exports all memory functions
│   │   │   ├── memory_store.py        # CRUD for memory_events + safety filter
│   │   │   ├── project_memory.py      # Reads docs/*.md, returns live rules
│   │   │   └── context_builder.py     # Assembles safe context for AI system prompts
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── skills_router.py       # GET /skills, POST /skills/{name}/run
│   │   │   ├── agents_router.py       # POST /agents/run
│   │   │   └── memory_router.py       # GET|DELETE /memory, /summary, /events
│   │   ├── safety/
│   │   │   ├── __init__.py
│   │   │   └── policy_engine.py       # Re-exports from policy_engine (V0.2 expansion point)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── stripe_service.py      # Stub — raises NotImplementedError
│   │   │   └── gumroad_service.py     # Stub — raises NotImplementedError
│   │   └── skills/
│   │       ├── __init__.py
│   │       ├── check_kill_switch.py
│   │       ├── fetch_btc_price.py
│   │       ├── summarize_revenue.py
│   │       ├── draft_outreach.py
│   │       ├── seo_audit_skill.py
│   │       ├── website_scan_skill.py
│   │       ├── audit_report_skill.py
│   │       ├── outreach_email_skill.py
│   │       ├── treasury_split_skill.py
│   │       ├── btc_allocation_skill.py
│   │       ├── csv_export_skill.py
│   │       ├── safety_policy_skill.py
│   │       └── memory_read_write_skill.py
│   └── tests/
│       ├── __init__.py
│       └── test_fake_sale.py          # 6 test suites; run: python -m tests.test_fake_sale
├── frontend/
│   ├── package.json
│   ├── vite.config.js                 # Proxies /api → :8000
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx                    # Router + sidebar nav (7 pages)
│       ├── App.css
│       ├── index.css
│       ├── api.js                     # Axios + interceptor + all 20 API call functions
│       ├── components/
│       │   ├── AgentLoopPanel.jsx     # Goal input → agent loop → steps trace
│       │   └── SkillsListPanel.jsx    # Skills browser + inline run
│       └── pages/
│           ├── Dashboard.jsx
│           ├── Revenue.jsx
│           ├── Treasury.jsx
│           ├── AgentTasks.jsx
│           ├── WalletSafety.jsx
│           ├── Memory.jsx             # Project memory — summary, rules, events, add note
│           └── Settings.jsx
└── aura-ai-studio/                    # Legacy static HTML (pre-React, keep as reference)
    ├── index.html
    ├── app.html
    ├── landing.html
    └── docs/GUIDE.md
```

---

## 12. V0.2 Recommended Prompt

> "Continue AutoSats Engine to V0.2. Goals:
> 1. Replace `audit_agent.py` random scores with the `website_scan` + `audit_report` skill chain in the `/agents/website-audit` route
> 2. Add `load_dotenv()` to `backend/app/main.py` startup so `DB_PATH` env var works
> 3. Add `MemoryViewerPanel.jsx` — shows agent runtime memory (TTL key-value) from `GET /memory`; wire into Settings or AgentTasks
> 4. Add `POST /revenue/webhook/gumroad` and `POST /revenue/webhook/stripe` stubs that parse the real payload format and log to `revenue_events` (still paper mode, no real payouts)
> 5. Add 3-5 integration tests to `backend/tests/` covering: POST /memory/events (happy path + safety filter rejection), GET /memory/summary, POST /agents/run with PlaceholderProvider
> Do not add real wallet operations. Do not add real payment processing. Paper mode only."
