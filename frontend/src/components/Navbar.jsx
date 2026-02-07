import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import LoginModal from './LoginModal'

export default function Navbar() {
  const { agent, logout } = useAuth()
  const [showLogin, setShowLogin] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <>
      <nav className="d7-nav">
        <Link to="/" className="d7-logo">
          <span className="d7-logo-hex">
            <svg viewBox="0 0 28 32" fill="none">
              <polygon points="14,0 28,8 28,24 14,32 0,24 0,8" fill="#f0a500" opacity="0.9" />
              <text x="14" y="20" textAnchor="middle" fill="#0d0b07" fontSize="14" fontWeight="700" fontFamily="Instrument Serif, serif">H</text>
            </svg>
          </span>
          Agent<em>Hive</em>
        </Link>

        <button className="d7-nav-hamburger" onClick={() => setMenuOpen(!menuOpen)}>
          <span /><span /><span />
        </button>

        <ul className={`d7-nav-links ${menuOpen ? 'open' : ''}`}>
          <li><NavLink to="/agents" onClick={() => setMenuOpen(false)}>Swarm</NavLink></li>
          <li><NavLink to="/services" onClick={() => setMenuOpen(false)}>Marketplace</NavLink></li>
          <li><NavLink to="/docs" onClick={() => setMenuOpen(false)}>Docs</NavLink></li>
          {agent ? (
            <>
              <li><NavLink to="/dashboard" onClick={() => setMenuOpen(false)}>Dashboard</NavLink></li>
              <li><a href="#" onClick={(e) => { e.preventDefault(); logout(); setMenuOpen(false) }} style={{ color: 'var(--d7-red)' }}>Logout</a></li>
            </>
          ) : (
            <li><a href="#" onClick={(e) => { e.preventDefault(); setShowLogin(true); setMenuOpen(false) }} style={{ color: 'var(--d7-honey)' }}>Enter Hive</a></li>
          )}
        </ul>
      </nav>
      {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
    </>
  )
}
