import { useEffect, useState } from 'react'
import { getBtcAllocations, postPaperAllocation, postKillSwitch, getSafetySettings, getRevenue } from '../api'

function fmt(n) { return `$${Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}` }
function fmtBtc(n) { return `₿ ${Number(n || 0).toFixed(8)}` }

export default function WalletSafety() {
  const [safety, setSafety] = useState(null)
  const [btcData, setBtcData] = useState(null)
  const [revenueEvents, setRevenueEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [killLoading, setKillLoading] = useState(false)
  const [killReason, setKillReason] = useState('')
  const [allocError, setAllocError] = useState('')
  const [allocSuccess, setAllocSuccess] = useState('')
  const [allocating, setAllocating] = useState(false)

  const [form, setForm] = useState({
    revenue_event_id: '',
    gross_amount: '',
    btc_allocation_usd: '',
    notes: '',
  })

  const load = () => {
    Promise.all([getSafetySettings(), getBtcAllocations(), getRevenue(50)])
      .then(([s, b, r]) => {
        setSafety(s.data)
        setBtcData(b.data)
        setRevenueEvents(r.data.events || [])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const toggleKillSwitch = async () => {
    setKillLoading(true)
    try {
      const newState = !safety?.kill_switch_active
      await postKillSwitch(newState, killReason)
      load()
      setKillReason('')
    } catch (err) {
      console.error(err)
    } finally {
      setKillLoading(false)
    }
  }

  const handleAllocate = async (e) => {
    e.preventDefault()
    setAllocError('')
    setAllocSuccess('')
    if (!form.revenue_event_id || !form.gross_amount || !form.btc_allocation_usd) {
      setAllocError('All fields required')
      return
    }
    setAllocating(true)
    try {
      const res = await postPaperAllocation({
        revenue_event_id: parseInt(form.revenue_event_id),
        gross_amount: parseFloat(form.gross_amount),
        btc_allocation_usd: parseFloat(form.btc_allocation_usd),
        notes: form.notes || null,
      })
      setAllocSuccess(`Paper allocation created! Simulated ${fmtBtc(res.data.simulated_btc)} @ $${res.data.btc_price_usd?.toLocaleString()}/BTC`)
      setForm({ revenue_event_id: '', gross_amount: '', btc_allocation_usd: '', notes: '' })
      load()
    } catch (err) {
      setAllocError(err.response?.data?.detail || 'Allocation failed')
    } finally {
      setAllocating(false)
    }
  }

  const killActive = safety?.kill_switch_active

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Wallet Safety</div>
        <div className="page-subtitle">Paper mode BTC simulation and emergency controls</div>
      </div>

      {killActive && (
        <div className="alert alert-danger" style={{ marginBottom: 20, fontSize: 14, fontWeight: 600 }}>
          ⛔ KILL SWITCH IS ACTIVE — All financial operations are halted system-wide
        </div>
      )}

      <div className="grid-3" style={{ marginBottom: 24 }}>
        <div className="card stat-accent-orange">
          <div className="card-title">Wallet Mode</div>
          <div className="card-value">PAPER</div>
          <div className="card-sub">No real BTC moves</div>
        </div>
        <div className="card stat-accent-orange">
          <div className="card-title">Total Simulated BTC</div>
          <div className="card-value">{fmtBtc(btcData?.summary?.total_simulated_btc)}</div>
          <div className="card-sub">Paper only</div>
        </div>
        <div className="card stat-accent-blue">
          <div className="card-title">Total Allocated USD</div>
          <div className="card-value">{fmt(btcData?.summary?.total_allocated_usd)}</div>
          <div className="card-sub">{btcData?.summary?.total_allocations || 0} allocations</div>
        </div>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <div className="section">
          <div className="section-header">
            <div className="section-title">Kill Switch Control</div>
          </div>
          <div className="card" style={{ border: killActive ? '1px solid var(--red)' : '1px solid var(--border)' }}>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 8 }}>
                The kill switch immediately halts all new revenue recording, wallet allocations, and agent actions.
                Use in case of errors, unexpected behavior, or security concerns.
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                <div style={{
                  width: 12, height: 12, borderRadius: '50%',
                  background: killActive ? 'var(--red)' : 'var(--green)',
                  boxShadow: killActive ? '0 0 8px var(--red)' : '0 0 8px var(--green)',
                }} />
                <span style={{ fontWeight: 700, color: killActive ? 'var(--red)' : 'var(--green)', fontSize: 14 }}>
                  {killActive ? 'KILL SWITCH ACTIVE' : 'SYSTEMS NORMAL'}
                </span>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Reason (optional)</label>
              <input
                placeholder="Why are you toggling the kill switch?"
                value={killReason}
                onChange={e => setKillReason(e.target.value)}
              />
            </div>
            <button
              className={`btn ${killActive ? 'btn-success' : 'btn-danger'}`}
              onClick={toggleKillSwitch}
              disabled={killLoading}
            >
              {killLoading ? 'Processing...' : killActive ? '✓ Deactivate Kill Switch' : '⛔ Activate Kill Switch'}
            </button>
          </div>
        </div>

        <div className="section">
          <div className="section-header">
            <div className="section-title">Paper BTC Allocation Simulator</div>
          </div>
          <div className="card">
            <div className="alert alert-info" style={{ marginBottom: 16, fontSize: 12 }}>
              PAPER MODE ONLY — No real Bitcoin is moved. This simulates what a future allocation would look like.
            </div>
            {allocError && <div className="alert alert-danger">{allocError}</div>}
            {allocSuccess && <div className="alert alert-success">{allocSuccess}</div>}
            <form onSubmit={handleAllocate}>
              <div className="form-group">
                <label className="form-label">Revenue Event ID *</label>
                <select value={form.revenue_event_id} onChange={e => {
                  const ev = revenueEvents.find(r => r.id === parseInt(e.target.value))
                  setForm(f => ({
                    ...f,
                    revenue_event_id: e.target.value,
                    gross_amount: ev ? ev.gross_amount : '',
                    btc_allocation_usd: ev ? (ev.gross_amount * 0.2).toFixed(2) : '',
                  }))
                }}>
                  <option value="">Select revenue event...</option>
                  {revenueEvents.map(e => (
                    <option key={e.id} value={e.id}>#{e.id} — {e.source} (${e.gross_amount})</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Gross Amount (USD) *</label>
                <input type="number" step="0.01" min="0.01" value={form.gross_amount} onChange={e => setForm(f => ({ ...f, gross_amount: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">BTC Allocation USD (20%) *</label>
                <input type="number" step="0.01" min="0.01" value={form.btc_allocation_usd} onChange={e => setForm(f => ({ ...f, btc_allocation_usd: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Notes</label>
                <input placeholder="Optional notes" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
              </div>
              {form.btc_allocation_usd && (
                <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12 }}>
                  Simulated @ $65,000/BTC = ₿{(parseFloat(form.btc_allocation_usd || 0) / 65000).toFixed(8)}
                </div>
              )}
              <button className="btn btn-primary" type="submit" disabled={allocating || killActive}>
                {allocating ? 'Simulating...' : '₿ Simulate Paper Allocation'}
              </button>
            </form>
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-header">
          <div className="section-title">Paper Allocation History</div>
        </div>
        <div className="card table-wrap">
          {loading ? <div className="loading">Loading...</div> : (
            (btcData?.allocations?.length === 0) ? (
              <div style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>No allocations yet.</div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Date</th>
                    <th>Revenue #</th>
                    <th>Allocated USD</th>
                    <th>BTC Price</th>
                    <th>Simulated BTC</th>
                    <th>Mode</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(btcData?.allocations || []).map(a => (
                    <tr key={a.id}>
                      <td style={{ color: 'var(--muted)' }}>{a.id}</td>
                      <td style={{ color: 'var(--muted)', fontSize: 12 }}>{a.created_at?.slice(0, 10)}</td>
                      <td style={{ color: 'var(--accent2)' }}>#{a.revenue_event_id}</td>
                      <td style={{ color: 'var(--yellow)', fontWeight: 600 }}>{fmt(a.allocated_usd)}</td>
                      <td style={{ color: 'var(--muted)' }}>${a.btc_price_usd?.toLocaleString()}</td>
                      <td style={{ color: 'var(--accent)', fontWeight: 600 }}>{fmtBtc(a.simulated_btc)}</td>
                      <td><span className="badge badge-orange">{a.wallet_mode}</span></td>
                      <td><span className="badge badge-blue">{a.status}</span></td>
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
