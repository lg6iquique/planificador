# POC — Sistema de Planificación Industrial para Bombas Hidráulicas

> **Prueba de Concepto (POC) Funcional** desarrollada en Django + Python + SQLite (preparada para PostgreSQL) para análisis, priorización multicriterio, gestión de capacidad, detección de cuellos de botella y simulación de órdenes de trabajo (OTs) en un taller metalmecánico de reparación y fabricación de bombas hidráulicas.

---

## 1. Objetivo de la POC

Demostrar de forma verificable y autónoma que los datos operacionales de un taller industrial pueden estructurarse y explotarse para generar información de alto valor para la toma de decisiones de planificación:
- Identificación de órdenes de trabajo (OTs), partes y componentes.
- Recorrido completo de rutas de trabajo mediante hojas de ruta y movimientos operacionales.
- Medición de duraciones reales, distinguiendo movimientos abiertos y cerrados.
- Análisis de holguras operacionales, Critical Ratio (CR) y regla WSPT.
- Priorización algorítmica multicriterio ponderada con explicabilidad en lenguaje natural.
- Cálculo de capacidad finita y utilización de máquinas con detección de cuellos de botella.
- Simulación interactiva de órdenes urgentes y cálculo del costo operacional estimado / costo de oportunidad.
- Auditoría continua de calidad de datos (Data Quality).
- Integración humano + sistema (Human-in-the-loop) para aceptar, modificar o rechazar secuencias propuestas.

---

## 2. Arquitectura del Proyecto

El sistema sigue las convenciones de `ARCHITECTURE.md` y las especificaciones de `PROMPT_BASE.md`:
- **Separación de responsabilidades:** `View/API → Service → Repository/ORM → Database`.
- **Apps modulares independientes:**
  - `planning`: Gestión de órdenes de trabajo, partes, componentes, hojas de ruta, máquinas, operadores y movimientos (`mct_*`), y planes de producción (`poc_*`).
  - `analytics`: Cálculo de duraciones reales, estadísticas históricas con Pandas/NumPy (mean, median, P50, P75, P90, P95, std), desviaciones y semáforos verde/amarillo/rojo.
  - `scheduling`: Motor de priorización multicriterio, cálculo de holgura, WSPT, secuenciamiento heurístico por máquina y simulación de inserción urgente de OTs.
  - `quality`: Auditoría de consistencia referencial, anomalías de fechas y panel ejecutivo.
- **Frontend limpio y funcional:** Basado en Django Templates, Bootstrap 5 y la estética visual de `template ui/img/imagen_template.PNG` (sidebar moderno, tarjetas redondeadas, badges de estado y tablas interactivas).

---

## 3. Instalación

### Requisitos Previos
- Python 3.12+
- Virtualenv (opcional o entorno local)

### Pasos de Instalación
```bash
# 1. Clonar o acceder al repositorio
cd planificador

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Aplicar migraciones para tablas del sistema y tablas POC (poc_*)
python manage.py migrate

# 4. Inicializar tablas mct_* y sembrar datos industriales de prueba
python manage.py init_poc_db
```

---

## 4. Configuración de Base de Datos (SQLite POC & MariaDB/PostgreSQL)

Por instrucción de desarrollo desatendido (línea 4 de `PROMPT_BASE.md`), esta POC utiliza **SQLite** para permitir portabilidad y ejecución autónoma inmediata en Windows sin requerir servicios de base de datos externos levantados:

```python
# config/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

Las tablas existentes del sistema original (`mct_*`) han sido modeladas con `managed = False` y nombres exactos de columnas, garantizando que el paso a PostgreSQL o MariaDB solo requiera cambiar la clave `DATABASES` en `settings.py` sin modificar el código de la aplicación.

---

## 5. Estructura de Tablas Utilizada

### 5.1 Tablas Operacionales Existentes (`mct_*`, managed=False)
- `mct_cliente`: Clientes mineros e industriales (Codelco, Escondida, Anglo American, etc.).
- `mct_producto`: Modelos de bombas hidráulicas (Warman 10x8, Sulzer MSD 400, Gorman-Rupp, Flygt).
- `mct_estadoorden`: Estados de ciclo de vida de la orden (Recepcionada, En Proceso, Bloqueada, etc.).
- `mct_ordentrabajo`: Entidad cabecera de la orden con fecha de recepción, fecha de entrega y prioridad comercial (1 a 5).
- `mct_componente`: Componentes principales (Carcasa voluta, eje forjado, impulsor cerrado, camisa, etc.).
- `mct_parte`: Piezas físicas de fabricación y reacondicionamiento con indicador `escritico` y costos.
- `mct_ordentrabajoparte`: Relación N:M entre OT, Parte y Componente.
- `mct_hojaruta`: Ruta de fabricación vinculada a cada parte.
- `mct_seccion`: Secciones de taller (Tornos, Fresas, CNC 5 Ejes, Mandrinado, Banco de Pruebas).
- `mct_actividad`: Operaciones estándar (Torneado cuello eje, mecanizado alabes, pruebas hidrostáticas, etc.).
- `mct_maquina`: Tornos, fresadoras y centros de mecanizado con disponibilidad de 40h semanales.
- `mct_operador`: Técnicos y especialistas asignados a máquinas y secciones.
- `mct_movimientoordentrabajo`: Registro de tiempos de operación (fechainicio, fechatermino, tiempotrabajado, reprocesos, estados).
- `mct_sla`: Tramos de SLA contractuales y alarmas.
- `mct_progavisos`: Seguimiento planificado vs real de hitos SLA.
- `mct_movimientobloqueo`: Registro de tiempos de bloqueo operacional por falta de planos o insumos.

### 5.2 Tablas Nuevas Propias de la POC (`poc_*`, managed=True)
- `poc_config_priorizacion`: Ponderaciones configurables de los factores de priorización y costos por hora.
- `poc_planificacion`: Encabezado de planes de secuencia heurística generados.
- `poc_planificacion_detalle`: Operaciones asignadas por máquina con secuencia y decisión humana.
- `poc_simulacion`: Registro de escenarios simulados (A, B, C), OTs diferidas y costos de oportunidad.
- `poc_evento_planificacion`: Bitácora de auditoría y gobernanza de eventos del motor.

---

## 6. Cómo Ejecutar Django

```bash
# Iniciar servidor de desarrollo
python manage.py runserver
```

Navegar a:
- **Dashboard Ejecutivo:** `http://127.0.0.1:8000/`
- **Órdenes de Trabajo:** `http://127.0.0.1:8000/planning/ordenes/`
- **Movimientos de Taller:** `http://127.0.0.1:8000/planning/movimientos/`
- **Análisis Estadístico:** `http://127.0.0.1:8000/analytics/tiempos/`
- **Desviaciones y Semáforos:** `http://127.0.0.1:8000/analytics/desviaciones/`
- **Priorización Inteligente:** `http://127.0.0.1:8000/scheduling/priorizacion/`
- **Plan y Secuencia:** `http://127.0.0.1:8000/scheduling/plan/`
- **Capacidad y Cuellos de Botella:** `http://127.0.0.1:8000/scheduling/capacidad/`
- **Simulación de Urgencias:** `http://127.0.0.1:8000/scheduling/simulacion/`
- **Calidad de Datos:** `http://127.0.0.1:8000/quality/audit/`

---

## 7. Cómo Ejecutar los Tests Automatizados

La suite incluye los **20 tests obligatorios (Sección 46)**, las pruebas de **casos límite y robustez (Sección 47)**, la prueba comparativa crítica de **OT A vs OT B (Sección 34)** y todas las vistas y endpoints API:

```bash
python manage.py test planning
```

Resultado esperado:
```text
Ran 44 tests in ~0.5s
OK
```

---

## 8. Catálogo de Endpoints API REST

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/ordenes/` | Listado JSON de órdenes de trabajo |
| `GET` | `/api/ordenes/<id>/` | Detalle JSON de OT con score y holgura |
| `GET` | `/api/componentes/` | Listado JSON de componentes de bombas |
| `GET` | `/api/partes/` | Listado JSON de partes físicas |
| `GET` | `/api/maquinas/` | Listado JSON de máquinas de taller |
| `GET` | `/api/operadores/` | Listado JSON de operadores |
| `GET` | `/api/hojas-ruta/` | Listado JSON de hojas de ruta |
| `GET` | `/api/movimientos/` | Listado JSON de movimientos operacionales |
| `GET` | `/api/capacidad/` | Utilización y cargas por máquina |
| `GET` | `/api/cuello-botella/` | Alertas de máquinas con utilización > 100% |
| `GET` | `/api/priorizacion/` | Ranking de OTs ordenadas por score de prioridad |
| `GET` | `/api/analisis/tiempos/` | Estadísticas (mean, median, P50-P95, std) |
| `GET` | `/api/analisis/desviaciones/` | Comparativa real vs estimado con semáforo |
| `POST/GET` | `/api/scheduling/calcular/` | Dispara el cálculo de nueva secuencia |
| `POST/GET` | `/api/simulaciones/urgencia/` | Ejecuta simulación de impacto de OT urgente |

---

## 9. Lógica de Priorización Multicriterio

### Fórmula de Ponderación
$$\text{ScorePrioridad} = 0.40 \cdot \text{ScoreDueDate} + 0.25 \cdot \text{ScoreHolgura} + 0.20 \cdot \text{ScoreImpacto} + 0.10 \cdot \text{ScoreWSPT} + 0.05 \cdot \text{ScoreComercial}$$

Todos los factores son normalizados a una escala de **0 a 100**:
1. **ScoreDueDate:** OTs con fecha de entrega más próxima (o vencida) obtienen mayor puntuación.
2. **ScoreHolgura:** OTs con holgura crítica o negativa ($\text{HorasDisponibles} - \text{HorasPendientes} \le 0$) reciben máxima prioridad.
3. **ScoreImpacto:** Valora la criticidad de componentes (voluta, impulsor balanceado) y valor de fabricación.
4. **ScoreWSPT:** $\frac{\text{Peso}}{\text{TiempoProcesamiento}}$ favoreciendo tareas de rápida resolución que liberan capacidad.
5. **ScoreComercial:** Nivel 1 a 5 explícito de cliente ($20 \times \text{Nivel}$).

### Explicabilidad Natural
Cada OT incluye una explicación redactada automáticamente para el planificador (ejemplo: *"OT priorizada debido a: fecha de entrega comprometida ya vencida, holgura operacional crítica (-24.0 hrs), alto impacto operacional con componentes críticos de bomba."*).

---

## 10. Lógica de Planificación, Capacidad y Simulación

### Capacidad y Cuellos de Botella
- $\text{Utilización} = \left(\frac{\text{HorasAsignadas}}{\text{HorasDisponibles}}\right) \times 100$
- Si $\text{Utilización} > 100\%$, el sistema genera una alerta visual de **capacidad insuficiente** y marca la máquina como cuello de botella (ej. Centro Mazak 5 Ejes M-05).

### Human-in-the-Loop
El motor produce una secuencia sugerida pero respeta el criterio del planificador humano:
- Los planes se inician en estado `BORRADOR`.
- El usuario puede **Aceptar**, **Modificar** o **Rechazar** tanto el plan completo como operaciones específicas.
- Todas las decisiones se auditan en `poc_evento_planificacion` para posterior entrenamiento de Machine Learning.

### Simulación de Urgencias y Costo de Oportunidad
- Al insertar una orden urgente, el motor compara 3 escenarios:
  - **Escenario A:** Minimizar costo / horas.
  - **Escenario B:** Maximizar fecha de entrega urgente (desplazamiento frontal).
  - **Escenario C:** Balanceado.
- Para cada OT desplazada se calcula:
  $$\text{HorasRetraso} = \text{NuevoInicio} - \text{InicioPlanificado}$$
  $$\text{CostoOperacionalHora} = \text{CostoHoraHombre} + \text{CostoHoraMaquina}$$
  $$\text{CostoOportunidad} = \text{HorasRetraso} \times \text{CostoOperacionalHora}$$

---

## 11. Limitaciones de la POC

1. **Heurística vs Optimización Matemática:** La POC utiliza reglas heurísticas de secuenciamiento y priorización multicriterio. No incluye aún solver MILP/CP (Constraint Programming) avanzado.
2. **Machine Learning:** Diseñado para recolectar datos y decisiones de aceptación/rechazo humano, pero los modelos predictivos (XGBoost/RandomForest) corresponden a fases posteriores.
3. **Turnos Complejos:** Asume turnos estándar de 40 horas semanales por recurso máquina sin modelar rotaciones de turnos nocturnos o festivos dinámicos.

---

## 12. Camino Hacia Producción con PostgreSQL

El diseño desacoplado de esta POC permite migrar a producción con mínimo esfuerzo:
1. **Configurar motor PostgreSQL en `settings.py`:**
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'db_traking',
           'USER': 'postgres',
           'PASSWORD': 'secret_password',
           'HOST': 'localhost',
           'PORT': '5432',
           'OPTIONS': {'options': '-c search_path=traking,public'},
       }
   }
   ```
2. **Tablas `mct_*`:** Ya existen en el dump `estructurasql.sql`. Al tener `managed = False`, Django se conectará a ellas sin intentar crearlas ni modificarlas.
3. **Tablas `poc_*`:** Ejecutar `python manage.py migrate` sobre PostgreSQL para crear únicamente las tablas analíticas y de auditoría del planificador.
