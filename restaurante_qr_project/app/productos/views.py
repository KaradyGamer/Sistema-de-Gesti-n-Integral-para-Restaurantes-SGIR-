# app/productos/views.py - VERSIÓN DEBUG PARA IMÁGENES
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Producto
import os
from django.conf import settings

@api_view(['GET'])
@permission_classes([AllowAny])
def productos_agrupados(request):
    """
    API para obtener productos agrupados por categoría para el menú del cliente
    ✅ VERSIÓN DEBUG CON LOGS DETALLADOS DE IMÁGENES
    """
    try:
        print(f"🍽️ Cargando productos para el menú del cliente")
        print(f"🔧 MEDIA_URL: {settings.MEDIA_URL}")
        print(f"🔧 MEDIA_ROOT: {settings.MEDIA_ROOT}")
        
        # Obtener todos los productos activos
        productos = Producto.objects.all().order_by('nombre')
        print(f"🍽️ Productos encontrados: {productos.count()}")
        
        # Agrupar productos por categoría
        productos_agrupados = {}
        
        for producto in productos:
            print(f"\n🍽️ Procesando producto: {producto.nombre} - ${producto.precio}")
            
            # ✅ SOLUCIÓN: Convertir categoría a string siempre
            try:
                if hasattr(producto, 'categoria') and producto.categoria:
                    if hasattr(producto.categoria, 'nombre'):
                        categoria = str(producto.categoria.nombre)
                    else:
                        categoria = str(producto.categoria)
                else:
                    categoria = 'Menú Principal'
            except Exception as e:
                print(f"  ⚠️ Error obteniendo categoría: {e}")
                categoria = 'Menú Principal'
            
            print(f"  📂 Categoría: {categoria}")
            
            if categoria not in productos_agrupados:
                productos_agrupados[categoria] = []
            
            # ✅ DEBUG DETALLADO DE IMAGEN
            imagen_url = ''
            print(f"  🔍 Verificando imagen del producto...")
            print(f"  🔍 hasattr(producto, 'imagen'): {hasattr(producto, 'imagen')}")
            
            if hasattr(producto, 'imagen'):
                print(f"  🔍 producto.imagen: {producto.imagen}")
                print(f"  🔍 str(producto.imagen): '{str(producto.imagen)}'")
                print(f"  🔍 bool(producto.imagen): {bool(producto.imagen)}")
                
                if producto.imagen:
                    try:
                        # Método 1: Verificar si tiene URL
                        if hasattr(producto.imagen, 'url'):
                            imagen_url = producto.imagen.url
                            print(f"  ✅ Método 1 - URL: {imagen_url}")
                            
                            # Verificar si el archivo existe físicamente
                            full_path = os.path.join(settings.MEDIA_ROOT, str(producto.imagen))
                            exists = os.path.exists(full_path)
                            print(f"  🔍 Archivo existe en {full_path}: {exists}")
                            
                        # Método 2: Verificar si tiene name
                        elif hasattr(producto.imagen, 'name') and producto.imagen.name:
                            imagen_url = f"{settings.MEDIA_URL}{producto.imagen.name}"
                            print(f"  ✅ Método 2 - Name: {imagen_url}")
                            
                        # Método 3: String directo
                        else:
                            imagen_str = str(producto.imagen).strip()
                            if imagen_str and imagen_str != '':
                                if imagen_str.startswith('http'):
                                    imagen_url = imagen_str
                                    print(f"  ✅ Método 3a - URL externa: {imagen_url}")
                                else:
                                    imagen_url = f"{settings.MEDIA_URL}{imagen_str}"
                                    print(f"  ✅ Método 3b - String local: {imagen_url}")
                                    
                    except Exception as e:
                        print(f"  ❌ Error procesando imagen: {e}")
                        imagen_url = ''
                else:
                    print(f"  📷 Imagen vacía o None")
            else:
                print(f"  📷 No tiene atributo imagen")
            
            print(f"  🎯 URL final de imagen: '{imagen_url}'")
            
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
            print(f"  ✅ Producto agregado a categoría '{categoria}'")
        
        # Convertir a lista para el frontend
        categorias_lista = []
        for categoria_nombre, productos_lista in productos_agrupados.items():
            categorias_lista.append({
                'nombre': str(categoria_nombre),
                'productos': productos_lista
            })
        
        print(f"\n✅ Enviando {len(categorias_lista)} categorías con productos")
        
        # ✅ Estructura de respuesta
        response_data = {
            'categorias': categorias_lista,
            'total_productos': int(productos.count())
        }
        
        # DEBUG: Mostrar respuesta completa
        print(f"🔍 RESPUESTA COMPLETA:")
        import json
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error cargando productos: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Response({
            'error': str(e),
            'categorias': [],
            'total_productos': 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def lista_productos(request):
    """
    API simple para obtener todos los productos
    """
    try:
        productos = Producto.objects.all()
        productos_data = []
        
        for producto in productos:
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
                    print(f"Error obteniendo imagen para {producto.nombre}: {e}")
                    imagen_url = ''
            
            productos_data.append({
                'id': producto.id,
                'nombre': str(producto.nombre),
                'precio': float(producto.precio),
                'descripcion': str(getattr(producto, 'descripcion', '')),
                'imagen': imagen_url,
                'disponible': bool(getattr(producto, 'disponible', True)),
            })
        
        return Response(productos_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error en lista_productos: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)