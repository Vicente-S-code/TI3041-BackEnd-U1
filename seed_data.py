import os
# pyrefly: ignore [missing-import]
import django
# pyrefly: ignore [missing-import]
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

# pyrefly: ignore [missing-import]
from django.contrib.auth.models import User
from inventario.models import Producto, Cliente, Venta, DetalleVenta

def run():
    print("=== Iniciando Poblacion de Datos para VentaControl Pro ===")

    # 1. Crear Superusuario para el Administrador / Profesor
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@ventacontrol.cl', 'admin123')
        print("[OK] Superusuario 'admin' creado exitosamente (Clave: admin123).")
    else:
        print("[INFO] Superusuario 'admin' ya existia.")

    # 2. Crear Catálogo de Productos
    productos_data = [
        # Stock Alto (> 20)
        {"nombre": "Bebida Cola Zero 1.5L", "codigo": "BEB-001", "precio": 1890, "stock": 45},
        {"nombre": "Arroz Grano Largo Selección 1kg", "codigo": "ARR-101", "precio": 1490, "stock": 60},
        {"nombre": "Aceite Vegetal Maravilla 900ml", "codigo": "ACE-201", "precio": 2350, "stock": 32},
        {"nombre": "Fideos Spaghetti N°5 400g", "codigo": "PAS-301", "precio": 890, "stock": 50},
        {"nombre": "Leche Entera Larga Vida 1L", "codigo": "LAC-401", "precio": 1150, "stock": 28},
        
        # Stock Medio (6 a 20)
        {"nombre": "Café Instantáneo Selección 170g", "codigo": "CAF-501", "precio": 4290, "stock": 14},
        {"nombre": "Detergente Líquido Concentrado 3L", "codigo": "LIM-601", "precio": 8990, "stock": 8},
        {"nombre": "Queso Laminado Gauda 250g", "codigo": "LAC-402", "precio": 2990, "stock": 12},
        {"nombre": "Galletas de Avena y Miel 200g", "codigo": "GAL-701", "precio": 1290, "stock": 18},

        # Stock Bajo / Crítico (<= 5)
        {"nombre": "Pack Pilas Alcalinas AA x4", "codigo": "ELE-801", "precio": 3490, "stock": 3},
        {"nombre": "Chocolate Amargo 70% Cacao 100g", "codigo": "DUL-901", "precio": 2190, "stock": 4},
        {"nombre": "Atún en Trozos en Aceite 160g", "codigo": "CON-111", "precio": 1590, "stock": 2},
    ]

    productos_creados = []
    for p_info in productos_data:
        prod, creado = Producto.objects.get_or_create(
            codigo=p_info['codigo'],
            defaults={
                'nombre': p_info['nombre'],
                'precio': p_info['precio'],
                'stock': p_info['stock']
            }
        )
        productos_creados.append(prod)
    print(f"[OK] {len(productos_creados)} productos sincronizados en inventario.")

    # 3. Crear Clientes (Habituales y Ocasionales)
    clientes_data = [
        # Habituales
        {
            "rut": "15.482.913-4",
            "nombre": "Francisca Morales Benítez",
            "correo": "f.morales@gmail.com",
            "telefono": "+56 9 9876 5432",
            "cliente_habitual": True
        },
        {
            "rut": "18.324.756-K",
            "nombre": "Matías Ignacio Silva Rojas",
            "correo": "matias.silva@outlook.cl",
            "telefono": "+56 9 8765 4321",
            "cliente_habitual": True
        },
        {
            "rut": "12.984.321-2",
            "nombre": "Gonzalo Patricio Herrera Vera",
            "correo": "g.herrera@empresa.cl",
            "telefono": "+56 9 7654 3210",
            "cliente_habitual": True
        },
        # Ocasionales (Boleta Rápida)
        {
            "rut": "19.876.543-1",
            "nombre": "Cliente Ocasional",
            "correo": None,
            "telefono": None,
            "cliente_habitual": False
        },
        {
            "rut": "14.567.890-8",
            "nombre": "Cliente Ocasional",
            "correo": None,
            "telefono": None,
            "cliente_habitual": False
        },
    ]

    clientes_creados = []
    for c_info in clientes_data:
        cli, _ = Cliente.objects.get_or_create(
            rut=c_info['rut'],
            defaults={
                'nombre': c_info['nombre'],
                'correo': c_info['correo'],
                'telefono': c_info['telefono'],
                'cliente_habitual': c_info['cliente_habitual']
            }
        )
        clientes_creados.append(cli)
    print(f"[OK] {len(clientes_creados)} clientes registrados.")

    # 4. Crear Transacciones de Venta Iniciales
    if Venta.objects.count() == 0:
        # Venta 1: Cliente Habitual (Francisca)
        p1 = Producto.objects.get(codigo="BEB-001")
        p2 = Producto.objects.get(codigo="GAL-701")
        total1 = (p1.precio * 2) + (p2.precio * 3)

        v1 = Venta.objects.create(
            cliente=clientes_creados[0],
            total=total1,
            fecha=timezone.now() - timedelta(hours=3)
        )
        DetalleVenta.objects.create(venta=v1, producto=p1, cantidad=2, subtotal=p1.precio * 2)
        DetalleVenta.objects.create(venta=v1, producto=p2, cantidad=3, subtotal=p2.precio * 3)

        # Venta 2: Boleta Rápida (Cliente Ocasional)
        p3 = Producto.objects.get(codigo="LIM-601")
        p4 = Producto.objects.get(codigo="LAC-401")
        total2 = (p3.precio * 1) + (p4.precio * 2)

        v2 = Venta.objects.create(
            cliente=clientes_creados[3],
            total=total2,
            fecha=timezone.now() - timedelta(hours=1)
        )
        DetalleVenta.objects.create(venta=v2, producto=p3, cantidad=1, subtotal=p3.precio * 1)
        DetalleVenta.objects.create(venta=v2, producto=p4, cantidad=2, subtotal=p4.precio * 2)

        print("[OK] 2 transacciones de venta de prueba generadas con exito.")
    else:
        print("[INFO] Ya existian ventas registradas.")

    print("\n=== Poblacion de Datos completada exitosamente ===")
    print("Acceda a http://127.0.0.1:8000/ para ver el Dashboard.")
    print("Admin: usuario='admin', contrasena='admin123'")



if __name__ == '__main__':
    run()
