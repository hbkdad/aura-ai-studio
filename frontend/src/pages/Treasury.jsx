import { useEffect, useState } from 'react'
import { getTreasurySummary, postTreasuryCalculate, putTreasuryRules, getRevenueCSV, postFakeSale } from '../api'

function fmt(n) { return `$${Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}` }

export default function Treasury() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [calcAmount, setCalcAmount] = useState('')
  const [calcResult, setCalcResult] = useState(null)
  const [calcError, setCalcError] = useState('')
  const [rules, setRules] = useState({
    tax_reserve_pct: 30, btc_allocation_pct: 20, operating_cash_pct: 40, tool_budget_pct: 10,
  })
  const [rulesSaved, setRulesSaved] = useState(false)
  const [rulesError, setRulesError] = useState('')
  const [saving, setSaving] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [testRunning, setTestRunning] = useState(false)

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
    setCalcError('')
    setCalcResult(null)
    const amount = parseFloat(calcAmount)
    if (!amount || amount <= 0) {
      setCalcError('Enter a positive amount to calculate')
      return
    }
    try {
      const res = await postTreasuryCalculate({ gross_amount: amount })
      setCalcResult(res.data)
    } catch (err) {
      setCalcError(err.friendlyMessage || 'Calculation failed')
    }
  }

  const handleSaveRules = async () => {
    setRulesError('')
    setSaving(true)
    try {
      // Send as request body — backend validates sum=100
      await putTreasuryRules(rules)
      setRulesSaved(true)
      setTimeout(() => setRulesSaved(false), 3000)
      load()
    } catch (err) {
      setRulesError(err.friendlyMessage || 'Failed to save rules')
    } finally {
      setSaving(false)
    }
  }

  const handleRunTest = async () => {
    setTestRunning(true)
    setTestResult(null)
    try {
      const res = await postFakeSale()
      setTestResult(res.data)
    } catch (err) {
      setTestResult({ result: 'ERROR', error: err.friendlyMessage })
    } finally {
      setTestRunning(false)
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
              <div className="card-sub">{summary?.event_count || 0} events</div>
            </div>
            <div className="card stat-accent-yellow">
              <div className="card-title">Tax Reserve ({rules.tax_reserve_pct}%)</div>
              <div className="card-value">{fmt(summary?.tax_reserve)}</div>
            </div>
            <div className="card stat-accent-orange">
              <div className="card-title">BTC Allocation ({rules.btc_allocation_pct}%)</div>
              <div className="card-value">{fmt(summary?.btc_allocation)}</div>
            </div>
            <div className="card stat-accent-green">
              <div className="card-title">Operating Cash ({rules.operating_cash_pct}%)</div>
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
                    ⚠ Percentages total {totalPct.toFixed(1)}% — must equal exactly 100%
                  </div>
                )}
                {rulesError && <div className="alert alert-danger">{rulesError}</div>}
                {[
                  { key: 'tax_reserve_pct', label: 'Tax Reserve %', color: 'var(--yellow)' },
                  { key: 'btc_allocation_pct', label: 'BTC Allocation %', color: 'var(--accent)' },
                  { key: 'operating_cash_pct', label: 'Operating Cash %', color: 'var(--green)' },
                  { key: 'tool_budget_pct', label: 'Tool / API Budget %', color: 'var(--accent2)' },
                ].map(({ key, label, color }) => (
                  <div className="form-group" key={key}>
                    <label className="form-label" style={{ color }}>
                      {label} — currently <strong>{rules[key]}%</strong>
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.5"
                      value={rules[key]}
                      onChange={e => setRules(r => ({ ...r, [key]: parseFloat(e.target.value) || 0 }))}
                    />
                  </div>
                ))}
                <div style={{ display: 'flex', gap: 10, marginTop: 8, alignItems: 'center' }}>
                  <button
                    className="btn btn-primary"
                    onClick={handleSaveRules}
                    disabled={saving || Math.abs(totalPct - 100) > 0.01}
                  >
                    {saving ? 'Saving...' : 'Save Rules'}
                  </button>
                  {rulesSaved && <span className="badge badge-green">Saved ✓</span>}
                  <span style={{ fontSize: 12, color: totalPct === 100 ? 'var(--green)' : 'var(--red)' }}>
                    Total: {totalPct.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            <div className="section">
              <div className="section-header">
                <div className="section-title">Calculate Breakdown</div>
              </div>
              <div className="card">
                {calcError && <div className="alert alert-danger">{calcError}</div>}
                <div className="form-group">
                  <label className="form-label">Gross Amount</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder="e.g. 100.00"
                    value={calcAmount}
                    onChange={e => setCalcAmount(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleCalculate()}
                  />
                </div>
                <button className="btn btn-secondary" onClick={handleCalculate}>Calculate</button>

                {calcResult && (
                  <div style={{ marginTop: 16 }}>
                    {[
                      { label: 'Gross',                              value: fmt(calcResult.gross),           color: 'var(--text)' },
                      { label: `Tax Reserve (${calcResult.percentages?.tax}%)`,      value: fmt(calcResult.tax_reserve),     color: 'var(--yellow)' },
                      { label: `BTC Allocation (${calcResult.percentages?.btc}%)`,   value: fmt(calcResult.btc_allocation),  color: 'var(--accent)' },
                      { label: `Operating Cash (${calcResult.percentages?.operating}%)`, value: fmt(calcResult.operating_cash), color: 'var(--green)' },
                      { label: `Tool Budget (${calcResult.percentages?.tools}%)`,    value: fmt(calcResult.tool_budget),     color: 'var(--accent2)' },
                      { label: 'Remainder',                          value: fmt(calcResult.remainder),        color: 'var(--muted)' },
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

          <div className="grid-2">
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

            <div className="section">
              <div className="section-header">
                <div className="section-title">Test: Fake $100 Sale</div>
              </div>
              <div className="card">
                <p style={{ color: 'var(--muted)', marginBottom: 16, fontSize: 13 }}>
                  Creates a $100 CAD test sale and confirms the treasury split is exactly
                  tax=30, btc=20, ops=40, tools=10.
                </p>
                <button className="btn btn-secondary" onClick={handleRunTest} disabled={testRunning}>
                  {testRunning ? 'Running...' : '⚡ Run Test Sale'}
                </button>

                {testResult && (
                  <div style={{ marginTop: 16 }}>
                    <div className={`alert ${testResult.result === 'PASS' ? 'alert-success' : 'alert-danger'}`}>
                      <strong>{testResult.result}</strong>
                      {testResult.error && ` — ${testResult.error}`}
                    </div>
                    {testResult.breakdown && (
                      <div>
                        {Object.entries(testResult.checks || {}).map(([k, ok]) => (
                          <div key={k} style={{ fontSize: 12, padding: '4px 0', color: ok ? 'var(--green)' : 'var(--red)' }}>
                            {ok ? '✓' : '✗'} {k.replace(/_/g, ' ')}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
