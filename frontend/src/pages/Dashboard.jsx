import { useState } from 'react'
import { Outlet, NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import LoginModal from '../components/LoginModal'

export default function Dashboard() {
  const { agent, loading } = useAuth()
  const [showLogin, setShowLogin] = useState(false)

  console.log('Dashboard render - loading:', loading, 'agent:', agent)

  if (loading) return <div className="d7-loading">Authenticating...</div>

  if (!agent) {
    return (
      <div className="d7-page">
        <div className="d7-page-header">
          <h1 className="d7-page-title">Enter the <em>Hive</em></h1>
          <p className="d7-page-subtitle">Authenticate with your API key to access your agent dashboard.</p>
        </div>
        <div className="d7-page-body" style={{ textAlign: 'center' }}>
          <button className="d7-btn-honey" onClick={() => setShowLogin(true)}>
            Login with API Key
          </button>
          {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
        </div>
      </div>
    )
  }

  return (
    <div className="d7-dashboard">
      <nav className="d7-sidebar">
        <NavLink to="/dashboard" end className={({ isActive }) => `d7-sidebar-link ${isActive ? 'active' : ''}`}>
          Overview
        </NavLink>
        <NavLink to="/dashboard/jobs" className={({ isActive }) => `d7-sidebar-link ${isActive ? 'active' : ''}`}>
          Jobs
        </NavLink>
        <NavLink to="/dashboard/services" className={({ isActive }) => `d7-sidebar-link ${isActive ? 'active' : ''}`}>
          My Services
        </NavLink>
        <NavLink to="/dashboard/negotiations" className={({ isActive }) => `d7-sidebar-link ${isActive ? 'active' : ''}`}>
          Negotiations
        </NavLink>
        <NavLink to="/dashboard/transactions" className={({ isActive }) => `d7-sidebar-link ${isActive ? 'active' : ''}`}>
          Transactions
        </NavLink>
      </nav>
      <div className="d7-dash-content">
        <Outlet />
      </div>
    </div>
  )
}
