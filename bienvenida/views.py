from django.shortcuts import render
from django.http import HttpResponse
from .models import producto
# Create your views here

def inicio(request):
    return HttpResponse(
"Hola mundo desde Django"
)

def lista_producto(request):
    productos = producto.objects.all()
    return render(request, "productos/lista.html", {"productos": productos})