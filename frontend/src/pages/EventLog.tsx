import { useCallback } from 'react'
import NavBar from '../components/NavBar'
import EventLogTable from '../components/EventLogTable'
import { useAppSelector } from '../hooks/useStore'
import { useSecurityEventStream } from '../hooks/useWebSocket'
import { apiSlice } from '../app/apiSlice'
import { useAppDispatch } from '../hooks/useStore'
import type { SecurityEvent } from '../types'

export default function EventLog() {
  const token = useAppSelector((s) => s.auth.access)
  const dispatch = useAppDispatch()
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

  // WebSocket — auto-refetch events when new data arrives
  const handleEvent = useCallback((_event: SecurityEvent) => {
    dispatch(apiSlice.util.invalidateTags(['Events']))
  }, [dispatch])

  const { isConnected } = useSecurityEventStream(handleEvent)

  const handleExport = useCallback((format: 'csv' | 'json') => {
    const url = `${baseUrl}/events/export/?format=${format}&hours=24`
    fetch(url, {
      headers: { Authorization: `Bearer ${token || ''}` },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const blobUrl = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = blobUrl
        a.download = `iwasms_events_24h.${format}`
        a.click()
        URL.revokeObjectURL(blobUrl)
      })
      .catch(() => {
        window.open(url, '_blank')
      })
  }, [token, baseUrl])

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
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {/* Export controls */}
        <div style={{
          padding: '12px 20px',
          backgroundColor: '#161B22',
          borderBottom: '1px solid #30363D',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}>
          <h1 style={{ color: '#E6EDF3', fontSize: '16px', fontWeight: 600, margin: 0 }}>
            Event Log
          </h1>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => handleExport('csv')}
              style={{
                padding: '6px 12px',
                backgroundColor: '#21262D',
                border: '1px solid #30363D',
                borderRadius: '4px',
                color: '#E6EDF3',
                fontSize: '12px',
                cursor: 'pointer',
                fontFamily: "'Space Grotesk', sans-serif",
              }}
            >
              Export CSV
            </button>
            <button
              onClick={() => handleExport('json')}
              style={{
                padding: '6px 12px',
                backgroundColor: '#21262D',
                border: '1px solid #30363D',
                borderRadius: '4px',
                color: '#E6EDF3',
                fontSize: '12px',
                cursor: 'pointer',
                fontFamily: "'Space Grotesk', sans-serif",
              }}
            >
              Export JSON
            </button>
          </div>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '1px', backgroundColor: '#30363D' }}>
          <div style={{ minHeight: '100%', backgroundColor: '#0D1117' }}>
            <EventLogTable />
          </div>
        </div>
      </div>
    </div>
  )
}
