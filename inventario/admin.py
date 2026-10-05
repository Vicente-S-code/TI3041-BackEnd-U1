"""
Configuración del Panel Administrativo de Django - inventario/admin.py
=======================================================================
Panel de administración avanzado, atractivo y optimizado para VentaControl Pro:
1. Inlines para detalle de venta con soporte para añadir/editar/eliminar ítems.
2. Cálculo automático y en tiempo real del Total de la venta basado en los inlines.
3. Resumen y agregación de totales en el changelist de Ventas.
4. Reporte analítico completo por rango de fechas (con KPIs, desglose tributario,
   ranking de productos más vendidos y exportación a CSV / impresión PDF).
5. Badges visuales de stock y tipo de cliente.
"""

from datetime import datetime, timedelta
import csv
import json

from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count

from .models import Producto, Cliente, Venta, DetalleVenta


# =====================================================================
# 1. ADMIN DE PRODUCTOS CON BADGES DE STOCK Y FORMATO CLP
# =====================================================================
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Configuración administrativa para el catálogo de productos."""
    list_display = ('codigo', 'nombre', 'precio_formateado', 'stock_badge_display', 'fecha_creacion_formateada')
    search_fields = ('nombre', 'codigo')
    list_filter = ('fecha_creacion',)
    ordering = ('-fecha_creacion',)
    list_per_page = 20

    @admin.display(description="Precio Unitario", ordering='precio')
    def precio_formateado(self, obj):
        return format_html(
            '<span style="font-weight: 600; font-family: monospace; font-size: 13px;">${} CLP</span>',
            f"{obj.precio:,}"
        )

    @admin.display(description="Estado de Stock", ordering='stock')
    def stock_badge_display(self, obj):
        """Genera un badge moderno con indicador de color según los umbrales de negocio."""
        if obj.stock > 20:
            bg_color = "rgba(16, 185, 129, 0.12)"
            text_color = "#059669"
            border_color = "rgba(16, 185, 129, 0.35)"
            dot_color = "#10b981"
            label = "Alto"
        elif obj.stock >= 6:
            bg_color = "rgba(245, 158, 11, 0.12)"
            text_color = "#d97706"
            border_color = "rgba(245, 158, 11, 0.35)"
            dot_color = "#f59e0b"
            label = "Medio"
        else:
            bg_color = "rgba(239, 68, 68, 0.14)"
            text_color = "#dc2626"
            border_color = "rgba(239, 68, 68, 0.35)"
            dot_color = "#ef4444"
            label = "Crítico / Bajo"

        return format_html(
            '<span style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; '
            'border-radius: 9999px; font-size: 12px; font-weight: 600; '
            'background-color: {}; color: {}; border: 1px solid {};">'
            '<span style="width: 8px; height: 8px; border-radius: 50%; background-color: {}; '
            'box-shadow: 0 0 6px {};"></span>'
            '{} ({} un.)'
            '</span>',
            bg_color, text_color, border_color, dot_color, dot_color, label, obj.stock
        )

    @admin.display(description="Fecha Registro", ordering='fecha_creacion')
    def fecha_creacion_formateada(self, obj):
        return timezone.localtime(obj.fecha_creacion).strftime('%d/%m/%Y %H:%M')


# =====================================================================
# 2. ADMIN DE CLIENTES CON IDENTIFICACIÓN DE CATEGORÍA
# =====================================================================
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """Configuración administrativa para clientes."""
    list_display = ('rut', 'nombre', 'tipo_cliente_badge', 'correo', 'telefono', 'total_ventas_asociadas')
    search_fields = ('rut', 'nombre', 'correo')
    list_filter = ('cliente_habitual',)
    ordering = ('nombre',)
    list_per_page = 20

    @admin.display(description="Categoría", ordering='cliente_habitual')
    def tipo_cliente_badge(self, obj):
        if obj.cliente_habitual:
            return format_html(
                '<span style="display: inline-flex; align-items: center; gap: 5px; padding: 3px 9px; '
                'border-radius: 9999px; font-size: 11px; font-weight: 600; '
                'background-color: rgba(59, 130, 246, 0.12); color: #2563eb; border: 1px solid rgba(59, 130, 246, 0.3);">'
                '★ Habitual</span>'
            )
        return format_html(
            '<span style="display: inline-flex; align-items: center; gap: 5px; padding: 3px 9px; '
            'border-radius: 9999px; font-size: 11px; font-weight: 500; '
            'background-color: rgba(148, 163, 184, 0.12); color: #64748b; border: 1px solid rgba(148, 163, 184, 0.3);">'
            'Ocasional</span>'
        )

    @admin.display(description="Boletas Registradas")
    def total_ventas_asociadas(self, obj):
        conteo = obj.ventas.count()
        return format_html('<strong>{}</strong> boletas', conteo)


# =====================================================================
# 3. INLINE PARA DETALLE DE VENTA CON CÁLCULO DE TOTAL AUTOMÁTICO
# =====================================================================
class DetalleVentaInline(admin.TabularInline):
    """
    Inline para gestionar los ítems de venta directamente en la vista de Venta.
    Permite agregar, editar o quitar productos, recalculando el subtotal y total.
    """
    model = DetalleVenta
    extra = 1
    autocomplete_fields = ['producto']
    fields = ('producto', 'cantidad', 'subtotal_display')
    readonly_fields = ('subtotal_display',)
    can_delete = True
    verbose_name = "Ítem de Venta"
    verbose_name_plural = "Detalle de Productos Vendidos"

    @admin.display(description="Subtotal Ítem ($)")
    def subtotal_display(self, obj):
        if obj.pk and obj.subtotal:
            return format_html(
                '<span style="font-weight: 700; color: #10b981; font-size: 13px;">${} CLP</span>',
                f"{obj.subtotal:,}"
            )
        return mark_safe('<span style="color: #94a3b8; font-style: italic;">Calculado al guardar</span>')


# =====================================================================
# 4. ADMIN DE VENTAS CON CÁLCULO DE TOTAL Y REPORTE POR FECHAS
# =====================================================================
@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    """Configuración administrativa para transacciones de venta."""
    list_display = ('numero_boleta', 'cliente_link', 'fecha_formateada', 'items_count', 'subtotal_neto_col', 'iva_col', 'total_formateado')
    search_fields = ('id', 'cliente__nombre', 'cliente__rut')
    list_filter = ('fecha', 'cliente__cliente_habitual')
    ordering = ('-fecha',)
    inlines = [DetalleVentaInline]
    readonly_fields = ('numero_boleta', 'total_calculado_display', 'subtotal_neto_display', 'iva_display')
    list_per_page = 20

    fieldsets = (
        ('Identificación de la Venta', {
            'fields': ('numero_boleta', 'cliente', 'fecha')
        }),
        ('Cálculo de Totales e Impuestos (19% IVA)', {
            'fields': ('total_calculado_display', 'subtotal_neto_display', 'iva_display'),
            'description': 'El Total se recalcula automáticamente sumando los subtotales de cada ítem en el Detalle inferior.'
        }),
    )

    def save_related(self, request, form, formsets, change):
        """
        Recalcula automáticamente el Total de la venta sumando los subtotales
        de todos los ítems agregados o modificados en los inlines.
        """
        super().save_related(request, form, formsets, change)
        obj = form.instance
        # Recalcular el total a partir de los detalles guardados
        nuevo_total = sum(item.subtotal for item in obj.detalles.all())
        if obj.total != nuevo_total:
            obj.total = nuevo_total
            obj.save(update_fields=['total'])

    @admin.display(description="Cliente", ordering='cliente__nombre')
    def cliente_link(self, obj):
        tipo = "Habitual" if obj.cliente.cliente_habitual else "Ocasional"
        return format_html(
            '<strong>{}</strong> <small style="color: #64748b;">({}) [{}]</small>',
            obj.cliente.nombre, obj.cliente.rut, tipo
        )

    @admin.display(description="Fecha Emisión", ordering='fecha')
    def fecha_formateada(self, obj):
        return timezone.localtime(obj.fecha).strftime('%d/%m/%Y %H:%M')

    @admin.display(description="Ítems")
    def items_count(self, obj):
        cant = sum(d.cantidad for d in obj.detalles.all())
        lineas = obj.detalles.count()
        return format_html('<span>{} un. <small>({} prod.)</small></span>', cant, lineas)

    @admin.display(description="Neto ($)")
    def subtotal_neto_col(self, obj):
        return format_html('<span style="color: #64748b;">${}</span>', f"{obj.subtotal_neto:,}")

    @admin.display(description="IVA 19% ($)")
    def iva_col(self, obj):
        return format_html('<span style="color: #f59e0b;">${}</span>', f"{obj.iva:,}")

    @admin.display(description="Total Venta ($)", ordering='total')
    def total_formateado(self, obj):
        return format_html(
            '<span style="font-weight: 700; color: #10b981; font-size: 13px;">${} CLP</span>',
            f"{obj.total:,}"
        )

    @admin.display(description="Monto Total Calculado")
    def total_calculado_display(self, obj):
        return format_html(
            '<div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); '
            'padding: 10px 16px; border-radius: 8px; display: inline-block;">'
            '<span style="font-size: 1.4rem; font-weight: 800; color: #10b981;">${} CLP</span>'
            '<div style="font-size: 11px; color: #059669; margin-top: 2px;">Cálculo automático de subtotales</div>'
            '</div>',
            f"{obj.total:,}"
        )

    @admin.display(description="Subtotal Neto (81%)")
    def subtotal_neto_display(self, obj):
        return format_html(
            '<span style="font-weight: 600; font-size: 14px;">${} CLP</span> '
            '<small style="color: #64748b;">(Monto base sin impuestos)</small>',
            f"{obj.subtotal_neto:,}"
        )

    @admin.display(description="IVA Débito Fiscal (19%)")
    def iva_display(self, obj):
        return format_html(
            '<span style="font-weight: 600; font-size: 14px; color: #f59e0b;">${} CLP</span> '
            '<small style="color: #64748b;">(Tasa IVA legal en Chile)</small>',
            f"{obj.iva:,}"
        )

    def changelist_view(self, request, extra_context=None):
        """
        Agrega métricas consolidadas (recaudación total, promedio, conteo)
        del conjunto de ventas filtrado actualmente.
        """
        extra_context = extra_context or {}
        try:
            cl = self.get_changelist_instance(request)
            qs = cl.get_queryset(request)
            agregados = qs.aggregate(
                total_monto=Sum('total'),
                total_conteo=Count('id')
            )
            total_monto = agregados['total_monto'] or 0
            total_conteo = agregados['total_conteo'] or 0
            ticket_promedio = round(total_monto / total_conteo) if total_conteo > 0 else 0
            neto_total = round(total_monto / 1.19)
            iva_total = total_monto - neto_total

            extra_context['cl_total_monto'] = total_monto
            extra_context['cl_total_ventas'] = total_conteo
            extra_context['cl_ticket_promedio'] = ticket_promedio
            extra_context['cl_neto_total'] = neto_total
            extra_context['cl_iva_total'] = iva_total
        except Exception:
            pass
        return super().changelist_view(request, extra_context=extra_context)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Inyecta el catálogo de productos con sus precios para cálculo dinámico en el inline."""
        extra_context = extra_context or {}
        try:
            productos_data = {
                str(p.id): {'precio': p.precio, 'nombre': p.nombre, 'stock': p.stock}
                for p in Producto.objects.all()
            }
            extra_context['productos_catalog_json'] = json.dumps(productos_data)
        except Exception:
            extra_context['productos_catalog_json'] = '{}'
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        """Registra la ruta personalizada para el reporte de ventas por rango de fechas."""
        urls = super().get_urls()
        custom_urls = [
            path(
                'reporte/',
                self.admin_site.admin_view(self.reporte_view),
                name='inventario_venta_reporte'
            ),
        ]
        return custom_urls + urls

    def reporte_view(self, request):
        """
        Vista administrativa para el Reporte de Ventas por Rango de Fechas.
        Permite filtrar transacciones por fechas, calcular métricas de recaudación,
        desglose tributario, unidades vendidas, ranking de productos y exportar a CSV.
        """
        hoy = timezone.localdate()
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        preset = request.GET.get('preset', '')

        # Aplicación de presets de rango de fechas
        if preset == 'hoy':
            fecha_inicio = hoy
            fecha_fin = hoy
        elif preset == '7dias':
            fecha_inicio = hoy - timedelta(days=7)
            fecha_fin = hoy
        elif preset == 'mes':
            fecha_inicio = hoy.replace(day=1)
            fecha_fin = hoy
        elif preset == 'ano':
            fecha_inicio = hoy.replace(month=1, day=1)
            fecha_fin = hoy
        elif preset == 'todo':
            primera_venta = Venta.objects.order_by('fecha').first()
            fecha_inicio = primera_venta.fecha.date() if primera_venta else (hoy - timedelta(days=30))
            fecha_fin = hoy
        else:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date() if fecha_inicio_str else (hoy - timedelta(days=30))
            except (ValueError, TypeError):
                fecha_inicio = hoy - timedelta(days=30)

            try:
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date() if fecha_fin_str else hoy
            except (ValueError, TypeError):
                fecha_fin = hoy

        # Consulta de ventas en el rango especificado
        ventas_qs = Venta.objects.filter(
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).select_related('cliente').prefetch_related('detalles__producto').order_by('-fecha')

        # Exportación a formato CSV si se solicita
        if request.GET.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="reporte_ventas_{fecha_inicio}_{fecha_fin}.csv"'
            response.write('\ufeff')  # BOM UTF-8 para compatibilidad nativa con Excel en español
            writer = csv.writer(response, delimiter=';')
            writer.writerow(['Folio', 'Fecha y Hora', 'RUT Cliente', 'Nombre Cliente', 'Tipo Cliente', 'Neto ($)', 'IVA 19% ($)', 'Total ($)', 'Cant. Ítems'])
            for v in ventas_qs:
                tipo = "Habitual" if v.cliente.cliente_habitual else "Ocasional"
                cant_items = sum(d.cantidad for d in v.detalles.all())
                writer.writerow([
                    v.numero_boleta,
                    timezone.localtime(v.fecha).strftime('%d/%m/%Y %H:%M:%S'),
                    v.cliente.rut,
                    v.cliente.nombre,
                    tipo,
                    v.subtotal_neto,
                    v.iva,
                    v.total,
                    cant_items
                ])
            return response

        # Cálculo de agregados y KPIs
        total_ventas = ventas_qs.count()
        agregados = ventas_qs.aggregate(total_monto=Sum('total'))
        total_recaudado = agregados['total_monto'] or 0
        total_neto = round(total_recaudado / 1.19)
        total_iva = total_recaudado - total_neto
        ticket_promedio = round(total_recaudado / total_ventas) if total_ventas > 0 else 0

        detalles_qs = DetalleVenta.objects.filter(venta__in=ventas_qs)
        res_unidades = detalles_qs.aggregate(total_unidades=Sum('cantidad'))
        total_unidades = res_unidades['total_unidades'] or 0

        # Ranking de productos más vendidos en el periodo
        top_productos = detalles_qs.values(
            'producto__codigo',
            'producto__nombre',
            'producto__precio'
        ).annotate(
            unidades_vendidas=Sum('cantidad'),
            monto_generado=Sum('subtotal')
        ).order_by('-unidades_vendidas')[:10]

        ventas_habituales = ventas_qs.filter(cliente__cliente_habitual=True).count()
        ventas_ocasionales = total_ventas - ventas_habituales

        context = {
            **self.admin_site.each_context(request),
            'title': 'Reporte de Ventas por Rango de Fechas',
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
            'preset': preset,
            'total_ventas': total_ventas,
            'total_recaudado': total_recaudado,
            'total_neto': total_neto,
            'total_iva': total_iva,
            'ticket_promedio': ticket_promedio,
            'total_unidades': total_unidades,
            'top_productos': top_productos,
            'ventas_habituales': ventas_habituales,
            'ventas_ocasionales': ventas_ocasionales,
            'ventas': ventas_qs[:100],
            'total_transacciones_ocultas': max(0, total_ventas - 100),
        }
        return render(request, 'admin/inventario/venta/reporte.html', context)
