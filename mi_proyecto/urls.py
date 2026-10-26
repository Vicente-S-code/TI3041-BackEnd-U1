"""
Enrutamiento Principal del Proyecto - mi_proyecto
==================================================
Conecta las rutas del panel de administración y delega el flujo comercial
hacia el archivo urls.py de la aplicación 'inventario'.
"""

from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from inventario.api import router


# Personalización de títulos del panel administrativo de Django
admin.site.site_header = "VentaControl Pro - Administración"
admin.site.site_title = "VentaControl Pro"
admin.site.index_title = "Panel de Gestión y Auditoría"

urlpatterns = [
    path("api-auth/", include("rest_framework.urls")),
    path('admin/', admin.site.urls),
    path('', include('inventario.urls')),
    path("api/", include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
