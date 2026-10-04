from django.urls import path
from scheduling import views

urlpatterns = [
    # Vistas HTML con Templates
    path('priorizacion/', views.priorizacion_view, name='scheduling_priorizacion'),
    path('plan/', views.plan_view, name='scheduling_plan'),
    path('capacidad/', views.capacidad_view, name='scheduling_capacidad'),
    path('simulacion/', views.simulacion_view, name='scheduling_simulacion'),

    # Endpoints API REST (Sección 43)
    path('api/priorizacion/', views.api_priorizacion, name='api_priorizacion'),
    path('api/capacidad/', views.api_capacidad, name='api_capacidad'),
    path('api/cuello-botella/', views.api_cuello_botella, name='api_cuello_botella'),
    path('api/scheduling/calcular/', views.api_scheduling_calcular, name='api_scheduling_calcular'),
    path('api/simulaciones/urgencia/', views.api_simulacion_urgencia, name='api_simulaciones_urgencia'),
]
