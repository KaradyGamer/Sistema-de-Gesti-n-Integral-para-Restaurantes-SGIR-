# app/productos/serializers.py

from rest_framework import serializers
from .models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'precio', 'categoria_nombre', 'disponible']

    def get_categoria_nombre(self, obj):
        """Retorna el nombre de la categoría o 'Sin Categoría' si no tiene"""
        if obj.categoria:
            return obj.categoria.nombre
        return 'Sin Categoría'
