import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip } from 'recharts'
import { format, parseISO } from 'date-fns'
import { useGetModelsQuery, useRetrainModelMutation } from '../app/apiSlice'
import type { MLModel } from '../types'

function GaugeChart({ value, color }: { value: number; color: string }) {
  const data = [
    { name: 'bg', value: 100, fill: '#30363D' },
    { name: 'val', value: value * 100, fill: color },
  ]

  return (
    <div style={{ width: 90, height: 90, position: 'relative' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart
          innerRadius="55%"
          outerRadius="100%"
          data={data}
          startAngle={180}
          endAngle={0}
          barSize={10}
        >
          <RadialBar dataKey="value" cornerRadius={0} isAnimationActive={false} />
          <Tooltip
            formatter={(v: number) => [`${v.toFixed(1)}%`, 'Score']}
            contentStyle={{
              backgroundColor: '#1C2128',
              border: '1px solid #30363D',
              borderRadius: '2px',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '10px',
            }}
          />
        </RadialBarChart>
      </ResponsiveContainer>
      <div
        style={{
          position: 'absolute',
          bottom: '10px',
          left: '50%',
          transform: 'translateX(-50%)',
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '14px',
          fontWeight: '700',
          color: color,
          whiteSpace: 'nowrap',
        }}
      >
        {(value * 100).toFixed(1)}
      </div>
    </div>
  )
}

function ModelCard({ model }: { model: MLModel }) {
  const [retrain, { isLoading }] = useRetrainModelMutation()

  const f1Color =
    model.f1_score > 0.9 ? '#3FB950' : model.f1_score > 0.75 ? '#E3B341' : '#F85149'

  return (
    <div
      className="card-elevated"
      style={{
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        borderLeft: model.is_active ? '2px solid #1F6FEB' : '2px solid #30363D',
      }}
    >
      {/* Name + status */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: '13px',
              fontWeight: '700',
              color: '#E6EDF3',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            {model.name.replace(/_/g, ' ')}
          </div>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '10px',
              color: '#6E7681',
              marginTop: '2px',
            }}
          >
            v{model.version}
          </div>
        </div>
        {model.is_active && (
          <span
            style={{
              backgroundColor: 'rgba(31,111,235,0.15)',
              border: '1px solid rgba(31,111,235,0.4)',
              color: '#58A6FF',
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: '9px',
              fontWeight: '600',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              padding: '2px 8px',
              borderRadius: '2px',
            }}
          >
            ACTIVE
          </span>
        )}
      </div>

      {/* Gauge + metrics */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <GaugeChart value={model.f1_score} color={f1Color} />

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '8px 16px',
            flex: 1,
          }}
        >
          {[
            ['F1 Score', `${(model.f1_score * 100).toFixed(1)}%`],
            ['AUC-ROC', `${(model.auc_roc * 100).toFixed(1)}%`],
            ['Accuracy', `${(model.accuracy * 100).toFixed(1)}%`],
            ['FP Rate', `${(model.false_positive_rate * 100).toFixed(2)}%`],
            ['Samples', model.trained_on_samples.toLocaleString()],
            [
              'Trained',
              (() => {
                try {
                  return format(parseISO(model.created_at), 'MM/dd HH:mm')
                } catch {
                  return '—'
                }
              })(),
            ],
          ].map(([label, value]) => (
            <div key={label}>
              <div
                style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontSize: '9px',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: '#6E7681',
                  marginBottom: '2px',
                }}
              >
                {label}
              </div>
              <div
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '13px',
                  fontWeight: '600',
                  color: '#E6EDF3',
                }}
              >
                {value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Retrain button */}
      <button
        className="btn btn-ghost"
        style={{ width: '100%' }}
        onClick={() => retrain(model.id)}
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            RETRAINING<span className="blink">_</span>
          </>
        ) : (
          'RETRAIN MODEL'
        )}
      </button>
    </div>
  )
}

export default function ModelPerformancePanel() {
  const { data, isLoading } = useGetModelsQuery()
  const models: MLModel[] = Array.isArray(data?.data) ? (data!.data as unknown as MLModel[]) : []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
      <div className="section-header" style={{ margin: 0 }}>
        Model Performance
      </div>

      {isLoading ? (
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
          LOADING<span className="blink">_</span>
        </div>
      ) : models.length === 0 ? (
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '12px',
            color: '#6E7681',
          }}
        >
          <span>NO TRAINED MODELS</span>
          <span style={{ fontSize: '10px', color: '#30363D' }}>
            Run: make train
          </span>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflow: 'auto' }}>
          {models.map((model) => (
            <ModelCard key={model.id} model={model} />
          ))}
        </div>
      )}
    </div>
  )
}
