# AutoSats Engine V0.1

Local-first web app for solo digital business owners to automate revenue tracking,
treasury allocation, AI-generated audit tasks, tax reserve calculation, and Bitcoin
allocation recommendations.

> **PAPER MODE ONLY in V0.1** — no real money moves, no private keys, no real BTC.

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
│   │   ├── wallet_service.py # Paper BTC simulator
│   │   └── tax_export.py     # CSV export for tax prep
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

## Setup

### 1. Backend

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file (edit as needed — all optional in paper mode)
cp .env.example .env

# Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server (proxies /api → localhost:8000)
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

---

## Default Treasury Rules

| Bucket | Default |
|---|---|
| Tax Reserve | 30% |
| BTC Allocation | 20% |
| Operating Cash | 40% |
| Tool / API Budget | 10% |

All rules are stored in the database and editable from the Settings page.

---

## Test Flow — Fake $100 Sale

1. Open the dashboard at `http://localhost:5173`
2. Navigate to **Revenue** → fill in the form:
   - Source: `gumroad`
   - Gross Amount: `100.00`
   - Description: `Digital product sale — test`
   - Payment Method: `gumroad`
3. Click **Record Revenue** → see the breakdown preview:
   - Tax Reserve: $30.00
   - BTC Allocation: $20.00
   - Operating Cash: $40.00
   - Tool Budget: $10.00
4. Navigate to **Wallet Safety** → select the revenue event → click **Simulate Paper Allocation**
   - Result: ₿ 0.00030769 simulated @ $65,000/BTC (paper only)
5. Navigate to **Agent Tasks** → run a website audit for any business
6. Navigate to **Treasury** → click **Download Revenue CSV** for tax export
7. Dashboard should now show all totals populated

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | System health + kill switch status |
| POST | `/revenue/manual` | Record a manual revenue event |
| GET | `/revenue` | List all revenue events |
| GET | `/treasury/summary` | Get full treasury breakdown |
| POST | `/treasury/calculate` | One-off allocation calculation |
| PUT | `/treasury/rules` | Update allocation percentages |
| GET | `/btc/allocations` | List paper BTC allocations |
| POST | `/agents/website-audit` | Run website audit agent |
| GET | `/agents/actions` | List all agent action logs |
| POST | `/wallet/paper/simulate-allocation` | Create paper BTC allocation |
| GET | `/exports/revenue-csv` | Download revenue CSV |
| POST | `/safety/kill-switch` | Toggle kill switch |
| GET | `/safety/settings` | Get safety settings |
| PUT | `/safety/settings` | Update safety limits |

---

## Environment Variables

See `backend/.env.example` — all optional in paper mode V0.1.

---

## Security

See [SECURITY.md](./SECURITY.md) for why V0.1 is paper mode only and the checklist
for enabling real money in future versions.
