from rest_framework import routers, viewsets

from .models import Producto, Cliente, Venta, DetalleVenta
from .serializers import ProductoSerializer,ClienteSerializer, VentaSerializer, DetalleVentaSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

router = routers.DefaultRouter()
router.register(r'productos', ProductoViewSet)

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

router = routers.DefaultRouter()
router.register(r'clientes', ClienteViewSet)

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer

router = routers.DefaultRouter()
router.register(r'ventas', VentaViewSet)

class DetalleVentaViewSet(viewsets.ModelViewSet):
    queryset = DetalleVenta.objects.all()
    serializer_class = DetalleVentaSerializer

router = routers.DefaultRouter()
router.register(r'detalleventas', DetalleVentaViewSet)