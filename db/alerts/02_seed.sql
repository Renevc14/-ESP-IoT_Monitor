-- Reglas de alerta (ASHRAE TC 9.9 + estándares de industria)
INSERT INTO alerts.alert_rules (device_id, sensor_type, operator, threshold, severity) VALUES
('d0000000-0000-0000-0000-000000000001', 'temperature', 'gt', 40.0, 'critical'),
('d0000000-0000-0000-0000-000000000001', 'temperature', 'gt', 35.0, 'warning'),
('d0000000-0000-0000-0000-000000000001', 'temperature', 'lt', 10.0, 'critical'),
('d0000000-0000-0000-0000-000000000001', 'temperature', 'lt', 15.0, 'warning'),
('d0000000-0000-0000-0000-000000000001', 'humidity', 'gt', 90.0, 'critical'),
('d0000000-0000-0000-0000-000000000001', 'humidity', 'gt', 80.0, 'warning'),
('d0000000-0000-0000-0000-000000000001', 'humidity', 'lt', 20.0, 'critical'),
('d0000000-0000-0000-0000-000000000001', 'humidity', 'lt', 30.0, 'warning'),
('d0000000-0000-0000-0000-000000000002', 'temperature', 'gt', 40.0, 'critical'),
('d0000000-0000-0000-0000-000000000002', 'temperature', 'gt', 35.0, 'warning'),
('d0000000-0000-0000-0000-000000000002', 'temperature', 'lt', 10.0, 'critical'),
('d0000000-0000-0000-0000-000000000003', 'energy', 'lt', -2.0, 'warning'),
('d0000000-0000-0000-0000-000000000003', 'energy', 'lt', -3.0, 'critical');
