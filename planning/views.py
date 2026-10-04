from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from planning.models import (
    MCTOrdenTrabajo, MCTOrdenTrabajoParte, MCTComponente,
    MCTParte, MCTHojaRuta, MCTMovimientoOrdenTrabajo,
    MCTMaquina, MCTOperador, MCTProgAvisos, MCTMovimientoBloqueo
)
from analytics.services.duration_service import calculate_real_duration, calculate_slack, calculate_critical_ratio
from scheduling.services.priority_service import calculate_priority_score


def ordenes_list_view(request):
    """Listado general de Órdenes de Trabajo con filtros y métricas."""
    query = request.GET.get('q', '').strip()
    cliente_id = request.GET.get('cliente')

    ots_qs = MCTOrdenTrabajo.objects.select_related('idcliente', 'idproducto', 'idestadoorden').all()

    if query:
        ots_qs = ots_qs.filter(nombreordentrabajo__icontains=query)
    if cliente_id:
        ots_qs = ots_qs.filter(idcliente_id=cliente_id)

    ots = []
    for ot in ots_qs:
        prio = calculate_priority_score(ot)
        slack = calculate_slack(ot)
        ots.append({
            'ot': ot,
            'score': prio['score_total'],
            'slack': slack,
            'prioridad_comercial': ot.prioridad or 1,
            'explicacion': prio['explicacion']
        })

    context = {
        'ots': ots,
        'query': query,
    }
    return render(request, 'planning/ordenes_list.html', context)


def orden_detail_view(request, id):
    """
    Vista detallada de la OT recorriendo la cadena completa:
    OT -> Partes -> Componentes -> Hojas de Ruta -> Movimientos -> Bloqueos -> SLAs.
    """
    ot = get_object_or_404(MCTOrdenTrabajo.objects.select_related('idcliente', 'idproducto', 'idestadoorden'), idordentrabajo=id)

    partes_rel = ot.partes.select_related('idparte', 'idcomponente').prefetch_related('hojas_ruta', 'hojas_ruta__movimientos').all()

    movimientos = ot.movimientos.select_related('idmaquina', 'idoperador', 'idactividad', 'idseccion').all()

    mov_analizados = []
    for m in movimientos:
        dur = calculate_real_duration(m)
        mov_analizados.append({
            'mov': m,
            'duracion': dur
        })

    prog_avisos = ot.prog_avisos.select_related('idsla').order_by('ordenproceso').all()

    prio = calculate_priority_score(ot)
    slack = calculate_slack(ot)
    cr = calculate_critical_ratio(ot)

    context = {
        'ot': ot,
        'partes_rel': partes_rel,
        'movimientos': mov_analizados,
        'prog_avisos': prog_avisos,
        'prioridad': prio,
        'slack': slack,
        'critical_ratio': cr,
    }
    return render(request, 'planning/orden_detail.html', context)


def movimientos_list_view(request):
    """Listado y control de movimientos de taller, abiertos, bloqueados y reprocesos."""
    movs = MCTMovimientoOrdenTrabajo.objects.select_related(
        'idordentrabajo', 'idmaquina', 'idoperador', 'idactividad', 'idseccion'
    ).order_by('-fechainicio').all()

    lista = []
    for m in movs:
        dur = calculate_real_duration(m)
        lista.append({
            'mov': m,
            'duracion': dur
        })

    bloqueos_activos = MCTMovimientoBloqueo.objects.filter(fechadesbloqueo__isnull=True).select_related('idoperador', 'idseccion')

    context = {
        'movimientos': lista,
        'bloqueos_activos': bloqueos_activos
    }
    return render(request, 'planning/movimientos_list.html', context)


# ==============================================================================
# API REST Endpoints (Sección 43)
# ==============================================================================

def api_ordenes(request):
    ots = MCTOrdenTrabajo.objects.all()
    data = []
    for ot in ots:
        data.append({
            'idordentrabajo': ot.idordentrabajo,
            'nombreordentrabajo': ot.nombreordentrabajo,
            'cliente': ot.idcliente.nombrecliente if ot.idcliente else None,
            'producto': ot.idproducto.nombreproducto if ot.idproducto else None,
            'prioridad_comercial': ot.prioridad,
            'fechaentrega': ot.fechaentrega.isoformat() if ot.fechaentrega else None,
        })
    return JsonResponse({'ordenes': data})


def api_orden_detail(request, id):
    ot = get_object_or_404(MCTOrdenTrabajo, idordentrabajo=id)
    prio = calculate_priority_score(ot)
    slack = calculate_slack(ot)
    data = {
        'idordentrabajo': ot.idordentrabajo,
        'nombreordentrabajo': ot.nombreordentrabajo,
        'cliente': ot.idcliente.nombrecliente if ot.idcliente else None,
        'producto': ot.idproducto.nombreproducto if ot.idproducto else None,
        'prioridad_score': prio['score_total'],
        'explicacion': prio['explicacion'],
        'holgura_horas': slack['holgura'],
        'estado_holgura': slack['estado'],
    }
    return JsonResponse(data)


def api_componentes(request):
    comps = MCTComponente.objects.all().values()
    return JsonResponse({'componentes': list(comps)})


def api_partes(request):
    partes = MCTParte.objects.all().values()
    return JsonResponse({'partes': list(partes)})


def api_maquinas(request):
    maqs = MCTMaquina.objects.all().values()
    return JsonResponse({'maquinas': list(maqs)})


def api_operadores(request):
    ops = MCTOperador.objects.all().values()
    return JsonResponse({'operadores': list(ops)})


def api_hojas_ruta(request):
    hojas = MCTHojaRuta.objects.all().values()
    return JsonResponse({'hojas_ruta': list(hojas)})


def api_movimientos(request):
    movs = MCTMovimientoOrdenTrabajo.objects.all()
    data = []
    for m in movs:
        dur = calculate_real_duration(m)
        data.append({
            'idmovimientoordentrabajo': m.idmovimientoordentrabajo,
            'idordentrabajo': m.idordentrabajo_id,
            'codhojaruta': m.codhojaruta,
            'maquina': m.idmaquina.nombremaquina if m.idmaquina else None,
            'operador': m.idoperador.nombreoperador if m.idoperador else None,
            'duracion_horas': dur['duracion_horas'],
            'estado': dur['estado'],
            'reproceso': bool(m.reprocesosol or m.reprocesocc or m.checkncbomba)
        })
    return JsonResponse({'movimientos': data})
