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

    if (!form.revenue_event_id) { setAllocError('Select a revenue event'); return }
    const gross = parseFloat(form.gross_amount)
    const alloc = parseFloat(form.btc_allocation_usd)
    if (isNaN(gross) || gross <= 0) { setAllocError('Gross amount must be positive'); return }
    if (isNaN(alloc) || alloc <= 0) { setAllocError('Allocation amount must be positive'); return }
    if (alloc > gross) { setAllocError(`Allocation ($${alloc.toFixed(2)}) cannot exceed gross revenue ($${gross.toFixed(2)})`); return }

    setAllocating(true)
    try {
      const res = await postPaperAllocation({
        revenue_event_id: parseInt(form.revenue_event_id),
        gross_amount: gross,
        btc_allocation_usd: alloc,
        notes: form.notes || null,
      })
      setAllocSuccess(
        `Paper allocation created! Simulated ${fmtBtc(res.data.simulated_btc)} @ $${res.data.btc_price_usd?.toLocaleString()}/BTC — PAPER ONLY`
      )
      setForm({ revenue_event_id: '', gross_amount: '', btc_allocation_usd: '', notes: '' })
      load()
    } catch (err) {
      setAllocError(err.friendlyMessage || 'Allocation failed')
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

      {/* Paper mode banner — always visible */}
      <div style={{
        background: '#1a2a1a',
        border: '1px solid #22c55e44',
        borderRadius: 8,
        padding: '12px 20px',
        marginBottom: 20,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
      }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--green)', boxShadow: '0 0 8px var(--green)', flexShrink: 0 }} />
        <div>
          <span style={{ color: 'var(--green)', fontWeight: 700, fontSize: 14 }}>PAPER MODE — No Real BTC Ever Moves</span>
          <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 12 }}>
            All allocations are simulated records only. Real transaction methods are blocked at the code level.
          </span>
        </div>
      </div>

      {killActive && (
        <div className="alert alert-danger" style={{ marginBottom: 20, fontSize: 14, fontWeight: 600 }}>
          ⛔ KILL SWITCH IS ACTIVE — All financial operations are halted system-wide
        </div>
      )}

      <div className="grid-3" style={{ marginBottom: 24 }}>
        <div className="card stat-accent-green">
          <div className="card-title">Wallet Mode</div>
          <div className="card-value">PAPER</div>
          <div className="card-sub">Simulation only — V0.1</div>
        </div>
        <div className="card stat-accent-orange">
          <div className="card-title">Total Simulated BTC</div>
          <div className="card-value">{fmtBtc(btcData?.summary?.total_simulated_btc)}</div>
          <div className="card-sub">Paper only — not real</div>
        </div>
        <div className="card stat-accent-blue">
          <div className="card-title">Total Allocated USD</div>
          <div className="card-value">{fmt(btcData?.summary?.total_allocated_usd)}</div>
          <div className="card-sub">{btcData?.summary?.total_allocations || 0} paper allocations</div>
        </div>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <div className="section">
          <div className="section-header">
            <div className="section-title">Kill Switch Control</div>
          </div>
          <div className="card" style={{ border: `1px solid ${killActive ? 'var(--red)' : 'var(--border)'}` }}>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12, lineHeight: 1.7 }}>
                The kill switch immediately halts all new revenue recording, wallet allocations,
                and agent actions. Use if you notice unexpected behavior.
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
              <strong>PAPER MODE ONLY</strong> — No real Bitcoin is moved. This simulates what a
              future allocation would look like. Real transfer functions are blocked at the code level.
            </div>
            {allocError && <div className="alert alert-danger">{allocError}</div>}
            {allocSuccess && <div className="alert alert-success">{allocSuccess}</div>}
            <form onSubmit={handleAllocate}>
              <div className="form-group">
                <label className="form-label">Revenue Event *</label>
                <select value={form.revenue_event_id} onChange={e => {
                  const ev = revenueEvents.find(r => r.id === parseInt(e.target.value))
                  setForm(f => ({
                    ...f,
                    revenue_event_id: e.target.value,
                    gross_amount: ev ? String(ev.gross_amount) : '',
                    btc_allocation_usd: ev ? (ev.gross_amount * 0.2).toFixed(2) : '',
                  }))
                }}>
                  <option value="">Select a revenue event...</option>
                  {revenueEvents.map(e => (
                    <option key={e.id} value={e.id}>
                      #{e.id} — {e.source} ({e.currency} ${e.gross_amount})
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="form-group">
                  <label className="form-label">Gross Amount *</label>
                  <input type="number" step="0.01" min="0.01" value={form.gross_amount}
                    onChange={e => setForm(f => ({ ...f, gross_amount: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">BTC Alloc USD (20%) *</label>
                  <input type="number" step="0.01" min="0.01" value={form.btc_allocation_usd}
                    onChange={e => setForm(f => ({ ...f, btc_allocation_usd: e.target.value }))} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Notes</label>
                <input placeholder="Optional notes" value={form.notes}
                  onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
              </div>
              {form.btc_allocation_usd && !isNaN(parseFloat(form.btc_allocation_usd)) && (
                <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12, padding: '8px 12px', background: 'var(--surface2)', borderRadius: 6 }}>
                  📄 PAPER: ${parseFloat(form.btc_allocation_usd || 0).toFixed(2)} ÷ $65,000/BTC
                  = ₿ {(parseFloat(form.btc_allocation_usd || 0) / 65000).toFixed(8)} (simulated)
                </div>
              )}
              <button className="btn btn-primary" type="submit" disabled={allocating || killActive}>
                {allocating ? 'Simulating...' : '₿ Simulate Paper Allocation'}
              </button>
              {killActive && (
                <div style={{ fontSize: 12, color: 'var(--red)', marginTop: 8 }}>
                  Kill switch is active — deactivate it first
                </div>
              )}
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
              <div style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>
                No paper allocations yet. Use the simulator above.
              </div>
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
                      <td><span className="badge badge-green">{a.wallet_mode?.toUpperCase()}</span></td>
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
