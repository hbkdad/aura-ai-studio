import { useEffect, useState } from 'react'
import { getMemorySummary, getMemoryEvents, postMemoryEvent } from '../api'

const TYPE_COLORS = {
  note:     'var(--accent2)',
  decision: 'var(--accent)',
  audit:    'var(--yellow)',
  rule:     'var(--green)',
  action:   'var(--muted)',
  warning:  'var(--red)',
}

const SOURCE_COLORS = {
  user:   'var(--green)',
  agent:  'var(--accent2)',
  system: 'var(--muted)',
}

function Badge({ text, color }) {
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, textTransform: 'uppercase',
      color, border: `1px solid ${color}`, borderRadius: 3,
      padding: '1px 6px', whiteSpace: 'nowrap',
    }}>
      {text}
    </span>
  )
}

export default function Memory() {
  const [summary, setSummary] = useState(null)
  const [events, setEvents] = useState([])
  const [loadingSum, setLoadingSum] = useState(true)
  const [loadingEvents, setLoadingEvents] = useState(true)
  const [filterType, setFilterType] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [expandedId, setExpandedId] = useState(null)

  const [form, setForm] = useState({
    title: '',
    content: '',
    memory_type: 'note',
    tags: '',
  })

  const loadSummary = () => {
    setLoadingSum(true)
    getMemorySummary()
      .then(r => setSummary(r.data))
      .catch(console.error)
      .finally(() => setLoadingSum(false))
  }

  const loadEvents = (type = filterType) => {
    setLoadingEvents(true)
    getMemoryEvents(50, type || null)
      .then(r => setEvents(r.data.events || []))
      .catch(console.error)
      .finally(() => setLoadingEvents(false))
  }

  useEffect(() => { loadSummary(); loadEvents() }, [])

  const handleFilterChange = (type) => {
    setFilterType(type)
    loadEvents(type)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitError('')
    setSubmitted(false)
    if (!form.title.trim() || !form.content.trim()) {
      setSubmitError('Title and content are required')
      return
    }
    setSubmitting(true)
    try {
      await postMemoryEvent({
        title: form.title.trim(),
        content: form.content.trim(),
        memory_type: form.memory_type,
        source: 'user',
        tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
      })
      setForm({ title: '', content: '', memory_type: 'note', tags: '' })
      setSubmitted(true)
      setTimeout(() => setSubmitted(false), 3000)
      loadEvents()
      loadSummary()
    } catch (err) {
      setSubmitError(err.friendlyMessage || 'Failed to save memory event')
    } finally {
      setSubmitting(false)
    }
  }

  const rules = summary?.rules
  const stats = summary?.stats
  const split = rules?.treasury_split
  const safety = rules?.safety

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Project Memory</div>
        <div className="page-subtitle">
          Decisions, rules, and audit history — locally stored, never leaves your machine
        </div>
      </div>

      {/* Summary Cards */}
      <div className="section">
        <div className="section-header">
          <div className="section-title">Project Summary</div>
        </div>
        {loadingSum ? (
          <div className="loading">Loading summary...</div>
        ) : summary ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12 }}>
            {[
              { label: 'Mode', value: summary.project?.mode, color: 'var(--yellow)' },
              { label: 'Version', value: summary.project?.version, color: 'var(--accent2)' },
              { label: 'Currency', value: summary.project?.currency, color: 'var(--green)' },
              { label: 'Revenue Events', value: stats?.revenue_events ?? '—', color: 'var(--text)' },
              { label: 'Total Gross (CAD)', value: stats?.total_gross_cad != null ? `$${stats.total_gross_cad.toFixed(2)}` : '—', color: 'var(--green)' },
              { label: 'BTC Allocations', value: stats?.btc_allocations ?? '—', color: 'var(--accent)' },
              { label: 'Agent Actions', value: stats?.agent_actions_logged ?? '—', color: 'var(--accent2)' },
              { label: 'Memory Events', value: stats?.memory_events ?? '—', color: 'var(--text)' },
            ].map(c => (
              <div key={c.label} className="card" style={{ padding: '14px 16px' }}>
                <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{c.label}</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: c.color, marginTop: 4 }}>{c.value}</div>
              </div>
            ))}
          </div>
        ) : null}
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        {/* Current Rules */}
        <div className="section">
          <div className="section-header">
            <div className="section-title">Current Rules</div>
          </div>
          <div className="card">
            {split && (
              <>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 10 }}>
                  Treasury Split
                </div>
                {[
                  { label: 'Tax Reserve', pct: split.tax_reserve_pct, color: 'var(--yellow)' },
                  { label: 'BTC Allocation', pct: split.btc_allocation_pct, color: 'var(--accent)' },
                  { label: 'Operating Cash', pct: split.operating_cash_pct, color: 'var(--green)' },
                  { label: 'Tool Budget', pct: split.tool_budget_pct, color: 'var(--accent2)' },
                ].map(r => (
                  <div key={r.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid var(--border)' }}>
                    <span style={{ fontSize: 13, color: 'var(--muted)' }}>{r.label}</span>
                    <span style={{ fontSize: 13, fontWeight: 700, color: r.color }}>{r.pct}%</span>
                  </div>
                ))}
              </>
            )}
            {safety && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 10 }}>
                  Safety
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <div style={{
                    width: 10, height: 10, borderRadius: '50%',
                    background: safety.kill_switch_active ? 'var(--red)' : 'var(--green)',
                  }} />
                  <span style={{ fontSize: 13, color: safety.kill_switch_active ? 'var(--red)' : 'var(--green)', fontWeight: 600 }}>
                    Kill switch {safety.kill_switch_active ? 'ACTIVE' : 'inactive'}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>Wallet: {safety.wallet_mode}</div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>Max allocation: ${safety.max_single_allocation_usd} USD</div>
              </div>
            )}
            {rules?.invariants && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                  Hard Rules
                </div>
                {rules.invariants.map((r, i) => (
                  <div key={i} style={{ fontSize: 11, color: 'var(--text)', padding: '3px 0', borderBottom: '1px solid var(--border)' }}>
                    — {r}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Add Memory Note */}
        <div className="section">
          <div className="section-header">
            <div className="section-title">Add Memory Note</div>
          </div>
          <div className="card">
            {submitError && (
              <div className="alert alert-danger">{submitError}</div>
            )}
            {submitted && (
              <div className="alert alert-warning" style={{ color: 'var(--green)', borderColor: 'var(--green)' }}>
                Memory event saved.
              </div>
            )}
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Title *</label>
                <input
                  placeholder="e.g. Changed BTC split to 25%"
                  value={form.title}
                  onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                  maxLength={200}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Content *</label>
                <textarea
                  placeholder="Describe the decision, rule change, or note..."
                  value={form.content}
                  onChange={e => setForm(f => ({ ...f, content: e.target.value }))}
                  style={{ width: '100%', minHeight: 80, resize: 'vertical', background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: 6, padding: 8, fontFamily: 'inherit', fontSize: 13 }}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="form-group">
                  <label className="form-label">Type</label>
                  <select
                    value={form.memory_type}
                    onChange={e => setForm(f => ({ ...f, memory_type: e.target.value }))}
                    style={{ width: '100%', background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: 6, padding: '8px 10px', fontSize: 13 }}
                  >
                    {['note', 'decision', 'audit', 'rule', 'action', 'warning'].map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Tags (comma-separated)</label>
                  <input
                    placeholder="treasury, settings"
                    value={form.tags}
                    onChange={e => setForm(f => ({ ...f, tags: e.target.value }))}
                  />
                </div>
              </div>
              <div className="alert alert-warning" style={{ fontSize: 11, marginBottom: 12 }}>
                Safety filter active — private keys, seed phrases, API keys, and passwords are rejected.
              </div>
              <button className="btn btn-primary" type="submit" disabled={submitting}>
                {submitting ? 'Saving...' : '◈ Save Memory Event'}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Memory Events Table */}
      <div className="section">
        <div className="section-header">
          <div className="section-title">Memory Events</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {['', 'note', 'decision', 'audit', 'rule', 'action', 'warning'].map(t => (
              <button
                key={t}
                onClick={() => handleFilterChange(t)}
                style={{
                  fontSize: 11, padding: '3px 10px', borderRadius: 3, cursor: 'pointer',
                  border: `1px solid ${filterType === t ? 'var(--accent)' : 'var(--border)'}`,
                  background: filterType === t ? 'var(--accent)' : 'var(--bg)',
                  color: filterType === t ? '#fff' : 'var(--muted)',
                }}
              >
                {t || 'All'}
              </button>
            ))}
          </div>
        </div>
        <div className="card table-wrap">
          {loadingEvents ? (
            <div className="loading">Loading events...</div>
          ) : events.length === 0 ? (
            <div style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>
              No memory events yet. Add your first note above.
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Source</th>
                  <th>Title</th>
                  <th>Tags</th>
                </tr>
              </thead>
              <tbody>
                {events.map(ev => (
                  <>
                    <tr
                      key={ev.id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => setExpandedId(expandedId === ev.id ? null : ev.id)}
                    >
                      <td style={{ color: 'var(--muted)' }}>{ev.id}</td>
                      <td style={{ color: 'var(--muted)', fontSize: 12 }}>{ev.created_at?.slice(0, 16).replace('T', ' ')}</td>
                      <td><Badge text={ev.memory_type} color={TYPE_COLORS[ev.memory_type] || 'var(--muted)'} /></td>
                      <td><Badge text={ev.source} color={SOURCE_COLORS[ev.source] || 'var(--muted)'} /></td>
                      <td style={{ fontWeight: 500 }}>{ev.title}</td>
                      <td style={{ fontSize: 11, color: 'var(--muted)' }}>
                        {ev.tags?.length > 0 ? ev.tags.join(', ') : '—'}
                      </td>
                    </tr>
                    {expandedId === ev.id && (
                      <tr key={`${ev.id}-detail`}>
                        <td colSpan={6} style={{
                          background: 'var(--bg)', padding: '12px 16px',
                          fontSize: 13, color: 'var(--text)', borderBottom: '1px solid var(--border)',
                          whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                        }}>
                          {ev.content}
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
