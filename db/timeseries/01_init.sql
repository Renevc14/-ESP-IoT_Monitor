-- ============================================================
-- timeseries-db: lecturas de sensores (processing escribe, analytics lee)
-- TimescaleDB hypertable. device_id es UUID sin FK (los dispositivos viven en registry-db).
-- ============================================================
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE SCHEMA IF NOT EXISTS iot;

CREATE TYPE iot.sensor_type AS ENUM ('temperature', 'humidity', 'energy');

CREATE TABLE iot.sensor_readings (
    id          BIGSERIAL,
    device_id   UUID NOT NULL,
    sensor_type iot.sensor_type NOT NULL,
    value       DECIMAL(10, 4) NOT NULL,
    unit        VARCHAR(20) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, recorded_at)
);

CREATE INDEX idx_sensor_readings_device_time ON iot.sensor_readings (device_id, recorded_at DESC);
CREATE INDEX idx_sensor_readings_sensor_type ON iot.sensor_readings (sensor_type, recorded_at DESC);

SELECT create_hypertable('iot.sensor_readings', 'recorded_at',
    chunk_time_interval => INTERVAL '1 week', if_not_exists => TRUE);
