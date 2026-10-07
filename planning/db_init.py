import logging
import datetime
from django.db import connection, transaction
from django.utils import timezone

logger = logging.getLogger('planning')


def _is_postgres():
    """Detecta si el motor activo es PostgreSQL. Evita import circular con db_utils."""
    try:
        from planning.db_utils import is_postgres
        return is_postgres()
    except Exception:
        from django.conf import settings
        engine = settings.DATABASES.get('default', {}).get('ENGINE', '')
        return 'postgresql' in engine


SQLITE_MCT_SCHEMA = """
CREATE TABLE IF NOT EXISTS mct_cliente (
    idcliente INTEGER PRIMARY KEY,
    rut TEXT,
    digito TEXT,
    nombrecliente TEXT,
    telefono TEXT,
    direccion TEXT,
    email TEXT,
    estado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mct_producto (
    idproducto INTEGER PRIMARY KEY,
    nombreproducto TEXT,
    idcliente INTEGER,
    caudal INTEGER,
    rpm INTEGER,
    altura INTEGER,
    potencia INTEGER,
    estado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mct_estadoorden (
    idestadoorden INTEGER PRIMARY KEY,
    nombreestado TEXT,
    estado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mct_ordentrabajo (
    idordentrabajo INTEGER PRIMARY KEY,
    idcliente INTEGER,
    idproducto INTEGER,
    idcotizacion INTEGER,
    idtipoorden INTEGER,
    nombreordentrabajo TEXT,
    ordencompra INTEGER,
    fecharecepcion TIMESTAMP,
    fechaentrega TIMESTAMP,
    fechasolicitudentrega TIMESTAMP,
    idusuario INTEGER,
    idestadoorden INTEGER,
    prioridad INTEGER DEFAULT 1,
    idfamilia INTEGER,
    fechacreacion TIMESTAMP,
    usuariocreacion TEXT
);

CREATE TABLE IF NOT EXISTS mct_componente (
    idcomponente INTEGER PRIMARY KEY,
    nombrecomponente TEXT,
    estado INTEGER DEFAULT 1,
    cantidad INTEGER DEFAULT 1,
    aplicafresa BOOLEAN DEFAULT 0,
    aplicaevaluacion BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS mct_parte (
    idparte INTEGER PRIMARY KEY,
    nombreparte TEXT,
    idplano INTEGER,
    idmaterial INTEGER,
    idtipoparte INTEGER,
    costofabricacion INTEGER,
    esprincipal INTEGER DEFAULT 0,
    escritico INTEGER DEFAULT 0,
    estado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mct_ordentrabajoparte (
    idordentrabajoparte INTEGER PRIMARY KEY,
    idordentrabajo INTEGER,
    idparte INTEGER,
    idcomponente INTEGER,
    itemparte INTEGER,
    itemcorr INTEGER
);

CREATE TABLE IF NOT EXISTS mct_hojaruta (
    idhojaruta INTEGER PRIMARY KEY,
    idordentrabajoparte INTEGER,
    codhojaruta TEXT,
    fechacreacion TIMESTAMP,
    fechafundicion TIMESTAMP,
    modalidad INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mct_seccion (
    idseccion INTEGER PRIMARY KEY,
    nombreseccion TEXT,
    codigoseccion TEXT,
    estado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mct_actividad (
    idactividad INTEGER PRIMARY KEY,
    nombreactividad TEXT,
    estado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mct_maquina (
    idmaquina INTEGER PRIMARY KEY,
    idsubseccion INTEGER,
    nombremaquina TEXT,
    codigomaquina TEXT,
    estado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mct_operador (
    idoperador INTEGER PRIMARY KEY,
    nombreoperador TEXT,
    rut TEXT,
    idmaquina INTEGER,
    idseccionprincipal INTEGER,
    idperfil INTEGER,
    estado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mct_movimientoordentrabajo (
    idmovimientoordentrabajo INTEGER PRIMARY KEY,
    idordentrabajo INTEGER,
    idhojaruta INTEGER,
    codhojaruta TEXT,
    idparte INTEGER,
    idmaquina INTEGER,
    idseccion INTEGER,
    idactividad INTEGER,
    idaccion INTEGER,
    fechainicio TIMESTAMP,
    fechatermino TIMESTAMP,
    codigoaccion TEXT,
    estadoactividad INTEGER DEFAULT 1,
    numeroinspeccion TEXT,
    idoperador INTEGER,
    tiempotrabajado INTEGER,
    idmotivocierre INTEGER,
    idcausacierre INTEGER,
    observacion TEXT,
    reprocesosol TEXT,
    reprocesocc TEXT,
    checkncbomba BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS mct_sla (
    idsla INTEGER PRIMARY KEY,
    nombresla TEXT,
    idestadoinicial INTEGER,
    idestadofinal INTEGER,
    escritico INTEGER DEFAULT 0,
    diastramo INTEGER,
    estado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mct_progavisos (
    idprogaviso INTEGER PRIMARY KEY AUTOINCREMENT,
    idordentrabajo INTEGER,
    idsla INTEGER,
    fecha_inicio TIMESTAMP,
    fecha_termino TIMESTAMP,
    fecha_inicio_aviso TIMESTAMP,
    dias_tramo INTEGER,
    estado INTEGER DEFAULT 1,
    fecha_real_termino TIMESTAMP,
    ordenproceso INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mct_movimientobloqueo (
    idmovimientobloqueo INTEGER PRIMARY KEY,
    idregistrotrabajo INTEGER,
    codhojaruta TEXT,
    idoperador INTEGER,
    idseccion INTEGER,
    idmotivobloqueo INTEGER,
    fecharebloqueo TIMESTAMP,
    fechadesbloqueo TIMESTAMP,
    idoperadordesbloquea INTEGER,
    estadobloqueo INTEGER DEFAULT 1
);
"""


def init_database_tables():
    """Ejecuta el DDL de SQLite para crear las tablas mct_* si no existen.
    
    En modo PostgreSQL, las tablas mct_* ya existen en el esquema 'traking'.
    Esta función solo ejecuta el DDL en SQLite.
    """
    if _is_postgres():
        logger.info("Modo PostgreSQL: tablas mct_* existen en la BD real (esquema traking). Omitiendo DDL SQLite.")
        return
    logger.info("Creando / verificando tablas mct_* en SQLite...")
    with connection.cursor() as cursor:
        cursor.executescript(SQLITE_MCT_SCHEMA)
    logger.info("Tablas mct_* creadas con éxito.")



def seed_poc_data():
    """
    Pobla la base de datos con información industrial de bombas hidráulicas
    y casos de prueba sintéticos controlados según la sección 45 del prompt base.

    En modo PostgreSQL:
    - Omite la creación de tablas mct_* (ya existen en esquema traking)
    - Omite la inserción de datos de prueba en tablas mct_*
    - Ejecuta solo la inicialización de PocConfigPriorizacion
    """
    if _is_postgres():
        logger.info("Modo PostgreSQL: omitiendo seed de datos mct_* (datos reales disponibles en PostgreSQL).")
        _init_poc_config()
        return

    init_database_tables()
    logger.info("Iniciando sembrado de datos industriales para la POC...")

    now = timezone.now() if timezone.is_aware(timezone.now()) else datetime.datetime.now()
    # Usaremos datetime naive estándar para consistencia
    if hasattr(now, 'tzinfo') and now.tzinfo is not None:
        now = now.replace(tzinfo=None)


    with connection.cursor() as cursor:
        # 1. Clientes
        cursor.execute("DELETE FROM mct_cliente;")
        clientes = [
            (101, '76123456', '7', 'Codelco División Andina', '+56 34 2492000', 'Av. Santa Teresa 555, Los Andes', 'contacto.andina@codelco.cl', 1),
            (102, '77234567', '8', 'Minera Escondida BHP', '+56 55 2240000', 'Av. de la Minería 501, Antofagasta', 'compras@bhp.com', 1),
            (103, '78345678', '9', 'Anglo American Los Bronces', '+56 2 22306000', 'Pedro de Valdivia 291, Santiago', 'operaciones@angloamerican.com', 1),
            (104, '79456789', 'K', 'Antofagasta Minerals Los Pelambres', '+56 53 2542000', 'Salamanca s/n, Coquimbo', 'abastecimiento@aminerals.cl', 1),
        ]
        cursor.executemany("INSERT INTO mct_cliente VALUES (?,?,?,?,?,?,?,?);", clientes)

        # 2. Productos (Bombas Hidráulicas Industriales)
        cursor.execute("DELETE FROM mct_producto;")
        productos = [
            (201, 'Bomba Slurry Centrífuga Warman 10x8', 101, 1200, 950, 45, 180, 1),
            (202, 'Bomba Multietapa Sulzer MSD 400', 102, 850, 1480, 220, 450, 1),
            (203, 'Bomba Autocebante Gorman-Rupp T8', 103, 400, 1150, 35, 75, 1),
            (204, 'Bomba Sumergible Flygt 3153', 104, 300, 1450, 28, 45, 1),
        ]
        cursor.executemany("INSERT INTO mct_producto VALUES (?,?,?,?,?,?,?,?);", productos)

        # 3. Estados de Orden
        cursor.execute("DELETE FROM mct_estadoorden;")
        estados = [
            (1, 'Recepcionada / Pendiente', 1),
            (2, 'En Proceso / Taller', 1),
            (3, 'Bloqueada / Espera', 1),
            (4, 'Control de Calidad', 1),
            (5, 'Terminada / Lista Despacho', 1),
        ]
        cursor.executemany("INSERT INTO mct_estadoorden VALUES (?,?,?);", estados)

        # 4. Secciones
        cursor.execute("DELETE FROM mct_seccion;")
        secciones = [
            (1, 'Mecanizado Tornos', 'SEC-TOR', 1),
            (2, 'Mecanizado Fresas', 'SEC-FRE', 1),
            (3, 'Mecanizado CNC 5 Ejes', 'SEC-CNC', 1),
            (4, 'Mandrinado Pesado', 'SEC-MAN', 1),
            (5, 'Armado y Ajuste', 'SEC-ARM', 1),
            (6, 'Banco de Pruebas Hidrostáticas', 'SEC-PRU', 1),
        ]
        cursor.executemany("INSERT INTO mct_seccion VALUES (?,?,?,?);", secciones)

        # 5. Actividades
        cursor.execute("DELETE FROM mct_actividad;")
        actividades = [
            (1, 'Torneado desbaste y terminado cuello eje', 1),
            (2, 'Fresado chaveteros y guías', 1),
            (3, 'Mecanizado multieje perfil álabe impulsor', 1),
            (4, 'Mandrinado cavidad voluta y pestañas', 1),
            (5, 'Ajuste estático y balanceo dinámico', 1),
            (6, 'Prueba hidrostática y curva Q-H', 1),
            (7, 'Inspección tintes penetrantes NDT', 1),
        ]
        cursor.executemany("INSERT INTO mct_actividad VALUES (?,?,?);", actividades)

        # 6. Máquinas (40h semanales de disponibilidad base)
        cursor.execute("DELETE FROM mct_maquina;")
        maquinas = [
            (1, 1, 'Torno Paralelo Pesado Boehringer', 'M-01', 1),
            (2, 1, 'Torno CNC Doosan Puma 400', 'M-02', 1),
            (3, 2, 'Fresadora Universal Correa', 'M-03', 1),
            (4, 4, 'Mandrinadora CNC WMW 110', 'M-04', 1),
            (5, 3, 'Centro Mecanizado 5 Ejes Mazak Variaxis', 'M-05', 1),  # Cuello de botella
            (6, 6, 'Banco Pruebas Hidráulicas Flowserve', 'M-06', 1),
        ]
        cursor.executemany("INSERT INTO mct_maquina VALUES (?,?,?,?,?);", maquinas)

        # 7. Operadores
        cursor.execute("DELETE FROM mct_operador;")
        operadores = [
            (1, 'Carlos Muñoz P.', '12.345.678-9', 1, 1, 1, 1),
            (2, 'Roberto Valenzuela G.', '13.456.789-0', 2, 1, 2, 1),
            (3, 'Eduardo Morales T.', '14.567.890-1', 3, 2, 2, 1),
            (4, 'Juan Pablo Silva L.', '15.678.901-2', 4, 4, 3, 1),
            (5, 'Rodrigo Fernández M.', '16.789.012-3', 5, 3, 3, 1),
            (6, 'Mario González A.', '17.890.123-4', 6, 6, 4, 1),
        ]
        cursor.executemany("INSERT INTO mct_operador VALUES (?,?,?,?,?,?,?);", operadores)

        # 8. Componentes
        cursor.execute("DELETE FROM mct_componente;")
        componentes = [
            (1, 'Carcasa Voluta Bomba Warman', 1, 1, 1, 1),
            (2, 'Eje Impulsor Forjado AISI 4140', 1, 1, 0, 1),
            (3, 'Impulsor Cerrado 5 Alabes Alto Cromo', 1, 1, 1, 1),
            (4, 'Camisa de Desgaste Frontal Ni-Hard', 1, 1, 0, 0),
            (5, 'Tapa de Succión con Brida ANSI', 1, 1, 1, 0),
        ]
        cursor.executemany("INSERT INTO mct_componente VALUES (?,?,?,?,?,?);", componentes)

        # 9. Partes
        cursor.execute("DELETE FROM mct_parte;")
        partes = [
            (1, 'Voluta Fundición Blanca 28% Cr', 1001, 1, 1, 2800, 1, 1, 1),  # Crítico
            (2, 'Eje Mecanizado Tratado', 1002, 2, 1, 1400, 1, 1, 1),        # Crítico
            (3, 'Impulsor 5 Alabes Balanceado', 1003, 1, 1, 2100, 1, 1, 1),    # Crítico
            (4, 'Camisa Desgaste Revestida', 1004, 3, 2, 750, 0, 0, 1),
            (5, 'Tapa Succión Mecanizada', 1005, 1, 2, 920, 0, 0, 1),
        ]
        cursor.executemany("INSERT INTO mct_parte VALUES (?,?,?,?,?,?,?,?,?);", partes)

        # 10. SLAs
        cursor.execute("DELETE FROM mct_sla;")
        slas = [
            (1, 'Evaluación y Diagnóstico Inicial', 1, 2, 1, 2, 1),
            (2, 'Mecanizado y Reacondicionamiento', 2, 3, 1, 7, 1),
            (3, 'Armado y Balanceo Dinámico', 3, 4, 1, 3, 1),
            (4, 'Pruebas Hidrostáticas y Calidad', 4, 5, 0, 2, 1),
        ]
        cursor.executemany("INSERT INTO mct_sla VALUES (?,?,?,?,?,?,?);", slas)

        # 11. Órdenes de Trabajo (OTs)
        # OTs con fechas relativas a 'now':
        # OT 30101 (OT A): Alta prioridad comercial (5), plazo muy ajustado (2 días), tiempo corto (4h).
        # OT 30102 (OT B): Media prioridad (2), plazo holgado (12 días), tiempo largo (26h).
        # OT 30103: En máquina M-05 (Mazak), plazo normal (5 días).
        # OT 30104: Con bloqueo registrado.
        # OT 30105: Con retraso en SLA.
        # OT 30106: OT urgente adicional para simulación.
        cursor.execute("DELETE FROM mct_ordentrabajo;")
        t_recep_1 = (now - datetime.timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
        t_entrega_1 = (now + datetime.timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')

        t_recep_2 = (now - datetime.timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')
        t_entrega_2 = (now + datetime.timedelta(days=12)).strftime('%Y-%m-%d %H:%M:%S')

        t_recep_3 = (now - datetime.timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        t_entrega_3 = (now + datetime.timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')

        t_recep_4 = (now - datetime.timedelta(days=4)).strftime('%Y-%m-%d %H:%M:%S')
        t_entrega_4 = (now + datetime.timedelta(days=4)).strftime('%Y-%m-%d %H:%M:%S')

        t_recep_5 = (now - datetime.timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
        t_entrega_5 = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')  # Entrega vencida (atrasada)

        t_recep_6 = now.strftime('%Y-%m-%d %H:%M:%S')
        t_entrega_6 = (now + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')  # Urgencia crítica

        ots = [
            (30101, 102, 202, 5001, 1, 'OT-30101 Bomba Sulzer Minera Escondida (OT A)', 9001, t_recep_1, t_entrega_1, t_entrega_1, 1, 2, 5, 1, t_recep_1, 'alexis'),
            (30102, 101, 201, 5002, 1, 'OT-30102 Bomba Warman Codelco (OT B)', 9002, t_recep_2, t_entrega_2, t_entrega_2, 1, 2, 2, 1, t_recep_2, 'alexis'),
            (30103, 104, 201, 5003, 1, 'OT-30103 Bomba Warman Los Pelambres', 9003, t_recep_3, t_entrega_3, t_entrega_3, 1, 2, 3, 1, t_recep_3, 'alexis'),
            (30104, 103, 203, 5004, 1, 'OT-30104 Bomba Gorman-Rupp Anglo American', 9004, t_recep_4, t_entrega_4, t_entrega_4, 1, 3, 4, 1, t_recep_4, 'alexis'),
            (30105, 101, 201, 5005, 1, 'OT-30105 Bomba Warman Andina Retrasada', 9005, t_recep_5, t_entrega_5, t_entrega_5, 1, 2, 4, 1, t_recep_5, 'alexis'),
            (30106, 102, 202, 5006, 1, 'OT-30106 Urgencia Parada de Planta Escondida', 9006, t_recep_6, t_entrega_6, t_entrega_6, 1, 1, 5, 1, t_recep_6, 'alexis'),
        ]
        cursor.executemany("INSERT INTO mct_ordentrabajo VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", ots)

        # 12. OT Partes (mct_ordentrabajoparte)
        cursor.execute("DELETE FROM mct_ordentrabajoparte;")
        ot_partes = [
            (401, 30101, 2, 2, 1, 1),  # OT 30101 (OT A): Eje impulsor (Crítico - Impacto Crítico)
            (402, 30102, 5, 5, 1, 1),  # OT 30102 (OT B): Tapa de succión (Estándar - Impacto Medio)
            (404, 30103, 3, 3, 1, 1),  # OT 30103: Impulsor Mazak 5 ejes
            (405, 30104, 4, 4, 1, 1),  # OT 30104: Camisa de desgaste
            (406, 30105, 1, 1, 1, 1),  # OT 30105: Voluta (Crítico)
        ]
        cursor.executemany("INSERT INTO mct_ordentrabajoparte VALUES (?,?,?,?,?,?);", ot_partes)

        # 13. Hojas de Ruta (mct_hojaruta)
        cursor.execute("DELETE FROM mct_hojaruta;")
        hojas = [
            (501, 401, 'HR-30101-EJE', t_recep_1, None, 1),
            (502, 402, 'HR-30102-TAP', t_recep_2, None, 1),
            (504, 404, 'HR-30103-IMP', t_recep_3, None, 1),
            (505, 405, 'HR-30104-CAM', t_recep_4, None, 1),
            (506, 406, 'HR-30105-VOL', t_recep_5, None, 1),
        ]
        cursor.executemany("INSERT INTO mct_hojaruta VALUES (?,?,?,?,?,?);", hojas)

        # 14. Movimientos de Orden de Trabajo (mct_movimientoordentrabajo)
        # Permite cálculos estadísticos, duración real, desviación, cuellos de botella, movimientos abiertos, reprocesos.
        cursor.execute("DELETE FROM mct_movimientoordentrabajo;")
        # Formatos de fecha para movimientos históricos y activos:
        # Movimiento 1 (Cerrado): 4.0 horas en M-02
        m1_ini = (now - datetime.timedelta(days=2, hours=6)).strftime('%Y-%m-%d %H:%M:%S')
        m1_fin = (now - datetime.timedelta(days=2, hours=2)).strftime('%Y-%m-%d %H:%M:%S')

        # Movimiento 2 (Cerrado con desviación alta y reproceso): 14.0 horas en M-04
        m2_ini = (now - datetime.timedelta(days=4, hours=16)).strftime('%Y-%m-%d %H:%M:%S')
        m2_fin = (now - datetime.timedelta(days=4, hours=2)).strftime('%Y-%m-%d %H:%M:%S')

        # Movimiento 3 (Cerrado en M-05 - Centro 5 ejes): 18.0 horas
        m3_ini = (now - datetime.timedelta(days=3, hours=20)).strftime('%Y-%m-%d %H:%M:%S')
        m3_fin = (now - datetime.timedelta(days=3, hours=2)).strftime('%Y-%m-%d %H:%M:%S')

        # Movimiento 4 (ABIERTO actualmente en M-05): inició hace 3.5 horas, sin término
        m4_ini = (now - datetime.timedelta(hours=3, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')

        # Movimiento 5 (BLOQUEADO en M-01)
        m5_ini = (now - datetime.timedelta(days=1, hours=8)).strftime('%Y-%m-%d %H:%M:%S')

        # Movimiento 6 (Cerrado histórico en M-05 para cola y cuello de botella): 15.0 horas
        m6_ini = (now - datetime.timedelta(days=5, hours=22)).strftime('%Y-%m-%d %H:%M:%S')
        m6_fin = (now - datetime.timedelta(days=5, hours=7)).strftime('%Y-%m-%d %H:%M:%S')

        # Movimiento 7 (Histórico en M-01): 8.0 horas
        m7_ini = (now - datetime.timedelta(days=6, hours=10)).strftime('%Y-%m-%d %H:%M:%S')
        m7_fin = (now - datetime.timedelta(days=6, hours=2)).strftime('%Y-%m-%d %H:%M:%S')

        # Movimiento 8 (Histórico en M-02): 5.0 horas
        m8_ini = (now - datetime.timedelta(days=7, hours=12)).strftime('%Y-%m-%d %H:%M:%S')
        m8_fin = (now - datetime.timedelta(days=7, hours=7)).strftime('%Y-%m-%d %H:%M:%S')

        # Movimiento 9 (Histórico en M-05 para generar alta carga/cuello de botella): 16.0 horas
        m9_ini = (now - datetime.timedelta(days=2, hours=20)).strftime('%Y-%m-%d %H:%M:%S')
        m9_fin = (now - datetime.timedelta(days=2, hours=4)).strftime('%Y-%m-%d %H:%M:%S')

        movimientos = [
            (601, 30101, 501, 'HR-30101-EJE', 2, 2, 1, 1, 1, m1_ini, m1_fin, 'ACC-MEC', 2, 'INSP-01', 2, 240, 1, 1, 'Mecanizado conforme eje templado', None, None, 0),
            (602, 30102, 502, 'HR-30102-TAP', 5, 4, 4, 4, 1, m2_ini, m2_fin, 'ACC-MAN', 2, 'INSP-02', 4, 840, 1, 2, 'Detectada porosidad en pestaña, requirió repaso', 'SOL-01', 'CC-POROSIDAD', 1),
            (603, 30103, 504, 'HR-30103-IMP', 3, 5, 3, 3, 1, m3_ini, m3_fin, 'ACC-CNC', 2, 'INSP-03', 5, 1080, 1, 1, 'Perfil de álabe conforme', None, None, 0),
            (604, 30103, 504, 'HR-30103-IMP', 3, 5, 3, 3, 1, m4_ini, None, 'ACC-CNC', 1, 'INSP-04', 5, None, None, None, 'En proceso actual en Mazak Variaxis', None, None, 0),
            (605, 30104, 505, 'HR-30104-CAM', 4, 1, 1, 1, 1, m5_ini, None, 'ACC-TOR', 3, 'INSP-05', 1, None, None, None, 'Movimiento bloqueado por falta de inserto cerámico', None, None, 0),
            (606, 30105, 506, 'HR-30105-VOL', 1, 5, 3, 3, 1, m6_ini, m6_fin, 'ACC-CNC', 2, 'INSP-06', 5, 900, 1, 1, 'Mecanizado cara apoyo', None, None, 0),
            (607, 30101, 501, 'HR-30101-EJE', 2, 1, 1, 1, 1, m7_ini, m7_fin, 'ACC-TOR', 2, 'INSP-07', 1, 480, 1, 1, 'Desbaste inicial eje', None, None, 0),
            (608, 30102, 502, 'HR-30102-TAP', 5, 2, 1, 1, 1, m8_ini, m8_fin, 'ACC-TOR', 2, 'INSP-08', 2, 300, 1, 1, 'Frenteado de bridas tapa', None, None, 0),
            (609, 30103, 504, 'HR-30103-IMP', 3, 5, 3, 3, 1, m9_ini, m9_fin, 'ACC-CNC', 2, 'INSP-09', 5, 960, 1, 1, 'Acabado de álabes complejos', None, None, 0),
        ]
        cursor.executemany("INSERT INTO mct_movimientoordentrabajo VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", movimientos)

        # 15. Movimiento Bloqueo (mct_movimientobloqueo)
        cursor.execute("DELETE FROM mct_movimientobloqueo;")
        bloq_ini = (now - datetime.timedelta(days=1, hours=6)).strftime('%Y-%m-%d %H:%M:%S')
        bloqueos = [
            (701, 605, 'HR-30104-CAM', 1, 1, 101, bloq_ini, None, None, 1),  # Bloqueo ACTIVO (no desbloqueado)
            (702, 602, 'HR-30102-TAP', 4, 4, 102, (now - datetime.timedelta(days=4, hours=10)).strftime('%Y-%m-%d %H:%M:%S'), (now - datetime.timedelta(days=4, hours=6)).strftime('%Y-%m-%d %H:%M:%S'), 4, 2),  # Bloqueo resuelto (4h)
        ]
        cursor.executemany("INSERT INTO mct_movimientobloqueo VALUES (?,?,?,?,?,?,?,?,?,?);", bloqueos)

        # 16. Programación de Avisos / SLAs (mct_progavisos)
        cursor.execute("DELETE FROM mct_progavisos;")
        p_ini_1 = (now - datetime.timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
        p_fin_1 = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        p_real_1 = (now - datetime.timedelta(days=1, hours=2)).strftime('%Y-%m-%d %H:%M:%S')

        p_ini_2 = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        p_fin_2 = (now + datetime.timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')

        progavisos = [
            (1, 30101, 1, p_ini_1, p_fin_1, p_ini_1, 2, 2, p_real_1, 1),
            (2, 30101, 2, p_ini_2, p_fin_2, p_ini_2, 3, 1, None, 2),
            (3, 30105, 2, (now - datetime.timedelta(days=8)).strftime('%Y-%m-%d %H:%M:%S'), (now - datetime.timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'), (now - datetime.timedelta(days=8)).strftime('%Y-%m-%d %H:%M:%S'), 6, 1, None, 2),  # Retrasado
        ]
        cursor.executemany("INSERT INTO mct_progavisos VALUES (?,?,?,?,?,?,?,?,?,?);", progavisos)

    logger.info("Datos sembrados exitosamente en mct_*.")

    # 17. Inicializar Configuración POC si no existe
    from planning.models import PocConfigPriorizacion
    config, created = PocConfigPriorizacion.objects.get_or_create(
        id=1,
        defaults={
            'nombre': 'Configuración Estándar POC Bombas',
            'peso_due_date': 0.40,
            'peso_holgura': 0.25,
            'peso_impacto': 0.20,
            'peso_wspt': 0.10,
            'peso_comercial': 0.05,
            'umbral_amarillo_horas': 2.0,
            'umbral_rojo_horas': 6.0,
            'costo_hora_hombre': 28.5,
            'costo_hora_maquina': 52.0,
            'is_active': True,
        }
    )
    if created:
        logger.info("Configuración de priorización POC creada con valores base.")
