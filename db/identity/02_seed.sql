-- Usuarios por defecto (passwords: Admin1234! / Operator1234!)
INSERT INTO auth.users (id, email, password_hash, role, full_name) VALUES
('a0000000-0000-0000-0000-000000000001', 'admin@iot.local',
 '$2b$12$KZ/UFmLsg4zg724B0p8ETeumDMlfia8PB2hv0mz9NV9.24HHYury.', 'admin', 'System Administrator'),
('a0000000-0000-0000-0000-000000000002', 'operator@iot.local',
 '$2b$12$zf4i8RuMUMrA5P6msQXBjOmMhI/icbXOfMPIIn4urUtmD1kZWOwQK', 'operator', 'IoT Operator')
ON CONFLICT (email) DO NOTHING;
