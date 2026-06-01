import { useEffect, useState } from 'react'
import { getSafetySettings, putSafetySettings, putTreasuryRules, getTreasurySummary } from '../api'

export default function Settings() {
  const [safety, setSafety] = useState(null)
  const [rules, setRules] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

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

  const saveAll = async () => {
    setSaving(true)
    try {
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
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="loading">Loading settings...</div>

  const totalPct = rules
    ? parseFloat(rules.tax_reserve_pct || 0) + parseFloat(rules.btc_allocation_pct || 0) +
      parseFloat(rules.operating_cash_pct || 0) + parseFloat(rules.tool_budget_pct || 0)
    : 0

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Settings</div>
        <div className="page-subtitle">Configure treasury rules and safety limits</div>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <div className="section">
          <div className="section-header">
            <div className="section-title">Treasury Allocation Rules</div>
          </div>
          <div className="card">
            {totalPct !== 100 && (
              <div className="alert alert-warning">
                ⚠ Percentages total {totalPct.toFixed(1)}% (must equal 100%)
              </div>
            )}
            {rules && ['tax_reserve_pct', 'btc_allocation_pct', 'operating_cash_pct', 'tool_budget_pct'].map(key => (
              <div className="form-group" key={key}>
                <label className="form-label">
                  {key === 'tax_reserve_pct' && 'Tax Reserve %'}
                  {key === 'btc_allocation_pct' && 'BTC Allocation %'}
                  {key === 'operating_cash_pct' && 'Operating Cash %'}
                  {key === 'tool_budget_pct' && 'Tool / API Budget %'}
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.5"
                  value={rules[key]}
                  onChange={e => setRules(r => ({ ...r, [key]: parseFloat(e.target.value) }))}
                />
              </div>
            ))}
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
                    type="number"
                    min="1"
                    step="50"
                    value={safety.max_single_allocation_usd}
                    onChange={e => setSafety(s => ({ ...s, max_single_allocation_usd: parseFloat(e.target.value) }))}
                  />
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>
                    Allocations above this amount will be rejected
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Require Confirmation Above (USD)</label>
                  <input
                    type="number"
                    min="1"
                    step="50"
                    value={safety.require_confirmation_above_usd}
                    onChange={e => setSafety(s => ({ ...s, require_confirmation_above_usd: parseFloat(e.target.value) }))}
                  />
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>
                    Flag allocations above this amount for review
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <button className="btn btn-primary" onClick={saveAll} disabled={saving || totalPct !== 100}>
          {saving ? 'Saving...' : 'Save All Settings'}
        </button>
        {saved && <span className="badge badge-green">Saved ✓</span>}
      </div>

      <div className="section" style={{ marginTop: 32 }}>
        <div className="section-header">
          <div className="section-title">System Information</div>
        </div>
        <div className="card">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {[
              { label: 'Version', value: 'V0.1.0' },
              { label: 'Mode', value: 'PAPER MODE' },
              { label: 'Database', value: 'SQLite (local)' },
              { label: 'Wallet', value: 'Paper Simulator — No Real Keys' },
              { label: 'AI Provider', value: 'Placeholder (OpenAI/Ollama ready)' },
              { label: 'Payments', value: 'Manual Entry (Stripe/Gumroad placeholders)' },
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
              {safety?.kill_switch_active ? 'KILL SWITCH ACTIVE — Go to Wallet Safety to manage' : 'Kill Switch Inactive — All systems normal'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
