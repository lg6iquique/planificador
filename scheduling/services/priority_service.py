import logging
import datetime
from django.utils import timezone
from planning.models import MCTOrdenTrabajo, PocConfigPriorizacion
from analytics.services.duration_service import (
    calculate_slack, calculate_wspt, get_current_time
)

logger = logging.getLogger('scheduling')


def get_active_config():
    """Obtiene la configuración activa de priorización o usa la predeterminada."""
    config = PocConfigPriorizacion.objects.filter(is_active=True).first()
    if not config:
        config = PocConfigPriorizacion(
            nombre='Configuración Default',
            peso_due_date=0.40,
            peso_holgura=0.25,
            peso_impacto=0.20,
            peso_wspt=0.10,
            peso_comercial=0.05,
            umbral_amarillo_horas=2.0,
            umbral_rojo_horas=6.0,
            costo_hora_hombre=28.5,
            costo_hora_maquina=52.0
        )
    return config


def calculate_priority_score(ot, config=None, all_ots=None):
    """
    Calcula el Score de Prioridad (0-100) y genera la explicación detallada
    según las secciones 31, 32 y 33 de PROMPT_BASE.md.
    Fórmula:
      Score = w_due * S_due + w_holgura * S_holgura + w_impact * S_impact + w_wspt * S_wspt + w_com * S_com
    """
    if config is None:
        config = get_active_config()

    now = get_current_time()

    # 1. Score Due Date (0-100)
    # Fecha más próxima -> mayor score
    if ot.fechaentrega:
        f_ent = ot.fechaentrega
        if hasattr(f_ent, 'tzinfo') and f_ent.tzinfo is not None:
            f_ent = f_ent.replace(tzinfo=None)
        dias_restantes = (f_ent - now).total_seconds() / 86400.0
        if dias_restantes <= 0:
            score_due = 100.0  # Vencida o entrega hoy
        elif dias_restantes >= 15.0:
            score_due = 15.0
        else:
            score_due = round(100.0 - (dias_restantes / 15.0) * 85.0, 1)
    else:
        dias_restantes = None
        score_due = 50.0

    # 2. Score Holgura (0-100)
    # Menor holgura -> mayor score
    slack_data = calculate_slack(ot)
    holgura_horas = slack_data['holgura']
    if slack_data['estado'] == 'SIN_FECHA_ENTREGA':
        score_holgura = 40.0
    elif holgura_horas <= 0:
        score_holgura = 100.0
    elif holgura_horas >= 48.0:
        score_holgura = 10.0
    else:
        score_holgura = round(100.0 - (holgura_horas / 48.0) * 90.0, 1)

    # 3. Score Impacto Operacional (0-100)
    # Basado en partes críticas, componentes involucrados y costo de fabricación
    tiene_criticos = False
    costo_total = 0
    partes_count = 0
    for otp in ot.partes.all():
        partes_count += 1
        if otp.idparte and otp.idparte.escritico:
            tiene_criticos = True
        if otp.idparte and otp.idparte.costofabricacion:
            costo_total += otp.idparte.costofabricacion

    base_impacto = 40.0
    if tiene_criticos:
        base_impacto += 35.0
    if costo_total > 2000:
        base_impacto += 15.0
    if partes_count > 1:
        base_impacto += 10.0
    score_impacto = min(100.0, base_impacto)

    # 4. Score WSPT (0-100)
    # Peso / Tiempo Procesamiento. Tareas cortas de alto impacto obtienen mayor WSPT
    horas_pendientes = slack_data.get('horas_pendientes', 8.0)
    peso_tarea = 5.0 if tiene_criticos else 3.0
    wspt_raw = calculate_wspt(peso_tarea, horas_pendientes)
    # Normalizar WSPT en escala 0-100 (típico entre 0.1 y 2.0)
    score_wspt = min(100.0, max(5.0, round(wspt_raw * 50.0, 1)))

    # 5. Score Comercial (0-100)
    # Escala 1 a 5 -> 20, 40, 60, 80, 100
    prio_comercial = ot.prioridad or 1
    score_comercial = round(min(5, max(1, prio_comercial)) * 20.0, 1)

    # Cálculo Ponderado Final
    w_due = config.peso_due_date
    w_holg = config.peso_holgura
    w_imp = config.peso_impacto
    w_wspt = config.peso_wspt
    w_com = config.peso_comercial

    score_total = round(
        (w_due * score_due) +
        (w_holg * score_holgura) +
        (w_imp * score_impacto) +
        (w_wspt * score_wspt) +
        (w_com * score_comercial),
        1
    )

    # Generación de Explicabilidad (Sección 33)
    razones = []
    if score_due >= 80:
        if dias_restantes is not None and dias_restantes <= 0:
            razones.append("fecha de entrega comprometida ya vencida")
        else:
            razones.append(f"fecha de entrega muy próxima ({dias_restantes:.1f} días restantes)")
    if score_holgura >= 80:
        razones.append(f"holgura operacional crítica ({holgura_horas:.1f} hrs)")
    if score_impacto >= 75:
        razones.append("alto impacto operacional con componentes críticos de bomba")
    if score_wspt >= 70:
        razones.append("alta eficiencia de procesamiento WSPT (tarea de rápida resolución)")
    if score_comercial >= 80:
        razones.append(f"prioridad comercial de cliente nivel {prio_comercial}/5")

    if not razones:
        explicacion = "OT en condiciones operacionales normales dentro de los márgenes programados."
    else:
        explicacion = f"OT priorizada debido a: {', '.join(razones)}."

    return {
        'idordentrabajo': ot.idordentrabajo,
        'nombreordentrabajo': ot.nombreordentrabajo,
        'cliente': ot.idcliente.nombrecliente if ot.idcliente else 'N/A',
        'score_total': score_total,
        'desglose': {
            'due_date': {'score': score_due, 'peso': w_due, 'contribucion': round(score_due * w_due, 1)},
            'holgura': {'score': score_holgura, 'peso': w_holg, 'contribucion': round(score_holgura * w_holg, 1)},
            'impacto': {'score': score_impacto, 'peso': w_imp, 'contribucion': round(score_impacto * w_imp, 1)},
            'wspt': {'score': score_wspt, 'peso': w_wspt, 'contribucion': round(score_wspt * w_wspt, 1)},
            'comercial': {'score': score_comercial, 'peso': w_com, 'contribucion': round(score_comercial * w_com, 1)},
        },
        'datos_base': {
            'dias_restantes': round(dias_restantes, 1) if dias_restantes is not None else None,
            'holgura_horas': holgura_horas,
            'horas_pendientes': horas_pendientes,
            'tiene_criticos': tiene_criticos,
            'prioridad_comercial': prio_comercial,
        },
        'explicacion': explicacion
    }


def prioritize_all_ots():
    """
    Evalúa y ordena todas las OTs activas según su Score de Prioridad descendente.
    """
    config = get_active_config()
    ots = MCTOrdenTrabajo.objects.select_related('idcliente', 'idproducto').prefetch_related(
        'partes', 'partes__idparte', 'partes__idcomponente', 'movimientos'
    ).all()

    ranked = []
    for ot in ots:
        res = calculate_priority_score(ot, config=config)
        ranked.append(res)

    ranked.sort(key=lambda x: x['score_total'], reverse=True)

    for i, item in enumerate(ranked, start=1):
        item['posicion'] = i

    return ranked
