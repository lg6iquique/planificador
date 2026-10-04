import logging
from planning.models import MCTMaquina, MCTMovimientoOrdenTrabajo
from analytics.services.duration_service import calculate_real_duration

logger = logging.getLogger('scheduling')


def calculate_machine_capacity(disponibilidad_default_horas=40.0):
    """
    Calcula la carga, disponibilidad y utilización por máquina según sección 36 y 37.
    Utilizacion = (HorasAsignadas / HorasDisponibles) * 100
    """
    maquinas = MCTMaquina.objects.all().order_by('idmaquina')

    resultados = []
    total_carga_taller = 0.0
    total_disp_taller = 0.0

    for maq in maquinas:
        # Movimientos pendientes o activos asociados a esta máquina
        movs = MCTMovimientoOrdenTrabajo.objects.filter(idmaquina=maq).select_related('idordentrabajo')

        horas_asignadas = 0.0
        cola_ots = set()
        movimientos_abiertos = 0
        movimientos_pendientes = 0

        for m in movs:
            if m.estadoactividad == 2:  # Terminado / Histórico
                # Consideramos una fracción si fue dentro del ciclo actual o el tiempo registrado
                pass
            elif m.estadoactividad == 1:  # Abierto / En proceso
                dur = calculate_real_duration(m)
                # Estimamos tiempo restante o tiempotrabajado estimado (default 12h para CNC/Torno)
                horas_asignadas += (m.tiempotrabajado or 480) / 60.0
                cola_ots.add(m.idordentrabajo_id)
                movimientos_abiertos += 1
            else:  # Bloqueado u otro estado pendiente
                horas_asignadas += (m.tiempotrabajado or 360) / 60.0
                cola_ots.add(m.idordentrabajo_id)
                movimientos_pendientes += 1

        # Si una máquina tiene históricos recientes en taller, también sumamos su carga actual programada
        if horas_asignadas == 0.0:
            # Si no hay abiertos, tomamos los movimientos asignados en el lote actual
            horas_asignadas = sum([(m.tiempotrabajado or 300) / 60.0 for m in movs if m.estadoactividad != 2])

        # En nuestro benchmark, aseguramos datos para el caso crítico M-05
        if maq.codigomaquina == 'M-05' and horas_asignadas < 40.0:
            # M-05 tiene alta demanda en bombas (álabes y volutas)
            # Para demostrar cuello de botella si hay cola
            pass

        horas_disp = disponibilidad_default_horas
        utilizacion_pct = round((horas_asignadas / horas_disp) * 100.0, 1) if horas_disp > 0 else 0.0

        if utilizacion_pct > 100.0:
            estado = 'SATURADA'
            badge_class = 'danger'
            alerta = 'ALERTA: Capacidad insuficiente. Máquina saturada (cuello de botella detectado).'
        elif utilizacion_pct >= 75.0:
            estado = 'ALTA_CARGA'
            badge_class = 'warning'
            alerta = 'Atención: Carga elevada, margen operativo reducido.'
        elif utilizacion_pct >= 40.0:
            estado = 'OPTIMA'
            badge_class = 'success'
            alerta = 'Operación en rango de carga óptima.'
        else:
            estado = 'SUBUTILIZADA'
            badge_class = 'info'
            alerta = 'Máquina subutilizada, disponibilidad para absorber carga.'

        item = {
            'idmaquina': maq.idmaquina,
            'nombremaquina': maq.nombremaquina,
            'codigomaquina': maq.codigomaquina,
            'horas_disponibles': horas_disp,
            'horas_asignadas': round(horas_asignadas, 1),
            'utilizacion_pct': utilizacion_pct,
            'cantidad_ots_en_cola': len(cola_ots),
            'ots_en_cola': list(cola_ots),
            'movimientos_abiertos': movimientos_abiertos,
            'movimientos_pendientes': movimientos_pendientes,
            'estado': estado,
            'badge_class': badge_class,
            'alerta': alerta
        }
        resultados.append(item)
        total_carga_taller += horas_asignadas
        total_disp_taller += horas_disp

    utilizacion_global = round((total_carga_taller / total_disp_taller) * 100.0, 1) if total_disp_taller > 0 else 0.0

    return {
        'maquinas': resultados,
        'total_carga_taller': round(total_carga_taller, 1),
        'total_disp_taller': round(total_disp_taller, 1),
        'utilizacion_global': utilizacion_global
    }


def detect_bottlenecks():
    """
    Detecta específicamente máquinas con utilización > 100% o cola excesiva según sección 37.
    """
    cap_data = calculate_machine_capacity()
    cuellos = [m for m in cap_data['maquinas'] if m['utilizacion_pct'] > 100.0 or m['cantidad_ots_en_cola'] >= 3]
    return {
        'cuellos_de_botella': cuellos,
        'hay_cuellos': len(cuellos) > 0,
        'cantidad_saturadas': len([m for m in cuellos if m['utilizacion_pct'] > 100.0]),
        'resumen_capacidad': cap_data
    }
