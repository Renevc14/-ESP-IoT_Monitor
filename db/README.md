# Esquemas de base de datos (Database per Service)

Cada microservicio tiene su **propia base de datos**; no hay un esquema compartido
ni Supabase. Los scripts SQL de cada carpeta se montan como *initdb* en el contenedor
Postgres correspondiente (`docker-compose.yml`) y se ejecutan en orden alfabético la
primera vez que arranca el volumen.

| Carpeta | Servicio dueño | Contenedor | Contenido |
|---|---|---|---|
| `db/identity/` | identity | `identity-db` (PostgreSQL 16) | `01_init.sql` (auth.users, auth.sessions, security.audit_logs) · `02_seed.sql` |
| `db/registry/` | registry | `registry-db` (PostgreSQL 16) | `01_init.sql` (iot.devices, iot.sensors) · `02_seed.sql` |
| `db/timeseries/` | processing / analytics | `timeseries-db` (TimescaleDB) | `01_init.sql` (hypertable iot.sensor_readings) · `02_policies.sql` (continuous aggregate, compresión, retención) |
| `db/alerts/` | alerts | `alerts-db` (PostgreSQL 16) | `01_init.sql` (alerts.alert_rules, alerts.alerts) · `02_seed.sql` |

Solo `timeseries-db` usa la extensión **TimescaleDB**; el resto son PostgreSQL 16
estándar. No hay claves foráneas entre bases distintas: la integridad referencial
cruzada se mantiene a nivel de aplicación (IDs UUID + composición de API).

## Arranque

No hay que ejecutar nada manualmente: `docker compose up` crea cada base y aplica
sus scripts. Para reinicializar desde cero (re-ejecutar los scripts):

```bash
docker compose down -v   # elimina los volúmenes de datos
docker compose up -d
```

> El DDL en `db/<servicio>/01_init.sql` es la **fuente de verdad** del esquema
> (no se usa Alembic); los modelos ORM de cada servicio deben reflejarlo.
