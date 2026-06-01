import { useEffect, useState } from 'react'
import { health, getTreasurySummary, getRevenue, getBtcAllocations, getAgentActions } from '../api'

function StatCard({ label, value, sub, accent }) {
  return (
    <div className={`card stat-accent-${accent || 'blue'}`}>
      <div className="card-title">{label}</div>
      <div className="card-value">{value}</div>
      {sub && <div className="card-sub">{sub}</div>}
    </div>
  )
}

function fmt(n) { return `$${Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` }
function fmtBtc(n) { return `₿ ${Number(n || 0).toFixed(6)}` }

export default function Dashboard() {
  const [status, setStatus] = useState(null)
  const [treasury, setTreasury] = useState(null)
  const [revenue, setRevenue] = useState(null)
  const [btc, setBtc] = useState(null)
  const [actions, setActions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      health(),
      getTreasurySummary(),
      getRevenue(5),
      getBtcAllocations(),
      getAgentActions(5),
    ])
      .then(([h, t, r, b, a]) => {
        setStatus(h.data)
        setTreasury(t.data)
        setRevenue(r.data)
        setBtc(b.data)
        setActions(a.data.actions || [])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading dashboard...</div>

  const killActive = status?.kill_switch_active

  return (
    <div>
      {killActive && (
        <div className="kill-banner">
          ⛔ KILL SWITCH ACTIVE — All operations halted. Go to Wallet Safety to deactivate.
        </div>
      )}

      <div className="page-header">
        <div className="page-title">Dashboard</div>
        <div className="page-subtitle">
          AutoSats Engine — {status?.mode} MODE &nbsp;·&nbsp;
          Wallet: <strong>{status?.wallet_mode?.toUpperCase()}</strong>
        </div>
      </div>

      <div className="grid-4">
        <StatCard label="Gross Revenue" value={fmt(treasury?.total_gross)} sub={`${treasury?.event_count || 0} events`} accent="orange" />
        <StatCard label="Tax Reserve (30%)" value={fmt(treasury?.tax_reserve)} sub="Set aside for taxes" accent="yellow" />
        <StatCard label="BTC Allocation (20%)" value={fmt(treasury?.btc_allocation)} sub={fmtBtc(btc?.summary?.total_simulated_btc)} accent="orange" />
        <StatCard label="Operating Cash (40%)" value={fmt(treasury?.operating_cash)} sub="Business operations" accent="green" />
      </div>

      <div className="grid-4">
        <StatCard label="Tool / API Budget (10%)" value={fmt(treasury?.tool_budget)} sub="Software & APIs" accent="blue" />
        <StatCard label="Remainder" value={fmt(treasury?.remainder)} sub="Unallocated" accent="blue" />
        <StatCard label="Wallet Mode" value={status?.wallet_mode?.toUpperCase() || 'PAPER'} sub="No real BTC moved" accent="green" />
        <StatCard
          label="Kill Switch"
          value={killActive ? 'ACTIVE ⛔' : 'SAFE ✓'}
          sub={killActive ? 'Operations halted' : 'All systems go'}
          accent={killActive ? 'red' : 'green'}
        />
      </div>

      <div className="grid-2">
        <div className="section">
          <div className="section-header">
            <div className="section-title">Recent Revenue</div>
          </div>
          <div className="card">
            {revenue?.events?.length === 0 ? (
              <div style={{ color: 'var(--muted)', padding: '20px 0', textAlign: 'center' }}>
                No revenue events yet. Add one in Revenue.
              </div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Source</th>
                      <th>Amount</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(revenue?.events || []).map(e => (
                      <tr key={e.id}>
                        <td>{e.source}</td>
                        <td style={{ color: 'var(--green)', fontWeight: 600 }}>{fmt(e.gross_amount)}</td>
                        <td style={{ color: 'var(--muted)' }}>{e.created_at?.slice(0, 10)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        <div className="section">
          <div className="section-header">
            <div className="section-title">Recent Agent Actions</div>
          </div>
          <div className="card">
            {actions.length === 0 ? (
              <div style={{ color: 'var(--muted)', padding: '20px 0', textAlign: 'center' }}>
                No agent actions yet.
              </div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th>Action</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {actions.map(a => (
                      <tr key={a.id}>
                        <td style={{ color: 'var(--accent2)' }}>{a.agent_name}</td>
                        <td>{a.action_type}</td>
                        <td>
                          <span className={`badge badge-${a.status === 'completed' ? 'green' : a.status === 'blocked' ? 'red' : 'yellow'}`}>
                            {a.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-header">
          <div className="section-title">Treasury Allocation Rules</div>
        </div>
        <div className="card">
          <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
            {[
              { label: 'Tax Reserve', pct: treasury?.rules?.tax_reserve_pct, color: 'var(--yellow)' },
              { label: 'BTC Allocation', pct: treasury?.rules?.btc_allocation_pct, color: 'var(--accent)' },
              { label: 'Operating Cash', pct: treasury?.rules?.operating_cash_pct, color: 'var(--green)' },
              { label: 'Tool Budget', pct: treasury?.rules?.tool_budget_pct, color: 'var(--accent2)' },
            ].map(r => (
              <div key={r.label} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: r.color }}>{r.pct}%</div>
                <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{r.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
