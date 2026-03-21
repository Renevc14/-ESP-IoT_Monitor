-- ============================================================
-- Migration 03: IoT devices + sensor readings (TimescaleDB hypertable)
-- ============================================================

CREATE TYPE iot.device_type AS ENUM ('temperature_sensor', 'humidity_sensor', 'energy_meter', 'multi_sensor');
CREATE TYPE iot.sensor_type AS ENUM ('temperature', 'humidity', 'energy');

CREATE TABLE iot.devices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL,
    device_type     iot.device_type NOT NULL DEFAULT 'multi_sensor',
    location        VARCHAR(255),
    auth_token_hash TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_devices_is_active ON iot.devices (is_active);

-- sensor_readings: TimescaleDB hypertable
-- NOTE: Do NOT add a PRIMARY KEY constraint on (id) alone when using hypertables
--       with time partitioning — include recorded_at in the PK if needed.
CREATE TABLE iot.sensor_readings (
    id          BIGSERIAL,
    device_id   UUID NOT NULL REFERENCES iot.devices(id),
    sensor_type iot.sensor_type NOT NULL,
    value       DECIMAL(10, 4) NOT NULL,
    unit        VARCHAR(20) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, recorded_at)
);

CREATE INDEX idx_sensor_readings_device_time ON iot.sensor_readings (device_id, recorded_at DESC);
CREATE INDEX idx_sensor_readings_sensor_type ON iot.sensor_readings (sensor_type, recorded_at DESC);

-- Convert to TimescaleDB hypertable partitioned weekly
SELECT create_hypertable(
    'iot.sensor_readings',
    'recorded_at',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);
