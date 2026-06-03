import { createClient, type Client } from 'graphql-ws'

const ANALYTICS_URL = import.meta.env.VITE_ANALYTICS_URL ?? 'http://localhost:8004'
const WS_URL = ANALYTICS_URL.replace(/^http/, 'ws') + '/graphql'

export interface LiveReading {
  deviceId: string
  sensorType: string
  value: number
  recordedAt: string
}

let client: Client | null = null
const statusListeners = new Set<(connected: boolean) => void>()

function emitStatus(connected: boolean) {
  statusListeners.forEach((cb) => cb(connected))
}

function getClient(): Client {
  if (!client) {
    client = createClient({
      // El token va como query param (se re-lee en cada reconexión) y el servidor
      // valida el JWT en el handshake del WebSocket.
      url: () => `${WS_URL}?token=${encodeURIComponent(sessionStorage.getItem('access_token') ?? '')}`,
      lazy: true,
      retryAttempts: 10,
      on: {
        connected: () => emitStatus(true),
        closed: () => emitStatus(false),
      },
    })
  }
  return client
}

export function onConnectionChange(cb: (connected: boolean) => void): () => void {
  statusListeners.add(cb)
  return () => statusListeners.delete(cb)
}

const READING_SUB = `
  subscription ReadingAdded($deviceId: String, $sensorType: String) {
    readingAdded(deviceId: $deviceId, sensorType: $sensorType) {
      deviceId
      sensorType
      value
      recordedAt
    }
  }
`

export function subscribeReadings(
  vars: { deviceId?: string; sensorType?: string },
  onReading: (r: LiveReading) => void,
): () => void {
  return getClient().subscribe<{ readingAdded: LiveReading }>(
    { query: READING_SUB, variables: vars },
    {
      next: (msg) => {
        const r = msg.data?.readingAdded
        if (r) onReading(r)
      },
      error: () => {},
      complete: () => {},
    },
  )
}
