"""
planning/db_utils.py — Capa de Acceso a Datos Centralizada

Módulo de utilidades para el manejo dual de motor de base de datos.
Todo el código de negocio debe usar estas funciones para detectar el motor activo.

Uso:
    from planning.db_utils import is_postgres, is_sqlite, get_db_info, test_connection

NUNCA dispersar lógica if/else por el código de negocio.
Este módulo es el único punto de decisión sobre el motor DB.
"""
import os
import logging
from django.conf import settings

logger = logging.getLogger('planning')


def get_db_engine() -> str:
    """
    Retorna el motor de base de datos activo: 'sqlite' o 'postgres'.
    Lee DB_ENGINE del entorno. Por defecto: 'sqlite'.
    """
    return getattr(settings, 'DB_ENGINE', os.environ.get('DB_ENGINE', 'sqlite')).lower()


def is_postgres() -> bool:
    """Retorna True si el motor activo es PostgreSQL."""
    return get_db_engine() == 'postgres'


def is_sqlite() -> bool:
    """Retorna True si el motor activo es SQLite."""
    return get_db_engine() == 'sqlite'


def get_db_info() -> dict:
    """
    Retorna información de conexión sin exponer contraseñas.

    Returns:
        dict con claves: engine, host, port, name, user, schema, engine_key
    """
    engine = get_db_engine()
    db_cfg = settings.DATABASES.get('default', {})

    if engine == 'postgres':
        return {
            'engine': 'PostgreSQL',
            'engine_key': 'postgres',
            'host': db_cfg.get('HOST', 'localhost'),
            'port': db_cfg.get('PORT', 5432),
            'name': db_cfg.get('NAME', ''),
            'user': db_cfg.get('USER', ''),
            'schema': os.environ.get('DB_SCHEMA', 'traking'),
            'password_masked': '***' if db_cfg.get('PASSWORD') else '(sin contraseña)',
        }
    else:
        return {
            'engine': 'SQLite',
            'engine_key': 'sqlite',
            'host': 'local',
            'port': None,
            'name': str(db_cfg.get('NAME', '')),
            'user': None,
            'schema': None,
            'password_masked': None,
        }


def test_connection() -> tuple[bool, str]:
    """
    Verifica que la conexión a la base de datos activa funcione.

    Returns:
        (True, mensaje_ok) o (False, mensaje_error_SIN_contraseña)
    """
    try:
        from django.db import connection
        with connection.cursor() as cur:
            if is_postgres():
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                return True, f"Conectado — {version[:60]}"
            else:
                cur.execute("SELECT sqlite_version();")
                version = cur.fetchone()[0]
                return True, f"Conectado — SQLite {version}"
    except Exception as e:
        # Filtrar contraseña del mensaje de error
        msg = str(e)
        for secret in ['password', 'contraseña', 'passw']:
            if secret in msg.lower():
                msg = "Error de autenticación. Revise la configuración de conexión."
                break
        return False, f"No fue posible conectar. {msg[:200]}"


def get_mct_tables_status() -> list[dict]:
    """
    Detecta todas las tablas mct_* en la base de datos activa y devuelve
    estado, cantidad de registros y columnas de cada una.

    Returns:
        Lista de dicts: {tabla, existe, registros, columnas, es_principal}
    """
    from django.db import connection, ProgrammingError, OperationalError

    TABLAS_PRINCIPALES = [
        'mct_ordentrabajo', 'mct_ordentrabajoparte', 'mct_componente',
        'mct_parte', 'mct_hojaruta', 'mct_movimientoordentrabajo',
        'mct_maquina', 'mct_operador', 'mct_progavisos', 'mct_movimientobloqueo',
        'mct_actividad', 'mct_seccion', 'mct_cliente', 'mct_producto',
        'mct_estadoorden', 'mct_sla',
    ]

    results = []
    schema = os.environ.get('DB_SCHEMA', 'traking')

    with connection.cursor() as cur:
        # Detectar todas las tablas mct_* existentes
        try:
            if is_postgres():
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = %s AND table_name LIKE 'mct_%%'
                    ORDER BY table_name;
                """, [schema])
            else:
                cur.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name LIKE 'mct_%'
                    ORDER BY name;
                """)
            found_tables = {row[0] for row in cur.fetchall()}
        except (ProgrammingError, OperationalError):
            found_tables = set()

        # Unión de tablas conocidas + detectadas
        all_tables = sorted(set(TABLAS_PRINCIPALES) | found_tables)

        for table in all_tables:
            exists = table in found_tables
            count = 0
            col_count = 0

            if exists:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cur.fetchone()[0]
                except (ProgrammingError, OperationalError):
                    count = -1
                    try:
                        connection.rollback()
                    except Exception:
                        pass

                try:
                    if is_postgres():
                        cur.execute("""
                            SELECT COUNT(*) FROM information_schema.columns
                            WHERE table_schema = %s AND table_name = %s;
                        """, [schema, table])
                    else:
                        cur.execute(f"PRAGMA table_info({table});")
                    col_count = cur.fetchone()[0] if is_postgres() else len(cur.fetchall())
                except (ProgrammingError, OperationalError):
                    col_count = 0

            results.append({
                'tabla': table,
                'existe': exists,
                'registros': count if exists else 0,
                'columnas': col_count,
                'es_principal': table in TABLAS_PRINCIPALES,
                'error': count == -1,
            })

    return results


def get_table_columns(table_name: str) -> list[dict]:
    """
    Retorna la lista de columnas de una tabla con tipo y nulabilidad.
    Solo permite tablas mct_* y poc_* (protección contra SQL injection).

    Args:
        table_name: Nombre de la tabla (sin prefijo de esquema)

    Returns:
        Lista de dicts: {nombre, tipo, nullable}
    """
    if not (table_name.startswith('mct_') or table_name.startswith('poc_')):
        return []

    from django.db import connection

    schema = os.environ.get('DB_SCHEMA', 'traking')
    cols = []

    with connection.cursor() as cur:
        if is_postgres():
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
            """, [schema, table_name])
            for row in cur.fetchall():
                cols.append({'nombre': row[0], 'tipo': row[1], 'nullable': row[2] == 'YES'})
        else:
            cur.execute(f"PRAGMA table_info({table_name});")
            for row in cur.fetchall():
                cols.append({'nombre': row[1], 'tipo': row[2], 'nullable': not bool(row[3])})

    return cols


def get_table_sample(table_name: str, limit: int = 50, offset: int = 0) -> tuple[list, list, int]:
    """
    Retorna una muestra de registros de una tabla mct_*.
    READ-ONLY — nunca modifica datos.
    Solo permite tablas mct_* (protección).

    Args:
        table_name: Nombre de la tabla
        limit: Máximo de filas a retornar (default 50)
        offset: Desplazamiento para paginación

    Returns:
        (columnas: list[str], filas: list[tuple], total: int)
    """
    if not table_name.startswith('mct_'):
        return [], [], 0

    from django.db import connection

    limit = min(limit, 200)  # límite de seguridad

    with connection.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        total = cur.fetchone()[0]

        cur.execute(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset};")
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    return cols, rows, total


def get_sqlite_vs_postgres_comparison() -> list[dict]:
    """
    Compara el conteo de registros de tablas mct_* entre SQLite y PostgreSQL.
    Solo ejecuta si ambas bases están accesibles.

    Returns:
        Lista de dicts: {tabla, sqlite_count, postgres_count}
    """
    TABLAS = [
        'mct_ordentrabajo', 'mct_ordentrabajoparte', 'mct_componente',
        'mct_parte', 'mct_hojaruta', 'mct_movimientoordentrabajo',
        'mct_maquina', 'mct_operador', 'mct_progavisos', 'mct_movimientobloqueo',
    ]

    results = []

    # Contar en SQLite
    sqlite_counts = {}
    try:
        import sqlite3
        from pathlib import Path
        sqlite_path = settings.BASE_DIR / 'db.sqlite3'
        if sqlite_path.exists():
            conn = sqlite3.connect(str(sqlite_path))
            cur = conn.cursor()
            for t in TABLAS:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {t};")
                    sqlite_counts[t] = cur.fetchone()[0]
                except Exception:
                    sqlite_counts[t] = None
            conn.close()
    except Exception:
        pass

    # Contar en PostgreSQL
    postgres_counts = {}
    try:
        import psycopg2
        pg_cfg = settings.DATABASES.get('default', {})
        schema = os.environ.get('DB_SCHEMA', 'traking')
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='',
            dbname='np_sis',
            options=f'-c search_path={schema},public',
            connect_timeout=3,
        )
        cur = conn.cursor()
        for t in TABLAS:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t};")
                postgres_counts[t] = cur.fetchone()[0]
            except Exception:
                postgres_counts[t] = None
                conn.rollback()
        conn.close()
    except Exception:
        pass

    for t in TABLAS:
        results.append({
            'tabla': t,
            'sqlite': sqlite_counts.get(t),
            'postgres': postgres_counts.get(t),
        })

    return results
