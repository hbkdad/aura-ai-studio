# AutoSats Engine — Project Memory

**Last updated:** 2026-06-01  
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
| HTTP client | httpx | Used inside OpenAI/Ollama providers |
| SEO crawling | pyseoanalyzer | **NOT yet in requirements.txt** |
| Tests | stdlib unittest | `backend/tests/test_fake_sale.py` |

### Frontend
| Component | Choice | Notes |
|-----------|--------|-------|
| Framework | React 18 + Vite | Dark dashboard theme |
| HTTP | Axios | Interceptor converts Pydantic errors to `err.friendlyMessage` |
| Routing | React Router v6 | 6 pages |
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
| `revenue_events` | Every logged sale — source, gross amount, currency (default CAD), metadata |
| `treasury_rules` | Active split percentages — default 30/20/40/10 |
| `btc_allocations` | Paper-mode BTC simulation records linked to revenue events |
| `agent_actions` | Audit log for every agent call, skill execution, and policy engine decision |
| `wallet_events` | Low-level wallet event stream (allocation, type, paper amounts) |
| `safety_settings` | Kill switch state, wallet mode, spending caps |
| `agent_memory` | Short-term (TTL) and long-term (persistent) key-value store for agent state |

`agent_memory` has a `UNIQUE(agent_name, memory_type, key)` constraint and uses `ON CONFLICT DO UPDATE SET` upsert semantics.

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
| POST | `/agents/website-audit` | Simulated audit (random scores + outreach email) |
| GET | `/agents/actions` | Agent action log |
| POST | `/wallet/paper/simulate-allocation` | Log paper BTC allocation |
| GET | `/exports/revenue-csv` | CRA-compatible CSV download |
| POST | `/safety/kill-switch` | Toggle kill switch |
| GET | `/safety/settings` | Read safety config |
| PUT | `/safety/settings` | Update spending caps |
| POST | `/test/fake-sale` | Integration test — $100 CAD fake sale, returns PASS/FAIL |

**Not yet wired to routes (built but no endpoints):**
- Skills: `GET /skills`, `POST /skills/{name}/run`
- Agent loop: `POST /agents/run`
- Memory: `GET /memory`, `DELETE /memory`

---

## 6. Frontend Pages

| Route | File | Status |
|-------|------|--------|
| `/` | `Dashboard.jsx` | Working |
| `/revenue` | `Revenue.jsx` | Working — uses live API rule pcts, CAD default |
| `/treasury` | `Treasury.jsx` | Working |
| `/agents` | `AgentTasks.jsx` | Working — website audit + action log |
| `/wallet` | `WalletSafety.jsx` | Working |
| `/settings` | `Settings.jsx` | Working — PUT body, not query params |

Frontend component folder (`frontend/src/components/`) exists but is **empty** — no shared components extracted yet.

---

## 7. Agent + Skills System (Built, Not Yet Routed)

### Skills (5 registered, auto-discovered from `backend/app/skills/`)

| Skill name | File | Required inputs | Notes |
|-----------|------|----------------|-------|
| `check_kill_switch` | `check_kill_switch.py` | none | Reads policy_engine |
| `fetch_btc_price` | `fetch_btc_price.py` | none | Returns simulated $65k |
| `summarize_revenue` | `summarize_revenue.py` | none | Calls revenue_agent stats |
| `draft_outreach` | `draft_outreach.py` | business_name, industry, city | Pure string template |
| `seo_audit` | `seo_audit_skill.py` | url | Wraps pyseoanalyzer; graceful ImportError fallback |

Skill contract: every file must expose `NAME`, `DESCRIPTION`, `REQUIRED_INPUTS`, `INPUT_SCHEMA`, `OUTPUT_SCHEMA`, `run(input: dict) -> dict`. Bad files are skipped with a warning on import — server never crashes on bad skill.

### Skill Registry (`backend/app/skill_registry.py`)
- Auto-discovers at import time via `pkgutil.iter_modules`
- `list_skills()` — returns schema for all registered skills
- `run_skill(name, input_data)` — validates required inputs, calls `run()`, logs to `agent_actions`

### AI Provider (`backend/app/ai_provider.py`)
- `PlaceholderProvider` — keyword routing, zero API keys, deterministic
- `OpenAIProvider` — httpx POST to OpenAI (gpt-4o-mini, JSON mode)
- `OllamaProvider` — httpx POST to `OLLAMA_BASE_URL/api/chat`
- `get_provider()` — picks based on `OPENAI_API_KEY` / `OLLAMA_BASE_URL` env vars

### Memory Service (`backend/app/memory_service.py`)
- `write_memory(agent_name, type, key, value, ttl_hours)` — UPSERT
- `read_memory(agent_name, type, key)` — returns None if expired
- `read_all_memory(agent_name?, type?)` — list all non-expired
- `clear_memory(agent_name?, type?, key?)` — delete with optional filters
- `_purge_expired()` — called lazily before every read

### Agent Runner — NOT YET WRITTEN
`backend/app/agent_runner.py` is the **next file to build**. It needs:
- `run_agent_loop(goal: str, session_id: str, max_steps: int = 10) -> dict`
- Think → Act → Observe loop using `get_provider().think()` + `run_skill()`
- Kill switch check at every step
- UUID session IDs
- All steps logged to `agent_actions`

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
- [x] 5 skills auto-discovered and registered
- [x] 3 AI providers implemented (no routes yet)
- [x] Frontend 6-page dark dashboard — all pages functional
- [x] Settings page saves treasury rules + safety limits via PUT body
- [x] Revenue page uses live API percentages (not hardcoded)
- [x] Axios interceptor converts Pydantic v2 error arrays to `err.friendlyMessage`
- [x] CRA-compatible CSV export at `GET /exports/revenue-csv`
- [x] Windows PowerShell setup instructions in README.md
- [x] SECURITY.md with code-level paper mode proof + testnet upgrade checklist

---

## 9. What Is Missing (Pending)

### Must-Have Before V0.1 Is Complete

| Item | Priority | File to write |
|------|----------|--------------|
| `agent_runner.py` — think/act/observe loop | HIGH | `backend/app/agent_runner.py` |
| API routers for skills, agents, memory | HIGH | `backend/app/routers/skills_router.py`, `agents_router.py`, `memory_router.py` |
| Wire routers into `main.py` | HIGH | `backend/app/main.py` (add 3 `include_router` calls + startup `_purge_expired`) |
| Add `pyseoanalyzer>=2025.4.3` + `httpx>=0.28.0` to requirements.txt | HIGH | `backend/requirements.txt` |
| `.env.example` with OPENAI_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL | MEDIUM | `backend/.env.example` |

### Nice-to-Have (Frontend Panels)

| Item | File to write |
|------|--------------|
| `AgentLoopPanel.jsx` — run a goal, see steps | `frontend/src/components/AgentLoopPanel.jsx` |
| `SkillsListPanel.jsx` — browse + run skills | `frontend/src/components/SkillsListPanel.jsx` |
| `MemoryViewerPanel.jsx` — inspect + clear memory | `frontend/src/components/MemoryViewerPanel.jsx` |
| Wire panels into AgentTasks + Settings pages | `AgentTasks.jsx`, `Settings.jsx` |
| Add `getSkills`, `runSkill`, `runAgentLoop`, `getMemory`, `clearMemory` to api.js | `frontend/src/api.js` |

### Known Issues / Gaps

| Issue | Impact |
|-------|--------|
| `requirements.txt` missing `pyseoanalyzer` + `httpx` | `seo_audit` skill and OpenAI/Ollama providers will fail on fresh install |
| `revenue_events.currency` column defaults to `'USD'` in schema but API defaults to `'CAD'` | Schema inconsistency — data written as CAD but column default says USD |
| `audit_agent.py` uses randomised scores (not real pyseoanalyzer) | `POST /agents/website-audit` scores are fake; `seo_audit` skill is the real path |
| No `.env.example` file | First-time setup unclear for OpenAI/Ollama config |
| No `backend/.env` file | `python-dotenv` is installed but never loaded; DB_PATH env var ignored without dotenv load |

---

## 10. Decisions Already Made

| Decision | Rationale |
|----------|-----------|
| SQLite not Postgres | Local-first, zero infra, single user |
| CAD as default currency | Canadian founder, CRA compliance |
| Paper mode hardcoded | Safety first; testnet/mainnet require explicit V0.2/V0.3 code changes |
| `WALLET_MODE` constant (not env var) | Prevents accidental real-money mode from a misconfigured .env |
| Pydantic v2 (not v1) | Chosen for `@field_validator`/`@model_validator` syntax; breaking change from v1 |
| Kill switch checked server-side, not client-side | Client-side is UI only; server must enforce |
| Skills as plain Python files (not classes) | Simpler for solo dev; discovery via `pkgutil` needs no registration step |
| PlaceholderProvider as default | App works out of the box with zero API keys; no friction for new users |
| Treasury must sum to 100% | Accounting correctness; remainder must always be zero |
| All agent actions logged to SQLite | CRA audit trail; no external logging dep |
| pyseoanalyzer over random scores for SEO skill | Real data > simulation; confirmed after deep research |

---

## 11. Current File Tree

```
aura-ai-studio/
├── README.md                          # Setup instructions (Mac + Windows PowerShell)
├── SECURITY.md                        # Paper mode proof + upgrade checklist
├── docs/
│   └── PROJECT_MEMORY.md              # This file
├── backend/
│   ├── requirements.txt               # ⚠ Missing pyseoanalyzer + httpx
│   ├── autosats.db                    # SQLite database (gitignored in production)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app, routes, Pydantic models
│   │   ├── db.py                      # Schema, get_db(), init_db()
│   │   ├── policy_engine.py           # Kill switch, log_agent_action, treasury validation
│   │   ├── revenue_agent.py           # record_manual_revenue, get_revenue_stats
│   │   ├── treasury.py                # calculate_breakdown, get_active_rules
│   │   ├── wallet_service.py          # Paper allocation, real-transfer stubs
│   │   ├── audit_agent.py             # Simulated website audit (random scores)
│   │   ├── tax_export.py              # CSV export with treasury breakdown
│   │   ├── memory_service.py          # write/read/clear agent memory (TTL + persistent)
│   │   ├── skill_registry.py          # Auto-discover + run skills, log to agent_actions
│   │   ├── ai_provider.py             # Placeholder / OpenAI / Ollama providers
│   │   └── skills/
│   │       ├── __init__.py
│   │       ├── check_kill_switch.py
│   │       ├── fetch_btc_price.py
│   │       ├── summarize_revenue.py
│   │       ├── draft_outreach.py
│   │       └── seo_audit_skill.py
│   └── tests/
│       ├── __init__.py
│       └── test_fake_sale.py          # 6 test suites; run: python -m tests.test_fake_sale
├── frontend/
│   ├── package.json
│   ├── vite.config.js                 # Proxies /api → :8000
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx                    # Router + sidebar nav
│       ├── App.css
│       ├── index.css
│       ├── api.js                     # Axios + interceptor + all API calls
│       ├── components/                # Empty — no shared components yet
│       └── pages/
│           ├── Dashboard.jsx
│           ├── Revenue.jsx
│           ├── Treasury.jsx
│           ├── AgentTasks.jsx
│           ├── WalletSafety.jsx
│           └── Settings.jsx
└── aura-ai-studio/                    # Legacy static HTML (pre-React)
    ├── index.html
    ├── app.html
    ├── landing.html
    └── docs/GUIDE.md
```

---

## 12. Next Recommended Prompt

> "Continue the V0.1 implementation. Complete the following in order:
> 1. Fix `backend/requirements.txt` — add `pyseoanalyzer>=2025.4.3` and `httpx>=0.28.0`
> 2. Fix the `revenue_events` schema — change the `currency` column default from `'USD'` to `'CAD'`
> 3. Write `backend/app/agent_runner.py` — think/act/observe loop, kill switch on every step, UUID session IDs, max 10 steps, all steps logged to agent_actions
> 4. Write `backend/app/routers/skills_router.py`, `agents_router.py`, `memory_router.py`
> 5. Wire the 3 routers into `main.py` and add `_purge_expired()` to startup
> 6. Create `backend/.env.example` with OPENAI_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL
> 7. Add `getSkills`, `runSkill`, `runAgentLoop`, `getMemory`, `clearMemory` to `frontend/src/api.js`
> 8. Write `AgentLoopPanel.jsx` and `SkillsListPanel.jsx` and wire into `AgentTasks.jsx`
> Commit and push all changes when done."
