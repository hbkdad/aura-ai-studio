import { useEffect, useState } from 'react'
import { getSkills, runSkill } from '../api'

export default function SkillsListPanel() {
  const [skills, setSkills] = useState([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(null)
  const [results, setResults] = useState({})
  const [errors, setErrors] = useState({})

  useEffect(() => {
    getSkills()
      .then(r => setSkills(r.data.skills || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleRun = async (skillName, requiredInputs) => {
    if (requiredInputs.length > 0) {
      setErrors(e => ({ ...e, [skillName]: `Requires inputs: ${requiredInputs.join(', ')} — use the Agent Loop to run this skill` }))
      return
    }
    setRunning(skillName)
    setErrors(e => ({ ...e, [skillName]: '' }))
    try {
      const res = await runSkill(skillName, {})
      setResults(r => ({ ...r, [skillName]: res.data.result }))
    } catch (err) {
      setErrors(e => ({ ...e, [skillName]: err.friendlyMessage || 'Skill failed' }))
    } finally {
      setRunning(null)
    }
  }

  return (
    <div className="section">
      <div className="section-header">
        <div className="section-title">Available Skills</div>
        <div className="section-subtitle" style={{ fontSize: 12, color: 'var(--muted)' }}>
          {skills.length} skill{skills.length !== 1 ? 's' : ''} registered — zero-input skills can run directly
        </div>
      </div>
      <div className="card">
        {loading ? (
          <div className="loading">Loading skills...</div>
        ) : skills.length === 0 ? (
          <div style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>No skills registered.</div>
        ) : (
          skills.map(skill => (
            <div key={skill.name} style={{
              padding: '12px 0',
              borderBottom: '1px solid var(--border)',
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent2)' }}>{skill.name}</span>
                    {skill.required_inputs.length === 0 && (
                      <span style={{ fontSize: 10, color: 'var(--green)', border: '1px solid var(--green)', borderRadius: 3, padding: '1px 5px' }}>
                        no inputs
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 4 }}>{skill.description}</div>
                  {skill.required_inputs.length > 0 && (
                    <div style={{ fontSize: 11, color: 'var(--yellow)' }}>
                      Required: {skill.required_inputs.join(', ')}
                    </div>
                  )}
                  {errors[skill.name] && (
                    <div style={{ fontSize: 11, color: 'var(--red)', marginTop: 4 }}>{errors[skill.name]}</div>
                  )}
                  {results[skill.name] && (
                    <div style={{
                      marginTop: 8, fontSize: 11, color: 'var(--text)',
                      background: 'var(--bg)', padding: 8, borderRadius: 4,
                      border: '1px solid var(--border)', wordBreak: 'break-word',
                    }}>
                      {JSON.stringify(results[skill.name]).slice(0, 300)}
                    </div>
                  )}
                </div>
                <button
                  className="btn"
                  style={{ fontSize: 12, padding: '4px 12px', whiteSpace: 'nowrap' }}
                  onClick={() => handleRun(skill.name, skill.required_inputs)}
                  disabled={running === skill.name}
                >
                  {running === skill.name ? 'Running...' : 'Run'}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
