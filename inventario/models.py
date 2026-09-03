"""
Módulo de Modelos de Datos - Aplicación Inventario y Control de Ventas
======================================================================
Este archivo define la capa de persistencia (Modelos) siguiendo la arquitectura
MVT (Modelo-Vista-Template) de Django y el patrón de mapeo objeto-relacional (ORM).

Modelos implementados:
1. Producto: Gestión del catálogo, códigos de barras/SKU, precios y control de existencias.
2. Cliente: Gestión de clientes habituales y soporte para clientes ocasionales (boleta rápida).
3. Venta: Cabecera de transacción comercial asociada a un cliente, fecha y total.
4. DetalleVenta: Ítems comercializados por cada venta, con cantidades y cálculo de subtotales.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


# =====================================================================
# MODELO: PRODUCTO
# =====================================================================
class Producto(models.Model):
    """
    Representa un artículo disponible para la venta en el establecimiento.
    
    Campos obligatorios según requerimiento:
    - nombre: Nombre descriptivo del producto.
    - codigo: Código de identificación único (SKU o código de barras).
    - precio: Valor unitario de venta (en CLP, debe ser mayor a 0).
    - stock: Cantidad de unidades físicas disponibles (no puede ser negativo).
    - fecha_creacion: Marca temporal del momento en que se registró el producto.
    """
    nombre = models.CharField(
        max_length=120,
        verbose_name="Nombre del Producto",
        help_text="Nombre comercial del producto (Obligatorio)."
    )
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código / SKU",
        help_text="Identificador único del producto en el inventario."
    )
    precio = models.PositiveIntegerField(
        verbose_name="Precio Unitario ($)",
        help_text="Precio de venta en CLP. Debe ser un valor estrictamente mayor a 0."
    )
    stock = models.IntegerField(
        default=0,
        verbose_name="Stock Disponible",
        help_text="Unidades físicas disponibles. No puede ser un valor negativo."
    )
    fecha_creacion = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Registro",
        help_text="Fecha y hora de incorporación al catálogo."
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        """Representación en texto del producto para interfaces y selects."""
        return f"[{self.codigo}] {self.nombre} - ${self.precio:,} (Stock: {self.stock})"

    def clean(self):
        """
        Validación a nivel de modelo para asegurar integridad de negocio.
        - Estructura de decisión: Comprueba que precio > 0 y stock >= 0.
        """
        super().clean()
        
        # Validación de negocio: El precio debe ser obligatoriamente mayor que cero
        if self.precio is not None and self.precio <= 0:
            raise ValidationError({
                'precio': 'El precio del producto debe ser un monto mayor a 0.'
            })
            
        # Validación de negocio: El inventario físico no admite existencias negativas
        if self.stock is not None and self.stock < 0:
            raise ValidationError({
                'stock': 'El stock disponible no puede ser una cantidad negativa.'
            })

    @property
    def stock_badge(self):
        """
        Determina la clasificación del stock mediante estructuras de decisión:
        - 'alto': Stock superior a 20 unidades (Verde).
        - 'medio': Stock entre 6 y 20 unidades (Amarillo).
        - 'bajo': Stock igual o menor a 5 unidades (Rojo).
        """
        if self.stock > 20:
            return {
                'nivel': 'Alto',
                'bg_color': 'bg-emerald-500/10',
                'text_color': 'text-emerald-600',
                'border_color': 'border-emerald-500/20',
                'dot_color': 'bg-emerald-500'
            }
        elif self.stock >= 6:
            return {
                'nivel': 'Medio',
                'bg_color': 'bg-amber-500/10',
                'text_color': 'text-amber-600',
                'border_color': 'border-amber-500/20',
                'dot_color': 'bg-amber-500'
            }
        else:
            return {
                'nivel': 'Bajo',
                'bg_color': 'bg-rose-500/10',
                'text_color': 'text-rose-600',
                'border_color': 'border-rose-500/20',
                'dot_color': 'bg-rose-500'
            }


# =====================================================================
# MODELO: CLIENTE
# =====================================================================
class Cliente(models.Model):
    """
    Representa a los compradores del establecimiento.
    
    Soporta dos modalidades operativas:
    1. Cliente Habitual: Registra datos de contacto completos para fidelización.
    2. Cliente Ocasional / Boleta Rápida: Registra únicamente el RUT exigido por ley para boleta.
    """
    rut = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="RUT",
        help_text="RUT del cliente (Formato: 12.345.678-9 o 12345678-K)."
    )
    nombre = models.CharField(
        max_length=120,
        blank=True,
        default="Cliente Ocasional",
        verbose_name="Nombre Completo",
        help_text="Nombre del cliente habitual o identificación genérica."
    )
    correo = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo Electrónico",
        help_text="Opcional para cliente habitual."
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono",
        help_text="Número de contacto o WhatsApp."
    )
    cliente_habitual = models.BooleanField(
        default=False,
        verbose_name="¿Es Cliente Habitual?",
        help_text="Indica si el comprador aceptó registrarse como cliente frecuente."
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre', 'rut']

    def __str__(self):
        """Retorna formato amigable del cliente con su RUT."""
        tipo = "Habitual" if self.cliente_habitual else "Ocasional"
        return f"{self.nombre} ({self.rut}) - [{tipo}]"

    def clean(self):
        """
        Validación de lógica de negocio:
        - Si cliente_habitual es True, el nombre no puede ser el genérico ni quedar vacío.
        """
        super().clean()
        if self.cliente_habitual:
            if not self.nombre or self.nombre.strip() == "Cliente Ocasional":
                raise ValidationError({
                    'nombre': 'Para registrar como cliente habitual debe ingresar el nombre completo.'
                })


# =====================================================================
# MODELO: VENTA
# =====================================================================
class Venta(models.Model):
    """
    Cabecera de la transacción de venta.
    
    Campos obligatorios según requerimiento:
    - cliente: Referencia al cliente asociado a la compra (mediante su RUT).
    - fecha: Fecha y hora exacta de la transacción.
    - total: Monto final acumulado a pagar.
    """
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='ventas',
        verbose_name="Cliente Asociado"
    )
    fecha = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha y Hora de Emisión"
    )
    total = models.PositiveIntegerField(
        default=0,
        verbose_name="Monto Total ($)"
    )

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta #{self.id:05d} - {self.cliente.nombre} (${self.total:,})"

    @property
    def numero_boleta(self):
        """Genera un folio con formato de 6 dígitos para la boleta comercial."""
        return f"BOL-{self.id:06d}"

    @property
    def subtotal_neto(self):
        """
        Cálculo del valor Neto (sin IVA) en base a la tasa de IVA en Chile (19%).
        Fórmula: Neto = Total / 1.19
        """
        if self.total > 0:
            return round(self.total / 1.19)
        return 0

    @property
    def iva(self):
        """
        Cálculo del IVA (19%) correspondiente al monto de la venta.
        Fórmula: IVA = Total - Neto
        """
        return self.total - self.subtotal_neto


# =====================================================================
# MODELO: DETALLE DE VENTA
# =====================================================================
class DetalleVenta(models.Model):
    """
    Ítem individual de productos que componen una venta específica.
    
    Campos obligatorios según requerimiento:
    - venta: Llave foránea que enlaza el detalle a su cabecera de venta.
    - producto: Llave foránea hacia el producto vendido.
    - cantidad: Número de unidades adquiridas.
    - subtotal: Monto parcial de este ítem (precio unitario * cantidad).
    """
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Venta"
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='detalles_venta',
        verbose_name="Producto Vendido"
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name="Cantidad"
    )
    subtotal = models.PositiveIntegerField(
        default=0,
        verbose_name="Subtotal Ítem ($)"
    )

    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} = ${self.subtotal:,}"

    def save(self, *args, **kwargs):
        """
        Calcula automáticamente el subtotal al guardar usando multiplicación:
        subtotal = precio del producto * cantidad vendida
        """
        if self.producto and self.cantidad:
            self.subtotal = self.producto.precio * self.cantidad
        super().save(*args, **kwargs)
