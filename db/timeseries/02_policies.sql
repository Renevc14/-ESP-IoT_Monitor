-- ============================================================
-- timeseries-db: ciclo de vida de los datos (TimescaleDB)
--   1. Continuous aggregate horario (tendencias históricas rápidas, refresco incremental)
--   2. Política de compresión (chunks antiguos)
--   3. Política de retención (descarte de datos crudos vencidos)
-- ============================================================

-- 1. Agregado continuo: promedios/min/max por hora, dispositivo y sensor.
--    Se materializa de forma incremental; el dashboard lo consulta en vez de
--    recalcular time_bucket sobre toda la tabla cruda.
CREATE MATERIALIZED VIEW iot.sensor_readings_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket(INTERVAL '1 hour', recorded_at) AS bucket,
    device_id,
    sensor_type,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    COUNT(*)   AS reading_count
FROM iot.sensor_readings
GROUP BY bucket, device_id, sensor_type
WITH NO DATA;

-- Real-time aggregation: combina los datos ya materializados con los más
-- recientes aún sin materializar, para que la última hora también aparezca.
ALTER MATERIALIZED VIEW iot.sensor_readings_hourly
    SET (timescaledb.materialized_only = false);

-- Refresco automático: rehace las últimas 3 horas cada hora (deja un margen de
-- 1 hora para no tocar el bucket en curso).
SELECT add_continuous_aggregate_policy('iot.sensor_readings_hourly',
    start_offset      => INTERVAL '3 days',
    end_offset        => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- 2. Compresión: los chunks con más de 7 días se comprimen (ahorro de espacio
--    y mejor lectura analítica). Se segmenta por dispositivo y tipo de sensor.
ALTER TABLE iot.sensor_readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id, sensor_type',
    timescaledb.compress_orderby   = 'recorded_at DESC'
);

SELECT add_compression_policy('iot.sensor_readings', INTERVAL '7 days');

-- 3. Retención: los datos crudos con más de 90 días se descartan por chunk
--    (las tendencias históricas siguen disponibles en el agregado continuo).
SELECT add_retention_policy('iot.sensor_readings', INTERVAL '90 days');
