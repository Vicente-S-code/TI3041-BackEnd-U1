# Resumen Ejecutivo del Proyecto: VentaControl Pro
**Caso 2: Aplicación de Control de Venta Básico**  
**Tecnologías:** Django 6.x &bull; SQLite &bull; Tailwind CSS &bull; django-crispy-forms &bull; crispy-tailwind

---

## 1. ¿Qué se implementó en el sistema?

El proyecto transforma una gestión manual de tienda en un **sistema SaaS empresarial** para digitalizar el catálogo de productos, existencias, clientes y ventas con emisión de boleta legal.

### Funcionalidades Obligatorias Desarrolladas
1. **Registro de Productos:** Formulario con `nombre`, `codigo` (SKU único), `precio` (> 0) y `stock` (>= 0).
2. **Control y Actualización de Stock:** Edición completa y modal rápido para sumar o fijar unidades.
3. **Eliminación Segura de Productos:** Confirmación previa con validación para no borrar productos con ventas asociadas.
4. **Inventario con Badges de Color:**
   - **Verde (Alto):** > 20 unidades.
   - **Amarillo (Medio):** 6 a 20 unidades.
   - **Rojo (Bajo/Crítico):** &le; 5 unidades.
   - **Buscador en tiempo real** por JavaScript (filtra instantáneamente).
5. **Terminal de Punto de Venta (POS):**
   - Catálogo interactivo a la izquierda.
   - Carrito reactivo a la derecha con cálculo automático de Subtotal, IVA (19%) y Total.
   - Transacción atómica (`transaction.atomic()`): Valida existencias y descuenta el stock de inmediato.
6. **Lógica de Clientes Dual:**
   - **Cliente Habitual:** Switch interactivo activado &rarr; Guarda nombre completo, correo y teléfono.
   - **Boleta Rápida (Cliente Ocasional):** Switch desactivado &rarr; Solicita únicamente el RUT por normativa legal.
7. **Boleta Electrónica Imprimible:**
   - Detalle de ítems, folio único, desglose tributario (Neto + IVA 19%) y botón de impresión con estilos térmicos (`@media print`).
8. **Dashboard Gerencial:**
   - KPIs de productos registrados, stock total, ventas del día y clientes habituales.
   - Gráficos analíticos simulados con barras de progreso Tailwind.

---

## 2. Arquitectura Django MVT Aplicada

```text
TI3041-BackEnd-U1/
│
├── mi_proyecto/            # Configuración global del proyecto
│   ├── settings.py         # Apps externas (crispy-forms, crispy-tailwind), i18n 'es-cl'
│   └── urls.py             # Enrutamiento general y personalización de Django Admin
│
├── inventario/             # Aplicación principal del negocio
│   ├── models.py           # Modelos: Producto, Cliente, Venta, DetalleVenta
│   ├── forms.py            # Formularios con crispy-forms, FormHelper y validaciones
│   ├── views.py            # 11 vistas: Dashboard, CRUD productos, clientes, POS, boleta
│   ├── urls.py             # Rutas semánticas (/productos/, /clientes/, /ventas/)
│   ├── admin.py            # Registro de modelos en Django Admin con filtros e inlines
│   ├── tests.py            # 9 pruebas unitarias automatizadas (100% aprobadas)
│   └── templates/inventario/ # 10 plantillas HTML estilizadas con Tailwind CSS
│       ├── base.html       # Layout SaaS, navbar con glassmorphism y mensajes Toast
│       ├── dashboard.html  # KPIs y gráficos
│       ├── producto_list.html
│       ├── producto_form.html
│       ├── producto_confirm_delete.html
│       ├── cliente_list.html
│       ├── cliente_form.html
│       ├── venta_pos.html  # Terminal POS
│       ├── venta_detail.html # Boleta electrónica imprimible
│       └── venta_list.html
│
├── static/css/custom.css   # Glassmorphism y reglas @media print
└── seed_data.py            # Script para poblar 12 productos, clientes y ventas de prueba
```

---

## 3. Puntos Evaluados en la Rúbrica

| Criterio | Justificación Técnica |
| :--- | :--- |
| **Variables y Operaciones** | Tipado de campos en ORM; cálculo de subtotal (`precio * cantidad`), IVA (`total - neto`) y neto (`round(total / 1.19)`). |
| **Estructuras de Decisión** | Condicionales `if/elif/else` para umbrales de stock, validación de sobreventa y alternancia de cliente habitual vs boleta rápida. |
| **Integración de Paquetes** | `django-crispy-forms` y `crispy-tailwind` integrados en `settings.py`, `forms.py` y templates. |
| **Validaciones** | Precio > 0, Stock >= 0, RUT obligatorio y normalizado, SKU único, nombre obligatorio. |
| **Transacciones Atómicas** | `with transaction.atomic():` en el checkout para garantizar consistencia y evitar sobreventa. |

---

## 4. Comandos para Ejecutar el Proyecto

```powershell
# 1. Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# 2. Iniciar el servidor
python manage.py runserver

# 3. Ejecutar pruebas unitarias (9 pruebas)
python manage.py test inventario
```

- **Web:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) (Usuario: `admin` | Clave: `admin123`)
