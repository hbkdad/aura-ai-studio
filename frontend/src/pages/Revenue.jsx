import { useEffect, useState } from 'react'
import { getRevenue, postManualRevenue, getTreasurySummary } from '../api'

function fmt(n) { return `$${Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}` }

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
    currency: 'USD',
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    if (!form.source || !form.gross_amount) { setError('Source and amount are required'); return }
    const amount = parseFloat(form.gross_amount)
    if (isNaN(amount) || amount <= 0) { setError('Amount must be a positive number'); return }

    setSubmitting(true)
    try {
      const res = await postManualRevenue({ ...form, gross_amount: amount })
      setSuccess(`Revenue recorded! ID #${res.data.id} — ${fmt(amount)} from ${form.source}`)
      setForm({ source: '', gross_amount: '', description: '', currency: 'USD', payment_method: 'manual', reference_id: '' })
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to record revenue')
    } finally {
      setSubmitting(false)
    }
  }

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
          <div className="card-title">Net (after tax)</div>
          <div className="card-value">{fmt((stats.total_gross || 0) * 0.7)}</div>
          <div className="card-sub">Estimate at 30% reserve</div>
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
                <label className="form-label">Gross Amount (USD) *</label>
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
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
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
                    placeholder="Optional order/invoice ID"
                    value={form.reference_id}
                    onChange={e => setForm(f => ({ ...f, reference_id: e.target.value }))}
                  />
                </div>
              </div>
              <div style={{ marginTop: 8 }}>
                {form.gross_amount && !isNaN(parseFloat(form.gross_amount)) && (
                  <div className="alert alert-info" style={{ marginBottom: 12 }}>
                    Preview: Tax=${(parseFloat(form.gross_amount) * 0.3).toFixed(2)} · BTC=${(parseFloat(form.gross_amount) * 0.2).toFixed(2)} · Ops=${(parseFloat(form.gross_amount) * 0.4).toFixed(2)} · Tools=${(parseFloat(form.gross_amount) * 0.1).toFixed(2)}
                  </div>
                )}
                <button className="btn btn-primary" type="submit" disabled={submitting}>
                  {submitting ? 'Recording...' : '+ Record Revenue'}
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="section">
          <div className="section-header">
            <div className="section-title">Treasury Snapshot</div>
          </div>
          <div className="card">
            {[
              { label: 'Tax Reserve (30%)', value: fmt(treasury?.tax_reserve), color: 'var(--yellow)' },
              { label: 'BTC Allocation (20%)', value: fmt(treasury?.btc_allocation), color: 'var(--accent)' },
              { label: 'Operating Cash (40%)', value: fmt(treasury?.operating_cash), color: 'var(--green)' },
              { label: 'Tool Budget (10%)', value: fmt(treasury?.tool_budget), color: 'var(--accent2)' },
              { label: 'Remainder', value: fmt(treasury?.remainder), color: 'var(--text)' },
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
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--muted)' }}>No revenue events yet.</div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Date</th>
                    <th>Source</th>
                    <th>Description</th>
                    <th>Method</th>
                    <th>Gross</th>
                    <th>Tax Reserve</th>
                    <th>BTC</th>
                    <th>Ops</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map(e => (
                    <tr key={e.id}>
                      <td style={{ color: 'var(--muted)' }}>{e.id}</td>
                      <td style={{ color: 'var(--muted)' }}>{e.created_at?.slice(0, 10)}</td>
                      <td style={{ color: 'var(--accent2)' }}>{e.source}</td>
                      <td style={{ color: 'var(--muted)' }}>{e.description || '—'}</td>
                      <td><span className="badge badge-blue">{e.payment_method}</span></td>
                      <td style={{ color: 'var(--green)', fontWeight: 600 }}>{fmt(e.gross_amount)}</td>
                      <td style={{ color: 'var(--yellow)' }}>{fmt(e.gross_amount * 0.3)}</td>
                      <td style={{ color: 'var(--accent)' }}>{fmt(e.gross_amount * 0.2)}</td>
                      <td>{fmt(e.gross_amount * 0.4)}</td>
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
