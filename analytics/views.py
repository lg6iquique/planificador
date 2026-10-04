from django.shortcuts import render
from django.http import JsonResponse
from planning.models import MCTMovimientoOrdenTrabajo, MCTOrdenTrabajo, PocConfigPriorizacion
from analytics.services.statistics_service import get_global_statistics
from analytics.services.duration_service import (
    calculate_real_duration, calculate_deviation, calculate_slack, calculate_critical_ratio
)


def analytics_tiempos_view(request):
    """Vista de análisis estadístico de duraciones (Sección 25 y 26)."""
    stats = get_global_statistics()
    context = {
        'stats': stats
    }
    return render(request, 'analytics/tiempos.html', context)


def analytics_desviaciones_view(request):
    """Vista de cálculo de desviaciones y semáforos (Sección 27)."""
    config = PocConfigPriorizacion.objects.filter(is_active=True).first()

    movs = MCTMovimientoOrdenTrabajo.objects.select_related(
        'idordentrabajo', 'idmaquina', 'idoperador', 'idactividad'
    ).filter(fechatermino__isnull=False).all()

    desviaciones = []
    resumen_semaforo = {'VERDE': 0, 'AMARILLO': 0, 'ROJO': 0}

    for m in movs:
        dur = calculate_real_duration(m)
        if dur['es_valido'] and not dur['es_abierto']:
            # Estimado base tomado de tiempotrabajado registrado o default 8h
            estimado = (m.tiempotrabajado or 480) / 60.0
            dev = calculate_deviation(dur['duracion_horas'], estimado, config)
            resumen_semaforo[dev['semaforo']] += 1
            desviaciones.append({
                'movimiento': m,
                'desviacion': dev,
                'reproceso': bool(m.reprocesosol or m.reprocesocc or m.checkncbomba)
            })

    # Análisis de holguras y Critical Ratio de OTs activas
    ots = MCTOrdenTrabajo.objects.filter(idestadoorden__in=[1, 2, 3]).select_related('idcliente')
    ots_analisis = []
    for ot in ots:
        slack = calculate_slack(ot)
        cr = calculate_critical_ratio(ot)
        ots_analisis.append({
            'ot': ot,
            'slack': slack,
            'critical_ratio': cr
        })

    context = {
        'desviaciones': desviaciones,
        'resumen_semaforo': resumen_semaforo,
        'ots_analisis': ots_analisis,
        'config': config
    }
    return render(request, 'analytics/desviaciones.html', context)


# ==============================================================================
# API Endpoints (Sección 43)
# ==============================================================================

def api_analisis_tiempos(request):
    stats = get_global_statistics()
    return JsonResponse(stats)


def api_analisis_desviaciones(request):
    config = PocConfigPriorizacion.objects.filter(is_active=True).first()
    movs = MCTMovimientoOrdenTrabajo.objects.filter(fechatermino__isnull=False).all()
    data = []
    for m in movs:
        dur = calculate_real_duration(m)
        if dur['es_valido']:
            estimado = (m.tiempotrabajado or 480) / 60.0
            dev = calculate_deviation(dur['duracion_horas'], estimado, config)
            data.append({
                'idmovimiento': m.idmovimientoordentrabajo,
                'idordentrabajo': m.idordentrabajo_id,
                'tiempo_real_horas': dev['tiempo_real_horas'],
                'tiempo_estimado_horas': dev['tiempo_estimado_horas'],
                'desviacion_horas': dev['desviacion_horas'],
                'desviacion_pct': dev['desviacion_pct'],
                'semaforo': dev['semaforo'],
            })
    return JsonResponse({'desviaciones': data})
