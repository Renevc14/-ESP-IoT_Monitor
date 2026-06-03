-- ============================================================
-- registry-db: catálogo de dispositivos (servicio registry)
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE SCHEMA IF NOT EXISTS iot;

CREATE TYPE iot.device_type AS ENUM ('temperature_sensor', 'humidity_sensor', 'energy_meter', 'multi_sensor');

CREATE TABLE iot.devices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL,
    device_type     iot.device_type NOT NULL DEFAULT 'multi_sensor',
    location        VARCHAR(255),
    auth_token_hash TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_devices_is_active ON iot.devices (is_active);
