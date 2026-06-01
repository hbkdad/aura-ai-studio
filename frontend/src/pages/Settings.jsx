import { useEffect, useState } from 'react'
import { getSafetySettings, putSafetySettings, putTreasuryRules, getTreasurySummary } from '../api'

export default function Settings() {
  const [safety, setSafety] = useState(null)
  const [rules, setRules] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [saveError, setSaveError] = useState('')

  const load = () => {
    Promise.all([getSafetySettings(), getTreasurySummary()])
      .then(([s, t]) => {
        setSafety(s.data)
        setRules(t.data.rules)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const totalPct = rules
    ? (rules.tax_reserve_pct || 0) + (rules.btc_allocation_pct || 0) +
      (rules.operating_cash_pct || 0) + (rules.tool_budget_pct || 0)
    : 0

  const saveAll = async () => {
    setSaveError('')
    setSaving(true)
    try {
      // Send request bodies — not query params
      await Promise.all([
        putSafetySettings({
          max_single_allocation_usd: safety.max_single_allocation_usd,
          require_confirmation_above_usd: safety.require_confirmation_above_usd,
        }),
        putTreasuryRules({
          tax_reserve_pct: rules.tax_reserve_pct,
          btc_allocation_pct: rules.btc_allocation_pct,
          operating_cash_pct: rules.operating_cash_pct,
          tool_budget_pct: rules.tool_budget_pct,
        }),
      ])
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
      load()
    } catch (err) {
      setSaveError(err.friendlyMessage || 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="loading">Loading settings...</div>

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Settings</div>
        <div className="page-subtitle">Configure treasury rules and safety limits</div>
      </div>

      {saveError && <div className="alert alert-danger">{saveError}</div>}

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <div className="section">
          <div className="section-header">
            <div className="section-title">Treasury Allocation Rules</div>
          </div>
          <div className="card">
            {Math.abs(totalPct - 100) > 0.01 && (
              <div className="alert alert-warning">
                ⚠ Percentages total {totalPct.toFixed(1)}% (must equal exactly 100%)
              </div>
            )}
            {rules && [
              { key: 'tax_reserve_pct',    label: 'Tax Reserve %',        color: 'var(--yellow)' },
              { key: 'btc_allocation_pct', label: 'BTC Allocation %',     color: 'var(--accent)' },
              { key: 'operating_cash_pct', label: 'Operating Cash %',     color: 'var(--green)' },
              { key: 'tool_budget_pct',    label: 'Tool / API Budget %',  color: 'var(--accent2)' },
            ].map(({ key, label, color }) => (
              <div className="form-group" key={key}>
                <label className="form-label" style={{ color }}>{label}</label>
                <input
                  type="number" min="0" max="100" step="0.5"
                  value={rules[key]}
                  onChange={e => setRules(r => ({ ...r, [key]: parseFloat(e.target.value) || 0 }))}
                />
              </div>
            ))}
            <div style={{ fontSize: 12, color: Math.abs(totalPct - 100) < 0.01 ? 'var(--green)' : 'var(--red)', marginBottom: 8 }}>
              Total: {totalPct.toFixed(1)}%
            </div>
          </div>
        </div>

        <div className="section">
          <div className="section-header">
            <div className="section-title">Safety Limits</div>
          </div>
          <div className="card">
            {safety && (
              <>
                <div className="form-group">
                  <label className="form-label">Max Single Allocation (USD)</label>
                  <input
                    type="number" min="1" step="50"
                    value={safety.max_single_allocation_usd}
                    onChange={e => setSafety(s => ({ ...s, max_single_allocation_usd: parseFloat(e.target.value) || 0 }))}
                  />
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>
                    Allocations above this amount will be rejected automatically
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Require Confirmation Above (USD)</label>
                  <input
                    type="number" min="1" step="50"
                    value={safety.require_confirmation_above_usd}
                    onChange={e => setSafety(s => ({ ...s, require_confirmation_above_usd: parseFloat(e.target.value) || 0 }))}
                  />
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>
                    Must be less than max single allocation
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 32 }}>
        <button
          className="btn btn-primary"
          onClick={saveAll}
          disabled={saving || Math.abs(totalPct - 100) > 0.01}
        >
          {saving ? 'Saving...' : 'Save All Settings'}
        </button>
        {saved && <span className="badge badge-green">Saved ✓</span>}
      </div>

      <div className="section">
        <div className="section-header">
          <div className="section-title">System Information</div>
        </div>
        <div className="card">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {[
              { label: 'Version', value: 'V0.1.0' },
              { label: 'Mode', value: 'PAPER MODE — No Real Money' },
              { label: 'Database', value: 'SQLite (local file)' },
              { label: 'Default Currency', value: 'CAD' },
              { label: 'Wallet', value: 'Paper Simulator — Real Transfers Blocked' },
              { label: 'AI Provider', value: 'Placeholder (OpenAI / Ollama ready)' },
              { label: 'Payments', value: 'Manual Entry (Stripe / Gumroad placeholders)' },
              { label: 'Treasury Split', value: '30% tax / 20% BTC / 40% ops / 10% tools' },
            ].map(r => (
              <div key={r.label} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{r.label}</div>
                <div style={{ fontSize: 13, color: 'var(--text)', marginTop: 2 }}>{r.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-header">
          <div className="section-title">Kill Switch Status</div>
        </div>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 12, height: 12, borderRadius: '50%',
              background: safety?.kill_switch_active ? 'var(--red)' : 'var(--green)',
              boxShadow: safety?.kill_switch_active ? '0 0 8px var(--red)' : '0 0 8px var(--green)',
            }} />
            <span style={{ fontWeight: 600, color: safety?.kill_switch_active ? 'var(--red)' : 'var(--green)' }}>
              {safety?.kill_switch_active
                ? 'KILL SWITCH ACTIVE — Go to Wallet Safety to manage'
                : 'Kill Switch Inactive — All systems normal'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
