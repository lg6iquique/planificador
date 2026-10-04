from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from planning.models import (
    MCTOrdenTrabajo, MCTMaquina, PocPlanificacion,
    PocPlanificacionDetalle, PocSimulacion, PocConfigPriorizacion
)
from scheduling.services.priority_service import prioritize_all_ots, get_active_config
from scheduling.services.capacity_service import calculate_machine_capacity, detect_bottlenecks
from scheduling.services.scheduler_service import generate_schedule, update_plan_decision
from scheduling.services.simulation_service import simulate_urgent_order


def priorizacion_view(request):
    """Vista de ranking de priorización inteligente y explicabilidad (Secciones 31-34)."""
    config = get_active_config()

    if request.method == 'POST':
        # Permite al usuario ajustar los pesos de priorización de la POC
        try:
            config.peso_due_date = float(request.POST.get('peso_due_date', 0.40))
            config.peso_holgura = float(request.POST.get('peso_holgura', 0.25))
            config.peso_impacto = float(request.POST.get('peso_impacto', 0.20))
            config.peso_wspt = float(request.POST.get('peso_wspt', 0.10))
            config.peso_comercial = float(request.POST.get('peso_comercial', 0.05))
            config.save()
            messages.success(request, 'Pesos de priorización actualizados correctamente.')
        except Exception as e:
            messages.error(request, f'Error al actualizar pesos: {e}')
        return redirect('scheduling_priorizacion')

    ranked_ots = prioritize_all_ots()
    context = {
        'ranked_ots': ranked_ots,
        'config': config
    }
    return render(request, 'scheduling/priorizacion.html', context)


def plan_view(request):
    """Vista de Secuencia Heurística Recomendada y Decisión Humano+Sistema (Secciones 35 y 42)."""
    ultimo_plan = PocPlanificacion.objects.prefetch_related(
        'detalles', 'detalles__orden_trabajo', 'detalles__maquina', 'detalles__movimiento'
    ).order_by('-created_at').first()

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'generar_nuevo':
            nuevo_plan = generate_schedule()
            messages.success(request, f'Nuevo plan {nuevo_plan.codigo} generado con éxito.')
            return redirect('scheduling_plan')
        elif accion == 'decision_detalle':
            detalle_id = request.POST.get('detalle_id')
            decision = request.POST.get('decision')
            nota = request.POST.get('nota', '')
            res = update_plan_decision(ultimo_plan.id, detalle_id=detalle_id, decision=decision, nota=nota)
            if res.get('success'):
                messages.success(request, f'Decisión guardada: {decision}.')
            return redirect('scheduling_plan')
        elif accion == 'decision_plan_completo':
            decision = request.POST.get('decision')
            nota = request.POST.get('observaciones', '')
            update_plan_decision(ultimo_plan.id, decision=decision, nota=nota)
            messages.success(request, f'Plan {ultimo_plan.codigo} marcado como {decision}.')
            return redirect('scheduling_plan')

    # Si no existe ningún plan, generar uno inicial
    if not ultimo_plan:
        ultimo_plan = generate_schedule()

    # Agrupar detalles por máquina para la vista
    detalles_por_maquina = {}
    for det in ultimo_plan.detalles.all():
        m_nom = det.maquina.nombremaquina
        if m_nom not in detalles_por_maquina:
            detalles_por_maquina[m_nom] = []
        detalles_por_maquina[m_nom].append(det)

    context = {
        'plan': ultimo_plan,
        'detalles_por_maquina': detalles_por_maquina
    }
    return render(request, 'scheduling/plan.html', context)


def capacidad_view(request):
    """Vista de Capacidad y Cuellos de Botella (Secciones 36 y 37)."""
    cap_data = calculate_machine_capacity()
    bottlenecks = detect_bottlenecks()
    context = {
        'capacidad': cap_data,
        'bottlenecks': bottlenecks
    }
    return render(request, 'scheduling/capacidad.html', context)


def simulacion_view(request):
    """Vista interactiva de Simulación de Inserción Urgente (Secciones 40 y 41)."""
    ots = MCTOrdenTrabajo.objects.all().order_by('-prioridad')
    simulacion_resultado = None

    if request.method == 'POST':
        ot_id = request.POST.get('ot_urgente_id')
        escenario = request.POST.get('escenario', 'B')
        if ot_id:
            simulacion_resultado = simulate_urgent_order(int(ot_id), escenario=escenario)
            messages.success(request, f'Simulación ejecutada para OT-{ot_id} en Escenario {escenario}.')
    else:
        # Por defecto simular para la OT más urgente del taller si existe
        primera_urgente = ots.first()
        if primera_urgente:
            simulacion_resultado = simulate_urgent_order(primera_urgente.idordentrabajo, escenario='B')

    simulaciones_historicas = PocSimulacion.objects.order_by('-fecha_simulacion')[:5]

    context = {
        'ots': ots,
        'resultado': simulacion_resultado,
        'historico': simulaciones_historicas
    }
    return render(request, 'scheduling/simulacion.html', context)


# ==============================================================================
# API Endpoints (Sección 43)
# ==============================================================================

def api_priorizacion(request):
    ranked = prioritize_all_ots()
    return JsonResponse({'ranking': ranked})


def api_capacidad(request):
    cap = calculate_machine_capacity()
    return JsonResponse(cap)


def api_cuello_botella(request):
    cuellos = detect_bottlenecks()
    return JsonResponse(cuellos)


@csrf_exempt
def api_scheduling_calcular(request):
    plan = generate_schedule()
    return JsonResponse({
        'success': True,
        'plan_id': plan.id,
        'codigo': plan.codigo,
        'detalles_count': plan.detalles.count()
    })


@csrf_exempt
def api_simulacion_urgencia(request):
    ot_id = request.POST.get('ot_id') or request.GET.get('ot_id')
    escenario = request.POST.get('escenario') or request.GET.get('escenario') or 'B'
    if not ot_id:
        return JsonResponse({'error': 'ot_id es requerido'}, status=400)
    res = simulate_urgent_order(int(ot_id), escenario=escenario)
    return JsonResponse(res)
