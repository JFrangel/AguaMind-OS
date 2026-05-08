# Camaleón OS — Cumplimiento Normativo y Soluciones a Cada Problema

> Documento maestro que mapea cada problema PTAP/PTAR con la normativa colombiana
> aplicable, las consecuencias por incumplimiento y la forma exacta como Camaleón OS
> evita las sanciones y resuelve cada falla.

> **Fuentes oficiales del proyecto:**
> - Tesis Paula A. Gómez Mina (2022) — *Diseño de programa de mantenimiento PTAP UNIAJC*
> - Plano técnico PTAP UNIAJC (Apéndice A · 3 filtros + tanque cloro + retrolavado)
> - Resolución 055 de enero 2025 — Plan de Seguridad y Privacidad UNIAJC
> - Reto Hackathon UNIAJC 2026

---

## 1. Marco Normativo Aplicable a la Solución

### 1.1 Calidad del Agua Potable y PTAP

| Norma | Contenido | Aplicación a Camaleón |
|-------|-----------|------------------------|
| **Decreto 1575 de 2007** (Min. Protección Social) | Sistema para protección y control de calidad del agua para consumo humano | Lavado y desinfección tanques **mínimo 2 veces/año** · monitoreo IRCA |
| **Resolución 2115 de 2007** (Min. Protección + Min. Ambiente + Min. Vivienda) | Características, instrumentos y frecuencias del sistema de control y vigilancia para calidad de agua | Define Índice de Riesgo de Calidad del Agua (IRCA), parámetros físico-químicos y microbiológicos |
| **Decreto 3930 de 2010** (Min. Ambiente y Desarrollo Sostenible) | Disposiciones relacionadas con los usos del recurso hídrico | Permisos de captación · concesión de aguas |
| **RAS 2000** Capítulo C.17 (Min. Vivienda) | Reglamento técnico Sector de Agua Potable y Saneamiento Básico — Operación y mantenimiento | Retrolavado de filtros **mínimo 2 veces/año** |

### 1.2 Vertimientos y PTAR

| Norma | Contenido | Aplicación a Camaleón |
|-------|-----------|------------------------|
| **Resolución 0631 de 2015** (Min. Ambiente) | Valores límite máximos permisibles en vertimientos puntuales a cuerpos de agua superficiales | DBO5 ≤ 90 mg/L · pH 6–9 · SST ≤ 90 mg/L · grasas y aceites ≤ 20 mg/L |
| **Decreto 050 de 2018** | Modificación del Decreto 3930 sobre vertimientos | Obligación de Plan de Cumplimiento |
| **Resolución 1207 de 2014** | Reúso de agua tratada para riego | Habilita reúso PTAR → riego cancha |

### 1.3 Seguridad de la Información (aplicable a Camaleón como sistema digital)

| Norma | Contenido | Aplicación a Camaleón |
|-------|-----------|------------------------|
| **Ley 1581 de 2012** (Habeas Data) | Marco general de protección de datos personales | Si registramos chat_id Telegram → manejo responsable |
| **Ley 1928 de 2018 + Decreto 338 de 2022** | Ciberseguridad y gestión de riesgos cibernéticos | Backend autenticado · cifrado HTTPS · logs auditables |
| **Ley 1712 de 2014** (Ley de Transparencia) | Publicación de datos abiertos | Dashboard público y reporte mensual abierto |
| **Resolución 055 UNIAJC enero 2025** | Plan de Seguridad y Privacidad de la Información institucional | Adherencia a la política institucional |
| **Decreto 1008 de 2018** | Política de Gobierno Digital | Interoperabilidad de datos · API REST estandarizada |
| **Ley 1931 de 2018** | Sostenibilidad y eficiencia energética en TIC | ESP32 ultra bajo consumo + cloud free tier |

### 1.4 Acuerdo con la Hackathon UNIAJC 2026

| Documento | Contenido |
|-----------|-----------|
| **Reto Hackathon UNIAJC** | Diseñar sistema inteligente que mida, analice y optimice uso de agua del campus integrando Sistemas + Electrónica + Industrial |
| **Lema "Tecnologías con propósito"** | La solución debe demostrar conciencia ambiental y social |

---

## 2. Equipos PTAP UNIAJC (datos reales del proyecto Gómez Mina 2022)

Inventario verificado del proyecto de mantenimiento (códigos UNIAJC oficiales):

| Código | Equipo | Marca | Especificación |
|--------|--------|-------|----------------|
| **CP-BS-01** | Bomba sumergible aljibe 1 | Barnes 4SP 2526 | 5 HP · 32 gal/min · 230 mca · 220V |
| **CP-BS-02** | Bomba sumergible aljibe 2 | Barnes 4SP 2511 | 2 HP · 32 gal/min · 100 mca · 220V |
| **SF-FT-01** | Filtro #1 (grava + arena sílice) | OHS Ingenieros Ltda | 861.53 L · 400 L/min |
| **SF-FT-02** | Filtro #2 (grava + arena + antracita) | OHS Ingenieros Ltda | 861.53 L · 400 L/min |
| **SF-FT-03** | Filtro #3 (grava + arena + carbón activado) | OHS Ingenieros Ltda | 861.53 L · 400 L/min |
| **SD-TM-01** | Tanque multiuso (cloración) | Ajover Wave | 250 L · polietileno |
| **SD-BD-01** | Bomba dosificadora cloro | LMI C111-362TI | 120V · 150 PSI · 2.50 GPH · 44 W |
| **AL-TA-01** | Tanque almacenamiento #1 | Externo | 36,000 L (36 m³) |
| **AL-TA-02** | Tanque almacenamiento #2 | Externo | 16,000 L (16 m³) |
| **SB-TH-01** | Tanque hidroneumático #1 | Altamira PRO XLB | 119 gal · 125 PSI máx |
| **SB-TH-02** | Tanque hidroneumático #2 | Altamira PRO XLB | 119 gal · 125 PSI máx |
| **SB-BC-03** | Bomba centrífuga #1 | Barmesa Pumps | distribución |
| **SB-BC-04** | Bomba centrífuga #2 | Barmesa Pumps | distribución |

> **Concentración cloro objetivo:** 3 ppm (Decreto 1575 de 2007 + Res. 2115)
> **Retrolavado actual:** 24 veces/año (excede norma RAS 2000 que pide 2/año)

---

## 3. Solución Detallada a Cada Problema PTAP

### 🔴 P1 — Ausencia total de medición desde 2011

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | Resolución 2115/2007 exige sistema de control y vigilancia. Sin medición no hay vigilancia → **incumplimiento parcial Capítulo IV-V** |
| **Sanción potencial** | Min. Salud puede ordenar suspensión de uso · multa hasta 1,000 SMMLV |
| **Solución Camaleón** | Nodo PTAP con YF-S201 (entrada + salida cada filtro), JSN-SR04T (tanques), MPX5700AP (presión), TSD-10 (turbidez) |
| **Cómo evita la sanción** | Genera reportes IRCA automáticos exportables a Min. Salud · cumplimiento Capítulo IV de Res 2115 |
| **Costo solución** | Nodo PTAP $1.4M COP · ROI 21 días |

---

### 🔴 P2 — Pérdidas 20-30% no contabilizadas

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | Decreto 3930/2010 exige uso eficiente del recurso hídrico. **Pérdidas > 25% violan principio de eficiencia** |
| **Sanción potencial** | CVC puede revocar concesión de aguas subterráneas |
| **Solución Camaleón** | Balance IN-OUT por edificio + IsolationForest + hidrófono acústico SW-420 |
| **Cómo evita la sanción** | TPP medible permite plan de reducción auditable y reportable a CVC |
| **Costo solución** | $2.4M COP por edificio (par IN+OUT) |

---

### 🟡 P3 — Riego con agua tratada innecesariamente

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | Resolución 1207/2014 habilita reúso de agua para riego, pero el agua tratada potable usada directamente para riego **viola principio de eficiencia** |
| **Sanción potencial** | Multa por uso ineficiente del recurso |
| **Solución Camaleón** | Solenoide EV-RC1 + higrómetros HW-080 → riego solo desde aljibe 2 (sin tratar) cuando humedad < 60% y horario nocturno |
| **Cómo evita la sanción** | Demuestra plan de reúso documentado (Resolución 1207/2014) |
| **Costo solución** | $2.5M COP nodo Cancha + Jardines |

---

### 🟡 P4 — Bombeo sin demanda real (sobreproducción)

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | Ley 1931/2018 exige eficiencia energética en infraestructuras. Bombeo innecesario = consumo eléctrico injustificable |
| **Sanción potencial** | Reportabilidad ambiental institucional · pierde puntos en acreditación |
| **Solución Camaleón** | Relay SSR + lógica del agente: bomba solo si Tanque A < 24,000 L Y demanda proyectada > 0 |
| **Cómo evita la sanción** | Reporte mensual de eficiencia energética con datos auditables |
| **Costo solución** | $33K COP (relay + driver) |

---

### 🔴 P5 — Acuífero sobreexplotado sin sensor freático

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | **Decreto 1076 de 2015** (Único Reglamentario Ambiental) obliga a **monitoreo de niveles piezométricos** en concesiones de agua subterránea |
| **Sanción potencial** | CVC puede revocar concesión + multa hasta 5,000 SMMLV |
| **Solución Camaleón** | Transductor sumergible 4-20 mA en cada aljibe → nivel freático en tiempo real con histórico |
| **Cómo evita la sanción** | Reporte automático de niveles a CVC (cumplimiento art. 2.2.3.2.7.3 Decreto 1076/2015) |
| **Costo solución** | $360K COP (2 transductores + cableado) |

---

### 🟡 P6 — Tuberías >10 años sin mantenimiento

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | RAS 2000 Capítulo G establece vida útil tuberías PVC 30-50 años pero requiere inspección anual |
| **Sanción potencial** | Infraestructura no mantenida → riesgo de afectación calidad |
| **Solución Camaleón** | SW-420 vibración + hidrófono ESP32 + EV automática para corte preventivo |
| **Cómo evita la sanción** | Bitácora digital de inspecciones y eventos auditable |
| **Costo solución** | $30K COP por punto crítico |

---

### 🟡 P7 — Tanques sin sensores de nivel

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | Decreto 1575/2007 exige garantizar continuidad del suministro. Desbordes o vaciados violan |
| **Sanción potencial** | Multa hasta 500 SMMLV por interrupción del servicio |
| **Solución Camaleón** | JSN-SR04T impermeable en cada tanque + alerta automática + corte EV salida |
| **Cómo evita la sanción** | Continuidad garantizada + bitácora de eventos |
| **Costo solución** | $60K COP (par sensores) |

---

### 🔴 P8 — Sin monitoreo de calidad del agua

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | **Resolución 2115/2007** exige medición continua de parámetros físico-químicos (Cap. IV) y microbiológicos (Cap. V). **Turbidez ≤ 2 NTU** para agua segura |
| **Sanción potencial** | IRCA inviable · suspensión de uso · multa hasta 1,000 SMMLV |
| **Solución Camaleón** | TSD-10 turbidez en tiempo real + alerta crítica si NTU > 4 + cierre EV-OUT-A automático |
| **Cómo evita la sanción** | Reporte IRCA mensual al INVIMA con datos auditables · cumplimiento total Capítulos IV-V Res 2115 |
| **Costo solución** | $55K COP (TSD-10) + futuras extensiones (pH, conductividad, cloro residual) |

---

### 🟡 P9 — Sin alertas ni KPIs

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | Decreto 1008/2018 (Gobierno Digital) requiere transformación digital · Ley 1712/2014 obliga a entidades públicas a publicar datos |
| **Sanción potencial** | Hallazgo en auditoría institucional |
| **Solución Camaleón** | Dashboard público con IEH, TPP, CPE, ICA + alertas Telegram + reporte PDF diario |
| **Cómo evita la sanción** | Cumple Ley de Transparencia + política Gobierno Digital |
| **Costo solución** | $0 (open source) |

---

### 🟡 P10 — Aljibe 2 sin control de derivación a riego

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | Concesión CVC pudo asignar caudal específico para riego sin control |
| **Sanción potencial** | Sobreuso = revocatoria parcial de concesión |
| **Solución Camaleón** | EV-RC1 con T-junction permite cortar riego sin afectar resto + medición exacta del caudal usado |
| **Cómo evita la sanción** | Reporte trimestral de uso real vs. concesión |
| **Costo solución** | $220K COP (electroválvula 1") |

---

## 4. Solución Detallada a Cada Problema PTAR

### 🔴 R1 — Capacidad subdimensionada (2,000 vs 8,234 usuarios)

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | Decreto 1575/2007 + Resolución 0631/2015 exigen tratamiento adecuado antes de vertimiento. Sobrecarga = tratamiento deficiente |
| **Sanción potencial** | Multa Resolución 0631 hasta 5,000 SMMLV + cierre temporal del campus |
| **Solución Camaleón** | Balance hídrico institucional → reporta uso real vs capacidad → justifica ampliación de PTAR ante CVC |
| **Cómo evita la sanción** | Reporte trimestral demuestra trazabilidad y plan de cumplimiento |
| **Costo solución** | $0 (con datos del balance ya implementado) |

---

### 🔴 R2 — Sin monitoreo Resolución 0631/2015

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | Resolución 0631/2015 fija límites obligatorios de vertimiento (DBO5, pH, SST, grasas, aceites) |
| **Sanción potencial** | Multa por exceso · pago por daños ambientales art. 31 Ley 99/1993 |
| **Solución Camaleón** | Sensores de calidad en salida PTAR: turbidez, pH, conductividad (Fase 3) |
| **Cómo evita la sanción** | Reporte mensual a CVC con datos en tiempo real · alerta automática si parámetro fuera de norma |
| **Costo solución** | $1.8M COP por PTAR (par Alameda + Entrada) |

---

### 🟡 R3 — Impacto sobre cuenca río Pance/Cauca

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | Política Nacional para Gestión Integral del Recurso Hídrico · POMCA río Cauca |
| **Sanción potencial** | Pérdida de licencia ambiental institucional |
| **Solución Camaleón** | Dashboard público "Pulso del río Pance" mostrando descargas tratadas vs límites |
| **Cómo evita la sanción** | Transparencia comunitaria + reporte trimestral a comunidad académica |
| **Costo solución** | $0 (con dashboard ya implementado) |

---

### 🟡 R4 — Balance PTAP-PTAR no medido

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | Decreto 1076/2015 exige uso eficiente y plan de cumplimiento ambiental |
| **Solución Camaleón** | Comparación automática Σ entradas edificios vs Σ entradas PTAR → ratio mensual |
| **Costo solución** | $0 |

---

### 🟡 R5 — Mantenimiento reactivo (solo cuando hay olor)

| Aspecto | Detalle |
|---------|---------|
| **Riesgo normativo** | RAS 2000 Capítulo E exige plan de mantenimiento preventivo |
| **Solución Camaleón** | Sensor turbidez en cámara de lodos PTAR + alerta automática para purgas programadas |
| **Costo solución** | $55K COP por PTAR |

---

## 5. Soluciones por Equipo PTAP (basado en proyecto Gómez Mina 2022)

El proyecto de grado de Paula Gómez (2022) identificó fallas concretas en cada equipo. Camaleón OS las atiende digitalmente:

### 5.1 Filtros (SF-FT-01, 02, 03)

| Falla identificada en tesis | Síntoma | Solución Camaleón |
|----------------------------|---------|-------------------|
| Sistema no filtra | Caudal bajo · presión anómala | YF-S201 detecta caudal anómalo + MPX5700AP detecta presión → alerta automática |
| Lechos colmatados | Necesidad de retrolavado | KPI específico "días desde último retrolavado" + alerta si > 14 días |
| Aire atrapado en tuberías | Caudal irregular | Vibración SW-420 + presión irregular detectan aire |
| Agua turbia | Filtros saturados | TSD-10 alerta crítica + cierre EV-OUT-A automático |
| Agua se descompone (cloro bajo) | Cloración insuficiente | (Fase 4) sensor cloro residual ORP/redox |

### 5.2 Bombas dosificadoras de cloro (SD-BD-01)

| Falla identificada | Solución Camaleón |
|---------------------|-------------------|
| Caudal insuficiente | Sensor flujo en línea de cloro + alerta |
| Bomba no arranca | Monitoreo eléctrico (corriente vía sensor SCT-013) |
| Caudal excesivo o irregular | Alerta automática si dosificación > 3 ppm objetivo |
| Dosificación interrumpida | Sensor cloro residual + alerta crítica |

### 5.3 Tanques hidroneumáticos (SB-TH-01, 02)

| Falla identificada | Solución Camaleón |
|---------------------|-------------------|
| No bombea / motor parado | Sensor presión MPX5700AP detecta caída |
| Membrana con fuga | Caída anormal de presión registrada |
| No alcanza presión deseada | KPI "presión nominal vs actual" |
| Aire en tubería de succión | Vibración SW-420 + análisis acústico |

### 5.4 Bombas centrífugas (SB-BC-03, 04)

| Falla identificada | Solución Camaleón |
|---------------------|-------------------|
| Motor no arranca | Sensor corriente SCT-013 + alerta |
| Rendimiento no constante | KPI variabilidad caudal |
| Presión baja | MPX5700AP + alerta crítica |
| Bomba no suministra agua | Caudalímetro YF-S201 detecta caudal cero |
| Fugas en sellos mecánicos | Vibración + caudal anómalo |

### 5.5 Tableros eléctricos

| Falla identificada | Solución Camaleón |
|---------------------|-------------------|
| Sobrecarga (fusibles quemados) | Sensor corriente + alerta antes de quema |
| Falsos contactos | Monitoreo continuo de patrones eléctricos |

### 5.6 Bombas sumergibles aljibes (CP-BS-01, 02)

| Falla identificada | Solución Camaleón |
|---------------------|-------------------|
| Bomba arranca sin agua | Sensor freático 4-20mA + corte automático |
| Fuga lubricante (contamina agua) | TSD-10 detecta turbidez anómala |
| Sobrecarga eléctrica | Sensor corriente + relay protección |

---

## 6. Plan de Cumplimiento Normativo Trimestral

Camaleón OS genera automáticamente el siguiente reporte cada trimestre:

```
┌──────────────────────────────────────────────────────────────────┐
│  REPORTE DE CUMPLIMIENTO NORMATIVO — TRIMESTRE Q1 2026            │
│  UNIAJC Sede Sur · Generado por Camaleón OS · Fecha: 2026-03-31  │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  CALIDAD DE AGUA (Resolución 2115/2007)                           │
│    ✓ Turbidez salida promedio:       1.4 NTU (límite ≤ 2)         │
│    ✓ Cloro residual promedio:        2.8 ppm (objetivo 3 ppm)      │
│    ✓ pH promedio:                     7.2 (rango 6.5-9.0)         │
│    ✓ IRCA mensual:                   3.1 (riesgo BAJO)            │
│                                                                    │
│  RECURSO HÍDRICO (Decreto 1076/2015)                              │
│    ✓ Caudal extraído aljibe 1:       45 L/min (concesión 60)      │
│    ✓ Nivel freático aljibe 1:        7.4 m (mín seguro 4 m)       │
│    ✓ Eficiencia hídrica IEH:          88.4% (meta > 90%)          │
│    ✓ Pérdidas TPP:                    11.6% (meta < 10%) ⚠️         │
│                                                                    │
│  VERTIMIENTOS (Resolución 0631/2015)                              │
│    ✓ DBO5 estimado salida PTAR:      78 mg/L (límite ≤ 90)        │
│    ✓ Turbidez salida PTAR:           45 NTU                       │
│    ✓ pH salida PTAR:                  7.5                         │
│                                                                    │
│  EFICIENCIA ENERGÉTICA (Ley 1931/2018)                            │
│    ✓ kWh consumidos bombeo:          82 (mes anterior 96)         │
│    ✓ Reducción mensual:              -14.6%                       │
│                                                                    │
│  ALERTAS Y MITIGACIONES                                            │
│    Total alertas críticas resueltas:  7                            │
│    Tiempo medio detección:            4.2 min                      │
│    Litros recuperados:                3,820 L                      │
│    CO₂ evitado:                       1.76 kg                      │
│                                                                    │
│  DOCUMENTOS GENERADOS PARA AUTORIDADES                             │
│    □ INVIMA: Reporte IRCA mensual ───── enviado 15/03/2026         │
│    □ CVC:    Reporte caudal trimestral ─ enviado 31/03/2026        │
│    □ Min Vivienda: Reporte RAS C.17 ──── pendiente                 │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 7. Plan de Acción para Eliminar Sanciones (5 pasos)

### Paso 1 · Implementar Fase 1 ($1.4M COP)
Nodo PTAP completo con 6 sensores → cumple Res 2115, Decreto 1575, Decreto 1076.

### Paso 2 · Generar Manual de Operación digital
Basado en el proyecto de grado de Gómez Mina (2022) + datos en tiempo real.

### Paso 3 · Configurar reporte automático IRCA
Backend FastAPI genera PDF mensual exportable al formato Min. Salud.

### Paso 4 · Conectar con SUI (Sistema Único de Información)
Decreto 2106 de 2019: digitalización de trámites con autoridades.

### Paso 5 · Auditoría externa
Empresa certificada valida los datos cada 6 meses · sello "PTAP Inteligente Certificada".

---

## 8. Resumen — ¿Cuánto se ahorra evitando sanciones?

| Sanción potencial evitada | Multa máxima |
|---------------------------|--------------|
| Suspensión de uso por IRCA fuera de norma | 1,000 SMMLV ≈ $1,300 millones COP |
| Revocatoria concesión CVC | 5,000 SMMLV ≈ $6,500 millones COP |
| Multa Resolución 0631/2015 | 5,000 SMMLV ≈ $6,500 millones COP |
| Multa Ley 1581/2012 (datos) | 2,000 SMMLV ≈ $2,600 millones COP |
| **TOTAL EXPOSICIÓN** | **$16,900 millones COP** |
| **Inversión Camaleón para evitarlo** | **$5–19 millones COP** (escalonable) |

> Camaleón OS no es solo una solución técnica — es **gestión de riesgo institucional** que protege a UNIAJC de exposición legal millonaria con una inversión < 0.1% del riesgo evitado.

---

*Documento maestro de cumplimiento normativo · Camaleón OS · Hackathon UNIAJC 2026*
*Basado en proyecto Gómez Mina (2022), Plano técnico PTAP UNIAJC, Resolución 055 UNIAJC 2025*
