"""
Configuración del Panel Administrativo de Django - inventario/admin.py
=======================================================================
Registra los modelos Producto, Cliente, Venta y DetalleVenta con filtros,
búsquedas avanzadas e inlines para auditoría completa desde el admin de Django.
"""

from django.contrib import admin
from .models import Producto, Cliente, Venta, DetalleVenta


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Configuración administrativa para el catálogo de productos."""
    list_display = ('codigo', 'nombre', 'precio', 'stock', 'fecha_creacion')
    search_fields = ('nombre', 'codigo')
    list_filter = ('fecha_creacion',)
    ordering = ('-fecha_creacion',)
    list_per_page = 20


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """Configuración administrativa para clientes."""
    list_display = ('rut', 'nombre', 'cliente_habitual', 'correo', 'telefono')
    search_fields = ('rut', 'nombre', 'correo')
    list_filter = ('cliente_habitual',)
    ordering = ('nombre',)
    list_per_page = 20


class DetalleVentaInline(admin.TabularInline):
    """Permite visualizar y editar los ítems de venta directamente en la vista de Venta."""
    model = DetalleVenta
    extra = 0
    readonly_fields = ('producto', 'cantidad', 'subtotal')
    can_delete = False


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    """Configuración administrativa para transacciones de venta."""
    list_display = ('numero_boleta', 'cliente', 'total', 'fecha')
    search_fields = ('id', 'cliente__nombre', 'cliente__rut')
    list_filter = ('fecha',)
    ordering = ('-fecha',)
    inlines = [DetalleVentaInline]
    list_per_page = 20
