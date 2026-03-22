# IoT Monitoring Platform

**Plataforma Full Stack de Monitoreo y Análisis de Datos IoT en Tiempo Real**
Basada en Arquitectura de Microservicios, GraphQL y Seguridad OWASP

> Proyecto Final de Especialidad — UCB "San Pablo" · Arquitectura y Desarrollo de Software Avanzado

---

## Architecture

```
Users / IoT Simulator
         │
         ▼ HTTP
    ┌─────────────┐
    │ API Gateway │  :8000  JWT Auth · RBAC · Rate Limiting (Redis)
    └──────┬──────┘
           │
    ┌──────┼────────────────────┐
    ▼      ▼                    ▼
┌──────────────┐  ┌─────────────────┐  ┌──────────────────────┐
│  Ingestion   │  │   Analytics     │  │       Alerts         │
│   :8001      │  │   :8004         │  │       :8003          │
│  FastAPI     │  │  Strawberry     │  │  Threshold Engine    │
│  REST ingest │  │  GraphQL API    │  │  WebSocket broadcast │
└──────┬───────┘  └─────────────────┘  └──────────┬───────────┘
       │                                            ▲
       ▼                                            │
  [RabbitMQ] ──── fanout exchange ─────────────────┘
  sensor_data_exchange                 (alerts_queue)
       │
       │ (processing_queue)
       ▼
┌──────────────┐
│  Processing  │
│   :8002      │
│  Consumer    │
└──────┬───────┘
       │
  ┌────┴──────────┐
  ▼               ▼
[Timescale Cloud]  [Redis :6379]
PostgreSQL 16      Cache · Rate limiting
+ TimescaleDB
  (external)
```

### Containers (8 total)

| Container | Port | Description |
|-----------|------|-------------|
| `gateway` | 8000 | API Gateway — JWT auth, RBAC, routing, rate limiting |
| `ingestion` | 8001 | IoT data ingestion — validates and publishes to RabbitMQ |
| `processing` | 8002 | Event consumer — stores readings in TimescaleDB + Redis |
| `alerts` | 8003 | Alert engine — threshold evaluation + WebSocket feed |
| `analytics` | 8004 | GraphQL API (Strawberry) — historical queries and statistics |
| `frontend` | 80 | React 18 dashboard — charts, alerts, device management |
| `rabbitmq` | 5672/15672 | Message broker — fanout exchange `sensor_data_exchange` |
| `redis` | 6379 | Cache (latest readings) + rate limiting sliding window |

**Database**: Timescale Cloud (external) — PostgreSQL 16 + TimescaleDB extension

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend services | FastAPI (Python 3.12) |
| Messaging | RabbitMQ 3.13, AMQP, fanout exchange |
| Database | Timescale Cloud (PostgreSQL 16 + TimescaleDB hypertable) |
| Cache | Redis 7 |
| GraphQL | Strawberry 0.261.1 (Python) |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + Recharts + Apollo Client |
| Auth | JWT HS256 · bcrypt (passlib) · RBAC (admin/operator/viewer) |
| Containers | Docker + Docker Compose v2 |

---

## Quickstart

### Prerequisites

- Docker + Docker Compose v2
- A [Timescale Cloud](https://cloud.timescale.com) service (PostgreSQL 16 + TimescaleDB)
- Node.js 20 (for local frontend development only)

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env — set your Timescale Cloud DATABASE_URL and JWT_SECRET_KEY
```

### 2. Run database migrations

Connect to your Timescale Cloud service and execute the scripts in order:

```bash
# Using psql with your Timescale Cloud connection string:
psql "$DATABASE_URL" -f db/migrations/01_schemas.sql
psql "$DATABASE_URL" -f db/migrations/02_auth_tables.sql
psql "$DATABASE_URL" -f db/migrations/03_iot_tables.sql
psql "$DATABASE_URL" -f db/migrations/04_alerts_tables.sql
psql "$DATABASE_URL" -f db/migrations/05_security_tables.sql
psql "$DATABASE_URL" -f db/migrations/06_seed_data.sql
```

See `db/README.md` for detailed instructions.

### 3. Start services

```bash
docker compose up --build -d
```

### 4. Verify all services

```bash
docker compose ps
# http://localhost:8000/docs     → Gateway API docs (Swagger)
# http://localhost:8004/graphql  → GraphQL playground
# http://localhost:15672         → RabbitMQ Management (guest/guest)
# http://localhost               → Frontend dashboard
```

### 5. Run the IoT simulator

```bash
# Continuous mode (real Cochabamba weather, every 60s)
docker run --rm --network <project>_default \
  -e GATEWAY_URL=http://gateway:8000 \
  -e INGESTION_URL=http://ingestion:8001 \
  -e MODE=continuous -e INTERVAL=60 \
  <project>-simulator

# Demo mode (scripted: normal → anomaly → recovery)
docker run --rm --network <project>_default \
  -e GATEWAY_URL=http://gateway:8000 \
  -e INGESTION_URL=http://ingestion:8001 \
  -e MODE=demo \
  <project>-simulator
```

---

## API Reference

### Gateway (`:8000`)

#### Authentication
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/login` | Login → access token + refresh token + user profile | Public |
| POST | `/auth/refresh` | Rotate refresh token | Refresh token |
| GET | `/users/me` | Current user profile | Any role |

#### Devices
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/devices` | List all devices | operator+ |
| POST | `/devices` | Register new device (token bcrypt-hashed) | admin |
| GET | `/devices/{id}` | Device detail | operator+ |
| PATCH | `/devices/{id}` | Update name, location, active status | admin |
| DELETE | `/devices/{id}` | Delete device | admin |

#### Alert Rules
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/alert-rules` | List rules, optional `?device_id=` filter | operator+ |
| POST | `/alert-rules` | Create rule for a device | admin |
| PATCH | `/alert-rules/{id}` | Update threshold, severity, or active status | admin |
| DELETE | `/alert-rules/{id}` | Delete rule | admin |

#### Alerts
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/alerts` | List alerts, optional `?status=` filter | operator+ |
| PATCH | `/alerts/{id}/acknowledge` | Acknowledge alert | operator+ |

### Ingestion (`:8001`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/ingest/reading` | Submit sensor reading → RabbitMQ | Bearer token |
| GET | `/health` | Service health check | Public |

### Alerts (`:8003`)

| Protocol | Endpoint | Description |
|----------|----------|-------------|
| WebSocket | `/ws/alerts` | Real-time alert stream (no auth required) |
| GET | `/alerts` | List alerts | Public |
| PATCH | `/alerts/{id}/acknowledge` | Acknowledge alert | Bearer token |

### Analytics — GraphQL (`:8004/graphql`)

```graphql
type Query {
  # Last N readings for a device and sensor type
  readings(deviceId: String!, sensorType: String!, limit: Int): [SensorReadingType!]!

  # Aggregate statistics per sensor type for a device over the last N hours
  deviceSummary(deviceId: String!, hours: Int!): [DeviceSummaryType!]!

  # Alert counts grouped by severity and status
  alertSummary: [AlertSummaryType!]!
}
```

---

## Sensor Models & Alert Thresholds

Three simulated outdoor stations in Cochabamba, Bolivia (real weather from Open-Meteo):

| Device | Sensors | Model |
|--------|---------|-------|
| Server Room Sensor (001) | temperature, humidity | Outdoor air + sensor noise |
| Office Climate Sensor (002) | temperature, humidity | +1.5°C microclimate offset (Zona Norte) |
| UPS Energy Monitor (003) | energy (kW, signed) | Solar panel: `(irradiance × 10m² × 20%) / 1000 − 0.15 kW` |

**Alert thresholds per device (configurable via API):**

| Sensor | Warning | Critical |
|--------|---------|----------|
| Temperature (°C) | >35 / <15 | >40 / <10 |
| Humidity (%) | >80 / <30 | >90 / <20 |
| Energy (kW, signed) | < −2.0 (deep discharge) | < −3.0 (fault) |

---

## RBAC Roles

| Role | Permissions |
|------|------------|
| `admin` | Full access — device CRUD, alert rules, user management |
| `operator` | Read all + acknowledge alerts + submit readings |
| `viewer` | Read-only access to devices, readings, alerts |

**Default credentials** (seeded by `06_seed_data.sql`):
- Admin: `admin@iot.local` / `Admin1234!`
- Operator: `operator@iot.local` / `Operator1234!`

---

## Security (OWASP Top Ten)

| Control | Implementation |
|---------|---------------|
| A01 — Broken Access Control | RBAC via FastAPI `Depends` on every endpoint |
| A02 — Cryptographic Failures | bcrypt (passlib) for passwords · JWT HS256 · TLS in production |
| A03 — Injection | SQLAlchemy ORM — zero raw SQL string interpolation |
| A05 — Security Misconfiguration | Restrictive CORS · per-IP rate limiting (Redis sliding window) |
| A07 — Auth Failures | JWT rotation on every `/auth/refresh` · 15min access / 7day refresh |
| A09 — Logging Failures | All auth events logged in `security.audit_logs` |

---

## Database Schema

```
Schema: auth
  users           UUID PK · email · password_hash · role(admin/operator/viewer) · full_name · is_active
  sessions        UUID PK · user_id FK · refresh_token_hash · expires_at

Schema: iot
  devices         UUID PK · name · device_type · location · auth_token_hash · is_active
  sensor_readings BIGSERIAL PK · device_id FK · sensor_type · value · unit · recorded_at
                  → TimescaleDB hypertable (weekly chunks on recorded_at)

Schema: alerts
  alert_rules     UUID PK · device_id FK · sensor_type · operator(gt/lt/gte/lte) · threshold · severity · is_active
  alerts          UUID PK · rule_id FK · device_id FK · triggered_value · severity · status(active/acknowledged/resolved) · created_at

Schema: security
  audit_logs      BIGSERIAL PK · user_id FK · action · resource · ip · details JSONB · created_at
```

---

## Project Structure

```
.
├── gateway/          # API Gateway — auth, RBAC, routing, rate limiting, proxy
│   ├── app/
│   └── Dockerfile
├── ingestion/        # IoT data ingestion service
│   ├── app/
│   └── Dockerfile
├── processing/       # RabbitMQ consumer — TimescaleDB + Redis writer
│   ├── app/
│   └── Dockerfile
├── alerts/           # Alert engine + WebSocket broadcaster
│   ├── app/
│   └── Dockerfile
├── analytics/        # GraphQL API (Strawberry)
│   ├── app/
│   └── Dockerfile
├── frontend/         # React 18 dashboard (Vite + Tailwind + Recharts)
│   ├── src/
│   └── Dockerfile
├── simulator/        # IoT device simulator — real Cochabamba weather (Open-Meteo)
├── db/
│   └── migrations/   # SQL scripts 01–06 — run against Timescale Cloud in order
├── tests/            # Integration tests (pytest + httpx)
├── docker-compose.yml
└── .env.example
```

---

## Development

```bash
# View all container logs
docker compose logs -f

# Follow a specific service
docker compose logs -f gateway

# Restart one service (resilience test)
docker compose restart ingestion

# Run integration tests (stack must be running)
cd tests && pip install -r requirements.txt && pytest -v
```

---

## License

Academic project — Universidad Católica Boliviana "San Pablo" 2026
