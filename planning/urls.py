from django.urls import path
from planning import views

urlpatterns = [
    # Vistas HTML con Templates
    path('ordenes/', views.ordenes_list_view, name='planning_ordenes_list'),
    path('ordenes/<int:id>/', views.orden_detail_view, name='planning_orden_detail'),
    path('movimientos/', views.movimientos_list_view, name='planning_movimientos_list'),

    # Endpoints API REST (Sección 43)
    path('api/ordenes/', views.api_ordenes, name='api_ordenes'),
    path('api/ordenes/<int:id>/', views.api_orden_detail, name='api_orden_detail'),
    path('api/componentes/', views.api_componentes, name='api_componentes'),
    path('api/partes/', views.api_partes, name='api_partes'),
    path('api/maquinas/', views.api_maquinas, name='api_maquinas'),
    path('api/operadores/', views.api_operadores, name='api_operadores'),
    path('api/hojas-ruta/', views.api_hojas_ruta, name='api_hojas_ruta'),
    path('api/movimientos/', views.api_movimientos, name='api_movimientos'),
]
