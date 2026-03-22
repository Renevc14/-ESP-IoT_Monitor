import { gql } from '@apollo/client/core'
import { useQuery } from '@apollo/client/react'
import { useEffect, useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api/client'

// ── GraphQL queries ────────────────────────────────────────────────────────────

const DEVICE_SUMMARY = gql`
  query DeviceSummary($deviceId: String!, $hours: Int!) {
    deviceSummary(deviceId: $deviceId, hours: $hours) {
      sensorType
      readingCount
      minValue
      maxValue
      avgValue
    }
  }
`

const BUCKETED_READINGS = gql`
  query BucketedReadings($deviceId: String!, $sensorType: String!, $hours: Int!, $bucketMinutes: Int!) {
    bucketedReadings(deviceId: $deviceId, sensorType: $sensorType, hours: $hours, bucketMinutes: $bucketMinutes) {
      bucket
      avgValue
      minValue
      maxValue
      readingCount
    }
  }
`

// Auto-select bucket size to keep ~50-80 points on the chart regardless of window
function autoBucket(hours: number): number {
  if (hours <= 1)  return 1
  if (hours <= 6)  return 5
  if (hours <= 24) return 30
  return 60
}

// ── Types & constants ──────────────────────────────────────────────────────────

interface Device {
  id: string
  name: string
  device_type: string
  is_active: boolean
}

const SENSOR_META: Record<string, { color: string; unit: string; label: string }> = {
  temperature: { color: '#f97316', unit: '°C', label: 'Temperature' },
  humidity:    { color: '#38bdf8', unit: '%',  label: 'Humidity'    },
  energy:      { color: '#4ade80', unit: ' kW', label: 'Power'     },
}

const TIME_OPTIONS = [
  { label: '1 h',  hours: 1  },
  { label: '6 h',  hours: 6  },
  { label: '24 h', hours: 24 },
  { label: '48 h', hours: 48 },
]

// ── Sub-components ─────────────────────────────────────────────────────────────

function StatCard({ label, value, unit, color }: { label: string; value: number | null | undefined; unit: string; color: string }) {
  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <p className={`text-2xl font-semibold ${color}`}>
        {value != null ? `${Number(value).toFixed(1)}${unit}` : '—'}
      </p>
    </div>
  )
}

function ReadingsChart({ deviceId, sensorType, color, unit, hours }: { deviceId: string; sensorType: string; color: string; unit: string; hours: number }) {
  const bucketMinutes = autoBucket(hours)
  const { data, loading } = useQuery(BUCKETED_READINGS, {
    variables: { deviceId, sensorType, hours, bucketMinutes },
    pollInterval: 30000,
  })

  const fmtTime = (iso: string) => {
    const d = new Date(iso)
    if (hours <= 6)  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    if (hours <= 24) return d.toLocaleString([], { weekday: 'short', hour: '2-digit', minute: '2-digit' })
    return d.toLocaleString([], { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  }

  const chartData = ((data as any)?.bucketedReadings ?? []).map((r: any) => ({
    time: fmtTime(r.bucket),
    value: Number(r.avgValue),
    min: Number(r.minValue),
    max: Number(r.maxValue),
  }))

  if (loading && chartData.length === 0) {
    return <div className="h-44 flex items-center justify-center text-slate-500 text-sm">Loading…</div>
  }
  if (!loading && chartData.length === 0) {
    return <div className="h-44 flex items-center justify-center text-slate-500 text-sm">No readings yet</div>
  }

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
        <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} unit={unit} width={48} />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#94a3b8' }}
          itemStyle={{ color }}
          formatter={(v: any) => [`${Number(v).toFixed(2)}${unit}`, 'avg']}
        />
        <Line type="monotone" dataKey="value" stroke={color} dot={false} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [devices, setDevices] = useState<Device[]>([])
  const [selectedId, setSelectedId] = useState<string>('')
  const [hours, setHours] = useState(24)

  useEffect(() => {
    api.get('/devices').then((r) => {
      const active: Device[] = r.data.filter((d: Device) => d.is_active)
      setDevices(active)
      if (active.length > 0 && !selectedId) setSelectedId(active[0].id)
    }).catch(() => {})
  }, [])

  const { data: summaryData } = useQuery(DEVICE_SUMMARY, {
    variables: { deviceId: selectedId, hours },
    skip: !selectedId,
    pollInterval: 30000,
  })

  const summaries: any[] = (summaryData as any)?.deviceSummary ?? []
  const tempSummary = summaries.find((s) => s.sensorType === 'temperature')
  const activeSensors = summaries.map((s) => s.sensorType)

  const selectedDevice = devices.find((d) => d.id === selectedId)

  return (
    <div>
      {/* ── Header + filters ── */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <h2 className="text-xl font-semibold text-white">Dashboard</h2>

        <div className="flex items-center gap-2 ml-auto">
          {/* Device selector */}
          <select
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
          >
            {devices.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>

          {/* Time window */}
          <div className="flex bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
            {TIME_OPTIONS.map((opt) => (
              <button
                key={opt.hours}
                onClick={() => setHours(opt.hours)}
                className={`px-3 py-1.5 text-xs transition-colors ${
                  hours === opt.hours
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Summary cards (temperature stats for selected device) ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard label="Avg Temp" value={tempSummary?.avgValue} unit="°C" color="text-orange-400" />
        <StatCard label="Min Temp" value={tempSummary?.minValue} unit="°C" color="text-blue-400" />
        <StatCard label="Max Temp" value={tempSummary?.maxValue} unit="°C" color="text-red-400" />
        <div className="bg-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-400 mb-1">Readings ({hours}h)</p>
          <p className="text-2xl font-semibold text-slate-100">
            {summaries.reduce((acc, s) => acc + s.readingCount, 0) || '—'}
          </p>
        </div>
      </div>

      {/* ── Charts ── */}
      {!selectedId ? (
        <p className="text-slate-400 text-sm">No devices available</p>
      ) : activeSensors.length === 0 ? (
        <div className="bg-slate-800 rounded-xl p-8 text-center text-slate-400 text-sm">
          No readings for <span className="text-white">{selectedDevice?.name}</span> in the last {hours}h
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {activeSensors.map((sensor) => {
            const meta = SENSOR_META[sensor] ?? { color: '#a78bfa', unit: '', label: sensor }
            return (
              <div key={`${selectedId}-${sensor}-${hours}`} className="bg-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-sm font-medium text-white">{selectedDevice?.name}</p>
                    <p className="text-xs text-slate-400">{meta.label}</p>
                  </div>
                  <span className="text-xs text-slate-500">last {hours}h · auto-refresh 10s</span>
                </div>
                <ReadingsChart
                  deviceId={selectedId}
                  sensorType={sensor}
                  color={meta.color}
                  unit={meta.unit}
                  hours={hours}
                />
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
