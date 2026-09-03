"""
Módulo de Enrutamiento de URLs - Aplicación Inventario
======================================================
Este archivo define el mapeo entre las peticiones HTTP (URLs) y las funciones controladoras
(Views), cumpliendo el enrutamiento declarativo del patrón MVT en Django.

Estructura de rutas:
- Dashboard: Métricas gerenciales y accesos directos.
- Productos: Catálogo, alta, edición, actualización de stock y eliminación.
- Clientes: Directorio y registro con switch de cliente habitual.
- Ventas: Terminal Punto de Venta (POS), boletas imprimibles e historial.
"""

from django.urls import path
from . import views

urlpatterns = [
    # 1. Dashboard principal
    path('', views.dashboard, name='dashboard'),

    # 2. Módulo de Productos e Inventario
    path('productos/', views.producto_list, name='producto_list'),
    path('productos/nuevo/', views.producto_create, name='producto_create'),
    path('productos/<int:pk>/editar/', views.producto_update, name='producto_update'),
    path('productos/<int:pk>/eliminar/', views.producto_delete, name='producto_delete'),
    path('productos/<int:pk>/stock/', views.producto_update_stock, name='producto_update_stock'),

    # 3. Módulo de Clientes
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/nuevo/', views.cliente_create, name='cliente_create'),

    # 4. Módulo de Ventas y POS
    path('ventas/', views.venta_list, name='venta_list'),
    path('ventas/nueva/', views.venta_pos, name='venta_pos'),
    path('ventas/<int:pk>/', views.venta_detail, name='venta_detail'),
]