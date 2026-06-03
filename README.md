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
[postgres-timescale]  [Redis :6379]
PostgreSQL 16          Cache · Rate limiting
+ TimescaleDB
  (contenedor local)
```

### Containers (10 total)

| Container | Port | Description |
|-----------|------|-------------|
| `gateway` | 8000 | API Gateway — JWT auth, RBAC, routing, rate limiting, security headers, audit |
| `ingestion` | 8001 | IoT data ingestion — validates and publishes to RabbitMQ |
| `processing` | 8002 | Event consumer — stores readings in TimescaleDB + Redis |
| `alerts` | 8003 | Alert engine — threshold evaluation + WebSocket + email (SMTP) |
| `analytics` | 8004 | GraphQL API (Strawberry) + CSV/JSON export |
| `frontend` | 80 | React dashboard — charts, alerts, devices, analytics, users |
| `postgres-timescale` | 5432 | PostgreSQL 16 + TimescaleDB — migrations auto-aplicadas al primer arranque |
| `rabbitmq` | 5672/15672 | Message broker — fanout exchange `sensor_data_exchange` |
| `redis` | 6379 | Cache (latest readings) + rate limiting sliding window |
| `mailhog` | 1025/8025 | SMTP de demostración para notificaciones de alertas (UI en :8025) |

**Database**: contenedor local `postgres-timescale` por defecto. `DATABASE_URL` puede apuntarse a Timescale Cloud (externo) sin más cambios.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend services | FastAPI (Python 3.12) |
| Messaging | RabbitMQ 3.13, AMQP, fanout exchange |
| Database | PostgreSQL 16 + TimescaleDB hypertable (contenedor local, override-able a Timescale Cloud) |
| Cache | Redis 7 |
| GraphQL | Strawberry 0.261.1 (Python) |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + Recharts + Apollo Client |
| Auth | JWT HS256 · bcrypt (passlib) · RBAC (admin/operator/viewer) |
| Containers | Docker + Docker Compose v2 |

---

## Quickstart

### Prerequisites

- Docker + Docker Compose v2
- Node.js 20 (solo para desarrollo local del frontend)

> No se requiere base de datos externa: el contenedor `postgres-timescale` se incluye en el stack y ejecuta las migraciones `db/migrations/01–06` automáticamente al primer arranque (volumen `pg-data`).

### 1. Configure environment

```bash
cp .env.example .env
# Genera un JWT_SECRET_KEY:  openssl rand -hex 32
# (Opcional) Para usar Timescale Cloud, descomenta y ajusta DATABASE_URL en .env
```

### 2. Start the whole stack (one command)

```bash
docker compose up --build -d
# Con simulador incluido:
docker compose --profile simulator up --build -d
```

El esquema y los datos de ejemplo (usuarios, dispositivos, reglas) se crean solos en el primer arranque.

### 3. Verify all services

```bash
docker compose ps
# http://localhost:8000/docs     → Gateway API docs (Swagger/OpenAPI)
# http://localhost:8004/graphql  → GraphQL playground
# http://localhost:8025          → MailHog (bandeja de emails de alerta)
# http://localhost:15672         → RabbitMQ Management (guest/guest)
# http://localhost               → Frontend dashboard
```

### 4. IoT simulator (perfil opcional)

```bash
# Modo continuo (clima real de Cochabamba vía Open-Meteo, cada 60s)
docker compose --profile simulator up -d simulator

# Modo demo (guión: normal → anomalía → recuperación) — dispara alertas + emails
MODE=demo docker compose --profile simulator up simulator
```

---

## API Reference

### Gateway (`:8000`)

#### Authentication
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/login` | Login → access token (body) + refresh token en **cookie HttpOnly** + perfil | Public |
| POST | `/auth/refresh` | Rota el refresh token (lee la cookie HttpOnly o el body) | Cookie/Refresh |
| POST | `/auth/logout` | Borra la cookie de refresh | Public |
| POST | `/auth/forgot-password` | Envía enlace de recuperación por email | Public |
| POST | `/auth/reset-password` | Restablece la contraseña con el token del email | Token |
| GET | `/users/me` | Current user profile | Any role |

#### Users / Admin
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/users` | List users | admin |
| POST | `/users` | Create user with role | admin |
| PATCH | `/users/{id}` | Update role / active / name | admin |
| GET | `/audit-logs` | Eventos de auditoría (OWASP A09) | admin |
| GET | `/system/health` | Estado de salud de los 5 servicios | operator+ |

#### Devices
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/devices` | List all devices | operator+ |
| POST | `/devices` | Registrar dispositivo; el token se autogenera y se devuelve **una sola vez** (HU-05) | admin |
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
| PATCH | `/alerts/{id}/resolve` | Resolve alert | operator+ |

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
  readings(deviceId: String, sensorType: String, limit: Int, hours: Int): [SensorReadingType!]!
  # avg/min/max + percentil 95 + tendencia (cambio neto) por tipo de sensor
  deviceSummary(deviceId: String!, hours: Int!): [DeviceSummaryType!]!
  alertSummary: AlertSummaryType!
  devices(isActive: Boolean): [DeviceType!]!
  alerts(deviceId: String, status: String, limit: Int): [AlertType!]!
  # agregación temporal con time_bucket() de TimescaleDB
  bucketedReadings(deviceId: String!, sensorType: String!, hours: Int, bucketMinutes: Int): [BucketedReadingType!]!
}

type Subscription {
  # Streaming de lecturas en tiempo real vía WebSocket (graphql-ws)
  readingAdded(deviceId: String, sensorType: String): SensorReadingType!
}
```

#### Export (REST, `:8004`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/export/readings.csv` | Lecturas en CSV (filtros `device_id`, `sensor_type`, `hours`, `limit`) |
| GET | `/export/readings.json` | Lecturas en JSON (mismos filtros) |

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
| A02 — Cryptographic Failures | Credenciales/tokens **no se guardan en claro**: contraseñas con bcrypt, refresh tokens con SHA-256, tokens de dispositivo con bcrypt. TLS 1.3 en despliegue de producción (ver nota abajo). |
| A03 — Injection | SQLAlchemy ORM — zero raw SQL string interpolation |
| A05 — Security Misconfiguration | Restrictive CORS · per-IP rate limiting (Redis) · security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy) |
| A07 — Auth Failures | Rotación de refresh en cada `/auth/refresh` · access 15min / refresh 7d · **refresh en cookie HttpOnly** |
| A09 — Logging Failures | Login OK/fallido, refresh, accesos denegados (403) y CRUD registrados en `security.audit_logs` (consultables en `/audit-logs` y la vista **Logs**) |

> **Nota TLS 1.3 / cifrado en reposo (A02, RNF-05):** en el entorno local de desarrollo el tráfico es HTTP (el documento, Cap. 5.2.4, acota OWASP a desarrollo). Las credenciales y tokens **ya se almacenan cifrados/hasheados** (no hay datos sensibles en claro). Para producción se documenta TLS 1.3 (reverse proxy) y cifrado de disco/columna; `COOKIE_SECURE=true` activa la cookie segura sobre HTTPS.

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
  alert_rules     UUID PK · device_id FK · sensor_type · operator(gt/lt/gte/lte) · threshold · severity · notification_emails[] · is_active
  alerts          UUID PK · rule_id FK · device_id FK · triggered_value · severity · status(active/acknowledged/resolved) · acknowledged_at · resolved_at · created_at

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
│   └── migrations/   # SQL 01–06 — auto-montadas en postgres-timescale al primer arranque
├── tests/            # Integration tests (pytest + httpx)
├── .github/workflows/ci.yml   # CI: unit (por servicio) + integración (stack completo)
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

### Tests & CI

```bash
# Pruebas unitarias por servicio (lógica de auth, evaluación de alertas, export)
cd gateway   && pip install -r requirements.txt pytest pytest-asyncio pytest-cov && pytest --cov=app
cd alerts    && pip install -r requirements.txt pytest pytest-asyncio pytest-cov && pytest --cov=app
cd analytics && pip install -r requirements.txt pytest pytest-asyncio pytest-cov && pytest --cov=app

# Pruebas de integración (3 escenarios obligatorios) contra el stack en ejecución
pip install -r tests/requirements.txt && pytest tests/ -v
```

Cada servicio aplica un **umbral de cobertura ≥80%** (`.coveragerc fail_under=80`) sobre su lógica de negocio.

```bash
# Prueba de carga del servicio de ingesta (RNF-01)
pip install httpx && python tests/load/load_test.py
```

GitHub Actions ejecuta en cada push/PR (`.github/workflows/ci.yml`): (1) pruebas unitarias por servicio con cobertura (gate 80%) y (2) pruebas de integración levantando el stack completo con Docker Compose. Adicionalmente, `.github/workflows/security-scan.yml` corre un **OWASP ZAP Baseline** (RNF-04) de forma manual/semanal contra el gateway.

> **Nota de rendimiento (RNF-01):** la herramienta de carga se incluye en `tests/load/`. El throughput medido en un host local con Docker Desktop (Windows) está limitado por el entorno; el objetivo de ≥1000 evt/s aplica a un despliegue escalado (Linux + múltiples instalaciones de consumidores, ver Cap. 14), que la arquitectura fanout + competing consumers soporta sin cambios en el productor.

---

## Deuda técnica conocida / Evolución

**API Gateway con responsabilidades de dominio (acoplamiento).** Actualmente el Gateway, además de enrutar/autenticar/limitar, **es dueño de la lógica** de usuarios, dispositivos y reglas de alerta, escribiendo directamente en los esquemas `auth`, `iot` y `alerts`.

- *Por qué es un punto a mejorar:* un API Gateway "puro" debería solo enrutar y delegar; al contener lógica de varios dominios se acopla a múltiples esquemas y dificulta el escalado/propiedad independiente de datos (relacionado con la decisión de instancia de BD compartida con esquemas por dominio, Cap. 8.2).
- *Por qué se mantiene así:* es una decisión pragmática y suficiente para el alcance académico local; el documento la contempla como **evolución** (Cap. 14).
- *Propuesta de solución (trabajo futuro):* extraer un **servicio de dominio** (p. ej. `registry`/`identity`) dueño de usuarios/dispositivos/reglas con su propia base; el Gateway pasaría a hacer solo *proxy* autenticado hacia ese servicio (como ya hace con `alerts`/`analytics`). Es una reestructuración, no una corrección, por lo que se difiere conscientemente.

> Otras mejoras ya aplicadas en esta etapa: autenticación en los WebSockets, `publisher_confirms` configurable (garantía de entrega por defecto), colas exclusivas por instancia para suscripciones escalables, e imágenes Docker fijadas por digest.

---

## License

Academic project — Universidad Católica Boliviana "San Pablo" 2026
