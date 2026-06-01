# AutoSats Engine V0.1

Local-first web app for solo digital business owners to automate revenue tracking,
treasury allocation, AI-generated audit tasks, tax reserve calculation, and Bitcoin
allocation recommendations.

> **PAPER MODE ONLY in V0.1** — no real money moves, no private keys, no real BTC.
> Default currency: **CAD**

---

## File Tree

```
autosats-engine/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── db.py             # SQLite setup, schema, init
│   │   ├── main.py           # FastAPI app + all routes
│   │   ├── treasury.py       # Allocation calculations
│   │   ├── policy_engine.py  # Rules, kill-switch, audit log
│   │   ├── revenue_agent.py  # Revenue recording & stats
│   │   ├── audit_agent.py    # Website audit AI agent
│   │   ├── wallet_service.py # Paper BTC simulator (real transfers blocked)
│   │   └── tax_export.py     # CSV export for tax prep
│   ├── tests/
│   │   └── test_fake_sale.py # Standalone test script
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Revenue.jsx
│   │   │   ├── Treasury.jsx
│   │   │   ├── AgentTasks.jsx
│   │   │   ├── WalletSafety.jsx
│   │   │   └── Settings.jsx
│   │   ├── api.js
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .gitignore
├── README.md
└── SECURITY.md
```

---

## Setup — macOS / Linux

### 1. Backend

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env file (all values are optional in paper mode)
cp .env.example .env

# Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API available at `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at `http://localhost:5173`

---

## Setup — Windows (PowerShell)

### 1. Backend

```powershell
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# If execution policy blocks the activate script, run once:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt

# Copy env file
Copy-Item .env.example .env

# Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend (PowerShell)

```powershell
cd frontend
npm install
npm run dev
```

Dashboard available at `http://localhost:5173`

---

## Test the Fake $100 Sale

### Option A — Run the test script directly (backend/)

```bash
# macOS / Linux
cd backend
source .venv/bin/activate
python -m tests.test_fake_sale
```

```powershell
# Windows PowerShell
cd backend
.venv\Scripts\Activate.ps1
python -m tests.test_fake_sale
```

Expected output:
```
=== Test: Treasury split on $100 CAD sale ===
  [PASS] tax_reserve:    expected=30.0, got=30.0
  [PASS] btc_allocation: expected=20.0, got=20.0
  [PASS] operating_cash: expected=40.0, got=40.0
  [PASS] tool_budget:    expected=10.0, got=10.0
  [PASS] remainder:      expected=0.0,  got=0.0
...
Overall: ALL TESTS PASSED
```

### Option B — Use the API endpoint (server must be running)

```bash
curl -X POST http://localhost:8000/test/fake-sale
```

```powershell
Invoke-RestMethod -Method POST -Uri http://localhost:8000/test/fake-sale
```

### Option C — Use the Treasury page UI

Navigate to **Treasury** → click **Run Test Sale** → see PASS/FAIL with per-check results.

---

## Export Revenue CSV

### Browser
Navigate to **Treasury** → **Download Revenue CSV**

### curl (macOS / Linux)
```bash
curl -o revenue_export.csv http://localhost:8000/exports/revenue-csv
```

### PowerShell
```powershell
Invoke-WebRequest -Uri http://localhost:8000/exports/revenue-csv -OutFile revenue_export.csv
```

---

## Default Treasury Rules

| Bucket | Default | Notes |
|---|---|---|
| Tax Reserve | 30% | Set aside for CRA / tax prep |
| BTC Allocation | 20% | Simulated in paper mode |
| Operating Cash | 40% | Business operations |
| Tool / API Budget | 10% | Software & subscriptions |

Rules are stored in the database and editable from the **Settings** or **Treasury** page.
All four percentages must always sum to exactly 100%.

---

## Validation Rules

- `source` is required and cannot be blank
- `gross_amount` must be greater than 0 — negative amounts are rejected with a clear error
- `currency` defaults to **CAD** — must be a 3-letter code
- Treasury rule percentages must sum to exactly 100%
- BTC allocation cannot exceed the gross revenue amount
- `require_confirmation_above_usd` must be less than `max_single_allocation_usd`

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | System health + kill switch status |
| POST | `/revenue/manual` | Record a manual revenue event |
| GET | `/revenue` | List all revenue events |
| GET | `/treasury/summary` | Get full treasury breakdown |
| POST | `/treasury/calculate` | One-off allocation calculation |
| PUT | `/treasury/rules` | Update allocation percentages (body, must sum to 100) |
| GET | `/btc/allocations` | List paper BTC allocations |
| POST | `/agents/website-audit` | Run website audit agent |
| GET | `/agents/actions` | List all agent action logs |
| POST | `/wallet/paper/simulate-allocation` | Create paper BTC allocation |
| GET | `/exports/revenue-csv` | Download revenue CSV |
| POST | `/safety/kill-switch` | Toggle kill switch |
| GET | `/safety/settings` | Get safety settings |
| PUT | `/safety/settings` | Update safety limits (body) |
| POST | `/test/fake-sale` | Run $100 CAD test and verify splits |

---

## Security

See [SECURITY.md](./SECURITY.md) for the full paper-mode security policy.

---

## Environment Variables

See `backend/.env.example` — all optional in paper mode V0.1.
