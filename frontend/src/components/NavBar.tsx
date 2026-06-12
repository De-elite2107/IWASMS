import { NavLink, useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/useStore'
import { logout } from '../app/authSlice'
import { useState, useEffect, useRef } from 'react'

interface NavBarProps {
  wsConnected?: boolean
}

const NAV_LINKS = [
  { to: '/', label: 'OVERVIEW', end: true },
  { to: '/live', label: 'LIVE FEED' },
  { to: '/events', label: 'EVENT LOG' },
  { to: '/threats', label: 'THREAT MAP' },
  { to: '/models', label: 'MODELS' },
]

export default function NavBar({ wsConnected = false }: NavBarProps) {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const user = useAppSelector((s) => s.auth.user)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleLogout = () => {
    dispatch(logout())
    navigate('/login')
  }

  return (
    <nav
      style={{
        height: '56px',
        backgroundColor: '#161B22',
        borderBottom: '1px solid #30363D',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 30,
        flexShrink: 0,
      }}
    >
      {/* Left — Brand */}
      <div
        style={{
          fontFamily: "'Space Grotesk', sans-serif",
          fontSize: '16px',
          fontWeight: '700',
          color: '#E6EDF3',
          letterSpacing: '0.04em',
          userSelect: 'none',
          flexShrink: 0,
        }}
      >
        ◈ IWASMS
      </div>

      {/* Centre — Nav links */}
      <div
        style={{
          display: 'flex',
          gap: '32px',
          alignItems: 'center',
          position: 'absolute',
          left: '50%',
          transform: 'translateX(-50%)',
        }}
      >
        {NAV_LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            style={{ paddingBottom: '2px' }}
          >
            {link.label}
          </NavLink>
        ))}
      </div>

      {/* Right — Status + User */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
        {/* WS Connection dot */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className={`status-dot ${wsConnected ? 'connected' : 'disconnected'}`} />
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '10px',
              color: wsConnected ? '#3FB950' : '#F85149',
              letterSpacing: '0.04em',
            }}
          >
            {wsConnected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>

        <div style={{ width: '1px', height: '20px', backgroundColor: '#30363D' }} />

        {/* User menu */}
        <div ref={menuRef} style={{ position: 'relative' }}>
          <button
            onClick={() => setShowUserMenu((v) => !v)}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '4px 8px',
              borderRadius: '2px',
            }}
          >
            <div
              style={{
                width: '28px',
                height: '28px',
                backgroundColor: '#1F6FEB',
                borderRadius: '2px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: "'Space Grotesk', sans-serif",
                fontSize: '11px',
                fontWeight: '700',
                color: '#E6EDF3',
              }}
            >
              {user?.username?.substring(0, 2).toUpperCase() || 'OP'}
            </div>
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: '11px',
                color: '#8B949E',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}
            >
              {user?.username || 'operator'}
            </span>
          </button>

          {showUserMenu && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                marginTop: '4px',
                backgroundColor: '#161B22',
                border: '1px solid #30363D',
                borderRadius: '2px',
                minWidth: '160px',
                zIndex: 50,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  padding: '8px 12px',
                  borderBottom: '1px solid #30363D',
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '10px',
                  color: '#6E7681',
                  letterSpacing: '0.04em',
                }}
              >
                {user?.email}
              </div>
              <button
                onClick={handleLogout}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  backgroundColor: 'transparent',
                  border: 'none',
                  textAlign: 'left',
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontSize: '12px',
                  fontWeight: '600',
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase',
                  color: '#F85149',
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => { (e.target as HTMLElement).style.backgroundColor = 'rgba(248,81,73,0.08)' }}
                onMouseLeave={(e) => { (e.target as HTMLElement).style.backgroundColor = 'transparent' }}
              >
                Terminate Session
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}
