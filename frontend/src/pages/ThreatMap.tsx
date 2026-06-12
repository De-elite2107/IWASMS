import { useMemo, useCallback } from 'react'
import NavBar from '../components/NavBar'
import { useGetOverviewStatsQuery } from '../app/apiSlice'
import { useSecurityEventStream } from '../hooks/useWebSocket'

/**
 * Threat Map page — Source IP geolocation heatmap (Section 3.8.1).
 *
 * Displays top attacking IPs with country-level aggregation.
 * In a production deployment, IP-to-geo resolution would use MaxMind GeoIP2.
 * For the MVP, this renders the IP attack distribution as a visual heatmap table.
 */

interface GeoEntry {
  source_ip: string
  count: number
  country?: string
  lat?: number
  lng?: number
}

// Simple IP-to-region heuristic for demo (production would use GeoIP2)
function getRegionFromIP(ip: string): string {
  const first = parseInt(ip.split('.')[0] || '0')
  if (first >= 1 && first <= 126) return 'North America'
  if (first >= 128 && first <= 191) return 'Europe'
  if (first >= 192 && first <= 223) return 'Asia-Pacific'
  return 'Other'
}

function getSeverityColor(count: number): string {
  if (count >= 50) return '#F85149'  // critical red
  if (count >= 20) return '#D29922'  // amber warning
  if (count >= 5) return '#58A6FF'   // blue info
  return '#8B949E'                    // grey low
}

export default function ThreatMap() {
  const { data: statsData, isLoading } = useGetOverviewStatsQuery(undefined, {
    pollingInterval: 15_000,
  })

  // WebSocket — refetch stats when new events arrive
  const handleEvent = useCallback(() => {}, [])
  const { isConnected } = useSecurityEventStream(handleEvent)

  const topIPs: GeoEntry[] = useMemo(() => {
    if (!statsData?.data?.top_attacking_ips) return []
    return statsData.data.top_attacking_ips.map((entry) => ({
      source_ip: entry.source_ip,
      count: entry.count,
      country: getRegionFromIP(entry.source_ip),
    }))
  }, [statsData])

  // Aggregate by region
  const regionAgg = useMemo(() => {
    const map: Record<string, number> = {}
    topIPs.forEach((e) => {
      const region = e.country || 'Unknown'
      map[region] = (map[region] || 0) + e.count
    })
    return Object.entries(map)
      .map(([region, count]) => ({ region, count }))
      .sort((a, b) => b.count - a.count)
  }, [topIPs])

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#0D1117' }}>
      <NavBar wsConnected={isConnected} />

      <div style={{ flex: 1, padding: '24px', overflow: 'auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '24px' }}>
          <h1 style={{ color: '#E6EDF3', fontSize: '20px', fontWeight: 600, margin: 0 }}>
            Threat Map
          </h1>
          <p style={{ color: '#8B949E', fontSize: '13px', marginTop: '4px' }}>
            Source IP geolocation and attack distribution
          </p>
        </div>

        {isLoading ? (
          <div style={{ color: '#8B949E', textAlign: 'center', padding: '48px' }}>
            Loading threat data...
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Region Heatmap */}
            <div style={{
              backgroundColor: '#161B22',
              borderRadius: '8px',
              border: '1px solid #30363D',
              padding: '20px',
            }}>
              <h2 style={{ color: '#E6EDF3', fontSize: '14px', fontWeight: 600, marginBottom: '16px' }}>
                Attack Source Regions
              </h2>
              {regionAgg.length === 0 ? (
                <p style={{ color: '#8B949E', fontSize: '13px' }}>No attack data in the last 24 hours.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {regionAgg.map((r) => (
                    <div key={r.region} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        width: '12px', height: '12px', borderRadius: '50%',
                        backgroundColor: getSeverityColor(r.count),
                        flexShrink: 0,
                      }} />
                      <span style={{ color: '#E6EDF3', fontSize: '13px', flex: 1 }}>
                        {r.region}
                      </span>
                      <span style={{
                        color: getSeverityColor(r.count),
                        fontSize: '14px',
                        fontFamily: "'JetBrains Mono', monospace",
                        fontWeight: 600,
                      }}>
                        {r.count}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Top Attacking IPs Table */}
            <div style={{
              backgroundColor: '#161B22',
              borderRadius: '8px',
              border: '1px solid #30363D',
              padding: '20px',
            }}>
              <h2 style={{ color: '#E6EDF3', fontSize: '14px', fontWeight: 600, marginBottom: '16px' }}>
                Top Attacking IPs (24h)
              </h2>
              {topIPs.length === 0 ? (
                <p style={{ color: '#8B949E', fontSize: '13px' }}>No attacks detected.</p>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      <th style={{ color: '#8B949E', fontSize: '11px', textAlign: 'left', padding: '6px 8px', borderBottom: '1px solid #30363D' }}>
                        IP ADDRESS
                      </th>
                      <th style={{ color: '#8B949E', fontSize: '11px', textAlign: 'left', padding: '6px 8px', borderBottom: '1px solid #30363D' }}>
                        REGION
                      </th>
                      <th style={{ color: '#8B949E', fontSize: '11px', textAlign: 'right', padding: '6px 8px', borderBottom: '1px solid #30363D' }}>
                        ATTACKS
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {topIPs.map((ip) => (
                      <tr key={ip.source_ip}>
                        <td style={{
                          color: '#E6EDF3', fontSize: '13px', padding: '8px',
                          fontFamily: "'JetBrains Mono', monospace",
                          borderBottom: '1px solid #21262D',
                        }}>
                          {ip.source_ip}
                        </td>
                        <td style={{ color: '#8B949E', fontSize: '13px', padding: '8px', borderBottom: '1px solid #21262D' }}>
                          {ip.country}
                        </td>
                        <td style={{
                          color: getSeverityColor(ip.count), fontSize: '13px',
                          fontFamily: "'JetBrains Mono', monospace",
                          fontWeight: 600, textAlign: 'right', padding: '8px',
                          borderBottom: '1px solid #21262D',
                        }}>
                          {ip.count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Attack Types Distribution */}
            <div style={{
              backgroundColor: '#161B22',
              borderRadius: '8px',
              border: '1px solid #30363D',
              padding: '20px',
              gridColumn: '1 / -1',
            }}>
              <h2 style={{ color: '#E6EDF3', fontSize: '14px', fontWeight: 600, marginBottom: '16px' }}>
                Attack Type Distribution (24h)
              </h2>
              {(!statsData?.data?.attack_type_distribution || statsData.data.attack_type_distribution.length === 0) ? (
                <p style={{ color: '#8B949E', fontSize: '13px' }}>No attack type data available.</p>
              ) : (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                  {statsData!.data.attack_type_distribution.map((item) => (
                    <div key={item.attack_type} style={{
                      backgroundColor: '#0D1117',
                      border: '1px solid #30363D',
                      borderRadius: '6px',
                      padding: '12px 16px',
                      minWidth: '140px',
                    }}>
                      <div style={{ color: '#8B949E', fontSize: '11px', textTransform: 'uppercase', marginBottom: '4px' }}>
                        {item.attack_type.replace(/_/g, ' ')}
                      </div>
                      <div style={{
                        color: '#F85149', fontSize: '20px',
                        fontFamily: "'JetBrains Mono', monospace", fontWeight: 700,
                      }}>
                        {item.count}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
