import { useState, useMemo } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table'
import { format, parseISO } from 'date-fns'
import { useGetEventsQuery, useGetEventDetailQuery } from '../app/apiSlice'
import type { SecurityEvent } from '../types'
import EventDetailDrawer from './EventDetailDrawer'

const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low', 'normal']

export default function EventLogTable() {
  const [page, setPage] = useState(1)
  const [severity, setSeverity] = useState('')
  const [attackType, setAttackType] = useState('')
  const [isAttack, setIsAttack] = useState<boolean | undefined>(undefined)
  const [searchIp, setSearchIp] = useState('')
  const [sorting, setSorting] = useState<SortingState>([{ id: 'timestamp', desc: true }])
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { data, isFetching } = useGetEventsQuery({
    page,
    page_size: 50,
    severity: severity || undefined,
    attack_type: attackType || undefined,
    is_attack: isAttack,
    source_ip: searchIp || undefined,
    ordering: sorting[0]
      ? `${sorting[0].desc ? '-' : ''}${sorting[0].id}`
      : '-timestamp',
  })

  const events = data?.data ?? []
  const meta = data?.meta

  const columns = useMemo<ColumnDef<SecurityEvent>[]>(
    () => [
      {
        accessorKey: 'timestamp',
        header: 'Timestamp',
        cell: ({ getValue }) => {
          try {
            return format(parseISO(getValue<string>()), 'yyyy-MM-dd HH:mm:ss')
          } catch {
            return getValue<string>()
          }
        },
      },
      {
        accessorKey: 'source_ip',
        header: 'Source IP',
        cell: ({ getValue }) => (
          <span style={{ color: '#8B949E' }}>{getValue<string>()}</span>
        ),
      },
      {
        accessorKey: 'http_method',
        header: 'Method',
        cell: ({ getValue }) => {
          const m = getValue<string>()
          return (
            <span style={{ color: m === 'POST' ? '#E3B341' : '#8B949E', fontWeight: 600 }}>
              {m}
            </span>
          )
        },
      },
      {
        accessorKey: 'url',
        header: 'URL',
        cell: ({ getValue }) => {
          const url = getValue<string>()
          const truncated = url.length > 50 ? url.substring(0, 50) + '…' : url
          return (
            <span title={url} style={{ color: '#E6EDF3' }}>
              {truncated}
            </span>
          )
        },
      },
      {
        accessorKey: 'attack_type',
        header: 'Attack Type',
        cell: ({ getValue }) => (
          <span style={{ color: '#8B949E', textTransform: 'uppercase', fontSize: '10px', letterSpacing: '0.04em' }}>
            {getValue<string>().replace(/_/g, ' ')}
          </span>
        ),
      },
      {
        accessorKey: 'severity',
        header: 'Severity',
        cell: ({ getValue }) => {
          const sev = getValue<string>()
          return <span className={`severity-badge ${sev}`}>{sev}</span>
        },
        sortingFn: (a, b) =>
          SEVERITY_ORDER.indexOf(a.original.severity) -
          SEVERITY_ORDER.indexOf(b.original.severity),
      },
      {
        accessorKey: 'confidence_score',
        header: 'Confidence',
        cell: ({ getValue }) => {
          const v = getValue<number>()
          const pct = (v * 100).toFixed(1)
          const color = v > 0.9 ? '#F85149' : v > 0.7 ? '#E3B341' : '#8B949E'
          return (
            <span style={{ color, fontFamily: "'JetBrains Mono', monospace" }}>
              {pct}%
            </span>
          )
        },
      },
      {
        accessorKey: 'alert_status',
        header: 'Status',
        enableSorting: false,
        cell: ({ getValue }) => {
          const s = getValue<string>()
          if (!s) return <span style={{ color: '#6E7681', fontSize: '10px' }}>—</span>
          const colors: Record<string, string> = {
            open: '#F85149',
            investigating: '#E3B341',
            resolved: '#3FB950',
            false_positive: '#6E7681',
          }
          return (
            <span
              style={{
                color: colors[s] || '#8B949E',
                fontSize: '10px',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              {s.replace(/_/g, ' ')}
            </span>
          )
        },
      },
    ],
    []
  )

  const table = useReactTable({
    data: events,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualSorting: true,
    manualPagination: true,
    pageCount: meta?.total_pages ?? 1,
  })

  return (
    <div className="card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header + Filters */}
      <div style={{ borderBottom: '1px solid #30363D', flexShrink: 0 }}>
        <div className="section-header">Event Log</div>

        <div
          style={{
            display: 'flex',
            gap: '8px',
            padding: '8px 12px',
            flexWrap: 'wrap',
            alignItems: 'center',
          }}
        >
          {/* Severity filter */}
          <select
            value={severity}
            onChange={(e) => { setSeverity(e.target.value); setPage(1) }}
            style={{
              backgroundColor: '#0D1117',
              border: '1px solid #30363D',
              color: severity ? '#E6EDF3' : '#6E7681',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '11px',
              padding: '5px 8px',
              borderRadius: '2px',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            <option value="">ALL SEVERITY</option>
            {['critical', 'high', 'medium', 'low', 'normal'].map((s) => (
              <option key={s} value={s}>
                {s.toUpperCase()}
              </option>
            ))}
          </select>

          {/* Attack type filter */}
          <select
            value={attackType}
            onChange={(e) => { setAttackType(e.target.value); setPage(1) }}
            style={{
              backgroundColor: '#0D1117',
              border: '1px solid #30363D',
              color: attackType ? '#E6EDF3' : '#6E7681',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '11px',
              padding: '5px 8px',
              borderRadius: '2px',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            <option value="">ALL TYPES</option>
            {[
              'sql_injection', 'xss', 'command_injection',
              'path_traversal', 'csrf', 'ldap_injection', 'normal'
            ].map((t) => (
              <option key={t} value={t}>
                {t.replace(/_/g, ' ').toUpperCase()}
              </option>
            ))}
          </select>

          {/* Is attack toggle */}
          <select
            value={isAttack === undefined ? '' : String(isAttack)}
            onChange={(e) => {
              setIsAttack(e.target.value === '' ? undefined : e.target.value === 'true')
              setPage(1)
            }}
            style={{
              backgroundColor: '#0D1117',
              border: '1px solid #30363D',
              color: isAttack !== undefined ? '#E6EDF3' : '#6E7681',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '11px',
              padding: '5px 8px',
              borderRadius: '2px',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            <option value="">ALL TRAFFIC</option>
            <option value="true">ATTACKS ONLY</option>
            <option value="false">NORMAL ONLY</option>
          </select>

          {/* IP search */}
          <input
            type="text"
            placeholder="FILTER BY IP..."
            value={searchIp}
            onChange={(e) => { setSearchIp(e.target.value); setPage(1) }}
            style={{
              backgroundColor: '#0D1117',
              border: '1px solid #30363D',
              color: '#E6EDF3',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '11px',
              padding: '5px 8px',
              borderRadius: '2px',
              outline: 'none',
              width: '140px',
            }}
          />

          <div style={{ flex: 1 }} />

          {/* Export buttons */}
          <button
            className="btn btn-ghost"
            style={{ padding: '5px 10px', fontSize: '10px' }}
            onClick={() => exportCSV(events)}
          >
            CSV
          </button>
          <button
            className="btn btn-ghost"
            style={{ padding: '5px 10px', fontSize: '10px' }}
            onClick={() => exportJSON(events)}
          >
            JSON
          </button>
        </div>
      </div>

      {/* Table */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <table className="data-table" style={{ minWidth: '900px' }}>
          <thead style={{ position: 'sticky', top: 0, backgroundColor: '#161B22', zIndex: 1 }}>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    style={{
                      cursor: header.column.getCanSort() ? 'pointer' : 'default',
                    }}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getIsSorted() === 'asc' ? ' ↑' : ''}
                    {header.column.getIsSorted() === 'desc' ? ' ↓' : ''}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {isFetching ? (
              <tr>
                <td
                  colSpan={columns.length}
                  style={{
                    textAlign: 'center',
                    padding: '32px',
                    color: '#6E7681',
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: '11px',
                  }}
                >
                  LOADING<span className="blink">_</span>
                </td>
              </tr>
            ) : events.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  style={{
                    textAlign: 'center',
                    padding: '32px',
                    color: '#6E7681',
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: '11px',
                  }}
                >
                  NO EVENTS MATCH FILTERS
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => setSelectedId(row.original.id)}
                  style={{ cursor: 'pointer' }}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {meta && meta.total_pages > 1 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 16px',
            borderTop: '1px solid #30363D',
            flexShrink: 0,
          }}
        >
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '10px',
              color: '#6E7681',
            }}
          >
            {meta.count.toLocaleString()} events — page {meta.page} / {meta.total_pages}
          </span>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              className="btn btn-ghost"
              style={{ padding: '4px 10px', fontSize: '10px' }}
              disabled={page === 1}
              onClick={() => setPage(1)}
            >
              «
            </button>
            <button
              className="btn btn-ghost"
              style={{ padding: '4px 10px', fontSize: '10px' }}
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
            >
              ‹
            </button>
            <button
              className="btn btn-ghost"
              style={{ padding: '4px 10px', fontSize: '10px' }}
              disabled={page === meta.total_pages}
              onClick={() => setPage((p) => p + 1)}
            >
              ›
            </button>
            <button
              className="btn btn-ghost"
              style={{ padding: '4px 10px', fontSize: '10px' }}
              disabled={page === meta.total_pages}
              onClick={() => setPage(meta.total_pages)}
            >
              »
            </button>
          </div>
        </div>
      )}

      {/* Detail Drawer */}
      {selectedId && (
        <EventDetailDrawer
          eventId={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  )
}

function exportCSV(events: SecurityEvent[]) {
  const headers = ['id', 'timestamp', 'source_ip', 'http_method', 'url', 'attack_type', 'severity', 'confidence_score']
  const rows = events.map((e) =>
    headers.map((h) => JSON.stringify((e as Record<string, unknown>)[h] ?? '')).join(',')
  )
  const csv = [headers.join(','), ...rows].join('\n')
  downloadBlob(csv, 'iwasms_events.csv', 'text/csv')
}

function exportJSON(events: SecurityEvent[]) {
  downloadBlob(JSON.stringify(events, null, 2), 'iwasms_events.json', 'application/json')
}

function downloadBlob(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
