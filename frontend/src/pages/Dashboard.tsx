import { useState, useCallback } from 'react'
import NavBar from '../components/NavBar'
import ThreatsKPIBar from '../components/ThreatsKPIBar'
import ThreatTimeline from '../components/ThreatTimeline'
import AttackCategoryRing from '../components/AttackCategoryRing'
import LiveEventFeed from '../components/LiveEventFeed'
import EventLogTable from '../components/EventLogTable'
import { useGetOverviewStatsQuery, useGetThreatTimelineQuery } from '../app/apiSlice'
import { useSecurityEventStream } from '../hooks/useWebSocket'
import type { SecurityEvent } from '../types'

export default function Dashboard() {
  const [liveEvents, setLiveEvents] = useState<SecurityEvent[]>([])

  const { data: statsData, isLoading: statsLoading } = useGetOverviewStatsQuery(undefined, {
    pollingInterval: 10_000,
  })
  const { data: timelineData, isLoading: timelineLoading } = useGetThreatTimelineQuery(
    { hours: 24 },
    { pollingInterval: 30_000 }
  )

  const handleEvent = useCallback((event: SecurityEvent) => {
    setLiveEvents((prev) => [event, ...prev].slice(0, 100))
  }, [])

  const { isConnected: wsConnected } = useSecurityEventStream(handleEvent)

  const stats = statsData?.data
  const timeline = timelineData?.data?.timeline ?? []

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#0D1117',
      }}
    >
      <NavBar wsConnected={wsConnected} />

      {/* Scrollable content area */}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        {/* Row 1 — KPI Bar */}
        <ThreatsKPIBar stats={stats} isLoading={statsLoading} />

        {/* Row 2 — Timeline + Ring side by side */}
        <div
          style={{
            display: 'flex',
            gap: '12px',
            minHeight: '280px',
            flexShrink: 0,
          }}
        >
          <div style={{ flex: 7, backgroundColor: '#161B22', borderRadius: '6px', border: '1px solid #30363D' }}>
            <ThreatTimeline data={timeline} isLoading={timelineLoading} />
          </div>
          <div style={{ flex: 3, backgroundColor: '#161B22', borderRadius: '6px', border: '1px solid #30363D' }}>
            <AttackCategoryRing stats={stats} isLoading={statsLoading} />
          </div>
        </div>

        {/* Row 3 — Live Feed + Event Log side by side */}
        <div
          style={{
            display: 'flex',
            gap: '12px',
            minHeight: '400px',
          }}
        >
          <div style={{
            flex: 4,
            backgroundColor: '#161B22',
            borderRadius: '6px',
            border: '1px solid #30363D',
            overflow: 'auto',
            maxHeight: '500px',
          }}>
            <LiveEventFeed events={liveEvents} />
          </div>
          <div style={{
            flex: 6,
            backgroundColor: '#161B22',
            borderRadius: '6px',
            border: '1px solid #30363D',
            overflow: 'auto',
            maxHeight: '500px',
          }}>
            <EventLogTable />
          </div>
        </div>
      </div>
    </div>
  )
}
