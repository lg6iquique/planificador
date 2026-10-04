from django.urls import path
from quality import views

urlpatterns = [
    path('audit/', views.quality_audit_view, name='quality_audit'),
    path('api/audit/', views.api_quality_audit, name='api_quality_audit'),
]
