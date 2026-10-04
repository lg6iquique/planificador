Contexto:
apoyate tecnicamente en readme.md y ARQUITECTURE.MD
desarrollo desantendido
para esta ocusion ocupar sqllite para reemplazar mariadb
Estoy trabajando en un proyecto Django llamado "planificador".

# POC — SISTEMA DE PLANIFICACIÓN INDUSTRIAL PARA BOMBAS HIDRÁULICAS

## 1. ROL DEL AGENTE

Actúa como un desarrollador Senior Full Stack + Data Engineer + especialista en sistemas de planificación industrial, análisis de datos y arquitectura Django.

Debes trabajar directamente sobre el proyecto y sobre el archivo SQL adjunto:

`estructurasql.sql`

El archivo contiene la estructura real de una base de datos PostgreSQL existente, con numerosas tablas, funciones, secuencias, índices y objetos.

Tu objetivo NO es reconstruir toda la aplicación existente.

Tu objetivo es construir una **POC funcional de un sistema de planificación de producción/reparación**, reutilizando y aprovechando las tablas reales que sean relevantes.

---

# 2. REGLA FUNDAMENTAL DE AUTONOMÍA

## IMPORTANTE: NO PREGUNTAR INNECESARIAMENTE

Procede de manera autónoma.

NO detengas el desarrollo para preguntar:

* qué nombre darle a una variable;
* qué nombre darle a una función;
* qué estructura de carpetas utilizar;
* qué formato de endpoint utilizar;
* qué librería estándar utilizar;
* si crear un test;
* si corregir un error evidente;
* si agregar validaciones;
* si documentar una función;
* si crear datos de prueba;
* si ejecutar una prueba;
* si continuar con la siguiente etapa.

Toma decisiones técnicas razonables y profesionales.

Si existen varias alternativas técnicamente válidas, elige la alternativa:

1. más simple;
2. mantenible;
3. compatible con Django;
4. compatible con futura migración a PostgreSQL;
5. adecuada para una POC;
6. que no obligue a rehacer posteriormente toda la arquitectura.

NO esperes confirmación para decisiones técnicas menores.

---

# 3. REGLA DE VALIDACIÓN

Aunque debes trabajar autónomamente, NO debes asumir que el código funciona.

Cada etapa debe ser validada mediante pruebas.

El principio es:

> IMPLEMENTAR → EJECUTAR → PROBAR → DETECTAR ERROR → CORREGIR → VOLVER A PROBAR.

No declares una etapa terminada solamente porque el código fue escrito.

Debes comprobar realmente:

* que Django inicia;
* que la base de datos conecta;
* que los modelos pueden consultar;
* que los JOIN principales funcionan;
* que los cálculos entregan resultados;
* que los endpoints responden;
* que los datos no generan errores;
* que los casos límite funcionan;
* que las pruebas automatizadas pasan.

Si una prueba falla, corrige el problema y vuelve a ejecutarla.

No me preguntes si deseas que corrijas el error.

Corrígelo.

---

# 4. OBJETIVO DE LA POC

Construir una primera versión funcional de un sistema capaz de analizar y apoyar la planificación de órdenes de trabajo relacionadas con fabricación, reparación y procesamiento de componentes de bombas hidráulicas.

La POC debe permitir demostrar:

1. identificación de órdenes de trabajo;
2. identificación de partes y componentes;
3. identificación de hojas de ruta;
4. identificación de actividades/movimientos;
5. identificación de máquinas;
6. identificación de trabajadores/operadores;
7. cálculo de duración real;
8. comparación entre tiempo planificado y tiempo real;
9. identificación de horas muertas/holguras;
10. identificación de bloqueos;
11. cálculo de prioridad;
12. generación de una secuencia recomendada;
13. análisis de capacidad;
14. identificación de posibles cuellos de botella;
15. simulación de una urgencia;
16. explicación de por qué una OT fue priorizada.

NO implementar todavía Machine Learning.

NO implementar todavía optimización matemática avanzada.

NO implementar todavía microservicios.

NO implementar Java/Spring Boot.

NO implementar todavía Angular.

La POC será exclusivamente:

**Python + Django + base de datos + lógica analítica/planificación.**

---

# 5. TECNOLOGÍA DE LA POC

Utilizar:

* Python
* Django
* Django ORM
* Django REST Framework si resulta conveniente para exponer API REST
* Pandas para análisis
* NumPy cuando sea necesario
* pytest o Django Test Framework
* MariaDB como base de datos de desarrollo de la POC
* Git

No utilizar Java.

No utilizar Spring Boot.

No utilizar Angular.

No utilizar microservicios.

La arquitectura debe quedar preparada para posteriormente agregar:

* PostgreSQL
* Angular
* Spring Boot, si posteriormente se decide incorporarlo
* Machine Learning
* optimización matemática.

---

# 6. BASE DE DATOS

## IMPORTANTE

El archivo `estructurasql.sql` corresponde a un dump PostgreSQL.

NO intentes ejecutar ciegamente el dump completo sobre MariaDB.

El archivo contiene elementos específicos de PostgreSQL, incluyendo:

* schema `traking`;
* sequences;
* funciones PL/pgSQL;
* casts;
* sintaxis PostgreSQL;
* funciones específicas;
* índices y objetos auxiliares.

Para esta POC:

1. analizar primero el SQL;
2. identificar las tablas relevantes;
3. utilizar solamente las tablas necesarias;
4. crear/adaptar en MariaDB solamente el subconjunto requerido;
5. conservar los nombres originales `mct_*` cuando sea razonable;
6. mantener los nombres de columnas originales cuando sea posible;
7. evitar modificar la estructura original innecesariamente;
8. documentar cualquier adaptación realizada.

La migración futura a PostgreSQL debe ser sencilla.

---

# 7. IMPORTANTE SOBRE LAS TABLAS

NO construir un modelo conceptual gigante con todas las tablas del SQL.

El archivo contiene muchas tablas que pertenecen a otras funcionalidades del sistema original.

Para esta POC utilizar un modelo conceptual reducido.

La relación central conocida es:

```text
mct_ordentrabajo
        |
        | 1:N
        v
mct_ordentrabajoparte
        |
        | idcomponente
        v
mct_componente
        |
        |
        +---- idparte
        |
        v
mct_hojaruta
        |
        | idhojaruta
        v
mct_movimientoordentrabajo
```

Pero esta relación debe ser VALIDADA contra el SQL antes de implementarse.

No inventar relaciones que no estén respaldadas por el esquema.

---

# 8. TABLAS PRINCIPALES DE LA POC

## 8.1 mct_ordentrabajo

Es la entidad principal de la orden de trabajo.

Utilizar los campos que realmente existan en el SQL.

Debe analizarse especialmente:

* idordentrabajo
* idcliente
* idcotizacion
* idtipoorden
* idproducto
* nombreordentrabajo
* ordencompra
* fecharecepcion
* fechaentrega
* idusuario
* fechasolicitudentrega
* idestadoorden
* prioridad
* idfamilia
* cualquier campo adicional relevante para planificación

NO inventar columnas.

Primero revisar la definición completa de la tabla en el SQL.

---

# 9. mct_ordentrabajoparte

Esta tabla es fundamental.

Relaciona:

```text
OT
 |
 +-- Parte
 |
 +-- Componente
```

El SQL confirma:

```text
idordentrabajoparte
idordentrabajo
idparte
idcomponente
itemparte
itemcorr
```

Utilizar esta tabla para determinar qué componentes/partes necesita procesar cada OT.

---

# 10. mct_componente

Representa los componentes principales de la bomba.

El SQL contiene, entre otros:

* idcomponente
* nombrecomponente
* estado
* evaluaciondirecta
* idareaclasificacion
* idresponsablefundicion
* aplicafresa
* aplicaevaluacion
* cantidad

Para la POC considerar al componente como una entidad importante para medir:

* cantidad de trabajo;
* criticidad;
* duración;
* impacto;
* historial;
* bloqueo potencial de la OT.

No inventar una columna de "criticidad" si no existe.

Si se necesita para la POC, puede derivarse mediante una regla configurable en Python o mediante una tabla de configuración propia de la POC.

---

# 11. mct_hojaruta

Esta tabla es fundamental.

El SQL contiene:

```text
idhojaruta
idordentrabajoparte
codhojaruta
fechacreacion
fechafundicion
modalidad
idhojarutatemp
```

Utilizarla para representar el flujo/ruta de trabajo de una parte.

La relación esperada es:

```text
mct_ordentrabajoparte
        |
        | idordentrabajoparte
        v
mct_hojaruta
```

Validar esta relación en el SQL.

---

# 12. mct_movimientoordentrabajo

Esta será una de las tablas MÁS IMPORTANTES de la POC.

El SQL muestra información como:

```text
idmovimientoordentrabajo
idordentrabajo
idhojaruta
codhojaruta
idparte
idmaquina
idseccion
idactividad
idaccion
fechainicio
fechatermino
codigoaccion
estadoactividad
numeroinspeccion
idoperador
idtipomovimiento
idsubseccion
tiempotrabajado
idmotivocierre
idcausacierre
observacion
...
```

Esta tabla debe utilizarse para obtener:

* tiempo real;
* duración de actividad;
* trabajador;
* máquina;
* parte;
* sección;
* actividad;
* acción;
* estado;
* movimientos abiertos/cerrados;
* reprocesos;
* observaciones;
* posibles horas muertas.

---

# 13. CÁLCULO DEL TIEMPO REAL

Para movimientos cerrados:

```text
TiempoReal =
    fechatermino - fechainicio
```

Expresar el resultado en:

* minutos;
* horas.

Si `fechatermino` es NULL:

```text
TiempoActual =
    ahora - fechainicio
```

Pero distinguir claramente:

```text
MOVIMIENTO ABIERTO
```

de

```text
MOVIMIENTO CERRADO
```

No mezclar ambos como si fueran tiempos reales definitivos.

---

# 14. mct_progavisos

Esta tabla DEBE ser analizada e incorporada a la POC.

Contiene:

* idordentrabajo
* idsla
* fecha_inicio
* fecha_termino
* fecha_inicio_aviso
* dias_tramo
* estado
* fecha_real_termino
* ordenproceso
* otros campos relacionados.

El campo:

```text
ordenproceso
```

representa el orden de ejecución del SLA según el propio SQL.

Utilizar esta tabla para comparar:

```text
PLANIFICADO
vs
REAL
```

y detectar:

* retrasos;
* adelantos;
* desviaciones;
* acumulación de retrasos;
* impacto de una etapa sobre las posteriores.

---

# 15. mct_movimientobloqueo

DEBE incorporarse al análisis.

La tabla contiene:

```text
idmovimientobloqueo
idregistrotrabajo
codhojaruta
idoperador
idseccion
idmotivobloqueo
fecharebloqueo
fechadesbloqueo
idoperadordesbloquea
estadobloqueo
```

Utilizarla para calcular:

```text
TiempoBloqueo =
    fechadesbloqueo - fecharebloqueo
```

Esto permitirá distinguir:

```text
TiempoTrabajo
TiempoBloqueado
TiempoEspera/Holgura
```

cuando los datos disponibles permitan hacerlo.

---

# 16. mct_maquina

Utilizar:

* idmaquina
* idsubseccion
* nombremaquina
* estado
* códigos de máquina disponibles.

Relacionar con:

```text
mct_movimientoordentrabajo.idmaquina
```

El objetivo es obtener:

```text
OT
→ Parte
→ Actividad
→ Máquina
→ Tiempo
```

Esto será la base para detectar utilización y posibles cuellos de botella.

---

# 17. mct_operador

Utilizar:

* idoperador
* nombreoperador
* estado
* idperfil
* idmaquina
* idseccionprincipal
* idcargo
* idarea
* iniciales

y otros campos relevantes.

Relacionar con:

```text
mct_movimientoordentrabajo.idoperador
```

Esto permitirá analizar:

* carga por trabajador;
* horas trabajadas;
* distribución de trabajo;
* concentración de actividades;
* disponibilidad, cuando los datos permitan determinarla.

---

# 18. OTRAS TABLAS QUE DEBES BUSCAR EN EL SQL

Antes de finalizar el modelo de la POC, revisa el archivo completo buscando tablas que puedan aportar información directamente relacionada con:

### Producto

Buscar:

* mct_producto
* mct_modelo
* mct_subfamilia
* mct_familia

### Parte

Buscar:

* mct_parte
* tablas relacionadas con tipo de parte
* tablas de componente/parte

### Actividad

Buscar:

* mct_actividad
* mct_accion
* mct_seccion
* mct_subseccion

### Planificación

Buscar:

* mct_progavisos
* tablas de SLA
* tablas de programación
* tablas de planificación

### Recursos

Buscar:

* mct_maquina
* mct_operador
* mct_operadorseccion
* tablas de turnos
* tablas de disponibilidad

### Bloqueos

Buscar:

* mct_movimientobloqueo
* motivos de bloqueo
* causas de cierre
* motivos de cierre

### Reprocesos / calidad

Buscar:

* campos de reproceso dentro de `mct_movimientoordentrabajo`;
* tablas de evaluación;
* tablas de defectos;
* tablas de rechazo;
* tablas de NCF.

### Materiales

Buscar:

* mct_material
* relaciones producto-parte
* relaciones parte-material.

---

# 19. CRITERIO PARA INCLUIR UNA TABLA

Una tabla solamente debe incorporarse al modelo de la POC si cumple al menos una de estas condiciones:

1. permite calcular tiempo;
2. permite conocer una OT;
3. permite conocer una parte;
4. permite conocer un componente;
5. permite conocer una actividad;
6. permite conocer una máquina;
7. permite conocer un trabajador;
8. permite conocer una fecha comprometida;
9. permite conocer una restricción;
10. permite conocer un bloqueo;
11. permite conocer un reproceso;
12. permite conocer una prioridad;
13. permite explicar una desviación.

No incorporar tablas solamente porque existen.

---

# 20. MODELO CONCEPTUAL REDUCIDO

La POC debe intentar llegar inicialmente a algo cercano a:

```text
CLIENTE
   |
   v
ORDEN_TRABAJO
   |
   +----------------------+
   |                      |
   v                      v
PRODUCTO              PROG_AVISOS
   |
   |
ORDEN_TRABAJO_PARTE
   |
   +------------+
   |            |
   v            v
PARTE       COMPONENTE
   |
   v
HOJA_RUTA
   |
   v
MOVIMIENTO_OT
   |
   +----------+----------+
   |          |          |
   v          v          v
MAQUINA   OPERADOR    ACTIVIDAD/ACCION
   |
   v
CAPACIDAD

MOVIMIENTO_OT
   |
   v
BLOQUEOS
```

Esta estructura es conceptual.

Debe ajustarse a las relaciones reales encontradas en el SQL.

---

# 21. NO CREAR UNA COPIA ARTIFICIAL DEL MODELO

No crear inmediatamente nuevas tablas duplicando todas las existentes.

Preferir:

```text
Django ORM
      |
      v
tablas existentes
```

cuando las tablas sean utilizables.

Para tablas existentes que Django no administra:

```python
class Meta:
    managed = False
    db_table = "mct_ordentrabajo"
```

cuando corresponda.

No ejecutar migraciones destructivas sobre tablas existentes.

---

# 22. TABLAS PROPIAS DE LA POC

Si se requiere guardar información nueva que no existe en el sistema original, sí se pueden crear tablas propias.

Por ejemplo:

```text
poc_config_priorizacion
poc_planificacion
poc_planificacion_detalle
poc_simulacion
poc_evento_planificacion
```

Pero mantenerlas separadas conceptualmente de las tablas originales.

Usar un nombre claro, por ejemplo:

```text
poc_*
```

Esto facilitará posteriormente separar:

```text
DATOS ORIGINALES
```

de

```text
DATOS GENERADOS POR EL SISTEMA DE PLANIFICACIÓN
```

---

# 23. ARQUITECTURA DJANGO

Crear una arquitectura limpia.

Ejemplo:

```text
project/
│
├── manage.py
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── planning/
│   ├── models/
│   ├── services/
│   ├── repositories/
│   ├── serializers/
│   ├── views/
│   ├── urls.py
│   ├── tests/
│   └── admin.py
│
├── analytics/
│   ├── services/
│   ├── calculations/
│   └── tests/
│
├── scheduling/
│   ├── services/
│   ├── rules/
│   ├── simulation/
│   └── tests/
│
├── database/
│   ├── scripts/
│   └── documentation/
│
└── docs/
```

No sobrearquitecturar.

La estructura puede simplificarse si el tamaño real de la POC no justifica tantos módulos.

---

# 24. SEPARACIÓN DE RESPONSABILIDADES

No colocar toda la lógica dentro de las views Django.

Separar:

```text
View/API
   ↓
Service
   ↓
Repository/ORM
   ↓
Database
```

La lógica analítica debe estar en servicios independientes.

Por ejemplo:

```python
calculate_real_duration()
calculate_deviation()
calculate_slack()
calculate_critical_ratio()
calculate_wspt()
calculate_priority_score()
calculate_machine_capacity()
detect_bottlenecks()
generate_schedule()
simulate_urgent_order()
calculate_opportunity_cost()
```

---

# 25. ANÁLISIS ESTADÍSTICO

La POC debe calcular inicialmente:

### Media

```text
mean
```

### Mediana

```text
median
```

### Percentiles

```text
P50
P75
P90
P95
```

### Desviación estándar

```text
std
```

### Mínimo y máximo

```text
min
max
```

Analizar duración por:

* componente;
* parte;
* actividad;
* máquina;
* operador;
* tipo de OT;
* producto;
* proceso.

---

# 26. TIEMPO ESTÁNDAR

No inventar un tiempo estándar arbitrario si existe información histórica suficiente.

Inicialmente calcular:

```text
TiempoEstimadoBase = MedianaHistórica
```

cuando existan suficientes observaciones comparables.

Cuando existan pocos registros:

```text
TiempoEstimadoBase = P75
```

o utilizar una regla configurable.

Documentar la decisión.

---

# 27. DESVIACIÓN

Calcular:

```text
DesviacionHoras =
TiempoReal - TiempoEstimado
```

y:

```text
DesviacionPorcentaje =
(TiempoReal - TiempoEstimado) / TiempoEstimado * 100
```

Semáforo:

```text
VERDE
AMARILLO
ROJO
```

Los límites deben ser configurables.

---

# 28. HOLGURA

Calcular:

```text
Holgura =
HorasDisponiblesHastaEntrega - HorasTrabajoPendientes
```

Interpretación:

```text
Holgura > 0
    existe margen

Holgura ≈ 0
    situación crítica

Holgura < 0
    existe riesgo de atraso
```

---

# 29. CRITICAL RATIO

Calcular:

```text
CriticalRatio =
HorasDisponiblesHastaEntrega / HorasTrabajoPendientes
```

Interpretación:

```text
> 1     margen
≈ 1     ajustado
< 1     riesgo
```

---

# 30. WSPT

Implementar como indicador:

```text
WSPT =
Peso / TiempoProcesamiento
```

Utilizarlo como una regla auxiliar.

No presentarlo como un algoritmo completo de scheduling.

---

# 31. PRIORIZACIÓN

Implementar inicialmente:

```text
ScorePrioridad =
    0.40 * ScoreDueDate
  + 0.25 * ScoreHolgura
  + 0.20 * ScoreImpacto
  + 0.10 * ScoreWSPT
  + 0.05 * ScoreComercial
```

Todos los factores deben normalizarse previamente a:

```text
0 - 100
```

---

# 32. PRIORIDAD COMERCIAL

La prioridad comercial debe ser explícita.

Escala:

```text
1 = Normal
2 = Importante
3 = Alta
4 = Muy alta
5 = Crítica
```

No permitir que la prioridad comercial domine silenciosamente el algoritmo.

Los pesos deben ser configurables.

---

# 33. EXPLICABILIDAD

Para cada OT mostrar algo similar a:

```text
OT 30215

Score total: 82.5

DueDate:       92
Holgura:       85
Impacto:       90
WSPT:          65
Comercial:     60

Razón principal:

"OT priorizada debido a baja holgura, fecha de entrega próxima
y alto impacto operacional."
```

La POC debe permitir explicar por qué una OT quedó antes que otra.

---

# 34. EJEMPLO CRÍTICO

Debe existir una prueba donde:

```text
OT A
Tiempo = 1 hora
Impacto = crítico

OT B
Tiempo = 9 horas
Impacto = medio
```

El sistema NO debe asumir automáticamente que A siempre va primero.

Debe evaluar:

* fecha de entrega;
* holgura;
* impacto;
* tiempo;
* recursos;
* máquina;
* efecto sobre las demás OT.

---

# 35. PRIORIDAD VS SCHEDULING

Mantener separadas estas tres ideas:

```text
PRIORIDAD
¿Qué debería atender primero?

SCHEDULING
¿Cuándo y dónde se ejecuta?

OPTIMIZACIÓN
¿Cuál es la mejor combinación considerando restricciones y objetivos?
```

La POC implementará principalmente:

```text
PRIORIDAD
+
SCHEDULING BÁSICO
```

---

# 36. CAPACIDAD

La planificación debe considerar que una máquina no puede ejecutar infinitas tareas simultáneamente.

Calcular:

```text
Utilizacion =
HorasAsignadas / HorasDisponibles * 100
```

Detectar:

```text
máquina saturada
máquina subutilizada
cola de trabajos
```

---

# 37. CUELLO DE BOTELLA

Detectar máquinas con:

* alta utilización;
* exceso de cola;
* muchas horas pendientes;
* múltiples OT esperando;
* elevada concentración de operaciones.

Ejemplo:

```text
Máquina M-05

Disponibilidad: 40 h
Carga:           47 h

Utilización: 117.5%

ALERTA:
Capacidad insuficiente.
```

---

# 38. HORAS MUERTAS

Analizar especialmente los movimientos de `mct_movimientoordentrabajo`.

El propio SQL contiene lógica para calcular diferencias de tiempo entre movimientos y horas muertas, por lo que esta información debe ser aprovechada como referencia funcional.

No asumir que toda diferencia entre movimientos es automáticamente "hora muerta".

Clasificar cuando sea posible:

```text
Trabajo
Espera
Bloqueo
Pausa
Reproceso
Cambio de actividad
```

---

# 39. REPROCESO

Buscar dentro de:

```text
mct_movimientoordentrabajo
```

campos como:

```text
reprocesosol
reprocesocc
checkncbomba
descripcioncc
```

y tablas adicionales de evaluación/rechazo.

Crear un indicador:

```text
CantidadReprocesos
```

cuando los datos permitan determinarlo.

---

# 40. COSTO DE OPORTUNIDAD

Cuando una OT urgente desplaza una OT planificada:

registrar:

```text
OT desplazada
Inicio planificado
Nuevo inicio
Horas de retraso
Costo hora hombre
Costo hora máquina
Costo operacional estimado
```

Fórmula inicial:

```text
HorasRetraso =
NuevoInicio - InicioPlanificado
```

```text
CostoOperacionHora =
CostoHoraHombre + CostoHoraMaquina
```

```text
CostoOportunidad =
HorasRetraso * CostoOperacionHora
```

Llamarlo:

**Costo operacional estimado / costo de oportunidad**

No presentarlo automáticamente como pérdida contable.

---

# 41. SIMULACIÓN

Crear una función:

```python
simulate_urgent_order()
```

Debe permitir:

```text
situación actual
vs
situación con nueva urgencia
```

Comparar:

### Escenario A

Minimizar horas/costo.

### Escenario B

Maximizar cumplimiento de fecha.

### Escenario C

Balancear costo y servicio.

Mostrar:

```text
OT desplazadas
horas desplazadas
máquinas saturadas
atrasos generados
costo operacional estimado
```

---

# 42. PLANIFICACIÓN HUMANO + SISTEMA

En esta POC el sistema NO debe reemplazar inicialmente al planificador.

Debe producir:

```text
Secuencia recomendada
```

El usuario debería poder conceptualmente:

```text
ACEPTAR
MODIFICAR
RECHAZAR
```

La decisión debe poder registrarse.

Esto será importante para una futura etapa de Machine Learning.

---

# 43. ENDPOINTS MÍNIMOS

Crear API REST cuando resulte apropiado:

```text
GET /api/ordenes/
GET /api/ordenes/{id}/
GET /api/componentes/
GET /api/partes/
GET /api/maquinas/
GET /api/operadores/
GET /api/hojas-ruta/
GET /api/movimientos/
GET /api/capacidad/
GET /api/priorizacion/
GET /api/cuello-botella/
GET /api/analisis/tiempos/
GET /api/analisis/desviaciones/

POST /api/scheduling/calcular/
POST /api/simulaciones/urgencia/
```

Adaptar los nombres a la arquitectura real del proyecto.

---

# 44. PRIMERA VERSIÓN DE UI

No crear Angular.

Utilizar:

* Django Templates;
* Bootstrap si resulta conveniente;
* tablas HTML;
* filtros;
* indicadores simples.

Pantallas mínimas:

```text
1. Inicio
2. Órdenes de Trabajo
3. Detalle OT
4. Movimientos
5. Análisis de tiempos
6. Priorización
7. Planificación
8. Capacidad
9. Cuellos de botella
10. Simulación
```

No construir un dashboard complejo.

La POC debe privilegiar la funcionalidad sobre el diseño.

---

# 45. DATOS REALES VS DATOS SINTÉTICOS

Si la base contiene suficientes datos reales:

usar datos reales para el análisis histórico.

No reemplazarlos innecesariamente por datos sintéticos.

Si faltan datos para probar determinados escenarios:

crear datos sintéticos controlados exclusivamente para testing.

Identificarlos claramente como:

```text
TEST
SYNTHETIC
POC
```

No mezclarlos silenciosamente con datos reales.

---

# 46. PRUEBAS OBLIGATORIAS

Crear pruebas para:

### Test 1

Django inicia correctamente.

### Test 2

Conexión a MariaDB.

### Test 3

Consulta de OT.

### Test 4

OT → OT Parte.

### Test 5

OT Parte → Componente.

### Test 6

OT Parte → Hoja de Ruta.

### Test 7

Hoja de Ruta → Movimiento.

### Test 8

Movimiento → Máquina.

### Test 9

Movimiento → Operador.

### Test 10

Cálculo de duración.

### Test 11

Cálculo de desviación.

### Test 12

Cálculo de holgura.

### Test 13

Critical Ratio.

### Test 14

WSPT.

### Test 15

Priority Score.

### Test 16

Máquina saturada.

### Test 17

Movimiento abierto.

### Test 18

Movimiento bloqueado.

### Test 19

Urgencia que desplaza otra OT.

### Test 20

Explicabilidad de prioridad.

---

# 47. CASOS LÍMITE

También probar:

```text
fechainicio NULL
fechatermino NULL
fechatermino < fechainicio
OT sin componente
OT sin máquina
OT sin operador
OT sin hoja de ruta
máquina inexistente
tiempo cero
tiempo negativo
fecha de entrega vencida
holgura negativa
máquina sin capacidad
varias OT para la misma máquina
```

El sistema no debe romperse.

Debe entregar errores controlados o resultados explícitos.

---

# 48. VALIDACIÓN DE DATOS

Crear una rutina de Data Quality.

Validar:

```text
OT sin fecha
OT sin fecha entrega
OT sin parte
OT sin componente
OT sin hoja de ruta
movimiento sin OT
movimiento sin máquina
movimiento sin operador
duración negativa
movimiento abierto
datos duplicados
fechas inconsistentes
```

Generar un resumen:

```text
Total registros
Registros válidos
Registros con problemas
% calidad
Principales problemas
```

---

# 49. LOGGING

Implementar logging básico.

Registrar:

```text
inicio de cálculo
fin de cálculo
cantidad de OT procesadas
errores
warnings
tiempo de ejecución
```

No utilizar `print()` como mecanismo principal de logging.

---

# 50. DOCUMENTACIÓN AUTOMÁTICA

Crear:

```text
README.md
```

Debe explicar:

1. objetivo;
2. arquitectura;
3. instalación;
4. configuración MariaDB;
5. estructura de tablas utilizada;
6. cómo ejecutar Django;
7. cómo ejecutar tests;
8. endpoints;
9. lógica de priorización;
10. lógica de planificación;
11. limitaciones de la POC;
12. camino hacia PostgreSQL.

---

# 51. RESULTADO ESPERADO

Al finalizar debe existir una POC ejecutable donde pueda realizarse algo similar a:

```text
1. Seleccionar fecha de planificación.

2. Obtener OT pendientes.

3. Obtener partes/componentes.

4. Obtener hojas de ruta.

5. Obtener movimientos históricos.

6. Calcular tiempos históricos.

7. Estimar tiempos.

8. Calcular holguras.

9. Calcular Critical Ratio.

10. Calcular prioridad.

11. Revisar capacidad de máquinas.

12. Generar secuencia recomendada.

13. Detectar cuellos de botella.

14. Simular una urgencia.

15. Mostrar impacto.

16. Explicar la decisión.
```

---

# 52. FUTURA EVOLUCIÓN

La arquitectura debe permitir evolucionar:

```text
POC ACTUAL

Django
Python
MariaDB
Django ORM
Pandas
Reglas de planificación
        |
        v
ETAPA 2

Django
PostgreSQL
REST API
Frontend
        |
        v
ETAPA 3

Scheduling avanzado
Optimización
        |
        v
ETAPA 4

Machine Learning
XGBoost
Random Forest
Predicción de duración
Predicción de atraso
Predicción de reproceso
        |
        v
ETAPA 5

Optimización matemática
Constraint Programming
What-if avanzado
Aprendizaje continuo
```

---

# 53. MACHINE LEARNING FUTURO

NO implementar ahora.

Pero diseñar los datos para posteriormente poder predecir:

```text
TiempoRealReparacion
ProbabilidadAtraso
ProbabilidadReproceso
```

Posibles variables futuras:

```text
Modelo
Producto
Componente
Parte
TipoOrden
TipoTrabajo
Máquina
Operador
Turno
CargaMáquina
TiempoHistórico
Bloqueos
Reprocesos
Prioridad
Urgencia
Complejidad
```

---

# 54. NO HACER

No hacer:

* Java;
* Spring Boot;
* Angular;
* microservicios;
* Kafka;
* Kubernetes;
* ML prematuro;
* optimización matemática compleja en la primera iteración;
* dashboard sofisticado;
* reconstrucción de todas las tablas del SQL;
* modificación destructiva de tablas existentes;
* ejecución ciega del dump PostgreSQL sobre MariaDB;
* copiar toda la lógica PL/pgSQL existente a Django.

La POC debe demostrar primero que:

**LOS DATOS EXISTENTES PUEDEN SER UTILIZADOS PARA GENERAR INFORMACIÓN ÚTIL PARA PLANIFICACIÓN.**

---

# 55. PROCEDIMIENTO DE EJECUCIÓN DEL AGENTE

Ejecuta las siguientes fases SIN solicitar confirmación:

## FASE 1 — INSPECCIÓN

Analizar:

```text
estructurasql.sql
```

Identificar las tablas relevantes.

Generar internamente un mapa de relaciones.

No crear todavía toda la aplicación.

---

## FASE 2 — MODELO REDUCIDO

Seleccionar las tablas necesarias.

Documentar:

```text
tabla
PK
FK
propósito
relaciones
campos relevantes
```

Diferenciar:

```text
TABLA EXISTENTE
TABLA NUEVA POC
```

---

## FASE 3 — BASE DE DATOS POC

Preparar MariaDB.

Crear/adaptar únicamente las estructuras necesarias.

Validar:

```text
CREATE
INSERT
SELECT
JOIN
```

---

## FASE 4 — DJANGO

Crear proyecto Django.

Configurar:

```text
settings
database
apps
models
urls
```

Validar que Django arranca.

---

## FASE 5 — ORM

Crear modelos para las tablas relevantes.

Preferir `managed=False` cuando se trate de tablas existentes que no deben ser administradas por Django.

Crear modelos administrados para las tablas nuevas `poc_*`.

Ejecutar pruebas de consulta.

---

## FASE 6 — ANALYTICS

Implementar:

```text
duraciones
estadísticas
desviaciones
holguras
Critical Ratio
WSPT
```

Probar con datos reales y/o sintéticos.

---

## FASE 7 — PRIORIZACIÓN

Implementar:

```text
Priority Score
```

Agregar explicación de cada factor.

Crear tests.

---

## FASE 8 — CAPACIDAD

Implementar:

```text
capacidad
utilización
cola
saturación
cuellos de botella
```

Crear tests.

---

## FASE 9 — SCHEDULING

Implementar una primera secuencia heurística.

No pretender resolver todavía un problema industrial completo de optimización.

Validar restricciones básicas:

```text
máquina
capacidad
fecha entrega
prioridad
tiempo
```

---

## FASE 10 — SIMULACIÓN

Implementar:

```text
urgencia
desplazamiento
retraso
impacto
costo de oportunidad
```

Crear casos de prueba.

---

## FASE 11 — UI/API

Exponer los resultados mediante Django.

La información debe ser entendible por un usuario de planificación.

---

## FASE 12 — PRUEBA FINAL

Ejecutar TODA la batería de pruebas.

No terminar si existen errores conocidos.

Mostrar al final:

```text
Tests ejecutados
Tests aprobados
Tests fallidos
Errores corregidos
Advertencias
Limitaciones
```

---

# 56. CRITERIO DE TERMINACIÓN

Considera la POC terminada solamente cuando:

* Django inicia;
* MariaDB conecta;
* modelos principales funcionan;
* consultas principales funcionan;
* datos pueden recorrer la cadena:

OT → Parte → Componente → Hoja de Ruta → Movimiento;

* movimientos pueden relacionarse con máquina y operador;
* tiempos pueden calcularse;
* desviaciones pueden calcularse;
* bloqueos pueden analizarse;
* prioridad puede calcularse;
* capacidad puede calcularse;
* cuellos de botella pueden detectarse;
* una secuencia puede generarse;
* una urgencia puede simularse;
* el impacto puede medirse;
* las pruebas principales pasan;
* existe documentación;
* no existen errores críticos conocidos.

---

# 57. PRINCIPIO FINAL

No busques construir todavía el sistema definitivo.

Construye una POC técnicamente correcta que permita demostrar, con datos reales de la estructura existente, que es posible pasar de:

```text
DATOS OPERACIONALES
        ↓
ANÁLISIS
        ↓
TIEMPOS
        ↓
DESVIACIONES
        ↓
HOLGURAS
        ↓
PRIORIDAD
        ↓
CAPACIDAD
        ↓
PLANIFICACIÓN
        ↓
SIMULACIÓN
        ↓
DECISIÓN EXPLICABLE
```

El valor de esta POC está en demostrar la viabilidad técnica y analítica antes de invertir en una arquitectura mayor.

Trabaja de forma autónoma.

No preguntes innecesariamente.

Analiza primero.

Implementa después.

Prueba todo.

Corrige los errores.

Y continúa hasta obtener una POC funcional y verificable.
