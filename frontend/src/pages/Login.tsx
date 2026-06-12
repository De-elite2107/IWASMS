import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLoginMutation } from '../app/apiSlice'
import { setCredentials } from '../app/authSlice'
import { useAppDispatch } from '../hooks/useStore'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [login, { isLoading }] = useLoginMutation()
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      const result = await login({ username, password }).unwrap()
      if (result.data) {
        dispatch(
          setCredentials({
            access: result.data.access,
            refresh: result.data.refresh,
            user: result.data.user,
          })
        )
        navigate('/')
      } else {
        setError(result.error ? String(result.error) : 'Authentication failed')
      }
    } catch (err: unknown) {
      const e = err as { data?: { error?: string }; error?: string }
      setError(e?.data?.error || e?.error || 'Authentication failed')
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: '#0D1117',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
    >
      {/* Subtle grid overlay */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(48,54,61,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(48,54,61,0.3) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          width: '100%',
          maxWidth: '400px',
          backgroundColor: '#161B22',
          border: '1px solid #30363D',
          borderRadius: '2px',
          padding: '40px',
          position: 'relative',
          zIndex: 1,
        }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: '24px',
              fontWeight: '700',
              color: '#E6EDF3',
              letterSpacing: '0.04em',
              marginBottom: '6px',
            }}
          >
            ◈ IWASMS
          </div>
          <div
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: '11px',
              fontWeight: '600',
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              color: '#8B949E',
            }}
          >
            Security Monitoring System
          </div>
          <div
            style={{
              width: '40px',
              height: '1px',
              backgroundColor: '#30363D',
              margin: '20px auto 0',
            }}
          />
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <input
              id="username"
              type="text"
              placeholder="USERNAME"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              className="input-field"
              style={{ letterSpacing: '0.06em' }}
            />
            <input
              id="password"
              type="password"
              placeholder="PASSWORD"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="input-field"
              style={{ letterSpacing: '0.12em' }}
            />
          </div>

          {error && (
            <div
              style={{
                marginTop: '16px',
                padding: '10px 14px',
                backgroundColor: 'rgba(248,81,73,0.1)',
                borderLeft: '3px solid #F85149',
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: '12px',
                color: '#F85149',
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            style={{
              marginTop: '24px',
              width: '100%',
              padding: '12px',
              backgroundColor: isLoading ? '#1C2128' : '#1F6FEB',
              color: '#E6EDF3',
              border: 'none',
              borderRadius: '2px',
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: '13px',
              fontWeight: '700',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'background 150ms',
            }}
          >
            {isLoading ? (
              <span>
                AUTHENTICATING<span className="blink">_</span>
              </span>
            ) : (
              'ACCESS SYSTEM'
            )}
          </button>
        </form>

        {/* Footer hint */}
        <div
          style={{
            marginTop: '24px',
            textAlign: 'center',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '10px',
            color: '#6E7681',
            letterSpacing: '0.04em',
          }}
        >
          RESTRICTED ACCESS — AUTHORISED PERSONNEL ONLY
        </div>
      </div>
    </div>
  )
}
