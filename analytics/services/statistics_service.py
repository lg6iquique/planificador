import logging
import numpy as np
import pandas as pd
from planning.models import MCTMovimientoOrdenTrabajo
from analytics.services.duration_service import calculate_real_duration

logger = logging.getLogger('analytics')


def get_movimientos_dataframe():
    """
    Extrae los movimientos de trabajo cerrados a un DataFrame de Pandas para análisis estadístico.
    """
    movimientos = MCTMovimientoOrdenTrabajo.objects.select_related(
        'idordentrabajo', 'idmaquina', 'idoperador', 'idactividad', 'idparte'
    ).all()

    rows = []
    for m in movimientos:
        dur = calculate_real_duration(m)
        if dur['es_valido'] and not dur['es_abierto']:
            rows.append({
                'idmovimiento': m.idmovimientoordentrabajo,
                'idordentrabajo': m.idordentrabajo_id,
                'idmaquina': m.idmaquina_id,
                'nombremaquina': m.idmaquina.nombremaquina if m.idmaquina else 'Sin Máquina',
                'codigomaquina': m.idmaquina.codigomaquina if m.idmaquina else 'N/A',
                'idoperador': m.idoperador_id,
                'nombreoperador': m.idoperador.nombreoperador if m.idoperador else 'Sin Operador',
                'idactividad': m.idactividad_id,
                'nombreactividad': m.idactividad.nombreactividad if m.idactividad else 'Sin Actividad',
                'idparte': m.idparte_id,
                'nombreparte': m.idparte.nombreparte if m.idparte else 'Sin Parte',
                'duracion_horas': dur['duracion_horas'],
                'duracion_minutos': dur['duracion_minutos'],
                'checkncbomba': bool(m.checkncbomba),
                'reproceso': bool(m.reprocesosol or m.reprocesocc or m.checkncbomba),
            })

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def calculate_distribution_stats(series):
    """
    Calcula mean, median, P50, P75, P90, P95, std, min, max para una serie de datos numéricos.
    """
    if series.empty or len(series) == 0:
        return {
            'count': 0,
            'mean': 0.0,
            'median': 0.0,
            'p50': 0.0,
            'p75': 0.0,
            'p90': 0.0,
            'p95': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'tiempo_estimado_base': 0.0
        }

    arr = series.dropna().to_numpy()
    if len(arr) == 0:
        return {
            'count': 0, 'mean': 0.0, 'median': 0.0, 'p50': 0.0,
            'p75': 0.0, 'p90': 0.0, 'p95': 0.0, 'std': 0.0,
            'min': 0.0, 'max': 0.0, 'tiempo_estimado_base': 0.0
        }

    count = int(len(arr))
    mean_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    p50_val = float(np.percentile(arr, 50))
    p75_val = float(np.percentile(arr, 75))
    p90_val = float(np.percentile(arr, 90))
    p95_val = float(np.percentile(arr, 95))
    std_val = float(np.std(arr, ddof=1)) if count > 1 else 0.0
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))

    # Regla Sección 26: Mediana si n >= 3, P75 si n < 3
    if count >= 3:
        tiempo_estimado_base = median_val
        criterio = 'Mediana Histórica (n >= 3)'
    else:
        tiempo_estimado_base = p75_val
        criterio = 'P75 Histórico (n < 3)'

    return {
        'count': count,
        'mean': round(mean_val, 2),
        'median': round(median_val, 2),
        'p50': round(p50_val, 2),
        'p75': round(p75_val, 2),
        'p90': round(p90_val, 2),
        'p95': round(p95_val, 2),
        'std': round(std_val, 2),
        'min': round(min_val, 2),
        'max': round(max_val, 2),
        'tiempo_estimado_base': round(tiempo_estimado_base, 2),
        'criterio_estimacion': criterio
    }


def get_global_statistics():
    """
    Retorna resumen estadístico global de duraciones y reprocesos en taller.
    """
    df = get_movimientos_dataframe()
    if df.empty:
        return {
            'global': calculate_distribution_stats(pd.Series(dtype=float)),
            'por_maquina': [],
            'por_actividad': [],
            'por_operador': [],
            'por_parte': [],
            'total_reprocesos': 0,
            'pct_reprocesos': 0.0
        }

    global_stats = calculate_distribution_stats(df['duracion_horas'])

    # Desglose por máquina
    por_maquina = []
    for maquina_nom, group in df.groupby('nombremaquina'):
        stats = calculate_distribution_stats(group['duracion_horas'])
        por_maquina.append({
            'nombre': maquina_nom,
            'stats': stats,
            'reprocesos': int(group['reproceso'].sum())
        })

    # Desglose por actividad
    por_actividad = []
    for act_nom, group in df.groupby('nombreactividad'):
        stats = calculate_distribution_stats(group['duracion_horas'])
        por_actividad.append({
            'nombre': act_nom,
            'stats': stats,
            'reprocesos': int(group['reproceso'].sum())
        })

    # Desglose por operador
    por_operador = []
    for op_nom, group in df.groupby('nombreoperador'):
        stats = calculate_distribution_stats(group['duracion_horas'])
        por_operador.append({
            'nombre': op_nom,
            'stats': stats,
            'reprocesos': int(group['reproceso'].sum())
        })

    # Desglose por parte
    por_parte = []
    for part_nom, group in df.groupby('nombreparte'):
        stats = calculate_distribution_stats(group['duracion_horas'])
        por_parte.append({
            'nombre': part_nom,
            'stats': stats,
            'reprocesos': int(group['reproceso'].sum())
        })

    total_rep = int(df['reproceso'].sum())
    pct_rep = round((total_rep / len(df)) * 100.0, 1) if len(df) > 0 else 0.0

    return {
        'global': global_stats,
        'por_maquina': por_maquina,
        'por_actividad': por_actividad,
        'por_operador': por_operador,
        'por_parte': por_parte,
        'total_reprocesos': total_rep,
        'pct_reprocesos': pct_rep
    }
