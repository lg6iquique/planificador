import datetime
from django.test import TestCase
from planning.db_init import seed_poc_data
from planning.models import (
    MCTOrdenTrabajo, MCTMovimientoOrdenTrabajo, MCTMaquina,
    MCTOrdenTrabajoParte, MCTHojaRuta, PocConfigPriorizacion
)
from analytics.services.duration_service import (
    calculate_real_duration, calculate_deviation, calculate_slack,
    calculate_critical_ratio, calculate_wspt, get_current_time
)
from scheduling.services.priority_service import calculate_priority_score
from scheduling.services.capacity_service import calculate_machine_capacity
from scheduling.services.scheduler_service import generate_schedule


class EdgeCasesTests(TestCase):
    """
    Pruebas de casos límite y robustez operativa según la Sección 34 y 47 del PROMPT_BASE.md.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        seed_poc_data()

    def test_seccion_34_ot_a_vs_ot_b_evaluacion_integral(self):
        """
        Sección 34: OT A (corta, crítica) vs OT B (larga, media).
        El sistema no debe asumir ciegamente que A siempre precede a B sin evaluar:
        fecha de entrega, holgura, impacto, recursos y tiempo.
        """
        ot_a = MCTOrdenTrabajo.objects.get(idordentrabajo=30101)  # Corta, crítica
        ot_b = MCTOrdenTrabajo.objects.get(idordentrabajo=30102)  # Larga, media

        score_a = calculate_priority_score(ot_a)
        score_b = calculate_priority_score(ot_b)

        # OT A tiene fecha más cercana (2 días) vs OT B (12 días)
        # por lo que el score de DueDate y Holgura de A es mayor que el de B
        self.assertGreater(score_a['desglose']['due_date']['score'], score_b['desglose']['due_date']['score'])
        self.assertGreater(score_a['desglose']['impacto']['score'], score_b['desglose']['impacto']['score'])
        self.assertGreater(score_a['score_total'], score_b['score_total'])

        # Ahora invertimos el caso: si OT B tiene fecha de entrega para HOY (urgente) y OT A para el próximo mes:
        now = get_current_time()
        ot_b.fechaentrega = now + datetime.timedelta(hours=2)
        ot_b.save()
        ot_a.fechaentrega = now + datetime.timedelta(days=30)
        ot_a.save()

        score_a_mod = calculate_priority_score(ot_a)
        score_b_mod = calculate_priority_score(ot_b)

        # Ahora OT B debe superar a OT A debido a la inminencia de su fecha y holgura crítica
        self.assertGreater(score_b_mod['desglose']['due_date']['score'], score_a_mod['desglose']['due_date']['score'])
        self.assertGreater(score_b_mod['score_total'], score_a_mod['score_total'])

    def test_fechainicio_null(self):
        """Caso límite: fechainicio NULL no rompe el sistema."""
        mov = MCTMovimientoOrdenTrabajo.objects.create(
            idmovimientoordentrabajo=8801,
            idordentrabajo_id=30101,
            fechainicio=None,
            fechatermino=None,
            estadoactividad=1
        )
        res = calculate_real_duration(mov)
        self.assertFalse(res['es_valido'])
        self.assertEqual(res['estado'], 'SIN_FECHA_INICIO')
        self.assertEqual(res['duracion_horas'], 0.0)

    def test_fechatermino_null(self):
        """Caso límite: fechatermino NULL (movimiento abierto) es tratado con tiempo continuo."""
        now = get_current_time()
        mov = MCTMovimientoOrdenTrabajo.objects.create(
            idmovimientoordentrabajo=8802,
            idordentrabajo_id=30101,
            fechainicio=now - datetime.timedelta(hours=5),
            fechatermino=None,
            estadoactividad=1
        )
        res = calculate_real_duration(mov)
        self.assertTrue(res['es_valido'])
        self.assertTrue(res['es_abierto'])
        self.assertAlmostEqual(res['duracion_horas'], 5.0, delta=0.5)

    def test_fechatermino_menor_a_fechainicio(self):
        """Caso límite: fechatermino < fechainicio entrega error controlado y previene caída."""
        now = get_current_time()
        mov = MCTMovimientoOrdenTrabajo.objects.create(
            idmovimientoordentrabajo=8803,
            idordentrabajo_id=30101,
            fechainicio=now,
            fechatermino=now - datetime.timedelta(hours=3),
            estadoactividad=2
        )
        res = calculate_real_duration(mov)
        self.assertFalse(res['es_valido'])
        self.assertEqual(res['estado'], 'TIEMPO_INCONSISTENTE_NEGATIVO')
        self.assertIn('anterior a fechainicio', res['error'])

    def test_ot_sin_componente_ni_partes(self):
        """Caso límite: OT sin partes ni componentes calcula score con valores por defecto controlados."""
        now = get_current_time()
        ot_vacia = MCTOrdenTrabajo.objects.create(
            idordentrabajo=8804,
            nombreordentrabajo='OT Vacía Sin Partes',
            fecharecepcion=now,
            fechaentrega=now + datetime.timedelta(days=5),
            prioridad=1
        )
        res = calculate_priority_score(ot_vacia)
        self.assertGreater(res['score_total'], 0.0)
        self.assertFalse(res['datos_base']['tiene_criticos'])

    def test_ot_fecha_entrega_vencida(self):
        """Caso límite: OT con fecha de entrega ya vencida entrega holgura negativa y alerta crítica."""
        now = get_current_time()
        ot_vencida = MCTOrdenTrabajo.objects.create(
            idordentrabajo=8805,
            nombreordentrabajo='OT Vencida',
            fecharecepcion=now - datetime.timedelta(days=10),
            fechaentrega=now - datetime.timedelta(days=2),
            prioridad=4
        )
        slack = calculate_slack(ot_vencida, horas_trabajo_pendientes=10.0)
        self.assertLess(slack['holgura'], 0.0)
        self.assertEqual(slack['estado'], 'CRITICO')

        prio = calculate_priority_score(ot_vencida)
        self.assertEqual(prio['desglose']['due_date']['score'], 100.0)
        self.assertEqual(prio['desglose']['holgura']['score'], 100.0)

    def test_tiempo_cero_y_tiempo_negativo(self):
        """Caso límite: WSPT con tiempo cero maneja división de forma segura."""
        val_cero = calculate_wspt(peso=5.0, tiempo_procesamiento_horas=0.0)
        self.assertEqual(val_cero, 999.0)

        val_negativo = calculate_wspt(peso=5.0, tiempo_procesamiento_horas=-2.0)
        self.assertEqual(val_negativo, 999.0)

    def test_varias_ots_para_la_misma_maquina(self):
        """Caso límite: Varias OTs secuenciadas en la misma máquina generan cola ordenada sin superponerse."""
        plan = generate_schedule()
        detalles_m5 = plan.detalles.filter(maquina__codigomaquina='M-05').order_by('orden_secuencia')
        if detalles_m5.count() >= 2:
            d1 = detalles_m5[0]
            d2 = detalles_m5[1]
            # La segunda tarea debe iniciar después o al finalizar la primera
            self.assertGreaterEqual(d2.fecha_inicio_estimada, d1.fecha_fin_estimada)
