from django.shortcuts import render
from django.http import JsonResponse
from planning.models import MCTOrdenTrabajo, MCTMovimientoOrdenTrabajo, MCTMaquina, PocPlanificacion
from quality.services.quality_service import run_data_quality_audit
from scheduling.services.capacity_service import detect_bottlenecks
from scheduling.services.priority_service import prioritize_all_ots


def dashboard_home(request):
    """Vista principal / Dashboard Ejecutivo del sistema."""
    total_ots = MCTOrdenTrabajo.objects.count()
    ots_activas = MCTOrdenTrabajo.objects.filter(idestadoorden__in=[1, 2, 3]).count()
    total_movimientos = MCTMovimientoOrdenTrabajo.objects.count()
    movimientos_abiertos = MCTMovimientoOrdenTrabajo.objects.filter(estadoactividad=1).count()

    cuellos_info = detect_bottlenecks()
    ranked_ots = prioritize_all_ots()
    top_prioritarias = ranked_ots[:5]

    planes_recientes = PocPlanificacion.objects.all().order_by('-created_at')[:4]
    audit_data = run_data_quality_audit()

    context = {
        'total_ots': total_ots,
        'ots_activas': ots_activas,
        'total_movimientos': total_movimientos,
        'movimientos_abiertos': movimientos_abiertos,
        'cuellos_info': cuellos_info,
        'top_prioritarias': top_prioritarias,
        'planes_recientes': planes_recientes,
        'calidad_pct': audit_data['porcentaje_calidad'],
        'anomalias_count': audit_data['total_anomalias_detectadas'],
    }
    return render(request, 'quality/dashboard_home.html', context)


def quality_audit_view(request):
    """Vista de auditoría y Data Quality del taller."""
    audit_data = run_data_quality_audit()
    context = {
        'audit': audit_data
    }
    return render(request, 'quality/audit.html', context)


def api_quality_audit(request):
    """API endpoint para reporte de calidad de datos."""
    audit_data = run_data_quality_audit()
    return JsonResponse(audit_data)
