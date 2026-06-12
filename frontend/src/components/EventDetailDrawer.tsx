import { useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useGetEventDetailQuery, useResolveAlertMutation, useMarkFalsePositiveMutation } from '../app/apiSlice'

interface EventDetailDrawerProps {
  eventId: string
  onClose: () => void
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#F85149',
  high: '#E3B341',
  medium: '#58A6FF',
  low: '#3FB950',
  normal: '#3FB950',
}

export default function EventDetailDrawer({ eventId, onClose }: EventDetailDrawerProps) {
  const { data, isLoading } = useGetEventDetailQuery(eventId)
  const [resolveAlert, { isLoading: resolving }] = useResolveAlertMutation()
  const [markFP, { isLoading: markingFP }] = useMarkFalsePositiveMutation()

  const event = data?.data

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  const handleResolve = async () => {
    if (!event?.alert?.id) return
    await resolveAlert({ id: event.alert.id })
  }

  const handleFP = async () => {
    if (!event?.alert?.id) return
    await markFP({ id: event.alert.id })
  }

  return (
    <>
      {/* Overlay */}
      <div className="drawer-overlay" onClick={onClose} />

      {/* Drawer panel */}
      <div className="drawer">
        {/* Header */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '16px 20px',
            borderBottom: '1px solid #30363D',
            position: 'sticky',
            top: 0,
            backgroundColor: '#161B22',
            zIndex: 1,
          }}
        >
          <div>
            <div
              style={{
                fontFamily: "'Space Grotesk', sans-serif",
                fontSize: '11px',
                fontWeight: '600',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                color: '#8B949E',
                marginBottom: '4px',
              }}
            >
              Event Detail
            </div>
            {event && (
              <span className={`severity-badge ${event.severity}`}>{event.severity}</span>
            )}
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: '1px solid #30363D',
              color: '#8B949E',
              cursor: 'pointer',
              borderRadius: '2px',
              padding: '4px 10px',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '12px',
            }}
          >
            ✕
          </button>
        </div>

        {isLoading ? (
          <div
            style={{
              padding: '32px',
              textAlign: 'center',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '12px',
              color: '#6E7681',
            }}
          >
            LOADING<span className="blink">_</span>
          </div>
        ) : event ? (
          <div style={{ padding: '20px' }}>
            {/* Core info */}
            <InfoGrid
              rows={[
                ['Event ID', event.id.substring(0, 16) + '…'],
                ['Timestamp', formatTs(event.timestamp)],
                ['Source IP', event.source_ip],
                ['Method', event.http_method],
                ['Attack Type', event.attack_type.replace(/_/g, ' ').toUpperCase()],
                ['Confidence', `${(event.confidence_score * 100).toFixed(2)}%`],
                ['Latency', `${event.processing_latency_ms.toFixed(2)} ms`],
              ]}
            />

            {/* URL */}
            <Section title="Request URL">
              <div
                className="code-block"
                style={{ fontSize: '11px', wordBreak: 'break-all', whiteSpace: 'pre-wrap' }}
              >
                {event.url}
              </div>
            </Section>

            {/* Raw request */}
            {event.raw_request && Object.keys(event.raw_request).length > 0 && (
              <Section title="Raw Request">
                <div className="code-block" style={{ maxHeight: '200px', overflow: 'auto', fontSize: '10px' }}>
                  {JSON.stringify(event.raw_request, null, 2)}
                </div>
              </Section>
            )}

            {/* ML predictions */}
            {event.predictions && event.predictions.length > 0 && (
              <Section title="ML Prediction Breakdown">
                {event.predictions.map((pred) => {
                  const probEntries = Object.entries(pred.raw_probabilities)
                    .filter(([_, v]) => Array.isArray(v))
                    .map(([model, probs]) => ({
                      model,
                      attack_prob: Array.isArray(probs) ? (probs[1] ?? 0) : 0,
                    }))

                  return (
                    <div key={pred.id} style={{ marginBottom: '12px' }}>
                      <div
                        style={{
                          fontFamily: "'JetBrains Mono', monospace",
                          fontSize: '10px',
                          color: '#6E7681',
                          marginBottom: '8px',
                          letterSpacing: '0.04em',
                        }}
                      >
                        {pred.model_name} — {pred.predicted_label.replace(/_/g, ' ').toUpperCase()} (
                        {(pred.confidence * 100).toFixed(1)}%)
                      </div>
                      {probEntries.length > 0 && (
                        <ResponsiveContainer width="100%" height={80}>
                          <BarChart data={probEntries} margin={{ top: 0, right: 0, left: -30, bottom: 0 }}>
                            <XAxis
                              dataKey="model"
                              tick={{ fill: '#6E7681', fontSize: 9, fontFamily: "'JetBrains Mono', monospace" }}
                              tickLine={false}
                              axisLine={false}
                            />
                            <YAxis domain={[0, 1]} tick={false} axisLine={false} />
                            <Tooltip
                              formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, 'Attack Prob']}
                              contentStyle={{
                                backgroundColor: '#1C2128',
                                border: '1px solid #30363D',
                                borderRadius: '2px',
                                fontFamily: "'JetBrains Mono', monospace",
                                fontSize: '10px',
                              }}
                            />
                            <Bar dataKey="attack_prob" barSize={20} radius={0}>
                              {probEntries.map((entry) => (
                                <Cell
                                  key={entry.model}
                                  fill={entry.attack_prob > 0.7 ? '#F85149' : entry.attack_prob > 0.4 ? '#E3B341' : '#1F6FEB'}
                                  fillOpacity={0.85}
                                />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      )}
                    </div>
                  )
                })}
              </Section>
            )}

            {/* Alert section */}
            {event.alert && (
              <Section title="Alert Status">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <InfoGrid
                    rows={[
                      ['Status', event.alert.status.replace(/_/g, ' ').toUpperCase()],
                      ['Created', formatTs(event.alert.created_at)],
                      ['Assigned', event.alert.assigned_to_username || '—'],
                    ]}
                  />
                  {event.alert.analyst_notes && (
                    <div
                      style={{
                        padding: '8px',
                        backgroundColor: '#0D1117',
                        border: '1px solid #30363D',
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: '11px',
                        color: '#8B949E',
                        lineHeight: '1.5',
                      }}
                    >
                      {event.alert.analyst_notes}
                    </div>
                  )}
                </div>
              </Section>
            )}

            {/* Action buttons */}
            {event.alert && event.alert.status === 'open' && (
              <Section title="Quick Actions">
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <button
                    className="btn btn-ghost"
                    style={{ flex: 1 }}
                    onClick={handleResolve}
                    disabled={resolving}
                  >
                    {resolving ? 'Resolving…' : 'Resolve Alert'}
                  </button>
                  <button
                    className="btn btn-danger"
                    style={{ flex: 1 }}
                    onClick={handleFP}
                    disabled={markingFP}
                  >
                    {markingFP ? 'Marking…' : 'False Positive'}
                  </button>
                </div>
              </Section>
            )}
          </div>
        ) : (
          <div
            style={{
              padding: '32px',
              textAlign: 'center',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '11px',
              color: '#F85149',
            }}
          >
            FAILED TO LOAD EVENT
          </div>
        )}
      </div>
    </>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '20px' }}>
      <div
        style={{
          fontFamily: "'Space Grotesk', sans-serif",
          fontSize: '10px',
          fontWeight: '600',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: '#6E7681',
          marginBottom: '8px',
          paddingBottom: '4px',
          borderBottom: '1px solid #30363D',
        }}
      >
        {title}
      </div>
      {children}
    </div>
  )
}

function InfoGrid({ rows }: { rows: [string, string][] }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '110px 1fr',
        gap: '4px 12px',
        marginBottom: '16px',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '11px',
      }}
    >
      {rows.map(([label, value]) => (
        <>
          <span key={`l-${label}`} style={{ color: '#6E7681', letterSpacing: '0.04em' }}>
            {label}
          </span>
          <span
            key={`v-${label}`}
            style={{ color: '#E6EDF3', overflow: 'hidden', textOverflow: 'ellipsis' }}
          >
            {value}
          </span>
        </>
      ))}
    </div>
  )
}

function formatTs(ts: string) {
  try {
    return format(parseISO(ts), 'yyyy-MM-dd HH:mm:ss')
  } catch {
    return ts
  }
}
