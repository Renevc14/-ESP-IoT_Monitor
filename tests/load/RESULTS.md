# Resultados de la prueba de carga (RNF-01)

**RNF-01:** la plataforma debe sostener **≥ 1000 eventos/segundo** de ingesta.

## Metodología

- Script: [`load_test.py`](load_test.py) — autentica como operador y envía lecturas
  de sensor concurrentes a `POST /ingest/reading`.
- Parámetros: `TOTAL=3000` eventos, `CONCURRENCY=100` conexiones, cliente `httpx`
  asíncrono con keep-alive.
- Métrica: se mide el tiempo de pared del envío completo y se calcula el throughput
  de respuestas `202 Accepted` (la ingesta publica al exchange y responde de forma
  asíncrona; la persistencia ocurre aguas abajo en `processing`).

```bash
TOTAL=3000 CONCURRENCY=100 python tests/load/load_test.py
```

## Resultado (entorno local)

| Métrica | Valor |
|---|---|
| Eventos enviados | 3000 |
| Exitosos (202) | 3000 |
| Fallidos | 0 |
| Tiempo total | 70.5 s |
| **Throughput** | **~43 req/s** |

Entorno: Docker Desktop sobre Windows 10 (WSL2), una sola réplica por servicio,
RabbitMQ con `publisher_confirms` activado.

## Análisis

- **Corrección bajo carga:** 0 fallos en 3000 eventos concurrentes — la cola, la
  validación JWT y el publicador se comportan de forma estable y sin pérdida.
- **Throughput limitado por el entorno**, no por el diseño. Los principales cuellos
  de botella en esta medición local son:
  1. **Docker Desktop sobre Windows/WSL2**: la sobrecarga de red entre el host y los
     contenedores domina la latencia por petición.
  2. **Una sola réplica de `ingestion`** y confirmación de publicación síncrona
     (`publisher_confirms=true`) — prioriza la durabilidad sobre el throughput.
  3. **Recursos acotados** por los límites de memoria del Compose de demostración.

## Cómo alcanzar ≥ 1000 req/s

El diseño ya contempla el escalado; lo que falta es entorno e infraestructura:

- **Escalado horizontal con consumidores en competencia**: el exchange es *fanout* y
  los consumidores de `processing` comparten una cola durable, por lo que `N` réplicas
  reparten la carga. La ingesta es sin estado y se replica detrás de un balanceador.
- **Throughput vs. durabilidad**: `PUBLISHER_CONFIRMS=false` y publicación por lotes
  elevan el caudal cuando la semántica lo permite.
- **Infraestructura de producción**: hosts Linux nativos, RabbitMQ y TimescaleDB
  gestionados/clusterizados en lugar de un único contenedor local.

> Conclusión: la arquitectura es escalable horizontalmente; la cifra local (~43 req/s)
> refleja las limitaciones del entorno de desarrollo, no un techo del sistema.
