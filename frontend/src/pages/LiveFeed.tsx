import { useState, useCallback } from 'react'
import NavBar from '../components/NavBar'
import LiveEventFeed from '../components/LiveEventFeed'
import { useSecurityEventStream } from '../hooks/useWebSocket'
import { useGetEventsQuery } from '../app/apiSlice'
import type { SecurityEvent } from '../types'

export default function LiveFeed() {
  const [liveEvents, setLiveEvents] = useState<SecurityEvent[]>([])
  const [stats, setStats] = useState({ total: 0, attacks: 0 })

  // Pre-populate with last 50 events
  const { data } = useGetEventsQuery({ page: 1, page_size: 50, ordering: '-timestamp' })
  const historicalEvents = data?.data ?? []

  const handleEvent = useCallback((event: SecurityEvent) => {
    setLiveEvents((prev) => [event, ...prev].slice(0, 200))
    setStats((s) => ({
      total: s.total + 1,
      attacks: s.attacks + (event.is_attack ? 1 : 0),
    }))
  }, [])

  const { isConnected } = useSecurityEventStream(handleEvent)

  const allEvents = liveEvents.length > 0 ? liveEvents : historicalEvents

  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#0D1117',
        overflow: 'hidden',
      }}
    >
      <NavBar wsConnected={isConnected} />

      {/* Stats strip */}
      <div
        style={{
          display: 'flex',
          gap: '1px',
          backgroundColor: '#30363D',
          flexShrink: 0,
        }}
      >
        {[
          { label: 'LIVE EVENTS', value: stats.total },
          { label: 'ATTACKS DETECTED', value: stats.attacks },
          {
            label: 'ATTACK RATE',
            value: stats.total > 0 ? `${((stats.attacks / stats.total) * 100).toFixed(1)}%` : '0.0%',
          },
        ].map(({ label, value }) => (
          <div
            key={label}
            className="card"
            style={{ flex: 1, padding: '12px 20px' }}
          >
            <div className="metric-label">{label}</div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: '22px',
                fontWeight: '700',
                color: label.includes('ATTACK') && value !== '0.0%' && value !== 0 ? '#F85149' : '#E6EDF3',
                marginTop: '4px',
              }}
            >
              {value}
            </div>
          </div>
        ))}
      </div>

      {/* Full feed */}
      <div style={{ flex: 1, overflow: 'auto', backgroundColor: '#0D1117' }}>
        <LiveEventFeed events={allEvents} />
      </div>
    </div>
  )
}
