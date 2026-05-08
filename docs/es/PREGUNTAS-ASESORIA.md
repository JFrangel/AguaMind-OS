# Camaleón OS — Preguntas para la Asesoría con el Jurado

> Preguntas estratégicas que el equipo puede hacer durante los espacios de
> tutoría con los expertos del Hackathon UNIAJC 2026, organizadas por ingeniería.

---

## A. Preguntas de Estrategia General (todo el equipo)

### Validación de la propuesta
1. ¿La propuesta de **Camaleón OS** se alinea con la visión de la universidad de convertirse en un **Smart Campus**?
2. ¿Existen restricciones presupuestales que debamos considerar para ser realistas con la inversión inicial de **$1,043,000 COP** propuesta?
3. ¿Hay limitaciones contractuales con el proveedor actual de mantenimiento que afecten la instalación de los nodos IoT?
4. ¿Qué procesos administrativos deberíamos considerar para una eventual implementación piloto post-hackathon?
5. ¿Cómo evalúa el jurado la combinación de **hardware bajo costo + IA + comunidad** vs. soluciones más industrialmente maduras?

### Alcance y diferenciación
6. De los 4 criterios de evaluación (Novedad, Aplicación Industrial, Inventiva, Impacto), ¿cuál considera más crítico para el contexto UNIAJC?
7. ¿La existencia de tesis previas (Aristizábal & Largacha 2025, Arias Montoya 2024) puede usarse como evidencia de necesidad real o resta novedad?
8. ¿Hay equipos compitiendo con propuestas similares? ¿En qué deberíamos enfocar nuestro diferenciador?

---

## B. Ingeniería Electrónica — Preguntas Técnicas

### Sensores y circuito
1. ¿Los **sensores YF-S201** son adecuados para el caudal real de los aljibes UNIAJC (113.56 L/min combinado), o deberíamos considerar **YF-DN50** para mayor rango?
2. Para detectar fugas no visibles, ¿es viable un **hidrófono piezoeléctrico ESP32-INMP441** con clasificador acústico, o requiere hardware más especializado?
3. ¿El **MPX5700AP** soporta la presión real de la red de distribución del campus? ¿Cuál es la presión típica?
4. ¿Qué consideraciones de **protección IP** (humedad, polvo) son críticas para el gabinete del nodo en exterior?
5. Para el **acondicionamiento del 4-20mA** (sensor freático), ¿es suficiente una resistencia shunt 150Ω o necesitamos un amplificador de aislamiento?

### Comunicación y energía
6. ¿La **WiFi 2.4 GHz del campus** tiene cobertura suficiente en la PTAP? ¿Existe red alterna?
7. ¿Es viable usar **MQTT vía HiveMQ Cloud free tier**, o hay políticas que requieran broker on-premise?
8. ¿Cómo recomienda manejar la **autonomía energética** ante cortes? ¿Batería 18650 + TP4056 es suficiente o necesitamos UPS?
9. ¿Los **electrovalves DC 12V** son apropiados o deberíamos usar válvulas neumáticas industriales?

### Validación y calibración
10. ¿Cuál es el **proceso de certificación metrológica** que debería seguir cada sensor antes del despliegue?
11. ¿Cómo validar el **firmware en MicroPython** vs. la opción C nativa con ESP-IDF?

---

## C. Ingeniería de Sistemas — Preguntas Técnicas

### Arquitectura de software
1. ¿La arquitectura **multi-agente con LangGraph** es apropiada para el caso de uso, o se ve sobre-ingenierizada para 1-5 nodos iniciales?
2. ¿El uso de **FastAPI + SvelteKit + Supabase** cumple los **estándares de portabilidad y mantenibilidad** que exige el reto?
3. ¿Cómo evaluar la **seguridad de la API** considerando que controla actuadores físicos (electroválvulas)?
4. ¿Qué nivel de **resiliencia** se espera ante caídas del backend o la red?

### IA y datos
5. ¿La **detección por IsolationForest** es suficiente o se espera un modelo más sofisticado (LSTM, autoencoders)?
6. ¿Hay restricciones para usar **LLMs cloud** (Groq/OpenRouter/Gemini) por privacidad de datos del campus?
7. ¿Cómo manejar la **explicabilidad** de las decisiones del agente (por qué cerró la válvula X)?
8. ¿El **agente debe pedir confirmación humana** antes de ejecutar acciones físicas, o puede actuar autónomamente?

### Interfaces y usuarios
9. ¿El **Diseño Centrado en Usuario (UCD)** debe priorizar al operario de mantenimiento o al estudiante?
10. ¿La integración con **Telegram** es apropiada o deberíamos usar canales institucionales (correo, intranet)?
11. ¿Cuál es el público objetivo del **dashboard público en hall de edificios**?

### Despliegue
12. ¿La universidad tiene restricciones para **deploy en cloud** (Vercel, Koyeb)? ¿Debe ser on-premise?
13. ¿Existe ya **infraestructura compatible** (Active Directory, SSO) que debamos integrar?

---

## D. Ingeniería Industrial — Preguntas Técnicas

### KPIs y medición
1. ¿Las **fórmulas de IEH, TPP y CPE** se alinean con estándares ICONTEC GTC 24 o normativa nacional?
2. ¿El **CPE de 14.04 L/estudiante/día** está alineado con benchmarks similares en otras universidades públicas?
3. ¿Es válido proponer un **KPI adicional ICA (Índice Calidad Agua)** basado en turbidez o requiere parámetros más amplios?
4. ¿Qué frecuencia de **reporte de KPIs** es apropiada para gestión universitaria (diario, semanal, mensual)?

### Lean y mejora continua
5. ¿Las **7 mudas identificadas** se pueden documentar formalmente con metodología **Value Stream Mapping**?
6. ¿El **diagrama Ishikawa** es la herramienta apropiada o sería mejor un **árbol de fallas (FTA)**?
7. ¿Las **acciones de mejora** propuestas están alineadas con metodologías Lean Six Sigma reconocidas?

### Costo-beneficio y ROI
8. ¿Los costos en **COP** que estamos proyectando ($3,500/m³) son realistas para tarifa industrial EMCALI?
9. ¿La **TIR > 1,000%** es defendible ante un comité financiero, o es preferible un cálculo más conservador?
10. ¿Deberíamos incluir **costos ocultos** como capacitación al personal, mantenimiento de sensores, etc.?
11. ¿El **horizonte de 5 años** es apropiado para cálculo de VPN, o se prefiere 10 años para infraestructura?

### Sostenibilidad
12. ¿Cómo cuantificar el **impacto en ODS** de manera auditable para reporte de sostenibilidad institucional?
13. ¿La **Resolución 0631/2015** aplica a vertimientos del campus o solo aguas de proceso industrial?
14. ¿Qué métricas usan otras universidades colombianas para reportar **uso eficiente del agua**?

### Gamificación
15. ¿Es viable crear un **sistema de Créditos Hídricos** que afecte presupuesto real de bienestar universitario?
16. ¿Cómo evitar que la **eco-competencia** entre edificios genere conflictos en lugar de cooperación?
17. ¿Se puede integrar con sistemas existentes de **bienestar estudiantil** (puntos canjeables, descuentos)?

---

## E. Preguntas de Ejecución y Negocio

### Implementación post-hackathon
1. ¿Cuál es el **proceso para escalar de prototipo a piloto institucional**?
2. ¿Qué **alianzas** debería buscar el equipo (Gobernación del Valle, EMCALI, universidades vecinas)?
3. ¿Cómo presentar el caso a **rectoría** para obtener financiación de la Fase 1 ($1M COP)?
4. ¿Existe **convocatoria interna** para proyectos de innovación que pudiéramos aplicar?

### Modelo de negocio
5. Si Camaleón OS funciona en UNIAJC, ¿podría **comercializarse** a otras universidades como producto/servicio?
6. ¿Cómo balancear el **modelo open source** con potencial monetización (consultoría, soporte)?
7. ¿La universidad tiene políticas de **propiedad intelectual** que debamos considerar?

### Equipo y continuidad
8. ¿Cómo asegurar la **continuidad del proyecto** una vez termine el hackathon (estudiantes graduándose)?
9. ¿Es viable convertir Camaleón OS en una **electiva** o **proyecto de grado** con el grupo de investigación?

---

## F. Preguntas Críticas que el Jurado Probablemente Hará

### Defensa anticipada
1. **"¿Por qué crear un nuevo sistema cuando hay SCADA industrial probado?"**
   → *Camaleón OS no compite con SCADA — los complementa con IA, gamificación y costo accesible. SCADA cuesta $50M+, Camaleón $1M y abre datos a comunidad.*

2. **"¿La IA es realmente necesaria o están sobre-ingenierizando?"**
   → *Sin IA solo tenemos umbrales fijos. La IA correlaciona caudal+presión+vibración para detectar fugas que ningún umbral simple detectaría. Y aprende del histórico del campus.*

3. **"¿Qué pasa si el agente toma una decisión incorrecta y cierra una válvula crítica?"**
   → *Doble validación: 3 agentes deben coincidir + alerta humana en < 30s + override manual desde dashboard. En piloto Fase 1 se requiere confirmación humana antes de actuar.*

4. **"¿Por qué no usar sensores comerciales certificados?"**
   → *Para Fase 1 (validación de hipótesis) los sensores económicos son suficientes. Una vez probado el ROI, Fase 2 escala con sensores certificados ICONTEC.*

5. **"¿Cómo se sostiene el sistema si los estudiantes que lo crearon se gradúan?"**
   → *Open source · documentación profesional · alianza con grupo de investigación · electiva de profundización · transferencia gradual al área de servicios generales.*

6. **"¿La universidad tiene WiFi cubriendo la PTAP?"**
   → *Sí en hall, parcial en exterior. Plan B: módem 4G dedicado por nodo ($45K/mes equivalente).*

7. **"¿Qué pasa con el agua que ya está en las tuberías cuando se cierra la válvula?"**
   → *La válvula corta el flujo aguas arriba. El agua aguas abajo continúa hacia los puntos de uso normales. Cero impacto en servicio.*

---

*Lista de preguntas estratégicas · Camaleón OS · Hackathon UNIAJC 2026*
