import { useState, useEffect, useRef, useCallback } from 'react'
import type { SecurityEvent } from '../types'
import { format, parseISO } from 'date-fns'

interface LiveEventFeedProps {
  events: SecurityEvent[]
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#F85149',
  high: '#E3B341',
  medium: '#58A6FF',
  low: '#3FB950',
  normal: '#3FB950',
}

function EventRow({ event, isNew }: { event: SecurityEvent; isNew: boolean }) {
  const rowRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isNew || !rowRef.current) return
    rowRef.current.classList.add('flash-highlight')
    const timer = setTimeout(() => {
      rowRef.current?.classList.remove('flash-highlight')
    }, 900)
    return () => clearTimeout(timer)
  }, [isNew])

  const ts = (() => {
    try {
      return format(parseISO(event.timestamp), 'HH:mm:ss')
    } catch {
      return '--:--:--'
    }
  })()

  const urlTruncated =
    event.url.length > 38 ? event.url.substring(0, 38) + '…' : event.url

  return (
    <div
      ref={rowRef}
      className={`slide-in`}
      style={{
        display: 'grid',
        gridTemplateColumns: '68px 72px 46px 1fr 120px 50px',
        gap: '0 8px',
        padding: '5px 12px',
        borderBottom: '1px solid rgba(48,54,61,0.4)',
        alignItems: 'center',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '11px',
        transition: 'background 800ms',
        cursor: 'default',
      }}
    >
      {/* Timestamp */}
      <span style={{ color: '#6E7681', flexShrink: 0 }}>{ts}</span>

      {/* Severity badge */}
      <span className={`severity-badge ${event.severity}`}>{event.severity}</span>

      {/* Method */}
      <span
        style={{
          color: event.http_method === 'POST' ? '#E3B341' : '#8B949E',
          fontWeight: '600',
        }}
      >
        {event.http_method}
      </span>

      {/* URL */}
      <span
        style={{
          color: '#E6EDF3',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
        title={event.url}
      >
        {urlTruncated}
      </span>

      {/* Attack type */}
      <span
        style={{
          color: SEVERITY_COLORS[event.severity] || '#8B949E',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          fontSize: '10px',
          letterSpacing: '0.04em',
        }}
        title={event.attack_type}
      >
        {event.attack_type.replace(/_/g, '_').toUpperCase()}
      </span>

      {/* Confidence */}
      <span
        style={{
          color: '#8B949E',
          textAlign: 'right',
          flexShrink: 0,
        }}
      >
        {(event.confidence_score * 100).toFixed(0)}%
      </span>
    </div>
  )
}

export default function LiveEventFeed({ events }: LiveEventFeedProps) {
  const [displayEvents, setDisplayEvents] = useState<SecurityEvent[]>([])
  const [newIds, setNewIds] = useState<Set<string>>(new Set())
  const scrollRef = useRef<HTMLDivElement>(null)
  const prevIdsRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    if (events.length === 0) return

    const incomingIds = new Set(events.map((e) => e.id))
    const fresh = events.filter((e) => !prevIdsRef.current.has(e.id))

    if (fresh.length === 0 && displayEvents.length === 0) {
      setDisplayEvents(events.slice(0, 50))
      events.forEach((e) => prevIdsRef.current.add(e.id))
      return
    }

    if (fresh.length > 0) {
      setNewIds(new Set(fresh.map((e) => e.id)))
      setDisplayEvents((prev) => {
        const combined = [...fresh, ...prev].slice(0, 50)
        return combined
      })
      fresh.forEach((e) => prevIdsRef.current.add(e.id))
      setTimeout(() => setNewIds(new Set()), 1000)
    }
  }, [events])

  return (
    <div className="card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '10px 16px',
          borderBottom: '1px solid #30363D',
        }}
      >
        <span className="section-header" style={{ padding: 0, border: 'none' }}>
          Live Event Feed
        </span>
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '10px',
            color: '#6E7681',
          }}
        >
          {displayEvents.length} / 50
        </span>
      </div>

      {/* Column headers */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '68px 72px 46px 1fr 120px 50px',
          gap: '0 8px',
          padding: '5px 12px',
          borderBottom: '1px solid #30363D',
          fontFamily: "'Space Grotesk', sans-serif",
          fontSize: '9px',
          fontWeight: '600',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: '#6E7681',
          flexShrink: 0,
        }}
      >
        <span>Time</span>
        <span>Severity</span>
        <span>Method</span>
        <span>URL</span>
        <span>Attack Type</span>
        <span style={{ textAlign: 'right' }}>Conf</span>
      </div>

      {/* Scrollable event list */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
        }}
      >
        {displayEvents.length === 0 ? (
          <div
            style={{
              padding: '32px',
              textAlign: 'center',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '11px',
              color: '#6E7681',
            }}
          >
            AWAITING EVENTS<span className="blink">_</span>
          </div>
        ) : (
          displayEvents.map((event) => (
            <EventRow
              key={event.id}
              event={event}
              isNew={newIds.has(event.id)}
            />
          ))
        )}
      </div>
    </div>
  )
}
