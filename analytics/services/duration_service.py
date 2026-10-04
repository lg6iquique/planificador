import logging
import datetime
from django.utils import timezone
import numpy as np
import pandas as pd
from planning.models import (
    MCTMovimientoOrdenTrabajo, MCTMovimientoBloqueo,
    MCTOrdenTrabajo, PocConfigPriorizacion
)

logger = logging.getLogger('analytics')


def get_current_time():
    """Retorna datetime naive para comparaciones consistentes en SQLite."""
    now = timezone.now()
    if hasattr(now, 'tzinfo') and now.tzinfo is not None:
        return now.replace(tzinfo=None)
    return now


def calculate_real_duration(movimiento):
    """
    Calcula la duración en horas y minutos para un movimiento de OT.
    Distingue explícitamente entre movimiento ABIERTO y CERRADO.
    Maneja casos límite: fechainicio nulo, fechatermino < fechainicio.
    """
    if not movimiento.fechainicio:
        return {
            'idmovimiento': movimiento.idmovimientoordentrabajo,
            'estado': 'SIN_FECHA_INICIO',
            'duracion_horas': 0.0,
            'duracion_minutos': 0.0,
            'es_abierto': False,
            'es_valido': False,
            'error': 'El movimiento no posee fechainicio registrada.'
        }

    ini = movimiento.fechainicio
    if hasattr(ini, 'tzinfo') and ini.tzinfo is not None:
        ini = ini.replace(tzinfo=None)

    # Caso CERRADO
    if movimiento.fechatermino:
        fin = movimiento.fechatermino
        if hasattr(fin, 'tzinfo') and fin.tzinfo is not None:
            fin = fin.replace(tzinfo=None)

        diff = (fin - ini).total_seconds()
        if diff < 0:
            return {
                'idmovimiento': movimiento.idmovimientoordentrabajo,
                'estado': 'TIEMPO_INCONSISTENTE_NEGATIVO',
                'duracion_horas': round(diff / 3600.0, 2),
                'duracion_minutos': round(diff / 60.0, 1),
                'es_abierto': False,
                'es_valido': False,
                'error': f'fechatermino ({fin}) es anterior a fechainicio ({ini}).'
            }

        return {
            'idmovimiento': movimiento.idmovimientoordentrabajo,
            'estado': 'CERRADO',
            'duracion_horas': round(diff / 3600.0, 2),
            'duracion_minutos': round(diff / 60.0, 1),
            'es_abierto': False,
            'es_valido': True,
            'error': None
        }

    # Caso ABIERTO (en proceso actual)
    now = get_current_time()
    diff = (now - ini).total_seconds()
    if diff < 0:
        diff = 0.0

    return {
        'idmovimiento': movimiento.idmovimientoordentrabajo,
        'estado': 'ABIERTO',
        'duracion_horas': round(diff / 3600.0, 2),
        'duracion_minutos': round(diff / 60.0, 1),
        'es_abierto': True,
        'es_valido': True,
        'error': None
    }


def calculate_block_time(bloqueo):
    """
    Calcula el tiempo de bloqueo en horas según sección 15.
    TiempoBloqueo = fechadesbloqueo - fecharebloqueo
    Si no ha sido desbloqueado: ahora - fecharebloqueo
    """
    if not bloqueo.fecharebloqueo:
        return {'horas': 0.0, 'estado': 'SIN_FECHA', 'desbloqueado': False}

    ini = bloqueo.fecharebloqueo
    if hasattr(ini, 'tzinfo') and ini.tzinfo is not None:
        ini = ini.replace(tzinfo=None)

    if bloqueo.fechadesbloqueo:
        fin = bloqueo.fechadesbloqueo
        if hasattr(fin, 'tzinfo') and fin.tzinfo is not None:
            fin = fin.replace(tzinfo=None)
        horas = max(0.0, (fin - ini).total_seconds() / 3600.0)
        return {'horas': round(horas, 2), 'estado': 'DESBLOQUEADO', 'desbloqueado': True}
    else:
        now = get_current_time()
        horas = max(0.0, (now - ini).total_seconds() / 3600.0)
        return {'horas': round(horas, 2), 'estado': 'BLOQUEO_ACTIVO', 'desbloqueado': False}


def calculate_deviation(tiempo_real_horas, tiempo_estimado_horas, config=None):
    """
    Calcula desviación en horas, porcentaje y asigna semáforo según sección 27:
    - VERDE: <= umbral amarillo
    - AMARILLO: > umbral amarillo y <= umbral rojo
    - ROJO: > umbral rojo
    """
    if not config:
        config = PocConfigPriorizacion.objects.filter(is_active=True).first()

    umbral_amarillo = config.umbral_amarillo_horas if config else 2.0
    umbral_rojo = config.umbral_rojo_horas if config else 6.0

    desviacion_horas = round(tiempo_real_horas - tiempo_estimado_horas, 2)
    if tiempo_estimado_horas > 0:
        desviacion_pct = round((desviacion_horas / tiempo_estimado_horas) * 100.0, 1)
    else:
        desviacion_pct = 0.0

    if desviacion_horas <= umbral_amarillo:
        semaforo = 'VERDE'
        badge_class = 'success'
    elif desviacion_horas <= umbral_rojo:
        semaforo = 'AMARILLO'
        badge_class = 'warning'
    else:
        semaforo = 'ROJO'
        badge_class = 'danger'

    return {
        'tiempo_real_horas': tiempo_real_horas,
        'tiempo_estimado_horas': tiempo_estimado_horas,
        'desviacion_horas': desviacion_horas,
        'desviacion_pct': desviacion_pct,
        'semaforo': semaforo,
        'badge_class': badge_class,
        'umbral_amarillo': umbral_amarillo,
        'umbral_rojo': umbral_rojo,
    }


def calculate_slack(orden_trabajo, horas_trabajo_pendientes=None):
    """
    Calcula la holgura según sección 28:
    Holgura = HorasDisponiblesHastaEntrega - HorasTrabajoPendientes
    """
    now = get_current_time()
    if not orden_trabajo.fechaentrega:
        return {
            'horas_disponibles': 0.0,
            'horas_pendientes': horas_trabajo_pendientes or 0.0,
            'holgura': 0.0,
            'estado': 'SIN_FECHA_ENTREGA',
            'mensaje': 'La OT no tiene fecha de entrega fijada.'
        }

    f_entrega = orden_trabajo.fechaentrega
    if hasattr(f_entrega, 'tzinfo') and f_entrega.tzinfo is not None:
        f_entrega = f_entrega.replace(tzinfo=None)

    horas_disponibles = (f_entrega - now).total_seconds() / 3600.0

    if horas_trabajo_pendientes is None:
        # Calcular trabajo pendiente estimando horas de movimientos no terminados
        movs = orden_trabajo.movimientos.all()
        pendientes = 0.0
        for m in movs:
            if m.estadoactividad != 2:  # No cerrado
                pendientes += (m.tiempotrabajado or 240) / 60.0
        if pendientes == 0.0:
            pendientes = 8.0  # Estimación base mínima si no hay movimientos
        horas_trabajo_pendientes = pendientes

    holgura = round(horas_disponibles - horas_trabajo_pendientes, 2)

    if holgura > 12.0:
        estado = 'HOLGADO'
        badge = 'success'
        mensaje = 'Existe holgura suficiente para entrega conforme.'
    elif holgura >= 0:
        estado = 'AJUSTADO'
        badge = 'warning'
        mensaje = 'Situación ajustada; se requiere supervisar posibles bloqueos.'
    else:
        estado = 'CRITICO'
        badge = 'danger'
        mensaje = 'Holgura negativa. Existe alto riesgo de retraso o fecha vencida.'

    return {
        'horas_disponibles': round(horas_disponibles, 1),
        'horas_pendientes': round(horas_trabajo_pendientes, 1),
        'holgura': holgura,
        'estado': estado,
        'badge': badge,
        'mensaje': mensaje
    }


def calculate_critical_ratio(orden_trabajo, horas_trabajo_pendientes=None):
    """
    Calcula el Critical Ratio según sección 29:
    CriticalRatio = HorasDisponiblesHastaEntrega / HorasTrabajoPendientes
    > 1: Margen
    ~ 1: Ajustado
    < 1: Riesgo
    """
    now = get_current_time()
    if not orden_trabajo.fechaentrega:
        return {'cr': 1.0, 'estado': 'SIN_FECHA', 'badge': 'secondary'}

    f_entrega = orden_trabajo.fechaentrega
    if hasattr(f_entrega, 'tzinfo') and f_entrega.tzinfo is not None:
        f_entrega = f_entrega.replace(tzinfo=None)

    horas_disponibles = max(0.1, (f_entrega - now).total_seconds() / 3600.0)

    if horas_trabajo_pendientes is None:
        pendientes = sum([(m.tiempotrabajado or 240) / 60.0 for m in orden_trabajo.movimientos.all() if m.estadoactividad != 2])
        horas_trabajo_pendientes = pendientes if pendientes > 0 else 6.0

    if horas_trabajo_pendientes <= 0:
        cr = 99.0
    else:
        cr = round(horas_disponibles / horas_trabajo_pendientes, 2)

    if cr > 1.2:
        estado = 'MARGEN'
        badge = 'success'
    elif cr >= 0.9:
        estado = 'AJUSTADO'
        badge = 'warning'
    else:
        estado = 'RIESGO'
        badge = 'danger'

    return {
        'cr': cr,
        'estado': estado,
        'badge': badge,
        'horas_disponibles': round(horas_disponibles, 1),
        'horas_pendientes': round(horas_trabajo_pendientes, 1),
    }


def calculate_wspt(peso, tiempo_procesamiento_horas):
    """
    Calcula WSPT según sección 30:
    WSPT = Peso / TiempoProcesamiento
    """
    if tiempo_procesamiento_horas <= 0:
        return 999.0
    return round(peso / tiempo_procesamiento_horas, 3)
