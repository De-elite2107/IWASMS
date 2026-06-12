import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import type { OverviewStats } from '../types'

interface AttackCategoryRingProps {
  stats?: OverviewStats
  isLoading?: boolean
}

const CATEGORY_COLORS: Record<string, string> = {
  sql_injection: '#F85149',
  command_injection: '#F85149',
  xss: '#E3B341',
  ldap_injection: '#E3B341',
  path_traversal: '#58A6FF',
  csrf: '#58A6FF',
  brute_force: '#E3B341',
  dos: '#F85149',
  normal: '#3FB950',
  unknown: '#6E7681',
}

const formatLabel = (s: string) => s.replace(/_/g, ' ').toUpperCase()

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean
  payload?: Array<{ name: string; value: number; payload: { attack_type: string; count: number; pct: number } }>
}) => {
  if (!active || !payload?.length) return null
  const { attack_type, count, pct } = payload[0].payload
  return (
    <div
      style={{
        backgroundColor: '#1C2128',
        border: '1px solid #30363D',
        borderRadius: '2px',
        padding: '8px 12px',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '11px',
        color: '#E6EDF3',
      }}
    >
      <div style={{ color: '#8B949E', marginBottom: '4px', letterSpacing: '0.04em' }}>
        {formatLabel(attack_type)}
      </div>
      <div>
        <span style={{ color: CATEGORY_COLORS[attack_type] || '#6E7681' }}>{count}</span>
        <span style={{ color: '#6E7681' }}> ({pct.toFixed(1)}%)</span>
      </div>
    </div>
  )
}

export default function AttackCategoryRing({ stats, isLoading }: AttackCategoryRingProps) {
  const distribution = stats?.attack_type_distribution ?? []
  const total = distribution.reduce((s, d) => s + d.count, 0)

  const pieData = distribution.map((d) => ({
    ...d,
    pct: total > 0 ? (d.count / total) * 100 : 0,
  }))

  return (
    <div className="card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="section-header">Attack Distribution</div>

      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '16px',
        }}
      >
        {isLoading ? (
          <div
            style={{
              flex: 1,
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
        ) : pieData.length === 0 ? (
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '12px',
              color: '#6E7681',
            }}
          >
            NO ATTACKS DETECTED
          </div>
        ) : (
          <>
            {/* Donut chart */}
            <div style={{ width: 140, height: 140, position: 'relative', flexShrink: 0 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius="60%"
                    outerRadius="80%"
                    dataKey="count"
                    nameKey="attack_type"
                    strokeWidth={0}
                    isAnimationActive={false}
                  >
                    {pieData.map((entry) => (
                      <Cell
                        key={entry.attack_type}
                        fill={CATEGORY_COLORS[entry.attack_type] || '#6E7681'}
                        fillOpacity={0.85}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              {/* Center label */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  pointerEvents: 'none',
                }}
              >
                <span
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: '22px',
                    fontWeight: '700',
                    color: '#E6EDF3',
                    lineHeight: 1,
                  }}
                >
                  {total}
                </span>
                <span
                  style={{
                    fontFamily: "'Space Grotesk', sans-serif",
                    fontSize: '9px',
                    letterSpacing: '0.1em',
                    color: '#6E7681',
                    textTransform: 'uppercase',
                    marginTop: '2px',
                  }}
                >
                  ATTACKS
                </span>
              </div>
            </div>

            {/* Legend list */}
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                overflow: 'hidden',
              }}
            >
              {pieData.slice(0, 7).map((entry) => (
                <div
                  key={entry.attack_type}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '8px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0 }}>
                    <div
                      style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '1px',
                        backgroundColor: CATEGORY_COLORS[entry.attack_type] || '#6E7681',
                        flexShrink: 0,
                      }}
                    />
                    <span
                      style={{
                        fontFamily: "'Space Grotesk', sans-serif",
                        fontSize: '10px',
                        letterSpacing: '0.04em',
                        color: '#8B949E',
                        textTransform: 'uppercase',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {entry.attack_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
                    <span
                      style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: '11px',
                        color: '#E6EDF3',
                      }}
                    >
                      {entry.count}
                    </span>
                    <span
                      style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: '11px',
                        color: '#6E7681',
                        width: '38px',
                        textAlign: 'right',
                      }}
                    >
                      {entry.pct.toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
