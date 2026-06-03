-- ============================================================
-- alerts-db: reglas de alerta + alertas (servicio alerts, contexto de alertado)
-- device_id / acknowledged_by son UUID sin FK (viven en registry-db / identity-db).
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE SCHEMA IF NOT EXISTS iot;
CREATE SCHEMA IF NOT EXISTS alerts;

-- sensor_type se replica aquí (cada BD es independiente)
CREATE TYPE iot.sensor_type AS ENUM ('temperature', 'humidity', 'energy');
CREATE TYPE alerts.severity_level AS ENUM ('warning', 'critical');
CREATE TYPE alerts.alert_status AS ENUM ('active', 'acknowledged', 'resolved');
CREATE TYPE alerts.rule_operator AS ENUM ('gt', 'lt', 'gte', 'lte');

CREATE TABLE alerts.alert_rules (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id           UUID NOT NULL,
    sensor_type         iot.sensor_type NOT NULL,
    operator            alerts.rule_operator NOT NULL,
    threshold           DECIMAL(10, 4) NOT NULL,
    severity            alerts.severity_level NOT NULL,
    notification_emails TEXT[] NOT NULL DEFAULT '{}',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_alert_rules_device ON alerts.alert_rules (device_id, sensor_type, is_active);

CREATE TABLE alerts.alerts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id         UUID NOT NULL REFERENCES alerts.alert_rules(id),
    device_id       UUID NOT NULL,
    triggered_value DECIMAL(10, 4) NOT NULL,
    severity        alerts.severity_level NOT NULL,
    status          alerts.alert_status NOT NULL DEFAULT 'active',
    acknowledged_by UUID,
    acknowledged_at TIMESTAMPTZ,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_alerts_status ON alerts.alerts (status, created_at DESC);
CREATE INDEX idx_alerts_device ON alerts.alerts (device_id, created_at DESC);
