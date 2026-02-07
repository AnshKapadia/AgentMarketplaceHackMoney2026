import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'

export default function LoginModal({ onClose }) {
  const { login } = useAuth()
  const [key, setKey] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!key.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/agents/me', {
        headers: { 'X-Agent-Key': key.trim(), 'Content-Type': 'application/json' }
      })
      if (!res.ok) throw new Error('Invalid API key')
      login(key.trim())
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="d7-modal-overlay" onClick={onClose}>
      <div className="d7-modal" onClick={e => e.stopPropagation()}>
        <button className="d7-modal-close" onClick={onClose}>&times;</button>
        <h2 className="d7-modal-title">Enter the <em style={{ color: 'var(--d7-honey)', fontStyle: 'italic' }}>Hive</em></h2>
        <p className="d7-modal-desc">
          Enter your Agent API key to access the dashboard. You received this key when you registered your agent via the CLI.
        </p>
        {error && <div className="d7-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <input
            className="d7-input"
            type="text"
            placeholder="agnt_xxxxxxxxxxxxxxxx"
            value={key}
            onChange={e => setKey(e.target.value)}
            autoFocus
          />
          <button type="submit" className="d7-btn-honey" style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
            {loading ? 'Verifying...' : 'Authenticate'}
          </button>
        </form>
      </div>
    </div>
  )
}
