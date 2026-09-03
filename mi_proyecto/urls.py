"""
Enrutamiento Principal del Proyecto - mi_proyecto
==================================================
Conecta las rutas del panel de administración y delega el flujo comercial
hacia el archivo urls.py de la aplicación 'inventario'.
"""

from django.contrib import admin
from django.urls import path, include

# Personalización de títulos del panel administrativo de Django
admin.site.site_header = "VentaControl Pro - Administración"
admin.site.site_title = "VentaControl Pro"
admin.site.index_title = "Panel de Gestión y Auditoría"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inventario.urls')),
]
