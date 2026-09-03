"""
Módulo de Vistas - Aplicación Inventario y Control de Ventas
============================================================
Este archivo implementa los controladores y la lógica de negocio siguiendo el
patrón MVT de Django. Contiene:
- Operaciones matemáticas (cálculo de totales, IVA 19%, sumatorias de stock).
- Estructuras de decisión y operadores lógicos (control de inventario, validaciones).
- Transacciones atómicas seguras en base de datos para ventas e inventario.
- Mensajes flash tipo Toast para retroalimentación visual al usuario.
"""

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, F, Count
from django.utils import timezone
from datetime import datetime, time

from .models import Producto, Cliente, Venta, DetalleVenta
from .forms import ProductoForm, ClienteForm, ActualizarStockForm


# =====================================================================
# VISTA 1: DASHBOARD GERENCIAL (PANTALLA PRINCIPAL)
# =====================================================================
def dashboard(request):
    """
    Vista principal que consolida indicadores clave de rendimiento (KPIs),
    métricas de inventario, ventas del día y accesos rápidos del sistema.
    """
    # 1. Variables y operaciones de cálculo de métricas
    total_productos = Producto.objects.count()
    
    # Operación de agregación: Sumatoria del stock acumulado de todos los productos
    resultado_stock = Producto.objects.aggregate(total_stock=Sum('stock'))
    stock_total = resultado_stock['total_stock'] if resultado_stock['total_stock'] is not None else 0

    # Definición de límites del día actual (desde 00:00:00 hasta 23:59:59)
    hoy = timezone.now().date()
    inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
    fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

    # Ventas realizadas durante la jornada de hoy
    ventas_hoy_qs = Venta.objects.filter(fecha__range=(inicio_dia, fin_dia))
    cantidad_ventas_hoy = ventas_hoy_qs.count()
    
    resultado_ventas = ventas_hoy_qs.aggregate(monto_hoy=Sum('total'))
    monto_ventas_hoy = resultado_ventas['monto_hoy'] if resultado_ventas['monto_hoy'] is not None else 0

    # Conteo de clientes registrados según categoría
    clientes_habituales = Cliente.objects.filter(cliente_habitual=True).count()
    total_clientes = Cliente.objects.count()

    # Productos en alerta crítica (Stock bajo <= 5 unidades)
    productos_bajo_stock = Producto.objects.filter(stock__lte=5).order_by('stock')[:5]

    # Últimas 5 transacciones registradas en el sistema
    ultimas_ventas = Venta.objects.select_related('cliente').order_by('-fecha')[:5]

    # Simulación de datos analíticos para barras porcentuales Tailwind
    # Distribución de stock: alto (>20), medio (6-20), bajo (<=5)
    stock_alto_count = Producto.objects.filter(stock__gt=20).count()
    stock_medio_count = Producto.objects.filter(stock__gte=6, stock__lte=20).count()
    stock_bajo_count = Producto.objects.filter(stock__lte=5).count()

    # Operación de cálculo de porcentajes con estructura de decisión preventiva (división por cero)
    if total_productos > 0:
        pct_alto = round((stock_alto_count / total_productos) * 100)
        pct_medio = round((stock_medio_count / total_productos) * 100)
        pct_bajo = round((stock_bajo_count / total_productos) * 100)
    else:
        pct_alto, pct_medio, pct_bajo = 0, 0, 0

    contexto = {
        'total_productos': total_productos,
        'stock_total': stock_total,
        'cantidad_ventas_hoy': cantidad_ventas_hoy,
        'monto_ventas_hoy': monto_ventas_hoy,
        'clientes_habituales': clientes_habituales,
        'total_clientes': total_clientes,
        'productos_bajo_stock': productos_bajo_stock,
        'ultimas_ventas': ultimas_ventas,
        'distribucion_stock': {
            'alto': {'conteo': stock_alto_count, 'pct': pct_alto},
            'medio': {'conteo': stock_medio_count, 'pct': pct_medio},
            'bajo': {'conteo': stock_bajo_count, 'pct': pct_bajo},
        }
    }
    return render(request, 'inventario/dashboard.html', contexto)


# =====================================================================
# VISTA 2: LISTADO DE PRODUCTOS / INVENTARIO
# =====================================================================
def producto_list(request):
    """
    Muestra la tabla moderna de inventario con:
    - Buscador dinámico por nombre o código.
    - Filtro por estado de stock (todos, bajo, medio, alto).
    - Badges visuales de colores (verde, amarillo, rojo).
    """
    # Consulta base con ordenamiento descendente por fecha de registro
    productos_qs = Producto.objects.all().order_by('-fecha_creacion')
    
    # 1. Estructura de decisión: Búsqueda por texto (query GET)
    query = request.GET.get('q', '').strip()
    if query:
        productos_qs = productos_qs.filter(nombre__icontains=query) | productos_qs.filter(codigo__icontains=query)

    # 2. Estructura de decisión: Filtro por estado de stock
    estado_filtro = request.GET.get('estado', 'todos')
    if estado_filtro == 'bajo':
        productos_qs = productos_qs.filter(stock__lte=5)
    elif estado_filtro == 'medio':
        productos_qs = productos_qs.filter(stock__gte=6, stock__lte=20)
    elif estado_filtro == 'alto':
        productos_qs = productos_qs.filter(stock__gt=20)

    form_stock = ActualizarStockForm()

    contexto = {
        'productos': productos_qs,
        'query': query,
        'estado_filtro': estado_filtro,
        'form_stock': form_stock,
        'total_registros': productos_qs.count()
    }
    return render(request, 'inventario/producto_list.html', contexto)


# =====================================================================
# VISTA 3: REGISTRO DE PRODUCTO
# =====================================================================
def producto_create(request):
    """
    Permite registrar un nuevo artículo en el catálogo con validación de:
    - Nombre obligatorio
    - Código único
    - Precio mayor a 0
    - Stock no negativo
    """
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        # Estructura de decisión: Verificar si el formulario pasó todas las reglas
        if form.is_valid():
            producto = form.save()
            messages.success(
                request,
                f"¡Producto '{producto.nombre}' registrado exitosamente con código {producto.codigo}!"
            )
            return redirect('producto_list')
        else:
            messages.error(
                request,
                "No fue posible guardar el producto. Por favor revise las observaciones indicadas."
            )
    else:
        form = ProductoForm()

    return render(request, 'inventario/producto_form.html', {
        'form': form,
        'titulo': 'Registrar Nuevo Producto',
        'accion': 'Guardar Producto'
    })


# =====================================================================
# VISTA 4: EDICIÓN DE PRODUCTO
# =====================================================================
def producto_update(request, pk):
    """Permite modificar los atributos de un producto existente."""
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"El producto '{producto.nombre}' ha sido actualizado correctamente."
            )
            return redirect('producto_list')
        else:
            messages.error(
                request,
                "Por favor corrija los errores en el formulario antes de guardar."
            )
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'inventario/producto_form.html', {
        'form': form,
        'producto': producto,
        'titulo': f'Editar Producto: {producto.nombre}',
        'accion': 'Actualizar Producto'
    })


# =====================================================================
# VISTA 5: ACTUALIZACIÓN RÁPIDA DE STOCK
# =====================================================================
def producto_update_stock(request, pk):
    """
    Permite actualizar existencias de stock directamente:
    - Modo 'sumar': suma unidades al stock actual (llegada de mercadería).
    - Modo 'fijar': establece un nuevo valor absoluto de stock.
    """
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        form = ActualizarStockForm(request.POST)
        if form.is_valid():
            modo = form.cleaned_data['modo']
            cantidad = form.cleaned_data['cantidad']
            
            # Operaciones aritméticas y estructuras de decisión
            stock_anterior = producto.stock
            if modo == 'sumar':
                producto.stock += cantidad
            elif modo == 'fijar':
                if cantidad < 0:
                    messages.error(request, "El stock no puede ser fijado en un valor negativo.")
                    return redirect('producto_list')
                producto.stock = cantidad
            
            producto.save()
            messages.success(
                request,
                f"Stock de '{producto.nombre}' actualizado: {stock_anterior} -> {producto.stock} unidades."
            )
        else:
            messages.error(request, "Datos de actualización de stock inválidos.")
            
    return redirect('producto_list')


# =====================================================================
# VISTA 6: ELIMINACIÓN DE PRODUCTO
# =====================================================================
def producto_delete(request, pk):
    """
    Confirmación y eliminación segura de un producto.
    Valida si el producto tiene ventas asociadas antes de permitir su borrado.
    """
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        # Validación de integridad referencial: Verificar si tiene ventas registradas
        if producto.detalles_venta.exists():
            messages.warning(
                request,
                f"No se puede eliminar el producto '{producto.nombre}' porque cuenta con registros históricos de venta asociados."
            )
            return redirect('producto_list')
            
        nombre_eliminado = producto.nombre
        producto.delete()
        messages.success(request, f"El producto '{nombre_eliminado}' fue eliminado exitosamente.")
        return redirect('producto_list')

    return render(request, 'inventario/producto_confirm_delete.html', {'producto': producto})


# =====================================================================
# VISTA 7: LISTADO DE CLIENTES
# =====================================================================
def cliente_list(request):
    """Muestra el directorio de clientes clasificados entre habituales y ocasionales."""
    clientes = Cliente.objects.annotate(total_compras=Count('ventas')).order_by('-cliente_habitual', 'nombre')
    
    # Métricas de clientes
    total_clientes = clientes.count()
    total_habituales = Cliente.objects.filter(cliente_habitual=True).count()
    total_ocasionales = total_clientes - total_habituales

    return render(request, 'inventario/cliente_list.html', {
        'clientes': clientes,
        'total_clientes': total_clientes,
        'total_habituales': total_habituales,
        'total_ocasionales': total_ocasionales
    })


# =====================================================================
# VISTA 8: REGISTRO DE CLIENTES (CON SWITCH HABITUAL)
# =====================================================================
def cliente_create(request):
    """
    Formulario interactivo para registrar clientes:
    - Switch elegante: ¿Desea registrarse como cliente habitual?
    - Si está activado: Guarda nombre, correo y teléfono.
    - Si está desactivado: Guarda únicamente RUT como cliente ocasional.
    """
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            tipo = "habitual" if cliente.cliente_habitual else "ocasional"
            messages.success(
                request,
                f"Cliente {cliente.nombre} ({cliente.rut}) registrado exitosamente como cliente {tipo}."
            )
            return redirect('cliente_list')
        else:
            messages.error(request, "Por favor corrija los errores en el formulario de cliente.")
    else:
        form = ClienteForm()

    return render(request, 'inventario/cliente_form.html', {'form': form})


# =====================================================================
# VISTA 9: NUEVA VENTA (TERMINAL PUNTO DE VENTA - POS)
# =====================================================================
def venta_pos(request):
    """
    Terminal Punto de Venta (POS) interactivo:
    - Panel Izquierdo: Catálogo de productos disponibles con stock en tiempo real y buscador.
    - Panel Derecho: Carro de compra dinámico, cálculo de Subtotal, IVA (19%) y Total.
    - Selector de Cliente: Elección de cliente habitual o ingreso rápido de RUT para boleta.
    - Transacción Atómica: Descuento seguro de inventario y generación de boleta.
    """
    if request.method == 'POST':
        # Procesamiento de la orden de venta
        datos_carro_raw = request.POST.get('carro_data', '[]')
        rut_cliente = request.POST.get('cliente_rut', '').strip().upper()
        cliente_id = request.POST.get('cliente_id', '')

        # 1. Validación de cliente
        cliente = None
        if cliente_id:
            cliente = Cliente.objects.filter(id=cliente_id).first()
        elif rut_cliente:
            # Limpiar formato de RUT
            rut_limpio = rut_cliente.replace('.', '').replace(' ', '')
            if '-' not in rut_limpio and len(rut_limpio) >= 2:
                rut_limpio = f"{rut_limpio[:-1]}-{rut_limpio[-1]}"
            
            # Obtener cliente existente o crear uno nuevo ocasional para emisión rápida de boleta
            cliente, creado = Cliente.objects.get_or_create(
                rut=rut_limpio,
                defaults={
                    'nombre': 'Cliente Ocasional',
                    'cliente_habitual': False
                }
            )

        if not cliente:
            messages.error(request, "Debe ingresar un RUT válido o seleccionar un cliente para emitir la boleta.")
            return redirect('venta_pos')

        # 2. Deserializar ítems del carro enviados desde el frontend (JSON)
        try:
            items = json.loads(datos_carro_raw)
        except json.JSONDecodeError:
            items = []

        # Validación: El carro no puede estar vacío
        if not items:
            messages.error(request, "El carro de compras está vacío. Agregue productos antes de procesar la venta.")
            return redirect('venta_pos')

        # 3. Transacción atómica en la base de datos: Todo se ejecuta o nada se aplica
        try:
            with transaction.atomic():
                monto_total = 0
                detalles_a_crear = []

                # Primera pasada: Validar stock suficiente para todos los ítems
                for item in items:
                    producto_id = item.get('id')
                    cantidad = int(item.get('cantidad', 0))

                    if cantidad <= 0:
                        raise ValueError("La cantidad de cada ítem debe ser al menos 1.")

                    # Bloqueo de fila para evitar condiciones de carrera (select_for_update)
                    producto = Producto.objects.select_for_update().get(id=producto_id)

                    # Estructura de decisión: Comprobación de inventario suficiente
                    if producto.stock < cantidad:
                        raise ValueError(
                            f"Stock insuficiente para '{producto.nombre}'. Disponibles: {producto.stock}, Solicitados: {cantidad}."
                        )

                    subtotal_item = producto.precio * cantidad
                    monto_total += subtotal_item

                    detalles_a_crear.append({
                        'producto': producto,
                        'cantidad': cantidad,
                        'subtotal': subtotal_item
                    })

                # Crear la cabecera de la venta
                venta = Venta.objects.create(
                    cliente=cliente,
                    total=monto_total,
                    fecha=timezone.now()
                )

                # Descontar stock físico y guardar cada detalle de venta
                for detalle_info in detalles_a_crear:
                    prod = detalle_info['producto']
                    cant = detalle_info['cantidad']
                    
                    # Operación de descuento de inventario
                    prod.stock -= cant
                    prod.save()

                    # Guardar el detalle de venta asociado
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=prod,
                        cantidad=cant,
                        subtotal=detalle_info['subtotal']
                    )

                messages.success(
                    request,
                    f"¡Venta {venta.numero_boleta} procesada con éxito por un total de ${venta.total:,}!"
                )
                return redirect('venta_detail', pk=venta.pk)

        except ValueError as err:
            messages.error(request, str(err))
            return redirect('venta_pos')
        except Exception as exc:
            messages.error(request, f"Error inesperado al registrar la venta: {str(exc)}")
            return redirect('venta_pos')

    # Solicitud GET: Renderizar pantalla del POS
    productos = Producto.objects.filter(stock__gt=0).order_by('nombre')
    todos_productos = Producto.objects.all().order_by('nombre')
    clientes_habituales = Cliente.objects.filter(cliente_habitual=True).order_by('nombre')

    return render(request, 'inventario/venta_pos.html', {
        'productos': productos,
        'todos_productos': todos_productos,
        'clientes_habituales': clientes_habituales,
    })


# =====================================================================
# VISTA 10: DETALLE DE VENTA / BOLETA ELECTRÓNICA IMPRIMIBLE
# =====================================================================
def venta_detail(request, pk):
    """
    Renderiza la boleta electrónica de venta con formato comercial oficial:
    - Número de folio único
    - Fecha y hora
    - Identificación del cliente (RUT y Nombre)
    - Desglose de ítems, precio unitario y subtotales
    - Desglose tributario: Subtotal Neto, IVA (19%) y Total
    - Optimizado para impresión física o PDF mediante botón 'Imprimir'
    """
    venta = get_object_or_404(
        Venta.objects.select_related('cliente').prefetch_related('detalles__producto'),
        pk=pk
    )
    return render(request, 'inventario/venta_detail.html', {'venta': venta})


# =====================================================================
# VISTA 11: HISTORIAL DE VENTAS
# =====================================================================
def venta_list(request):
    """Auditoría y listado de todas las ventas emitidas."""
    ventas = Venta.objects.select_related('cliente').order_by('-fecha')
    
    # Agregaciones globales de ventas
    total_recaudado = ventas.aggregate(total=Sum('total'))['total'] or 0
    total_transacciones = ventas.count()

    return render(request, 'inventario/venta_list.html', {
        'ventas': ventas,
        'total_recaudado': total_recaudado,
        'total_transacciones': total_transacciones,
    })