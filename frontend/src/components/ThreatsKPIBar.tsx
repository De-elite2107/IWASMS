import { useCountUp } from '../hooks/useCountUp'
import type { OverviewStats } from '../types'

interface ThreatsKPIBarProps {
  stats?: OverviewStats
  isLoading?: boolean
}

function MetricCard({
  label,
  value,
  unit,
  isAlert,
  colorOverride,
  isLoading,
}: {
  label: string
  value: number
  unit?: string
  isAlert?: boolean
  colorOverride?: string
  isLoading?: boolean
}) {
  const animated = useCountUp(isLoading ? 0 : value)

  const getLatencyColor = () => {
    if (label.includes('LATENCY')) {
      if (value < 50) return '#3FB950'
      if (value < 100) return '#E3B341'
      return '#F85149'
    }
    return colorOverride || '#E6EDF3'
  }

  return (
    <div
      className="card"
      style={{
        flex: 1,
        padding: '20px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Accent line top */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '2px',
          backgroundColor: isAlert && value > 0 ? '#F85149' : '#30363D',
        }}
      />

      <div className="metric-label">{label}</div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
        <span
          className="metric-value"
          style={{
            color: getLatencyColor(),
            transition: 'color 300ms',
          }}
        >
          {isLoading ? (
            <span style={{ color: '#30363D' }}>
              ----<span className="blink">_</span>
            </span>
          ) : (
            unit === '%' ? animated.toFixed(1) : animated.toLocaleString()
          )}
        </span>
        {unit && !isLoading && (
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '14px',
              color: '#8B949E',
            }}
          >
            {unit}
          </span>
        )}

        {/* Blinking alert indicator */}
        {isAlert && value > 0 && !isLoading && (
          <span
            className="blink pulse-alert"
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#F85149',
              display: 'inline-block',
              marginLeft: '4px',
            }}
          />
        )}
      </div>
    </div>
  )
}

export default function ThreatsKPIBar({ stats, isLoading }: ThreatsKPIBarProps) {
  return (
    <div
      style={{
        display: 'flex',
        gap: '1px',
        backgroundColor: '#30363D',
      }}
    >
      <MetricCard
        label="Active Alerts"
        value={stats?.active_alerts ?? 0}
        isAlert
        isLoading={isLoading}
      />
      <MetricCard
        label="Detection Rate (24h)"
        value={stats?.detection_rate ?? 0}
        unit="%"
        colorOverride="#58A6FF"
        isLoading={isLoading}
      />
      <MetricCard
        label="False Positive Rate"
        value={stats?.false_positive_rate ?? 0}
        unit="%"
        isLoading={isLoading}
      />
      <MetricCard
        label="Avg Latency"
        value={Math.round(stats?.avg_latency_ms ?? 0)}
        unit="ms"
        isLoading={isLoading}
      />
      <MetricCard
        label="Events (24h)"
        value={stats?.events_last_24h ?? 0}
        colorOverride="#8B949E"
        isLoading={isLoading}
      />
    </div>
  )
}
