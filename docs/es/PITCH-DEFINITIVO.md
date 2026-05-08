# AguaMind OS — Pitch Definitivo (5 minutos)

> Versión final del pitch tras feedback del jurado.
> Foco: **agentes IA cognitivos + acción autónoma + economía circular**.
> Cero énfasis en "dashboard bonito". Total énfasis en "lo que ningún
> sistema hace antes".

---

## 0:00 – 0:30 · APERTURA QUE ROMPE EXPECTATIVAS

> *"Antes de empezar, tengo una pregunta para el jurado: ¿cuántos litros de
> agua perdió esta universidad mientras yo decía estas palabras?*
>
> *La respuesta es: 9 litros. Y nadie en UNIAJC se ha enterado todavía.*
>
> *Cada minuto, en silencio, esta planta de tratamiento del 2011 deja
> escapar agua que nadie mide. Lleva 13 años haciéndolo.*
>
> *Hoy les vamos a presentar el sistema que va a escuchar esas tuberías,
> entender qué dicen, y actuar antes de que sea tarde."*

---

## 0:30 – 1:15 · EL PROBLEMA NO ES LA FUGA, ES LA CEGUERA

Tres datos que el jurado debe recordar:

```
  113.56  L/min     ← caudal entrada PTAP
   45,367  L/día    ← consumo medido
   13,610  L/día    ← pérdidas estimadas (30%)
        0  sensores ← ninguno mide nada
```

> *"Y mientras 8,234 personas usan agua sin saberlo, las dos PTAR del
> campus (Alameda y Entrada, cada una con 2 modulos de 1,000 estudiantes)
> tienen capacidad combinada para 4,000 estudiantes. Eso significa que
> cada día estamos descargando aguas residuales que pueden no cumplir la
> Resolución 0631 del Ministerio de Ambiente.*
>
> *Una multa por incumplimiento es 5,000 SMMLV. Hoy. Seis mil quinientos
> millones de pesos. Eso es 6,500 veces lo que cuesta nuestra solución."*

---

## 1:15 – 2:30 · LA INNOVACIÓN: 5 AGENTES IA QUE DELIBERAN

> *"Lo que vamos a mostrarles ahora no es un dashboard. Es un cerebro.*
>
> *AguaMind OS no tiene 'una IA'. Tiene cinco. Y cada una hace algo
> diferente. Y deliberan entre ellas antes de actuar. Como un comité
> técnico de mantenimiento que nunca duerme."*

```
        [Sensor detecta vibración + presión cae 28%]
                          ↓
                  [Orchestrator]
                          ↓
        ┌──────────┬──────┴──────┬──────────┐
        ↓          ↓             ↓          ↓
    Systems    Sensor       Industrial  Mitigation
    Agent      Agent        Agent       Agent
        ↓          ↓             ↓          ↓
    "anomalía" "señales OK" "patrón Lean" "cierro EV-A2"
                          ↓
              [Decisión consensual en 3 segundos]
                          ↓
        [Cierra válvula → notifica → genera OT]
```

**Aquí abrimos el dashboard en vivo. Click en tab "Mitigación".**

> *"En la pantalla pueden ver el mapa del campus en tiempo real. PTAP,
> aljibes, los dos tanques, los seis edificios, las dos PTAR descargando
> al río Pance.*
>
> *Voy a inyectar una fuga ahora mismo."* **[Click en "leak"]**
>
> *"En 5 segundos, el SystemsAgent detectó la anomalía. El SensorAgent
> validó las señales. El IndustrialAgent reconoció el patrón Lean. El
> MitigationAgent cerró la electroválvula EV-A2. Y nuestros teléfonos
> recibieron este mensaje de Telegram."* **[mostrar Telegram]**

---

## 2:30 – 3:30 · LO QUE HACEMOS QUE NADIE HACE

Cinco diferenciadores irrepetibles:

### 1. Escuchamos las tuberías (acústico + TinyML)
> *"Cada nodo ESP32 ejecuta un modelo de IA local de 2 KB que aprende la
> 'huella sonora' del agua corriendo por las tuberías. Detecta fugas
> antes de que sean visibles. Esto se llama Edge ML Federado y es la misma
> tecnología que usa Singapur en su Smart Water Network."*

### 2. Tokenizamos el CO₂ evitado
> *"Cada acción del agente genera un token criptográfico auditable. UNIAJC
> puede vender estos créditos en mercados voluntarios de carbono. La
> universidad no solo ahorra agua: gana ingresos por sostenibilidad."*

### 3. Gamificamos con economía real
> *"Smart Water Ledger. Un crédito hídrico es un metro cúbico ahorrado.
> Mil créditos son tres millones y medio de pesos que la facultad
> reinvierte en proyectos propuestos por estudiantes. La cafetería ya
> está liderando con 320 créditos este mes."*

### 4. Cumplimos la ley sin esfuerzo
> *"Reporte mensual al INVIMA, trimestral a la CVC, semestral al
> Ministerio de Vivienda. Todo automático. Cero papeleo. Cero riesgo
> de sanción."*

### 5. Hablamos. Literalmente.
> *"El jefe de mantenimiento no usa pantallas. Usa voz. 'AguaMind, ¿cómo
> está el tanque A?' Y AguaMind responde por audio en Telegram. En español.
> En tiempo real."*

---

## 3:30 – 4:15 · EL IMPACTO REAL EN NÚMEROS

```
  $1.4 millones COP    ← inversión Fase 1 (un nodo PTAP)
       21 días         ← período de recuperación
       470 %           ← TIR a 5 años
   16.5 M de litros    ← agua recuperada en 5 años
       7.6 ton CO₂     ← evitadas en 5 años
        5 ODS          ← directamente impactados
       8,234 usuarios  ← beneficiados
        4 universidades en cola para replicar (proyecciones equipo)
```

> *"Y el dato que más nos importa: en seis meses, AguaMind OS protege a
> UNIAJC de una exposición legal de DIECISIETE MIL MILLONES DE PESOS por
> incumplimiento normativo. Esa es la pregunta que sus auditores de
> calidad les van a hacer mañana."*

---

## 4:15 – 4:45 · POR QUÉ NO PODÍAMOS NO HACER ESTO

> *"Tres cosas hicimos que ningún equipo competidor puede igualar:*
>
> *Primero: leímos las tres tesis de UNIAJC sobre la PTAP. Aristizábal y
> Largacha, 2025. Arias Montoya, 2024. Mosquera y Lozano, 2024. Cada una
> documenta un problema. Nosotros los resolvemos todos con un solo sistema.*
>
> *Segundo: respetamos el plano técnico real de la PTAP que ustedes nos
> dieron. Tres filtros: grava, antracita, carbón activado. Tanque de
> cloración. Dos tanques de almacenamiento. Bombas Barnes, hidroneumáticos
> Altamira. Códigos oficiales: SF-FT-01, SD-BD-01. Todos están en
> nuestro modelo.*
>
> *Tercero: integramos las normas. Decreto 1575 de 2007. Resolución 2115.
> Decreto 1076 de 2015. Resolución 0631 de 2015. La Ley 1581 de Habeas
> Data. La Ley 1712 de Transparencia. Hasta la Resolución 055 de UNIAJC
> de enero de este año.*
>
> *No vinimos a improvisar. Vinimos a resolver."*

---

## 4:45 – 5:00 · CIERRE QUE QUEDA EN LA CABEZA

> *"AguaMind OS no es un proyecto. Es un manifiesto.*
>
> *Decimos que las universidades públicas pueden ser laboratorios de
> Smart Cities. Decimos que un equipo de tres ingenierías puede construir
> en dos días lo que multinacionales cobran en cincuenta millones. Decimos
> que el código abierto es el nuevo activismo ambiental.*
>
> *Y decimos: gracias por dejarnos demostrarlo.*
>
> *AguaMind OS. Tecnología con Propósito. Inteligencia con Conciencia.*
>
> *El agua de UNIAJC, bajo control. Hoy. Mañana. Y en cada universidad
> colombiana que copie nuestro repositorio."*

---

## ANEXO — Q&A anticipado

### "¿Por qué no usaron un SCADA tradicional?"
> Cuesta $50 millones, es cerrado, no aprende, no cumple normativa
> automáticamente, no se conecta con la comunidad. Nuestro sistema cuesta
> $1.4M, es open source, multiagente y replicable.

### "¿Qué pasa si el agente toma una decisión incorrecta?"
> Triple validación: 5 agentes deben coincidir, alerta humana en menos de
> 30 segundos, override manual desde dashboard. En Fase 1 piloto requerimos
> confirmación humana antes de actuar.

### "¿Cómo aseguran la calidad de los datos?"
> SensorAgent valida cada lectura contra rangos físicos imposibles. Cero
> tolerancia a sensores defectuosos. Calibración trimestral documentada.

### "¿Y si los estudiantes que crearon esto se gradúan?"
> El código está en GitHub público. La documentación está en español.
> El semillero SEGESTOP puede continuar el proyecto. Y existen más de 50
> ingenieros graduados al año en UNIAJC que pueden mantenerlo.

### "¿Qué piensan hacer los próximos 6 meses?"
> Mes 1: instalar el primer nodo en la PTAP.
> Mes 2-3: extender a Bloque A y Cancha.
> Mes 4-6: sensores en PTAR + reporte automático CVC.
> Mes 7+: replicación a Sede Norte y Centro.

---

*Pitch versión 2.0 · Post-feedback jurado · AguaMind OS*
