import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "autosats.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS revenue_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                source TEXT NOT NULL,
                description TEXT,
                gross_amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                payment_method TEXT DEFAULT 'manual',
                reference_id TEXT,
                metadata TEXT
            );

            CREATE TABLE IF NOT EXISTS treasury_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                name TEXT NOT NULL,
                tax_reserve_pct REAL NOT NULL DEFAULT 30.0,
                btc_allocation_pct REAL NOT NULL DEFAULT 20.0,
                operating_cash_pct REAL NOT NULL DEFAULT 40.0,
                tool_budget_pct REAL NOT NULL DEFAULT 10.0,
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS btc_allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                revenue_event_id INTEGER REFERENCES revenue_events(id),
                gross_amount REAL NOT NULL,
                allocated_usd REAL NOT NULL,
                btc_price_usd REAL,
                simulated_btc REAL,
                wallet_mode TEXT NOT NULL DEFAULT 'paper',
                status TEXT NOT NULL DEFAULT 'simulated',
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS agent_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                agent_name TEXT NOT NULL,
                action_type TEXT NOT NULL,
                input_data TEXT,
                output_data TEXT,
                status TEXT NOT NULL DEFAULT 'completed',
                duration_ms INTEGER,
                error_message TEXT
            );

            CREATE TABLE IF NOT EXISTS wallet_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                event_type TEXT NOT NULL,
                wallet_mode TEXT NOT NULL DEFAULT 'paper',
                amount_usd REAL,
                simulated_btc REAL,
                btc_price_usd REAL,
                from_address TEXT DEFAULT 'PAPER_MODE',
                to_address TEXT DEFAULT 'PAPER_MODE',
                tx_hash TEXT DEFAULT 'SIMULATED',
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS safety_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                kill_switch_active INTEGER NOT NULL DEFAULT 0,
                wallet_mode TEXT NOT NULL DEFAULT 'paper',
                max_single_allocation_usd REAL DEFAULT 1000.0,
                require_confirmation_above_usd REAL DEFAULT 500.0,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                memory_type TEXT NOT NULL CHECK(memory_type IN ('short_term','long_term')),
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                expires_at TEXT,
                UNIQUE(agent_name, memory_type, key)
            );

            CREATE INDEX IF NOT EXISTS idx_agent_memory_agent_type
                ON agent_memory (agent_name, memory_type);

            CREATE INDEX IF NOT EXISTS idx_agent_memory_expires
                ON agent_memory (expires_at)
                WHERE expires_at IS NOT NULL;
        """)

        row = conn.execute("SELECT COUNT(*) as cnt FROM treasury_rules").fetchone()
        if row["cnt"] == 0:
            conn.execute("""
                INSERT INTO treasury_rules (name, tax_reserve_pct, btc_allocation_pct, operating_cash_pct, tool_budget_pct)
                VALUES ('Default Policy', 30.0, 20.0, 40.0, 10.0)
            """)

        row = conn.execute("SELECT COUNT(*) as cnt FROM safety_settings").fetchone()
        if row["cnt"] == 0:
            conn.execute("""
                INSERT INTO safety_settings (kill_switch_active, wallet_mode)
                VALUES (0, 'paper')
            """)
