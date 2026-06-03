-- Dispositivos de ejemplo. Tokens crudos de prueba: device-token-001/002/003
INSERT INTO iot.devices (id, name, device_type, location, auth_token_hash) VALUES
('d0000000-0000-0000-0000-000000000001', 'Server Room Sensor', 'multi_sensor', 'Data Center - Rack A1',
 '$2b$12$MTqBJGAH.iGYNBQuqNaS5ej3o2f8kc6HQSv9yaBUtsTs6oEdRdnwq'),
('d0000000-0000-0000-0000-000000000002', 'Office Climate Sensor', 'multi_sensor', 'Office Floor 2',
 '$2b$12$MTqBJGAH.iGYNBQuqNaS5ej3o2f8kc6HQSv9yaBUtsTs6oEdRdnwq'),
('d0000000-0000-0000-0000-000000000003', 'UPS Energy Monitor', 'energy_meter', 'Data Center - UPS Room',
 '$2b$12$MTqBJGAH.iGYNBQuqNaS5ej3o2f8kc6HQSv9yaBUtsTs6oEdRdnwq')
ON CONFLICT (id) DO NOTHING;
