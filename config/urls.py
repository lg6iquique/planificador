from django.contrib import admin
from django.urls import path, include
from quality.views import dashboard_home
import planning.views as p_views
import analytics.views as a_views
import scheduling.views as s_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Dashboard Ejecutivo / Inicio
    path('', dashboard_home, name='dashboard_home'),

    # Módulos por Prefijo (Convención ARCHITECTURE.md)
    path('planning/', include('planning.urls')),
    path('analytics/', include('analytics.urls')),
    path('scheduling/', include('scheduling.urls')),
    path('quality/', include('quality.urls')),

    # Rutas API REST directas (Sección 43 del PROMPT_BASE.md)
    path('api/ordenes/', p_views.api_ordenes, name='api_root_ordenes'),
    path('api/ordenes/<int:id>/', p_views.api_orden_detail, name='api_root_orden_detail'),
    path('api/componentes/', p_views.api_componentes, name='api_root_componentes'),
    path('api/partes/', p_views.api_partes, name='api_root_partes'),
    path('api/maquinas/', p_views.api_maquinas, name='api_root_maquinas'),
    path('api/operadores/', p_views.api_operadores, name='api_root_operadores'),
    path('api/hojas-ruta/', p_views.api_hojas_ruta, name='api_root_hojas_ruta'),
    path('api/movimientos/', p_views.api_movimientos, name='api_root_movimientos'),
    path('api/capacidad/', s_views.api_capacidad, name='api_root_capacidad'),
    path('api/priorizacion/', s_views.api_priorizacion, name='api_root_priorizacion'),
    path('api/cuello-botella/', s_views.api_cuello_botella, name='api_root_cuello_botella'),
    path('api/analisis/tiempos/', a_views.api_analisis_tiempos, name='api_root_analisis_tiempos'),
    path('api/analisis/desviaciones/', a_views.api_analisis_desviaciones, name='api_root_analisis_desviaciones'),
    path('api/scheduling/calcular/', s_views.api_scheduling_calcular, name='api_root_scheduling_calcular'),
    path('api/simulaciones/urgencia/', s_views.api_simulacion_urgencia, name='api_root_simulaciones_urgencia'),
]
