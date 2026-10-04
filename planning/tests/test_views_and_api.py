from django.test import TestCase, Client
from django.urls import reverse
from planning.db_init import seed_poc_data
from planning.models import MCTOrdenTrabajo


class ViewsAndApiTests(TestCase):
    """
    Pruebas de todas las vistas con templates y endpoints API REST.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        seed_poc_data()

    def setUp(self):
        self.client = Client()

    def test_dashboard_home_view(self):
        """Prueba vista del dashboard principal."""
        resp = self.client.get(reverse('dashboard_home'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'quality/dashboard_home.html')
        self.assertTemplateUsed(resp, 'base.html')

    def test_planning_ordenes_list_view(self):
        """Prueba vista de listado de OTs."""
        resp = self.client.get(reverse('planning_ordenes_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'planning/ordenes_list.html')
        self.assertContains(resp, 'OT-30101')

    def test_planning_orden_detail_view(self):
        """Prueba vista de detalle de OT recorriendo cadena relacional."""
        resp = self.client.get(reverse('planning_orden_detail', kwargs={'id': 30101}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'planning/orden_detail.html')
        self.assertContains(resp, 'HR-30101-EJE')

    def test_planning_movimientos_view(self):
        """Prueba vista de movimientos de taller."""
        resp = self.client.get(reverse('planning_movimientos_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'planning/movimientos_list.html')

    def test_analytics_tiempos_view(self):
        """Prueba vista de análisis estadístico."""
        resp = self.client.get(reverse('analytics_tiempos'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'analytics/tiempos.html')

    def test_analytics_desviaciones_view(self):
        """Prueba vista de desviaciones y semáforos."""
        resp = self.client.get(reverse('analytics_desviaciones'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'analytics/desviaciones.html')

    def test_scheduling_priorizacion_view(self):
        """Prueba vista de priorización inteligente."""
        resp = self.client.get(reverse('scheduling_priorizacion'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'scheduling/priorizacion.html')

    def test_scheduling_plan_view(self):
        """Prueba vista de secuencia de plan y decisión humana."""
        resp = self.client.get(reverse('scheduling_plan'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'scheduling/plan.html')

    def test_scheduling_capacidad_view(self):
        """Prueba vista de capacidad y cuellos de botella."""
        resp = self.client.get(reverse('scheduling_capacidad'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'scheduling/capacidad.html')

    def test_scheduling_simulacion_view(self):
        """Prueba vista de simulación interactiva."""
        resp = self.client.get(reverse('scheduling_simulacion'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'scheduling/simulacion.html')

    def test_quality_audit_view(self):
        """Prueba vista de auditoría Data Quality."""
        resp = self.client.get(reverse('quality_audit'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'quality/audit.html')

    # Pruebas de API REST (Sección 43)
    def test_api_ordenes(self):
        resp = self.client.get(reverse('api_root_ordenes'))
        self.assertEqual(resp.status_code, 200)
        json_data = resp.json()
        self.assertIn('ordenes', json_data)
        self.assertGreaterEqual(len(json_data['ordenes']), 1)

    def test_api_orden_detail(self):
        resp = self.client.get(reverse('api_root_orden_detail', kwargs={'id': 30101}))
        self.assertEqual(resp.status_code, 200)
        json_data = resp.json()
        self.assertEqual(json_data['idordentrabajo'], 30101)

    def test_api_priorizacion(self):
        resp = self.client.get(reverse('api_root_priorizacion'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('ranking', resp.json())

    def test_api_capacidad(self):
        resp = self.client.get(reverse('api_root_capacidad'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('maquinas', resp.json())

    def test_api_simulacion_urgencia(self):
        resp = self.client.get(reverse('api_root_simulaciones_urgencia') + '?ot_id=30106&escenario=B')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['success'])
