import { useEffect, useState } from 'react'
import { postWebsiteAudit, getAgentActions } from '../api'
import AgentLoopPanel from '../components/AgentLoopPanel'
import SkillsListPanel from '../components/SkillsListPanel'

export default function AgentTasks() {
  const [actions, setActions] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const [form, setForm] = useState({
    business_name: '',
    website_url: '',
    industry: '',
    city: '',
    contact_email: '',
  })

  const loadActions = () => {
    getAgentActions(50)
      .then(r => setActions(r.data.actions || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(loadActions, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    if (!form.business_name || !form.website_url || !form.industry || !form.city) {
      setError('Business name, URL, industry, and city are required')
      return
    }
    setSubmitting(true)
    try {
      const res = await postWebsiteAudit(form)
      setResult(res.data)
      loadActions()
    } catch (err) {
      setError(err.response?.data?.detail || 'Audit failed')
    } finally {
      setSubmitting(false)
    }
  }

  const scoreColor = (s) => s >= 75 ? 'var(--green)' : s >= 50 ? 'var(--yellow)' : 'var(--red)'

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Agent Tasks</div>
        <div className="page-subtitle">AI-powered website audit, skill runner, and agent loop</div>
      </div>

      <AgentLoopPanel />
      <SkillsListPanel />

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <div className="section">
          <div className="section-header">
            <div className="section-title">Website Audit Agent</div>
          </div>
          <div className="card">
            {error && <div className="alert alert-danger">{error}</div>}
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Business Name *</label>
                <input placeholder="Acme Digital Agency" value={form.business_name} onChange={e => setForm(f => ({ ...f, business_name: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Website URL *</label>
                <input placeholder="https://example.com" value={form.website_url} onChange={e => setForm(f => ({ ...f, website_url: e.target.value }))} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="form-group">
                  <label className="form-label">Industry *</label>
                  <input placeholder="e.g. Real Estate" value={form.industry} onChange={e => setForm(f => ({ ...f, industry: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">City *</label>
                  <input placeholder="e.g. Austin, TX" value={form.city} onChange={e => setForm(f => ({ ...f, city: e.target.value }))} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Contact Email (optional)</label>
                <input placeholder="owner@example.com" value={form.contact_email} onChange={e => setForm(f => ({ ...f, contact_email: e.target.value }))} />
              </div>
              <button className="btn btn-primary" type="submit" disabled={submitting}>
                {submitting ? 'Running Audit...' : '⚡ Run Website Audit'}
              </button>
            </form>
          </div>
        </div>

        {result && (
          <div className="section">
            <div className="section-header">
              <div className="section-title">Audit Results — {result.business_name}</div>
            </div>
            <div className="card">
              <div style={{ display: 'flex', gap: 24, marginBottom: 20, flexWrap: 'wrap' }}>
                {[
                  { label: 'Design', score: result.scores?.design },
                  { label: 'SEO', score: result.scores?.seo },
                  { label: 'Mobile', score: result.scores?.mobile },
                  { label: 'Trust', score: result.scores?.trust },
                  { label: 'Overall', score: result.scores?.overall },
                ].map(s => (
                  <div key={s.label} style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 26, fontWeight: 700, color: scoreColor(s.score) }}>{s.score}</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase' }}>{s.label}</div>
                  </div>
                ))}
              </div>

              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8 }}>Top Issues</div>
                {result.top_issues?.map((issue, i) => (
                  <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid var(--border)', fontSize: 13, color: 'var(--red)' }}>
                    ✗ {issue}
                  </div>
                ))}
              </div>

              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8 }}>Recommendations</div>
                {result.top_recommendations?.map((r, i) => (
                  <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid var(--border)', fontSize: 13, color: 'var(--green)' }}>
                    ✓ {r}
                  </div>
                ))}
              </div>

              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8 }}>Outreach Email Draft</div>
                <pre>{result.outreach_email}</pre>
              </div>

              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8 }}>Paid Report Offer</div>
                <pre>{result.paid_report_copy}</pre>
              </div>

              <div className="alert alert-warning" style={{ marginTop: 16, fontSize: 12 }}>
                {result.disclaimer}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="section">
        <div className="section-header">
          <div className="section-title">Agent Action Log</div>
        </div>
        <div className="card table-wrap">
          {loading ? <div className="loading">Loading...</div> : (
            actions.length === 0 ? (
              <div style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>No agent actions logged yet.</div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Timestamp</th>
                    <th>Agent</th>
                    <th>Action</th>
                    <th>Status</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {actions.map(a => (
                    <tr key={a.id}>
                      <td style={{ color: 'var(--muted)' }}>{a.id}</td>
                      <td style={{ color: 'var(--muted)', fontSize: 12 }}>{a.created_at?.slice(0, 19)}</td>
                      <td style={{ color: 'var(--accent2)' }}>{a.agent_name}</td>
                      <td>{a.action_type}</td>
                      <td>
                        <span className={`badge badge-${a.status === 'completed' ? 'green' : a.status === 'blocked' ? 'red' : 'yellow'}`}>
                          {a.status}
                        </span>
                      </td>
                      <td style={{ color: 'var(--muted)' }}>{a.duration_ms ? `${a.duration_ms}ms` : '—'}</td>
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
