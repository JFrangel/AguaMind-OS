# WaterMind OS - Donde se almacenan los datos

> Responde la pregunta del jurado: *"Cada cuanto toman datos? Como los almacenan?"*
> Hackathon UNIAJC 2026 - v1.0

---

## Vision en una linea

Los datos viven en **5 capas de almacenamiento**, cada una optimizada para su latencia y duracion: **Edge (1,000 lecturas en flash), RAM (1 hora), Postgres (90 dias), Parquet (5 anos), PDF (permanente)**.

```
ESP32 NVS (offline buffer) -> RAM cache -> Supabase Postgres -> Parquet S3 -> PDF auditable
   1,000 lecturas              1 hora       90 dias            5 anos       permanente
```

---

## 1. Las 5 capas

| # | Capa | Tecnologia | Que guarda | Retencion | Acceso | Costo |
|---|------|-----------|-----------|-----------|--------|-------|
| 1 | **Edge** | NVS flash del ESP32 | Buffer de respaldo cuando no hay internet | 1,000 lecturas (~8 horas) | Solo lectura local | $0 (incluido en hardware) |
| 2 | **Hot** | RAM del backend FastAPI (dict en memoria) | Ultima hora de lecturas para responder queries rapidas | 1 hora | < 5 ms | $0 |
| 3 | **Warm** | Supabase Postgres + pgvector + PostGIS | Lecturas crudas, alertas, KPIs, acciones del agente | 90 dias indexados | < 50 ms | Plan gratis (500 MB) |
| 4 | **Cold** | Archivos Parquet en S3-compatible (Backblaze B2 / Cloudflare R2 free tier) | Export trimestral de tabla `water_readings` | 5 anos | Lectura via DuckDB ad-hoc | $0 - $5/mes |
| 5 | **Auditable** | PDFs firmados con hash SHA-256 + Jinja2 | Reportes mensuales para INVIMA, CVC, Min. Vivienda | Permanente | Linkable + verificable | $0 |

---

## 2. Esquema canonico (todas las capas usan el mismo)

Toda lectura, sin importar el sensor o el formato de origen, llega a la siguiente fila:

```sql
CREATE TABLE water_readings (
  id              BIGSERIAL PRIMARY KEY,
  timestamp       TIMESTAMPTZ NOT NULL,
  node_id         TEXT NOT NULL,                -- 'esp32-ptap-01'
  sensor_id       TEXT NOT NULL,                -- 'flow1' | 'FT-101'
  sensor_type     TEXT NOT NULL,                -- flow|pressure|level|...
  value           DOUBLE PRECISION NOT NULL,    -- valor en SI
  unit            TEXT NOT NULL,                -- 'L/min'|'kPa'|'NTU'|...
  raw             JSONB,                        -- valor crudo + unidad original
  quality         TEXT NOT NULL DEFAULT 'ok',   -- ok|suspect|out_of_range|invalid
  metadata        JSONB,                        -- modelo del sensor, calibracion
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_readings_ts          ON water_readings (timestamp DESC);
CREATE INDEX idx_readings_node_sensor ON water_readings (node_id, sensor_id, timestamp DESC);
CREATE INDEX idx_readings_quality     ON water_readings (quality) WHERE quality != 'ok';
```

Las tablas relacionadas (`alerts`, `kpis_hourly`, `mitigation_actions`, `valves_state`) referencian a `water_readings.id` para auditoria.

---

## 3. Frecuencias de muestreo y transmision

Definidas en `docs/es/WATERMIND-OS-MASTER.md` seccion 6.1, repetidas aqui para referencia:

| Variable | Muestreo (Hz) | Transmision (cada) | Formato | Justificacion |
|----------|--------------|---------------------|---------|---------------|
| Caudal | 1 Hz | 30 s (promedio + min + max + sigma) | esp32_compact JSON | Detectar picos sin saturar canal MQTT |
| Nivel tanques | 0.2 Hz | 30 s | esp32_compact JSON | Cambia lento; suficiente |
| Presion | 1 Hz | 30 s | esp32_compact JSON | Detectar caidas subitas |
| Turbidez | 0.033 Hz | 30 s | esp32_compact JSON | Cambia lento; alerta si > 4 NTU |
| Nivel freatico | 0.017 Hz | 5 min | esp32_compact JSON | Cambio gradual del acuifero |
| Vibracion | 100 Hz | Solo eventos | esp32_compact JSON | Deteccion acustica embebida |
| pH (Fase 3) | 0.033 Hz | 30 s | esp32_compact JSON | Critico para Resolucion 0631 |

---

## 4. Volumetria proyectada

Calculo conservador para un solo nodo (PTAP) con 6 sensores:

```
Lecturas/dia    = 6 sensores * 2,880 transmisiones/dia (cada 30s) ~ 17,280 filas
Tamano fila     = ~250 bytes (tipica)
Bytes/dia       = 17,280 * 250 = ~4.3 MB/dia/nodo
Bytes/mes       = ~130 MB/nodo

Para 5 nodos (Fase 2): ~650 MB/mes -> caben en plan gratis Supabase (500 MB) tras
                                       export trimestral a Parquet.
Para 10 nodos (Fase 3): ~1.3 GB/mes -> requiere plan Pro Supabase ($25/mes) o
                                        rotacion mas agresiva (60 dias en warm).
```

Estrategia: rotacion automatica `pg_cron` mueve filas con `created_at < NOW() - 90 days`
a un archivo Parquet por trimestre y las elimina de Postgres.

---

## 5. Backup y supervivencia ante caidas

| Falla | Que pasa | Donde se recuperan los datos |
|-------|----------|-------------------------------|
| Cae internet del campus | ESP32 guarda hasta 1,000 lecturas en NVS flash | Reenvia automaticamente cuando vuelve la conexion |
| Cae el broker MQTT | Backend usa endpoint `/water/ingest` HTTP fallback | Mismo schema canonico, sin perdida |
| Cae el backend FastAPI | ESP32 reintenta con backoff exponencial (1s, 2s, 4s, 8s, hasta 60s) | Cuando vuelve, drena el buffer NVS |
| Cae Supabase | El cache RAM del backend sigue sirviendo lecturas de la ultima hora | Lecturas siguientes se acumulan en cola; al volver, batch insert |
| Cae el PC del operador | El sistema sigue funcionando autonomamente desde el ESP32 + dashboard publico | Operador entra desde cualquier dispositivo via web |
| Borrado accidental de Postgres | Snapshots diarios de Supabase + Parquet trimestrales en S3 | Restore desde snapshot Supabase o reimport desde Parquet |

---

## 6. Acceso a los datos

### Para los ingenieros (queries ad-hoc)
- **Supabase Studio** -> SQL editor con autocomplete
- **DuckDB local** sobre Parquet: `duckdb` -> `SELECT * FROM 'water_readings_2026Q1.parquet'`
- **Endpoint REST**: `GET /water/history?from=...&to=...&sensor=...`

### Para el publico (transparencia, Ley 1712/2014)
- **Dashboard publico** en `/agua` con KPIs en vivo (sin login)
- **Endpoint abierto** `/water/reading` y `/water/agent/status`
- **PDFs mensuales** publicados en el sitio de UNIAJC

### Para los reguladores (INVIMA, CVC, Min. Vivienda)
- **PDF auditable** generado mensualmente con hash SHA-256 al pie
- **Adjunto Parquet** del periodo cuando se solicite verificacion granular

---

## 7. Privacidad y normativa de datos

| Norma | Aplica a | Implementacion |
|-------|---------|----------------|
| Ley 1581/2012 (Habeas Data) | Datos personales de reportes ciudadanos QR | Pseudonimizacion con hash + opt-in explicito |
| Ley 1712/2014 (Transparencia) | Mediciones del recurso publico | Dashboard + datasets descargables |
| Ley 1928/2018 (Ciberseguridad) | Infraestructura critica | TLS 8883 MQTT + auth Supabase |
| Decreto 338/2022 (Riesgos ciberneticos) | Operacion del sistema | Backups, logs auditables |
| Resolucion 055/2025 UNIAJC | Politica institucional | Cumplimiento del decalogo de seguridad de la informacion |

---

## 8. Checklist operacional

| Tarea | Frecuencia | Responsable | Donde queda registro |
|-------|-----------|-------------|----------------------|
| Verificar `quality != 'ok'` ratio < 5% | Cada 5 min (auto) | SensorAgent | tabla `alerts` |
| Snapshot Supabase | Diario 02:00 AM | Supabase auto | Backup gestionado |
| Export Parquet del trimestre anterior | Trimestral | `scripts/export_parquet.py` (cron) | S3 + log de exports |
| Generar PDF normativo | Mensual primer dia habil | `services/api/app/routers/reports.py` | tabla `reports` |
| Calibracion de sensores | Trimestral | Equipo electronica | Anexo manual + foto |
| Auditoria de accesos | Trimestral | Sistemas | Logs de Supabase + FastAPI |

---

## 9. Para la demo del hackathon

**Modo demo (lo que esta corriendo ahora):** todo en memoria. El simulador genera lecturas
en tiempo real (`water._simulate_sensors()`) sin necesidad de hardware ni base de datos.
Todas las queries responden de RAM. Es lo que permite que el dashboard funcione **offline
y sin claves**.

**Modo produccion:** se setea `DATABASE_URL` apuntando a Supabase (o cualquier Postgres
local) y los endpoints `/water/ingest/*` empiezan a persistir. El normalizador acepta
cualquier formato de cualquier sensor (ver [ANALISIS-Y-CAPAS-VISUALES.md](ANALISIS-Y-CAPAS-VISUALES.md)
seccion 2 para los 10 formatos soportados).

---

*v1.0 - Hackathon UNIAJC 2026 - github.com/JFrangel/WaterMind-OS*
