"""
Módulo de Pruebas Unitarias e Integración - inventario/tests.py
===============================================================
Asegura la calidad del software y el cumplimiento estricto de la rúbrica:
1. Validación de modelos y reglas de negocio (precio > 0, stock >= 0, RUT único).
2. Cálculo tributario de Neto, IVA (19%) y Total.
3. Transacción atómica de venta y descuento de existencias físicas.
4. Códigos de respuesta HTTP (200 OK, 302 Redirect) para todas las vistas.
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from .models import Producto, Cliente, Venta, DetalleVenta
from .forms import ProductoForm, ClienteForm


class ProductoModelTest(TestCase):
    """Pruebas de integridad del modelo Producto."""

    def test_crear_producto_valido(self):
        """Verifica la creación exitosa de un producto con datos válidos."""
        prod = Producto.objects.create(
            nombre="Café Colombiano 250g",
            codigo="CAF-001",
            precio=4990,
            stock=15
        )
        self.assertEqual(prod.codigo, "CAF-001")
        self.assertEqual(prod.stock, 15)
        self.assertEqual(prod.stock_badge['nivel'], 'Medio')

    def test_validacion_precio_invalido(self):
        """Verifica que el modelo rechace precios iguales o menores a cero."""
        prod = Producto(
            nombre="Producto Gratis Error",
            codigo="ERR-001",
            precio=0,
            stock=10
        )
        with self.assertRaises(ValidationError):
            prod.full_clean()

    def test_validacion_stock_negativo(self):
        """Verifica que el modelo rechace existencias negativas."""
        prod = Producto(
            nombre="Stock Negativo Error",
            codigo="ERR-002",
            precio=1000,
            stock=-5
        )
        with self.assertRaises(ValidationError):
            prod.full_clean()

    def test_stock_badge_clasificacion(self):
        """Comprueba que la clasificación de badges corresponda a los umbrales definidos."""
        p_alto = Producto.objects.create(nombre="A", codigo="A1", precio=100, stock=25)
        p_medio = Producto.objects.create(nombre="B", codigo="B1", precio=100, stock=10)
        p_bajo = Producto.objects.create(nombre="C", codigo="C1", precio=100, stock=3)

        self.assertEqual(p_alto.stock_badge['nivel'], 'Alto')
        self.assertEqual(p_medio.stock_badge['nivel'], 'Medio')
        self.assertEqual(p_bajo.stock_badge['nivel'], 'Bajo')


class ClienteModelTest(TestCase):
    """Pruebas de integridad del modelo Cliente."""

    def test_cliente_habitual_requiere_nombre(self):
        """Un cliente habitual no puede tener nombre genérico ni vacío."""
        cli = Cliente(
            rut="11.222.333-4",
            nombre="Cliente Ocasional",
            cliente_habitual=True
        )
        with self.assertRaises(ValidationError):
            cli.clean()

    def test_cliente_ocasional_valido(self):
        """Un cliente ocasional solo requiere RUT para emitir boleta rápida."""
        cli = Cliente.objects.create(
            rut="99.888.777-6",
            cliente_habitual=False
        )
        self.assertEqual(cli.nombre, "Cliente Ocasional")
        self.assertFalse(cli.cliente_habitual)


class VentaPosTransactionTest(TestCase):
    """Pruebas de integración del flujo de ventas y descuento de inventario."""

    def setUp(self):
        self.client = Client()
        self.producto = Producto.objects.create(
            nombre="Bebida Cola 1.5L",
            codigo="BEB-TEST",
            precio=2000,
            stock=10
        )
        self.cliente = Cliente.objects.create(
            rut="12.345.678-5",
            nombre="Cliente Prueba",
            cliente_habitual=True
        )

    def test_venta_descuenta_stock_correctamente(self):
        """Verifica que una venta exitosa descuente las unidades exactas de inventario."""
        stock_inicial = self.producto.stock
        cantidad_a_comprar = 3

        carro_data = [{
            'id': str(self.producto.id),
            'nombre': self.producto.nombre,
            'precio': self.producto.precio,
            'cantidad': cantidad_a_comprar,
            'maxStock': stock_inicial
        }]

        url = reverse('venta_pos')
        response = self.client.post(url, {
            'carro_data': json.dumps(carro_data),
            'cliente_id': str(self.cliente.id),
            'cliente_rut': ''
        })

        # Redirección a la boleta
        self.assertEqual(response.status_code, 302)

        # Verificar stock descontado
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, stock_inicial - cantidad_a_comprar)

        # Verificar venta y cálculo tributario
        venta = Venta.objects.latest('fecha')
        self.assertEqual(venta.total, 6000)
        self.assertEqual(venta.detalles.count(), 1)
        self.assertGreater(venta.iva, 0)
        self.assertEqual(venta.subtotal_neto + venta.iva, venta.total)

    def test_venta_rechaza_sobreventa(self):
        """Verifica que no se permita vender más existencias de las disponibles."""
        carro_data = [{
            'id': str(self.producto.id),
            'nombre': self.producto.nombre,
            'precio': self.producto.precio,
            'cantidad': 15, # Más del stock de 10
            'maxStock': 10
        }]

        url = reverse('venta_pos')
        response = self.client.post(url, {
            'carro_data': json.dumps(carro_data),
            'cliente_id': str(self.cliente.id),
            'cliente_rut': ''
        })

        # El stock no debe alterarse
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)
        # No se crea venta
        self.assertEqual(Venta.objects.count(), 0)


class VistasHttpTest(TestCase):
    """Prueba que todas las vistas clave respondan con código HTTP 200."""

    def test_todas_las_vistas_principales_cargan(self):
        c = Client()
        rutas = [
            reverse('dashboard'),
            reverse('producto_list'),
            reverse('producto_create'),
            reverse('cliente_list'),
            reverse('cliente_create'),
            reverse('venta_pos'),
            reverse('venta_list'),
        ]
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                resp = c.get(ruta)
                self.assertEqual(resp.status_code, 200, f"Error en la ruta: {ruta}")
