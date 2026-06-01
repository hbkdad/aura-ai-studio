import { useEffect, useState } from 'react'
import { getTreasurySummary, postTreasuryCalculate, putTreasuryRules, getRevenueCSV } from '../api'

function fmt(n) { return `$${Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}` }

export default function Treasury() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [calcAmount, setCalcAmount] = useState('')
  const [calcResult, setCalcResult] = useState(null)
  const [rules, setRules] = useState({ tax_reserve_pct: 30, btc_allocation_pct: 20, operating_cash_pct: 40, tool_budget_pct: 10 })
  const [rulesSaved, setRulesSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  const load = () => {
    getTreasurySummary()
      .then(r => {
        setSummary(r.data)
        if (r.data.rules) {
          setRules({
            tax_reserve_pct: r.data.rules.tax_reserve_pct,
            btc_allocation_pct: r.data.rules.btc_allocation_pct,
            operating_cash_pct: r.data.rules.operating_cash_pct,
            tool_budget_pct: r.data.rules.tool_budget_pct,
          })
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleCalculate = async () => {
    const amount = parseFloat(calcAmount)
    if (!amount || amount <= 0) return
    try {
      const res = await postTreasuryCalculate({ gross_amount: amount })
      setCalcResult(res.data)
    } catch (err) {
      console.error(err)
    }
  }

  const handleSaveRules = async () => {
    setSaving(true)
    try {
      await putTreasuryRules(rules)
      setRulesSaved(true)
      setTimeout(() => setRulesSaved(false), 3000)
      load()
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  const totalPct = Object.values(rules).reduce((a, v) => a + parseFloat(v || 0), 0)

  const handleExport = async () => {
    try {
      const res = await getRevenueCSV()
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = 'autosats_revenue_export.csv'
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Treasury</div>
        <div className="page-subtitle">Allocation rules, calculations, and tax export</div>
      </div>

      {loading ? <div className="loading">Loading...</div> : (
        <>
          <div className="grid-4" style={{ marginBottom: 24 }}>
            <div className="card stat-accent-orange">
              <div className="card-title">Total Gross</div>
              <div className="card-value">{fmt(summary?.total_gross)}</div>
            </div>
            <div className="card stat-accent-yellow">
              <div className="card-title">Tax Reserve</div>
              <div className="card-value">{fmt(summary?.tax_reserve)}</div>
            </div>
            <div className="card stat-accent-orange">
              <div className="card-title">BTC Allocation</div>
              <div className="card-value">{fmt(summary?.btc_allocation)}</div>
            </div>
            <div className="card stat-accent-green">
              <div className="card-title">Operating Cash</div>
              <div className="card-value">{fmt(summary?.operating_cash)}</div>
            </div>
          </div>

          <div className="grid-2">
            <div className="section">
              <div className="section-header">
                <div className="section-title">Allocation Policy Rules</div>
              </div>
              <div className="card">
                {totalPct !== 100 && (
                  <div className="alert alert-warning" style={{ marginBottom: 16 }}>
                    ⚠ Percentages total {totalPct.toFixed(1)}% — should equal 100%
                  </div>
                )}
                {['tax_reserve_pct', 'btc_allocation_pct', 'operating_cash_pct', 'tool_budget_pct'].map(key => (
                  <div className="form-group" key={key}>
                    <label className="form-label">
                      {key.replace(/_pct$/, '').replace(/_/g, ' ')} (%)
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
                <div style={{ display: 'flex', gap: 10, marginTop: 8, alignItems: 'center' }}>
                  <button className="btn btn-primary" onClick={handleSaveRules} disabled={saving || totalPct !== 100}>
                    {saving ? 'Saving...' : 'Save Rules'}
                  </button>
                  {rulesSaved && <span className="badge badge-green">Saved ✓</span>}
                </div>
              </div>
            </div>

            <div className="section">
              <div className="section-header">
                <div className="section-title">Calculate Breakdown</div>
              </div>
              <div className="card">
                <div className="form-group">
                  <label className="form-label">Gross Amount (USD)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder="e.g. 100.00"
                    value={calcAmount}
                    onChange={e => setCalcAmount(e.target.value)}
                  />
                </div>
                <button className="btn btn-secondary" onClick={handleCalculate}>Calculate</button>
                {calcResult && (
                  <div style={{ marginTop: 16 }}>
                    {[
                      { label: 'Gross', value: fmt(calcResult.gross), color: 'var(--text)' },
                      { label: `Tax Reserve (${calcResult.percentages?.tax}%)`, value: fmt(calcResult.tax_reserve), color: 'var(--yellow)' },
                      { label: `BTC Allocation (${calcResult.percentages?.btc}%)`, value: fmt(calcResult.btc_allocation), color: 'var(--accent)' },
                      { label: `Operating Cash (${calcResult.percentages?.operating}%)`, value: fmt(calcResult.operating_cash), color: 'var(--green)' },
                      { label: `Tool Budget (${calcResult.percentages?.tools}%)`, value: fmt(calcResult.tool_budget), color: 'var(--accent2)' },
                      { label: 'Remainder', value: fmt(calcResult.remainder), color: 'var(--muted)' },
                    ].map(r => (
                      <div key={r.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                        <span style={{ color: 'var(--muted)', fontSize: 13 }}>{r.label}</span>
                        <span style={{ color: r.color, fontWeight: 600, fontSize: 13 }}>{r.value}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="section">
            <div className="section-header">
              <div className="section-title">Tax Export</div>
            </div>
            <div className="card">
              <p style={{ color: 'var(--muted)', marginBottom: 16, fontSize: 13 }}>
                Export all revenue events with full treasury allocation breakdown as CSV for your accountant.
              </p>
              <button className="btn btn-secondary" onClick={handleExport}>
                ↓ Download Revenue CSV
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
