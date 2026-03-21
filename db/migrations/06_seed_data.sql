-- ============================================================
-- Migration 06: Seed data
-- Default users (passwords: Admin1234! / Operator1234!)
-- 3 sample devices with default alert rules
-- ============================================================

-- ── Users ────────────────────────────────────────────────────
INSERT INTO auth.users (id, email, password_hash, role, full_name) VALUES
(
    'a0000000-0000-0000-0000-000000000001',
    'admin@iot.local',
    '$2b$12$KZ/UFmLsg4zg724B0p8ETeumDMlfia8PB2hv0mz9NV9.24HHYury.',
    'admin',
    'System Administrator'
),
(
    'a0000000-0000-0000-0000-000000000002',
    'operator@iot.local',
    '$2b$12$zf4i8RuMUMrA5P6msQXBjOmMhI/icbXOfMPIIn4urUtmD1kZWOwQK',
    'operator',
    'IoT Operator'
)
ON CONFLICT (email) DO NOTHING;

-- ── Devices ──────────────────────────────────────────────────
-- auth_token_hash is bcrypt of the raw token; devices use these tokens to call /ingest/reading
-- For testing, raw tokens: device-token-001, device-token-002, device-token-003
INSERT INTO iot.devices (id, name, device_type, location, auth_token_hash) VALUES
(
    'd0000000-0000-0000-0000-000000000001',
    'Server Room Sensor',
    'multi_sensor',
    'Data Center - Rack A1',
    '$2b$12$MTqBJGAH.iGYNBQuqNaS5ej3o2f8kc6HQSv9yaBUtsTs6oEdRdnwq'
),
(
    'd0000000-0000-0000-0000-000000000002',
    'Office Climate Sensor',
    'multi_sensor',
    'Office Floor 2',
    '$2b$12$MTqBJGAH.iGYNBQuqNaS5ej3o2f8kc6HQSv9yaBUtsTs6oEdRdnwq'
),
(
    'd0000000-0000-0000-0000-000000000003',
    'UPS Energy Monitor',
    'energy_meter',
    'Data Center - UPS Room',
    '$2b$12$MTqBJGAH.iGYNBQuqNaS5ej3o2f8kc6HQSv9yaBUtsTs6oEdRdnwq'
)
ON CONFLICT (id) DO NOTHING;

-- ── Alert Rules (per ASHRAE TC 9.9 + industry standards) ────
-- Temperature rules for device 1 & 2
INSERT INTO alerts.alert_rules (device_id, sensor_type, operator, threshold, severity) VALUES
-- Temperature critical: > 40°C
('d0000000-0000-0000-0000-000000000001', 'temperature', 'gt', 40.0, 'critical'),
-- Temperature warning: > 35°C
('d0000000-0000-0000-0000-000000000001', 'temperature', 'gt', 35.0, 'warning'),
-- Temperature critical: < 10°C
('d0000000-0000-0000-0000-000000000001', 'temperature', 'lt', 10.0, 'critical'),
-- Temperature warning: < 15°C
('d0000000-0000-0000-0000-000000000001', 'temperature', 'lt', 15.0, 'warning'),
-- Humidity critical: > 90%
('d0000000-0000-0000-0000-000000000001', 'humidity', 'gt', 90.0, 'critical'),
-- Humidity warning: > 80%
('d0000000-0000-0000-0000-000000000001', 'humidity', 'gt', 80.0, 'warning'),
-- Humidity critical: < 20%
('d0000000-0000-0000-0000-000000000001', 'humidity', 'lt', 20.0, 'critical'),
-- Humidity warning: < 30%
('d0000000-0000-0000-0000-000000000001', 'humidity', 'lt', 30.0, 'warning'),
-- Office sensor temperature rules
('d0000000-0000-0000-0000-000000000002', 'temperature', 'gt', 40.0, 'critical'),
('d0000000-0000-0000-0000-000000000002', 'temperature', 'gt', 35.0, 'warning'),
('d0000000-0000-0000-0000-000000000002', 'temperature', 'lt', 10.0, 'critical'),
-- Energy rules for device 3
('d0000000-0000-0000-0000-000000000003', 'energy', 'gt', 4.5, 'critical'),
('d0000000-0000-0000-0000-000000000003', 'energy', 'gt', 3.5, 'warning');
