import logging
import datetime
from django.utils import timezone
from planning.models import (
    PocPlanificacion, PocPlanificacionDetalle, PocEventoPlanificacion,
    MCTOrdenTrabajo, MCTMaquina, MCTMovimientoOrdenTrabajo
)
from scheduling.services.priority_service import prioritize_all_ots
from analytics.services.duration_service import get_current_time

logger = logging.getLogger('scheduling')


def generate_schedule(fecha_planificacion=None, nombre_plan=None):
    """
    Genera una secuencia heurística recomendada por máquina (Secciones 35 y 42).
    Asigna órdenes de trabajo según su prioridad y genera el cronograma estimado.
    """
    now = get_current_time()
    if not fecha_planificacion:
        fecha_planificacion = now.date()

    # Obtener ranking de prioridad
    ranked_ots = prioritize_all_ots()
    codigo_plan = f"PLAN-{fecha_planificacion.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"

    plan = PocPlanificacion.objects.create(
        codigo=codigo_plan,
        fecha_planificacion=fecha_planificacion,
        descripcion=nombre_plan or f"Planificación Operativa Taller {fecha_planificacion}",
        estado='BORRADOR',
        observaciones='Secuencia heurística generada por motor de priorización multicriterio.'
    )

    detalles = []
    # Rastrear disponibilidad temporal de cada máquina (cursor temporal)
    cursor_tiempo_maquina = {}
    maquinas = {m.idmaquina: m for m in MCTMaquina.objects.all()}
    for mid in maquinas:
        # Inicio a las 08:00 del día de planificación
        cursor_tiempo_maquina[mid] = datetime.datetime.combine(fecha_planificacion, datetime.time(8, 0))

    # Para cada OT en orden de prioridad, planificar sus requerimientos
    for ot_data in ranked_ots:
        ot_id = ot_data['idordentrabajo']
        score = ot_data['score_total']
        ot = MCTOrdenTrabajo.objects.filter(idordentrabajo=ot_id).first()
        if not ot:
            continue

        # Obtener los movimientos de la OT
        movs = ot.movimientos.all().select_related('idmaquina')
        if not movs.exists():
            # Si no tiene movimientos específicos asignados, asignar a máquina principal según tipo de bomba
            target_maquina_id = 1 if (ot_id % 2 == 0) else 5
            maquina = maquinas.get(target_maquina_id)
            if not maquina:
                continue

            duracion_estimada = 6.0
            t_inicio = cursor_tiempo_maquina[target_maquina_id]
            t_fin = t_inicio + datetime.timedelta(hours=duracion_estimada)
            cursor_tiempo_maquina[target_maquina_id] = t_fin

            # Orden de secuencia en la máquina
            orden_sec = PocPlanificacionDetalle.objects.filter(
                planificacion=plan, maquina=maquina
            ).count() + 1

            detalle = PocPlanificacionDetalle.objects.create(
                planificacion=plan,
                orden_trabajo=ot,
                movimiento=None,
                maquina=maquina,
                orden_secuencia=orden_sec,
                fecha_inicio_estimada=t_inicio,
                fecha_fin_estimada=t_fin,
                duracion_estimada_horas=duracion_estimada,
                score_prioridad=score,
                decision_humana='PROPUESTO',
                nota_planificador=f"Asignación automática basada en Score Prioridad: {score}"
            )
            detalles.append(detalle)
        else:
            for mov in movs:
                # Si el movimiento ya está terminado (cerrado), no se reprograma
                if mov.estadoactividad == 2:
                    continue

                maquina = mov.idmaquina or maquinas.get(1)
                mid = maquina.idmaquina
                duracion_estimada = (mov.tiempotrabajado or 360) / 60.0

                t_inicio = cursor_tiempo_maquina.get(mid, datetime.datetime.combine(fecha_planificacion, datetime.time(8, 0)))
                t_fin = t_inicio + datetime.timedelta(hours=duracion_estimada)
                cursor_tiempo_maquina[mid] = t_fin

                orden_sec = PocPlanificacionDetalle.objects.filter(
                    planificacion=plan, maquina=maquina
                ).count() + 1

                detalle = PocPlanificacionDetalle.objects.create(
                    planificacion=plan,
                    orden_trabajo=ot,
                    movimiento=mov,
                    maquina=maquina,
                    orden_secuencia=orden_sec,
                    fecha_inicio_estimada=t_inicio,
                    fecha_fin_estimada=t_fin,
                    duracion_estimada_horas=duracion_estimada,
                    score_prioridad=score,
                    decision_humana='PROPUESTO',
                    nota_planificador=f"Operación {mov.codigoaccion or 'MEC'}: {ot_data['explicacion']}"
                )
                detalles.append(detalle)

    # Registrar evento
    PocEventoPlanificacion.objects.create(
        tipo_evento='GENERACION_PLAN',
        descripcion=f"Generado plan {codigo_plan} con {len(detalles)} operaciones recomendadas.",
        usuario='sistema_planificador'
    )

    logger.info(f"Plan {codigo_plan} generado exitosamente con {len(detalles)} detalles.")
    return plan


def update_plan_decision(plan_id, detalle_id=None, decision='ACEPTADO', nota=''):
    """
    Registra la decisión humana (ACEPTAR, MODIFICAR, RECHAZAR) según sección 42.
    """
    plan = PocPlanificacion.objects.filter(id=plan_id).first()
    if not plan:
        return {'success': False, 'error': 'Plan no encontrado'}

    if detalle_id:
        det = PocPlanificacionDetalle.objects.filter(id=detalle_id, planificacion=plan).first()
        if det:
            det.decision_humana = decision
            if nota:
                det.nota_planificador = nota
            det.save()
            PocEventoPlanificacion.objects.create(
                tipo_evento='DECISION_HUMANA',
                descripcion=f"Detalle {det.id} en Plan {plan.codigo} marcado como {decision}: {nota}",
                usuario='planificador'
            )
            return {'success': True, 'detalle': det}
    else:
        # Actualización de plan completo
        plan.estado = decision
        if nota:
            plan.observaciones = nota
        plan.save()
        PocEventoPlanificacion.objects.create(
            tipo_evento='ESTADO_PLAN',
            descripcion=f"Plan {plan.codigo} actualizado a {decision}.",
            usuario='planificador'
        )
        return {'success': True, 'plan': plan}
