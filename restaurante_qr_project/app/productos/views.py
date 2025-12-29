# app/productos/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Producto
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def productos_agrupados(request):
    """
    API para obtener productos agrupados por categoría para el menú del cliente
    """
    try:
        logger.debug("Cargando productos para el menú del cliente")

        # Obtener todos los productos activos
        productos = Producto.objects.filter(activo=True).order_by('nombre')
        logger.debug(f"Productos encontrados: {productos.count()}")
        
        # Agrupar productos por categoría
        productos_agrupados = {}
        
        for producto in productos:
            # Convertir categoría a string
            try:
                if hasattr(producto, 'categoria') and producto.categoria:
                    categoria = str(producto.categoria.nombre if hasattr(producto.categoria, 'nombre') else producto.categoria)
                else:
                    categoria = 'Menú Principal'
            except Exception as e:
                logger.warning(f"Error obteniendo categoría: {e}")
                categoria = 'Menú Principal'

            if categoria not in productos_agrupados:
                productos_agrupados[categoria] = []

            # Procesar imagen
            imagen_url = ''
            if hasattr(producto, 'imagen') and producto.imagen:
                try:
                    if hasattr(producto.imagen, 'url'):
                        imagen_url = producto.imagen.url
                    elif hasattr(producto.imagen, 'name') and producto.imagen.name:
                        imagen_url = f"{settings.MEDIA_URL}{producto.imagen.name}"
                    else:
                        imagen_str = str(producto.imagen).strip()
                        if imagen_str and imagen_str != '':
                            imagen_url = imagen_str if imagen_str.startswith('http') else f"{settings.MEDIA_URL}{imagen_str}"
                except Exception as e:
                    logger.warning(f"Error procesando imagen para {producto.nombre}: {e}")
                    imagen_url = ''
            
            # ✅ Crear diccionario del producto
            producto_data = {
                'id': producto.id,
                'nombre': str(producto.nombre),
                'precio': float(producto.precio),
                'descripcion': str(getattr(producto, 'descripcion', '')),
                'imagen': imagen_url,  # ✅ URL de imagen
                'disponible': bool(getattr(producto, 'disponible', True)),
            }
            
            productos_agrupados[categoria].append(producto_data)
        
        # Convertir a lista para el frontend
        categorias_lista = []
        for categoria_nombre, productos_lista in productos_agrupados.items():
            categorias_lista.append({
                'nombre': str(categoria_nombre),
                'productos': productos_lista
            })

        # ✅ Estructura de respuesta
        response_data = {
            'categorias': categorias_lista,
            'total_productos': int(productos.count())
        }

        logger.debug(f"Enviando {len(categorias_lista)} categorías con {productos.count()} productos")

        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Error cargando productos: {str(e)}")

        return Response({
            'error': str(e),
            'categorias': [],
            'total_productos': 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def lista_productos(request):
    """
    API simple para obtener todos los productos activos y disponibles
    Incluye información de stock y categoría para el selector visual
    """
    try:
        # Filtrar solo productos activos Y disponibles
        productos = Producto.objects.filter(
            activo=True,
            disponible=True
        ).select_related('categoria').order_by('categoria__nombre', 'nombre')

        productos_data = []

        for producto in productos:
            # Procesar imagen
            imagen_url = ''
            if hasattr(producto, 'imagen') and producto.imagen:
                try:
                    if hasattr(producto.imagen, 'url'):
                        imagen_url = producto.imagen.url
                    elif hasattr(producto.imagen, 'name') and producto.imagen.name:
                        imagen_url = f"{settings.MEDIA_URL}{producto.imagen.name}"
                    else:
                        imagen_str = str(producto.imagen).strip()
                        if imagen_str and imagen_str != '':
                            if imagen_str.startswith('http'):
                                imagen_url = imagen_str
                            else:
                                imagen_url = f"{settings.MEDIA_URL}{imagen_str}"
                except Exception as e:
                    logger.warning(f"Error obteniendo imagen para {producto.nombre}: {e}")
                    imagen_url = ''

            # Obtener nombre de categoría
            categoria_nombre = 'Sin Categoría'
            if producto.categoria:
                categoria_nombre = producto.categoria.nombre

            productos_data.append({
                'id': producto.id,
                'nombre': str(producto.nombre),
                'precio': float(producto.precio),
                'descripcion': str(getattr(producto, 'descripcion', '')),
                'imagen': imagen_url,
                'disponible': bool(producto.disponible),
                'categoria_nombre': categoria_nombre,
                'stock_actual': int(producto.stock_actual) if producto.requiere_inventario else None,
                'stock_minimo': int(producto.stock_minimo) if producto.requiere_inventario else None,
                'requiere_inventario': bool(producto.requiere_inventario),
            })

        return Response({
            'productos': productos_data,
            'total': len(productos_data)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Error en lista_productos: {str(e)}")
        return Response({
            'error': str(e),
            'productos': [],
            'total': 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)