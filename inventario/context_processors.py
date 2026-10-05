"""
Context Processors para VentaControl Pro
=========================================
Proporciona estadísticas globales del sistema y del inventario
a las plantillas del panel administrativo de Django.
"""

from django.db.models import Sum
from .models import Producto, Cliente, Venta


def admin_stats(request):
    """
    Inyecta contadores y métricas agregadas en las vistas de administración.
    Permite mostrar tarjetas KPI atractivas en la pantalla principal del Admin.
    """
    if request.path.startswith('/admin/'):
        try:
            total_productos = Producto.objects.count()
            total_clientes = Cliente.objects.count()
            total_ventas = Venta.objects.count()
            res_total = Venta.objects.aggregate(total_acumulado=Sum('total'))
            total_recaudado = res_total['total_acumulado'] if res_total['total_acumulado'] is not None else 0
            
            return {
                'admin_kpi_productos': total_productos,
                'admin_kpi_clientes': total_clientes,
                'admin_kpi_ventas': total_ventas,
                'admin_kpi_recaudado': total_recaudado,
            }
        except Exception:
            return {}
    return {}
