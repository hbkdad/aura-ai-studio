import { useEffect, useState } from 'react'
import { getRevenue, postManualRevenue, getTreasurySummary } from '../api'

function fmt(n) {
  return `$${Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`
}

export default function Revenue() {
  const [events, setEvents] = useState([])
  const [stats, setStats] = useState({})
  const [treasury, setTreasury] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [form, setForm] = useState({
    source: '',
    gross_amount: '',
    description: '',
    currency: 'CAD',
    payment_method: 'manual',
    reference_id: '',
  })

  const load = () => {
    Promise.all([getRevenue(100), getTreasurySummary()])
      .then(([r, t]) => {
        setEvents(r.data.events)
        setStats(r.data.stats)
        setTreasury(t.data)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  // Use actual rules from API, fall back to defaults
  const taxPct = treasury?.rules?.tax_reserve_pct ?? 30
  const btcPct = treasury?.rules?.btc_allocation_pct ?? 20
  const opPct = treasury?.rules?.operating_cash_pct ?? 40
  const toolPct = treasury?.rules?.tool_budget_pct ?? 10

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    const source = form.source.trim()
    if (!source) { setError('Source is required'); return }

    const amount = parseFloat(form.gross_amount)
    if (isNaN(amount) || amount <= 0) {
      setError('Amount must be a positive number greater than 0')
      return
    }

    setSubmitting(true)
    try {
      const res = await postManualRevenue({ ...form, source, gross_amount: amount })
      setSuccess(
        `Revenue recorded! ID #${res.data.id} — ${fmt(amount)} ${form.currency} from "${source}"`
      )
      setForm({
        source: '', gross_amount: '', description: '',
        currency: 'CAD', payment_method: 'manual', reference_id: '',
      })
      load()
    } catch (err) {
      setError(err.friendlyMessage || 'Failed to record revenue')
    } finally {
      setSubmitting(false)
    }
  }

  const previewAmount = parseFloat(form.gross_amount)
  const hasPreview = !isNaN(previewAmount) && previewAmount > 0

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Revenue</div>
        <div className="page-subtitle">Log sales and track income streams</div>
      </div>

      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="card stat-accent-orange">
          <div className="card-title">Total Gross</div>
          <div className="card-value">{fmt(stats.total_gross)}</div>
          <div className="card-sub">{stats.total_events || 0} events</div>
        </div>
        <div className="card stat-accent-green">
          <div className="card-title">Avg Sale</div>
          <div className="card-value">{fmt(stats.avg_sale)}</div>
        </div>
        <div className="card stat-accent-blue">
          <div className="card-title">Max Sale</div>
          <div className="card-value">{fmt(stats.max_sale)}</div>
        </div>
        <div className="card">
          <div className="card-title">Net (after {taxPct}% tax)</div>
          <div className="card-value">{fmt((stats.total_gross || 0) * (1 - taxPct / 100))}</div>
          <div className="card-sub">Based on active tax rule</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="section">
          <div className="section-header">
            <div className="section-title">Log Revenue Event</div>
          </div>
          <div className="card">
            {error && <div className="alert alert-danger">{error}</div>}
            {success && <div className="alert alert-success">{success}</div>}
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Source *</label>
                <input
                  placeholder="e.g. gumroad, stripe, consulting, freelance"
                  value={form.source}
                  onChange={e => setForm(f => ({ ...f, source: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Gross Amount *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="e.g. 100.00"
                  value={form.gross_amount}
                  onChange={e => setForm(f => ({ ...f, gross_amount: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Description</label>
                <input
                  placeholder="What was this payment for?"
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                <div className="form-group">
                  <label className="form-label">Currency</label>
                  <select value={form.currency} onChange={e => setForm(f => ({ ...f, currency: e.target.value }))}>
                    <option value="CAD">CAD</option>
                    <option value="USD">USD</option>
                    <option value="GBP">GBP</option>
                    <option value="EUR">EUR</option>
                    <option value="AUD">AUD</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Payment Method</label>
                  <select value={form.payment_method} onChange={e => setForm(f => ({ ...f, payment_method: e.target.value }))}>
                    <option value="manual">Manual</option>
                    <option value="stripe">Stripe</option>
                    <option value="gumroad">Gumroad</option>
                    <option value="paypal">PayPal</option>
                    <option value="crypto">Crypto</option>
                    <option value="bank_transfer">Bank Transfer</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Reference ID</label>
                  <input
                    placeholder="Optional"
                    value={form.reference_id}
                    onChange={e => setForm(f => ({ ...f, reference_id: e.target.value }))}
                  />
                </div>
              </div>

              {hasPreview && (
                <div className="alert alert-info" style={{ marginBottom: 12 }}>
                  <strong>Preview split:</strong>&nbsp;
                  Tax {taxPct}% = {fmt(previewAmount * taxPct / 100)} &nbsp;·&nbsp;
                  BTC {btcPct}% = {fmt(previewAmount * btcPct / 100)} &nbsp;·&nbsp;
                  Ops {opPct}% = {fmt(previewAmount * opPct / 100)} &nbsp;·&nbsp;
                  Tools {toolPct}% = {fmt(previewAmount * toolPct / 100)}
                </div>
              )}

              <button className="btn btn-primary" type="submit" disabled={submitting}>
                {submitting ? 'Recording...' : '+ Record Revenue'}
              </button>
            </form>
          </div>
        </div>

        <div className="section">
          <div className="section-header">
            <div className="section-title">Treasury Snapshot</div>
          </div>
          <div className="card">
            {[
              { label: `Tax Reserve (${taxPct}%)`,      value: fmt(treasury?.tax_reserve),    color: 'var(--yellow)' },
              { label: `BTC Allocation (${btcPct}%)`,   value: fmt(treasury?.btc_allocation),  color: 'var(--accent)' },
              { label: `Operating Cash (${opPct}%)`,    value: fmt(treasury?.operating_cash),  color: 'var(--green)' },
              { label: `Tool Budget (${toolPct}%)`,     value: fmt(treasury?.tool_budget),     color: 'var(--accent2)' },
              { label: 'Remainder',                      value: fmt(treasury?.remainder),       color: 'var(--text)' },
            ].map(r => (
              <div key={r.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ color: 'var(--muted)', fontSize: 13 }}>{r.label}</span>
                <span style={{ color: r.color, fontWeight: 600, fontSize: 13 }}>{r.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-header">
          <div className="section-title">All Revenue Events</div>
        </div>
        <div className="card table-wrap">
          {loading ? <div className="loading">Loading...</div> : (
            events.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--muted)' }}>
                No revenue events yet. Add one above.
              </div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Date</th>
                    <th>Source</th>
                    <th>Description</th>
                    <th>Currency</th>
                    <th>Method</th>
                    <th>Gross</th>
                    <th>Tax ({taxPct}%)</th>
                    <th>BTC ({btcPct}%)</th>
                    <th>Ops ({opPct}%)</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map(e => (
                    <tr key={e.id}>
                      <td style={{ color: 'var(--muted)' }}>{e.id}</td>
                      <td style={{ color: 'var(--muted)' }}>{e.created_at?.slice(0, 10)}</td>
                      <td style={{ color: 'var(--accent2)' }}>{e.source}</td>
                      <td style={{ color: 'var(--muted)' }}>{e.description || '—'}</td>
                      <td><span className="badge badge-blue">{e.currency}</span></td>
                      <td><span className="badge badge-blue">{e.payment_method}</span></td>
                      <td style={{ color: 'var(--green)', fontWeight: 600 }}>{fmt(e.gross_amount)}</td>
                      <td style={{ color: 'var(--yellow)' }}>{fmt(e.gross_amount * taxPct / 100)}</td>
                      <td style={{ color: 'var(--accent)' }}>{fmt(e.gross_amount * btcPct / 100)}</td>
                      <td>{fmt(e.gross_amount * opPct / 100)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )
          )}
        </div>
      </div>
    </div>
  )
}
