import {
  ComposedChart, Area, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from 'recharts'
import { format, parseISO } from 'date-fns'
import type { TimelinePoint } from '../types'

interface ThreatTimelineProps {
  data?: TimelinePoint[]
  isLoading?: boolean
}

const CustomTooltip = ({ active, payload, label }: {
  active?: boolean
  payload?: Array<{ name: string; value: number; color: string }>
  label?: string
}) => {
  if (!active || !payload?.length) return null

  const total = payload.find(p => p.name === 'total')?.value ?? 0
  const attacks = payload.find(p => p.name === 'attacks')?.value ?? 0
  const rate = total > 0 ? ((attacks / total) * 100).toFixed(1) : '0.0'

  return (
    <div
      style={{
        backgroundColor: '#1C2128',
        border: '1px solid #30363D',
        borderRadius: '2px',
        padding: '10px 14px',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '11px',
        color: '#E6EDF3',
        minWidth: '160px',
      }}
    >
      <div style={{ color: '#8B949E', marginBottom: '8px', letterSpacing: '0.04em' }}>
        {label ? format(parseISO(label), 'dd MMM HH:mm') : ''}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px' }}>
          <span style={{ color: '#8B949E' }}>TOTAL</span>
          <span style={{ color: '#E6EDF3' }}>{total}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px' }}>
          <span style={{ color: '#F85149' }}>ATTACKS</span>
          <span style={{ color: '#F85149' }}>{attacks}</span>
        </div>
        <div
          style={{
            borderTop: '1px solid #30363D',
            marginTop: '4px',
            paddingTop: '4px',
            display: 'flex',
            justifyContent: 'space-between',
            gap: '16px',
          }}
        >
          <span style={{ color: '#8B949E' }}>DETECT RATE</span>
          <span style={{ color: '#58A6FF' }}>{rate}%</span>
        </div>
      </div>
    </div>
  )
}

export default function ThreatTimeline({ data = [], isLoading }: ThreatTimelineProps) {
  const formatXAxis = (val: string) => {
    try {
      return format(parseISO(val), 'HH:mm')
    } catch {
      return val
    }
  }

  return (
    <div className="card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="section-header">Threat Timeline</div>

      <div style={{ flex: 1, padding: '16px 8px 8px' }}>
        {isLoading ? (
          <div
            style={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '12px',
              color: '#30363D',
            }}
          >
            LOADING<span className="blink">_</span>
          </div>
        ) : data.length === 0 ? (
          <div
            style={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '12px',
              color: '#6E7681',
            }}
          >
            NO DATA IN WINDOW
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <ComposedChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="totalGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1F6FEB" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#1F6FEB" stopOpacity={0.02} />
                </linearGradient>
              </defs>

              <CartesianGrid
                horizontal={false}
                vertical
                stroke="#30363D"
                strokeDasharray="4 8"
                strokeOpacity={0.5}
              />

              <XAxis
                dataKey="hour"
                tickFormatter={formatXAxis}
                tick={{
                  fill: '#6E7681',
                  fontSize: 10,
                  fontFamily: "'JetBrains Mono', monospace",
                }}
                tickLine={false}
                axisLine={{ stroke: '#30363D' }}
                interval="preserveStartEnd"
              />

              <YAxis
                tick={{
                  fill: '#6E7681',
                  fontSize: 10,
                  fontFamily: "'JetBrains Mono', monospace",
                }}
                tickLine={false}
                axisLine={false}
                width={32}
              />

              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(48,54,61,0.3)' }} />

              <Area
                type="monotone"
                dataKey="total"
                name="total"
                fill="url(#totalGradient)"
                stroke="#1F6FEB"
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 3, fill: '#58A6FF', stroke: 'none' }}
              />

              <Bar
                dataKey="attacks"
                name="attacks"
                fill="#F85149"
                fillOpacity={0.85}
                barSize={4}
                radius={0}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Legend */}
      <div
        style={{
          display: 'flex',
          gap: '20px',
          padding: '8px 16px 12px',
          borderTop: '1px solid #30363D',
        }}
      >
        {[
          { color: '#1F6FEB', label: 'TOTAL EVENTS' },
          { color: '#F85149', label: 'ATTACKS' },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '12px', height: '2px', backgroundColor: color }} />
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: '9px',
                letterSpacing: '0.08em',
                color: '#6E7681',
              }}
            >
              {label}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
