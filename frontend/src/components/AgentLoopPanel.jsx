import { useState } from 'react'
import { runAgentLoop } from '../api'

export default function AgentLoopPanel() {
  const [goal, setGoal] = useState('')
  const [maxSteps, setMaxSteps] = useState(10)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleRun = async (e) => {
    e.preventDefault()
    if (!goal.trim()) return
    setError('')
    setResult(null)
    setRunning(true)
    try {
      const res = await runAgentLoop(goal.trim(), null, maxSteps)
      setResult(res.data)
    } catch (err) {
      setError(err.friendlyMessage || 'Agent loop failed')
    } finally {
      setRunning(false)
    }
  }

  const statusColor = (s) => {
    if (s === 'done') return 'var(--green)'
    if (s === 'blocked') return 'var(--red)'
    if (s === 'error' || s === 'max_steps_reached') return 'var(--yellow)'
    return 'var(--muted)'
  }

  return (
    <div className="section">
      <div className="section-header">
        <div className="section-title">AI Agent Loop</div>
        <div className="section-subtitle" style={{ fontSize: 12, color: 'var(--muted)' }}>
          Give the agent a goal — it will plan and run skills automatically
        </div>
      </div>
      <div className="card">
        {error && <div className="alert alert-danger">{error}</div>}
        <form onSubmit={handleRun}>
          <div className="form-group">
            <label className="form-label">Goal</label>
            <input
              placeholder='e.g. "Check my revenue summary" or "What is the BTC price?"'
              value={goal}
              onChange={e => setGoal(e.target.value)}
              disabled={running}
            />
          </div>
          <div className="form-group" style={{ maxWidth: 160 }}>
            <label className="form-label">Max Steps (1–10)</label>
            <input
              type="number" min="1" max="10" step="1"
              value={maxSteps}
              onChange={e => setMaxSteps(Math.max(1, Math.min(10, parseInt(e.target.value) || 10)))}
              disabled={running}
            />
          </div>
          <button className="btn btn-primary" type="submit" disabled={running || !goal.trim()}>
            {running ? 'Running...' : '⚡ Run Agent'}
          </button>
        </form>
      </div>

      {result && (
        <div className="card" style={{ marginTop: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <span style={{
              fontSize: 12, fontWeight: 700, textTransform: 'uppercase',
              color: statusColor(result.status),
              border: `1px solid ${statusColor(result.status)}`,
              borderRadius: 4, padding: '2px 8px',
            }}>
              {result.status}
            </span>
            <span style={{ fontSize: 12, color: 'var(--muted)' }}>
              {result.steps_taken} step{result.steps_taken !== 1 ? 's' : ''} · {result.duration_ms}ms
            </span>
            <span style={{ fontSize: 11, color: 'var(--muted)', marginLeft: 'auto' }}>
              {result.session_id?.slice(0, 8)}
            </span>
          </div>

          {result.output && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 6 }}>Output</div>
              <div style={{ fontSize: 13, color: 'var(--text)', background: 'var(--bg)', padding: 12, borderRadius: 6, border: '1px solid var(--border)' }}>
                {result.output}
              </div>
            </div>
          )}

          {result.reason && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 6 }}>Reason</div>
              <div style={{ fontSize: 13, color: 'var(--yellow)' }}>{result.reason}</div>
            </div>
          )}

          {result.steps?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8 }}>Steps</div>
              {result.steps.map((s, i) => (
                <div key={i} style={{
                  padding: '8px 12px', marginBottom: 6, borderRadius: 4,
                  border: '1px solid var(--border)', background: 'var(--bg)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ fontSize: 11, color: 'var(--muted)' }}>Step {s.step}</span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent2)' }}>{s.skill}</span>
                    <span style={{
                      fontSize: 10, color: s.status === 'ok' ? 'var(--green)' : 'var(--red)',
                      marginLeft: 'auto',
                    }}>
                      {s.status} · {s.duration_ms}ms
                    </span>
                  </div>
                  {s.input && Object.keys(s.input).length > 0 && (
                    <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 2 }}>
                      Input: {JSON.stringify(s.input)}
                    </div>
                  )}
                  <div style={{ fontSize: 11, color: 'var(--text)', wordBreak: 'break-word' }}>
                    {typeof s.observation === 'object'
                      ? JSON.stringify(s.observation).slice(0, 200)
                      : String(s.observation).slice(0, 200)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
