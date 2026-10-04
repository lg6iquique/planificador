import datetime
from django.test import TestCase
from django.db import connection
from planning.db_init import seed_poc_data
from planning.models import (
    MCTOrdenTrabajo, MCTOrdenTrabajoParte, MCTComponente,
    MCTHojaRuta, MCTMovimientoOrdenTrabajo, MCTMaquina,
    MCTOperador, MCTMovimientoBloqueo, PocConfigPriorizacion
)
from analytics.services.duration_service import (
    calculate_real_duration, calculate_deviation, calculate_slack,
    calculate_critical_ratio, calculate_wspt, calculate_block_time, get_current_time
)
from scheduling.services.priority_service import calculate_priority_score, prioritize_all_ots
from scheduling.services.capacity_service import calculate_machine_capacity, detect_bottlenecks
from scheduling.services.simulation_service import simulate_urgent_order


class MandatoryPocTests(TestCase):
    """
    Batería de 20 pruebas obligatorias exigidas por la Sección 46 del PROMPT_BASE.md.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Sembrar datos en la base de pruebas de Django
        seed_poc_data()

    def test_01_django_inicia_correctamente(self):
        """Test 1: Django inicia correctamente."""
        from django.conf import settings
        self.assertTrue(settings.configured)
        self.assertIn('planning', settings.INSTALLED_APPS)

    def test_02_conexion_base_datos(self):
        """Test 2: Conexión a la base de datos (SQLite POC)."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            self.assertEqual(row[0], 1)

    def test_03_consulta_ot(self):
        """Test 3: Consulta de Órdenes de Trabajo."""
        ots = MCTOrdenTrabajo.objects.all()
        self.assertGreaterEqual(ots.count(), 1)
        ot_1 = MCTOrdenTrabajo.objects.filter(idordentrabajo=30101).first()
        self.assertIsNotNone(ot_1)
        self.assertIn('Bomba', ot_1.nombreordentrabajo)

    def test_04_ot_a_ot_parte(self):
        """Test 4: Relación OT → OT Parte."""
        ot = MCTOrdenTrabajo.objects.get(idordentrabajo=30101)
        partes = ot.partes.all()
        self.assertGreaterEqual(partes.count(), 1)
        self.assertEqual(partes.first().idordentrabajo_id, ot.idordentrabajo)

    def test_05_ot_parte_a_componente(self):
        """Test 5: Relación OT Parte → Componente."""
        ot_parte = MCTOrdenTrabajoParte.objects.get(idordentrabajoparte=401)
        comp = ot_parte.idcomponente
        self.assertIsNotNone(comp)
        self.assertIn('Eje', comp.nombrecomponente)

    def test_06_ot_parte_a_hoja_ruta(self):
        """Test 6: Relación OT Parte → Hoja de Ruta."""
        ot_parte = MCTOrdenTrabajoParte.objects.get(idordentrabajoparte=401)
        hojas = ot_parte.hojas_ruta.all()
        self.assertGreaterEqual(hojas.count(), 1)
        self.assertTrue(hojas.first().codhojaruta.startswith('HR-'))

    def test_07_hoja_ruta_a_movimiento(self):
        """Test 7: Relación Hoja de Ruta → Movimiento."""
        hr = MCTHojaRuta.objects.get(idhojaruta=501)
        movs = hr.movimientos.all()
        self.assertGreaterEqual(movs.count(), 1)

    def test_08_movimiento_a_maquina(self):
        """Test 8: Relación Movimiento → Máquina."""
        mov = MCTMovimientoOrdenTrabajo.objects.get(idmovimientoordentrabajo=601)
        self.assertIsNotNone(mov.idmaquina)
        self.assertEqual(mov.idmaquina.codigomaquina, 'M-02')

    def test_09_movimiento_a_operador(self):
        """Test 9: Relación Movimiento → Operador."""
        mov = MCTMovimientoOrdenTrabajo.objects.get(idmovimientoordentrabajo=601)
        self.assertIsNotNone(mov.idoperador)
        self.assertIn('Valenzuela', mov.idoperador.nombreoperador)

    def test_10_calculo_duracion(self):
        """Test 10: Cálculo de duración real en horas y minutos."""
        mov_cerrado = MCTMovimientoOrdenTrabajo.objects.get(idmovimientoordentrabajo=601)
        res = calculate_real_duration(mov_cerrado)
        self.assertEqual(res['estado'], 'CERRADO')
        self.assertAlmostEqual(res['duracion_horas'], 4.0, delta=0.5)
        self.assertAlmostEqual(res['duracion_minutos'], 240.0, delta=30.0)

    def test_11_calculo_desviacion(self):
        """Test 11: Cálculo de desviación y asignación de semáforo."""
        # 14h real vs 8h estimado -> desviación 6h -> AMARILLO/ROJO
        dev = calculate_deviation(14.0, 8.0)
        self.assertEqual(dev['desviacion_horas'], 6.0)
        self.assertAlmostEqual(dev['desviacion_pct'], 75.0, delta=1.0)
        self.assertIn(dev['semaforo'], ['AMARILLO', 'ROJO'])

        # 4h real vs 4h estimado -> desviación 0 -> VERDE
        dev_verde = calculate_deviation(4.0, 4.0)
        self.assertEqual(dev_verde['semaforo'], 'VERDE')

    def test_12_calculo_holgura(self):
        """Test 12: Cálculo de holgura operacional."""
        ot = MCTOrdenTrabajo.objects.get(idordentrabajo=30101)
        slack = calculate_slack(ot, horas_trabajo_pendientes=6.0)
        self.assertIn('holgura', slack)
        self.assertIn(slack['estado'], ['HOLGADO', 'AJUSTADO', 'CRITICO'])

    def test_13_critical_ratio(self):
        """Test 13: Cálculo de Critical Ratio (CR)."""
        ot = MCTOrdenTrabajo.objects.get(idordentrabajo=30101)
        cr = calculate_critical_ratio(ot, horas_trabajo_pendientes=6.0)
        self.assertGreater(cr['cr'], 0.0)
        self.assertIn(cr['estado'], ['MARGEN', 'AJUSTADO', 'RIESGO'])

    def test_14_wspt(self):
        """Test 14: Cálculo de indicador WSPT."""
        # WSPT = Peso / Tiempo
        val = calculate_wspt(peso=5.0, tiempo_procesamiento_horas=2.5)
        self.assertEqual(val, 2.0)

    def test_15_priority_score(self):
        """Test 15: Cálculo del Priority Score multicriterio."""
        ot = MCTOrdenTrabajo.objects.get(idordentrabajo=30101)
        res = calculate_priority_score(ot)
        self.assertGreaterEqual(res['score_total'], 0.0)
        self.assertLessEqual(res['score_total'], 100.0)
        self.assertIn('due_date', res['desglose'])
        self.assertIn('holgura', res['desglose'])
        self.assertIn('impacto', res['desglose'])
        self.assertIn('wspt', res['desglose'])
        self.assertIn('comercial', res['desglose'])

    def test_16_maquina_saturada(self):
        """Test 16: Detección de máquina saturada o cuello de botella."""
        # Forzar sobrecarga temporal en M-05 para validar alerta
        m5 = MCTMaquina.objects.get(codigomaquina='M-05')
        now = get_current_time()
        # Agregar movimiento de alta duración en M-05
        MCTMovimientoOrdenTrabajo.objects.create(
            idmovimientoordentrabajo=9901,
            idordentrabajo_id=30103,
            idmaquina=m5,
            fechainicio=now - datetime.timedelta(hours=50),
            estadoactividad=1,
            tiempotrabajado=3000  # 50 horas
        )
        cap = calculate_machine_capacity(disponibilidad_default_horas=40.0)
        m5_res = [m for m in cap['maquinas'] if m['codigomaquina'] == 'M-05'][0]
        self.assertGreater(m5_res['utilizacion_pct'], 100.0)
        self.assertEqual(m5_res['estado'], 'SATURADA')

    def test_17_movimiento_abierto(self):
        """Test 17: Identificación de movimiento abierto."""
        mov_abierto = MCTMovimientoOrdenTrabajo.objects.get(idmovimientoordentrabajo=604)
        res = calculate_real_duration(mov_abierto)
        self.assertEqual(res['estado'], 'ABIERTO')
        self.assertTrue(res['es_abierto'])
        self.assertGreater(res['duracion_horas'], 0.0)

    def test_18_movimiento_bloqueado(self):
        """Test 18: Identificación y cálculo de tiempo de bloqueo."""
        bloqueo = MCTMovimientoBloqueo.objects.get(idmovimientobloqueo=701)
        res = calculate_block_time(bloqueo)
        self.assertEqual(res['estado'], 'BLOQUEO_ACTIVO')
        self.assertFalse(res['desbloqueado'])
        self.assertGreater(res['horas'], 0.0)

    def test_19_urgencia_desplaza_ot(self):
        """Test 19: Simulación de urgencia que desplaza otra OT y mide costo de oportunidad."""
        sim = simulate_urgent_order(30106, escenario='B')
        self.assertTrue(sim['success'])
        self.assertGreater(sim['escenario_activo']['ots_desplazadas_count'], 0)
        self.assertGreater(sim['escenario_activo']['costo_oportunidad_total'], 0.0)

    def test_20_explicabilidad_prioridad(self):
        """Test 20: Explicabilidad en lenguaje natural de la decisión de priorización."""
        ot = MCTOrdenTrabajo.objects.get(idordentrabajo=30101)
        res = calculate_priority_score(ot)
        self.assertIsInstance(res['explicacion'], str)
        self.assertIn('OT priorizada debido a:', res['explicacion'])
