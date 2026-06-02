import { gql } from '@apollo/client/core'
import { useQuery } from '@apollo/client/react'
import { Download } from 'lucide-react'
import { useEffect, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api/client'

const ANALYTICS_URL = import.meta.env.VITE_ANALYTICS_URL ?? 'http://localhost:8004'

const DEVICE_SUMMARY = gql`
  query AnalyticsSummary($deviceId: String!, $hours: Int!) {
    deviceSummary(deviceId: $deviceId, hours: $hours) {
      sensorType
      avgValue
      minValue
      maxValue
      p95Value
      trend
      readingCount
    }
  }
`

const BUCKETED = gql`
  query AnalyticsBuckets($deviceId: String!, $sensorType: String!, $hours: Int!, $bucketMinutes: Int!) {
    bucketedReadings(deviceId: $deviceId, sensorType: $sensorType, hours: $hours, bucketMinutes: $bucketMinutes) {
      bucket
      avgValue
      minValue
      maxValue
    }
  }
`

function autoBucket(hours: number): number {
  if (hours <= 1) return 1
  if (hours <= 6) return 5
  if (hours <= 24) return 30
  return 60
}

const SENSORS = ['temperature', 'humidity', 'energy'] as const
const AGGREGATIONS = [
  { key: 'avgValue', label: 'Promedio' },
  { key: 'minValue', label: 'Mínimo' },
  { key: 'maxValue', label: 'Máximo' },
] as const
const PERIODS = [
  { label: '6 h', hours: 6 },
  { label: '24 h', hours: 24 },
  { label: '7 d', hours: 168 },
  { label: '30 d', hours: 720 },
]

interface Device { id: string; name: string; is_active: boolean }

export default function Analytics() {
  const [devices, setDevices] = useState<Device[]>([])
  const [deviceId, setDeviceId] = useState('')
  const [sensorType, setSensorType] = useState<string>('temperature')
  const [hours, setHours] = useState(24)
  const [agg, setAgg] = useState<typeof AGGREGATIONS[number]['key']>('avgValue')

  useEffect(() => {
    api.get('/devices').then((r) => {
      const list: Device[] = r.data
      setDevices(list)
      if (list.length && !deviceId) setDeviceId(list[0].id)
    }).catch(() => {})
  }, [])

  const { data: sumData } = useQuery(DEVICE_SUMMARY, {
    variables: { deviceId, hours },
    skip: !deviceId,
  })
  const { data: bucketData } = useQuery(BUCKETED, {
    variables: { deviceId, sensorType, hours, bucketMinutes: autoBucket(hours) },
    skip: !deviceId,
  })

  const summary = ((sumData as any)?.deviceSummary ?? []).find((s: any) => s.sensorType === sensorType)
  const chartData = ((bucketData as any)?.bucketedReadings ?? []).map((r: any) => ({
    time: new Date(r.bucket).toLocaleString([], { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }),
    value: Number(r[agg]),
  }))

  function exportUrl(fmt: 'csv' | 'json') {
    const params = new URLSearchParams({ device_id: deviceId, sensor_type: sensorType, hours: String(hours) })
    return `${ANALYTICS_URL}/export/readings.${fmt}?${params.toString()}`
  }

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <h2 className="text-xl font-semibold text-white">Analytics</h2>
        <div className="flex items-center gap-2 ml-auto">
          <a href={exportUrl('csv')} className="flex items-center gap-1 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs px-3 py-1.5 rounded-lg">
            <Download size={14} /> CSV
          </a>
          <a href={exportUrl('json')} className="flex items-center gap-1 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs px-3 py-1.5 rounded-lg">
            <Download size={14} /> JSON
          </a>
        </div>
      </div>

      {/* Selectors */}
      <div className="flex flex-wrap gap-3 mb-5">
        <select value={deviceId} onChange={(e) => setDeviceId(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white">
          {devices.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <select value={sensorType} onChange={(e) => setSensorType(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white">
          {SENSORS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={agg} onChange={(e) => setAgg(e.target.value as any)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white">
          {AGGREGATIONS.map((a) => <option key={a.key} value={a.key}>{a.label}</option>)}
        </select>
        <div className="flex bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          {PERIODS.map((p) => (
            <button key={p.hours} onClick={() => setHours(p.hours)}
              className={`px-3 py-1.5 text-xs transition-colors ${hours === p.hours ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        <Stat label="Promedio" value={summary?.avgValue} />
        <Stat label="Mínimo" value={summary?.minValue} />
        <Stat label="Máximo" value={summary?.maxValue} />
        <Stat label="P95" value={summary?.p95Value} />
        <Stat label="Tendencia" value={summary?.trend} signed />
      </div>

      {/* Chart */}
      <div className="bg-slate-800 rounded-xl p-4">
        {chartData.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-slate-500 text-sm">Sin datos para el periodo seleccionado</div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} width={48} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Line type="monotone" dataKey="value" stroke="#38bdf8" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

function Stat({ label, value, signed }: { label: string; value?: number; signed?: boolean }) {
  const v = value != null ? Number(value) : null
  const color = signed && v != null ? (v >= 0 ? 'text-green-400' : 'text-red-400') : 'text-slate-100'
  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <p className={`text-2xl font-semibold ${color}`}>
        {v != null ? `${signed && v >= 0 ? '+' : ''}${v.toFixed(2)}` : '—'}
      </p>
    </div>
  )
}
