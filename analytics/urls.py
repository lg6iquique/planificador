from django.urls import path
from analytics import views

urlpatterns = [
    # Vistas HTML con Templates
    path('tiempos/', views.analytics_tiempos_view, name='analytics_tiempos'),
    path('desviaciones/', views.analytics_desviaciones_view, name='analytics_desviaciones'),

    # Endpoints API REST (Sección 43)
    path('api/tiempos/', views.api_analisis_tiempos, name='api_analisis_tiempos'),
    path('api/desviaciones/', views.api_analisis_desviaciones, name='api_analisis_desviaciones'),
]
