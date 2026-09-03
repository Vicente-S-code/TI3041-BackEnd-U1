"""
Módulo de Formularios - Aplicación Inventario y Control de Ventas
=================================================================
Este archivo define la capa de formularios de Django (Forms / ModelForms).
Demuestra la integración con los paquetes externos obligatorios:
- django-crispy-forms: Para generación estructurada de layouts y renderizado estético.
- crispy-tailwind: Para adaptar la salida de crispy al diseño de Tailwind CSS.

Formularios implementados:
1. ProductoForm: Alta y edición de productos con validaciones de negocio.
2. ClienteForm: Registro de clientes con soporte para clientes habituales y ocasionales.
3. ActualizarStockForm: Ajuste ágil de existencias sin necesidad de editar todo el producto.
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML
from .models import Producto, Cliente


# =====================================================================
# FORMULARIO: PRODUCTO
# =====================================================================
class ProductoForm(forms.ModelForm):
    """
    Formulario basado en modelo para registrar y actualizar productos.
    
    Requerimientos de validación:
    - Nombre obligatorio.
    - Código único y obligatorio.
    - Precio mayor que 0.
    - Stock mayor o igual a 0 (no negativo).
    """
    class Meta:
        model = Producto
        fields = ['nombre', 'codigo', 'precio', 'stock']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej: Bebida Cola 1.5L, Arroz Grano Largo...',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200'
            }),
            'codigo': forms.TextInput(attrs={
                'placeholder': 'Ej: PROD-001, 7801234567890...',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 uppercase transition-all duration-200'
            }),
            'precio': forms.NumberInput(attrs={
                'placeholder': 'Ej: 1500',
                'min': '1',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200'
            }),
            'stock': forms.NumberInput(attrs={
                'placeholder': 'Ej: 25',
                'min': '0',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200'
            }),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializador del formulario. Configura FormHelper de crispy-forms
        para aplicar estilos modernos de Tailwind CSS a cada control.
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'productoForm'
        # Desactivamos tags de form automáticos de crispy para controlar el submit con diseño personalizado
        self.helper.form_tag = False

    def clean_nombre(self):
        """
        Validación del nombre:
        - Estructura de decisión: Verifica que el texto no esté vacío ni compuesto solo de espacios.
        """
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise forms.ValidationError("El nombre del producto es un campo obligatorio.")
        return nombre

    def clean_codigo(self):
        """
        Validación de código único:
        - Verifica unicidad excluyendo el registro actual en caso de edición.
        """
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        if not codigo:
            raise forms.ValidationError("El código del producto es obligatorio.")
            
        # Comprobar si ya existe otro producto con el mismo código
        consulta = Producto.objects.filter(codigo=codigo)
        if self.instance.pk:
            consulta = consulta.exclude(pk=self.instance.pk)
            
        if consulta.exists():
            raise forms.ValidationError(f"El código '{codigo}' ya se encuentra asignado a otro producto.")
        return codigo

    def clean_precio(self):
        """
        Validación del precio:
        - Operador relacional: precio > 0 obligatorio.
        """
        precio = self.cleaned_data.get('precio')
        if precio is None or precio <= 0:
            raise forms.ValidationError("El precio debe ser un número entero mayor a 0.")
        return precio

    def clean_stock(self):
        """
        Validación de inventario:
        - Operador relacional: stock >= 0 (no se admiten existencias negativas).
        """
        stock = self.cleaned_data.get('stock')
        if stock is None or stock < 0:
            raise forms.ValidationError("El stock inicial no puede ser un valor negativo.")
        return stock


# =====================================================================
# FORMULARIO: CLIENTE
# =====================================================================
class ClienteForm(forms.ModelForm):
    """
    Formulario para el registro de clientes con lógica condicional:
    - Si el switch 'cliente_habitual' está ACTIVO:
      Se requiere nombre completo, y se aceptan correo y teléfono.
    - Si el switch 'cliente_habitual' está INACTIVO:
      Se solicita únicamente el RUT para emitir boleta rápida.
    """
    class Meta:
        model = Cliente
        fields = ['rut', 'nombre', 'correo', 'telefono', 'cliente_habitual']
        widgets = {
            'rut': forms.TextInput(attrs={
                'placeholder': '12.345.678-9 o 12345678-K',
                'id': 'id_rut',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200'
            }),
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej: Juan Pérez González',
                'id': 'id_nombre',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200'
            }),
            'correo': forms.EmailInput(attrs={
                'placeholder': 'juan.perez@ejemplo.cl',
                'id': 'id_correo',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200'
            }),
            'telefono': forms.TextInput(attrs={
                'placeholder': '+56 9 1234 5678',
                'id': 'id_telefono',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200'
            }),
            'cliente_habitual': forms.CheckboxInput(attrs={
                'id': 'id_cliente_habitual',
                'class': 'sr-only peer'
            }),
        }

    def clean_rut(self):
        """
        Limpia y valida el formato del RUT:
        - Remueve puntos y espacios.
        - Asegura longitud mínima y formato con guión.
        """
        rut = self.cleaned_data.get('rut', '').strip().upper()
        if not rut:
            raise forms.ValidationError("El RUT es obligatorio para emitir cualquier boleta legal.")
            
        # Normalización: asegurar formato limpio
        rut_limpio = rut.replace('.', '').replace(' ', '')
        if '-' not in rut_limpio:
            if len(rut_limpio) >= 2:
                rut_limpio = f"{rut_limpio[:-1]}-{rut_limpio[-1]}"
            else:
                raise forms.ValidationError("El RUT ingresado no es válido.")

        # Verificar duplicados si no estamos editando
        consulta = Cliente.objects.filter(rut=rut_limpio)
        if self.instance.pk:
            consulta = consulta.exclude(pk=self.instance.pk)
        if consulta.exists():
            raise forms.ValidationError(f"El RUT {rut_limpio} ya se encuentra registrado en el sistema.")

        return rut_limpio

    def clean(self):
        """
        Estructura de decisión condicional según el requerimiento funcional:
        - Si cliente_habitual == True: Exige que el nombre no sea genérico.
        - Si cliente_habitual == False: Asigna automáticamente 'Cliente Ocasional'.
        """
        cleaned_data = super().clean()
        es_habitual = cleaned_data.get('cliente_habitual', False)
        nombre = cleaned_data.get('nombre', '').strip()

        # Condición: Si desea ser cliente habitual, debe proporcionar su nombre real
        if es_habitual:
            if not nombre or nombre.lower() == "cliente ocasional":
                self.add_error('nombre', "Para registrarse como cliente habitual debe ingresar el Nombre Completo.")
        else:
            # Si NO es habitual, asignamos nombre genérico si se dejó en blanco
            if not nombre:
                cleaned_data['nombre'] = "Cliente Ocasional"

        return cleaned_data


# =====================================================================
# FORMULARIO: ACTUALIZAR STOCK
# =====================================================================
class ActualizarStockForm(forms.Form):
    """
    Formulario especializado para operaciones rápidas de inventario:
    - Incrementar stock (ej: llegada de mercadería).
    - Fijar un nuevo stock absoluto.
    """
    MODO_CHOICES = [
        ('sumar', 'Sumar a existencias actuales (+)'),
        ('fijar', 'Establecer nuevo stock fijo (=)'),
    ]

    modo = forms.ChoiceField(
        choices=MODO_CHOICES,
        initial='sumar',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500'
        })
    )
    cantidad = forms.IntegerField(
        min_value=1,
        initial=10,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Cantidad de unidades',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500'
        })
    )