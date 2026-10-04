import logging
from planning.models import (
    MCTOrdenTrabajo, MCTOrdenTrabajoParte, MCTHojaRuta,
    MCTMovimientoOrdenTrabajo, MCTMaquina, MCTOperador
)
from analytics.services.duration_service import calculate_real_duration

logger = logging.getLogger('quality')


def run_data_quality_audit():
    """
    Rutina de Data Quality según sección 48 de PROMPT_BASE.md.
    Audita integridad referencial, fechas inconsistentes, duraciones anómalas
    y anomalías en órdenes de trabajo y movimientos.
    """
    problemas = []
    total_registros_evaluados = 0
    total_problemas = 0

    # 1. Auditoría de Órdenes de Trabajo
    ots = MCTOrdenTrabajo.objects.all()
    for ot in ots:
        total_registros_evaluados += 1
        problemas_ot = []

        if not ot.fecharecepcion and not ot.fechacreacion:
            problemas_ot.append('OT sin fecha de recepción ni de creación')
        if not ot.fechaentrega:
            problemas_ot.append('OT sin fecha de entrega comprometida')

        # Verificar si tiene partes asociadas
        partes_rel = ot.partes.all()
        if not partes_rel.exists():
            problemas_ot.append('OT sin partes asignadas')
        else:
            for p in partes_rel:
                if not p.idcomponente:
                    problemas_ot.append(f'Parte {p.idordentrabajoparte} sin componente asociado')
                if not p.hojas_ruta.exists():
                    problemas_ot.append(f'Parte {p.idordentrabajoparte} sin hoja de ruta generada')

        if problemas_ot:
            total_problemas += len(problemas_ot)
            problemas.append({
                'entidad': 'Orden de Trabajo',
                'id_registro': ot.idordentrabajo,
                'codigo': f"OT-{ot.idordentrabajo}",
                'descripcion': ot.nombreordentrabajo or 'Sin nombre',
                'problemas': problemas_ot,
                'severidad': 'ALTA' if 'sin fecha de entrega' in ' '.join(problemas_ot) else 'MEDIA'
            })

    # 2. Auditoría de Movimientos de Taller
    movs = MCTMovimientoOrdenTrabajo.objects.all()
    for m in movs:
        total_registros_evaluados += 1
        problemas_mov = []

        if not m.idordentrabajo_id:
            problemas_mov.append('Movimiento huérfano (sin orden de trabajo)')
        if not m.idmaquina_id:
            problemas_mov.append('Movimiento sin máquina asignada')
        if not m.idoperador_id:
            problemas_mov.append('Movimiento sin operador asignado')

        # Validación temporal y de duración
        dur = calculate_real_duration(m)
        if not dur['es_valido']:
            problemas_mov.append(f"Inconsistencia de duración: {dur['error']}")
        elif dur['es_abierto']:
            problemas_mov.append(f"Movimiento abierto en ejecución continua ({dur['duracion_horas']}h transcurridas)")

        if problemas_mov:
            total_problemas += len(problemas_mov)
            problemas.append({
                'entidad': 'Movimiento OT',
                'id_registro': m.idmovimientoordentrabajo,
                'codigo': f"MOV-{m.idmovimientoordentrabajo}",
                'descripcion': f"OT-{m.idordentrabajo_id} / HR-{m.codhojaruta or 'S/HR'}",
                'problemas': problemas_mov,
                'severidad': 'CRITICA' if any('Inconsistencia' in p for p in problemas_mov) else 'INFORMATIVA'
            })

    # 3. Auditoría de Hojas de Ruta
    hojas = MCTHojaRuta.objects.all()
    for h in hojas:
        total_registros_evaluados += 1
        problemas_hr = []
        if not h.idordentrabajoparte_id:
            problemas_hr.append('Hoja de ruta sin vínculo a orden de trabajo parte')

        if problemas_hr:
            total_problemas += len(problemas_hr)
            problemas.append({
                'entidad': 'Hoja de Ruta',
                'id_registro': h.idhojaruta,
                'codigo': f"HR-{h.codhojaruta or h.idhojaruta}",
                'descripcion': f"Modalidad {h.modalidad}",
                'problemas': problemas_hr,
                'severidad': 'MEDIA'
            })

    # 4. Cálculo de Indicadores de Calidad de Datos
    registros_validos = max(0, total_registros_evaluados - len(problemas))
    pct_calidad = round((registros_validos / total_registros_evaluados) * 100.0, 1) if total_registros_evaluados > 0 else 100.0

    logger.info(f"Auditoría Data Quality finalizada. {total_registros_evaluados} evaluados, calidad: {pct_calidad}%")

    return {
        'total_registros_evaluados': total_registros_evaluados,
        'registros_validos': registros_validos,
        'registros_con_problemas': len(problemas),
        'total_anomalias_detectadas': total_problemas,
        'porcentaje_calidad': pct_calidad,
        'detalles_problemas': problemas,
        'resumen_por_severidad': {
            'CRITICA': len([p for p in problemas if p['severidad'] == 'CRITICA']),
            'ALTA': len([p for p in problemas if p['severidad'] == 'ALTA']),
            'MEDIA': len([p for p in problemas if p['severidad'] == 'MEDIA']),
            'INFORMATIVA': len([p for p in problemas if p['severidad'] == 'INFORMATIVA']),
        }
    }
