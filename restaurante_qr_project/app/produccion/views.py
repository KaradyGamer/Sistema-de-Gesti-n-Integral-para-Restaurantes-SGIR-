"""
SGIR v40.5.0 - API Views de Producción
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from decimal import Decimal
import logging

from .models import Receta, Produccion
from .services import (
    crear_receta,
    actualizar_receta,
    registrar_produccion,
    aplicar_produccion,
    anular_produccion
)
from app.productos.models import Producto

logger = logging.getLogger('app.produccion')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_recetas(request):
    """GET: Lista todas las recetas | POST: Crea receta nueva"""
    if request.method == 'GET':
        recetas = Receta.objects.select_related('producto').prefetch_related('items__insumo').all()
        data = []
        for receta in recetas:
            data.append({
                'id': receta.id,
                'producto_id': receta.producto.id,
                'producto_nombre': receta.producto.nombre,
                'version': receta.version,
                'activo': receta.activo,
                'items': [
                    {
                        'insumo_id': item.insumo.id,
                        'insumo_nombre': item.insumo.nombre,
                        'cantidad': float(item.cantidad),
                        'unidad': item.insumo.unidad,
                        'merma_pct': float(item.merma_pct)
                    }
                    for item in receta.items.all()
                ]
            })
        return Response({'success': True, 'recetas': data})

    elif request.method == 'POST':
        try:
            producto_id = request.data.get('producto_id')
            items = request.data.get('items', [])

            producto = get_object_or_404(Producto, id=producto_id)
            receta = crear_receta(producto, items, request.user)

            return Response({
                'success': True,
                'message': f'Receta creada para {producto.nombre}',
                'receta_id': receta.id
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error al crear receta")
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def api_actualizar_receta(request, producto_id):
    """Actualiza receta existente"""
    try:
        producto = get_object_or_404(Producto, id=producto_id)
        items = request.data.get('items', [])

        receta = actualizar_receta(producto, items, request.user)

        return Response({
            'success': True,
            'message': f'Receta actualizada v{receta.version}',
            'version': receta.version
        })

    except ValidationError as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Error al actualizar receta")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_registrar_produccion(request):
    """Registra intención de producir"""
    try:
        producto_id = request.data.get('producto_id')
        cantidad = Decimal(str(request.data.get('cantidad', 0)))
        lote = request.data.get('lote', '')
        notas = request.data.get('notas', '')

        producto = get_object_or_404(Producto, id=producto_id)
        produccion = registrar_produccion(producto, cantidad, lote, notas, request.user)

        return Response({
            'success': True,
            'message': f'Producción registrada: {producto.nombre} x{cantidad}',
            'produccion_id': produccion.id
        }, status=status.HTTP_201_CREATED)

    except ValidationError as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Error al registrar producción")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_aplicar_produccion(request, produccion_id):
    """Aplica producción: descuenta insumos y aumenta stock producto"""
    try:
        produccion = aplicar_produccion(produccion_id, request.user)

        return Response({
            'success': True,
            'message': f'Producción aplicada: {produccion.producto.nombre} x{produccion.cantidad_producida}',
            'produccion_id': produccion.id
        })

    except ValidationError as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Error al aplicar producción")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_anular_produccion(request, produccion_id):
    """Anula producción (requiere PIN secundario)"""
    try:
        motivo = request.data.get('motivo', '')
        pin_secundario = request.data.get('pin_secundario', '')

        if not pin_secundario:
            return Response({
                'success': False,
                'error': 'Se requiere PIN secundario para anular producción'
            }, status=status.HTTP_400_BAD_REQUEST)

        produccion = anular_produccion(produccion_id, motivo, request.user, pin_secundario)

        return Response({
            'success': True,
            'message': f'Producción anulada: {produccion.producto.nombre}',
            'produccion_id': produccion.id
        })

    except ValidationError as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Error al anular producción")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_listado_producciones(request):
    """Lista producciones con filtros opcionales"""
    try:
        producciones = Produccion.objects.select_related('producto', 'receta', 'creado_por').all()

        # Filtros opcionales
        fecha_ini = request.GET.get('fecha_ini')
        fecha_fin = request.GET.get('fecha_fin')
        producto_id = request.GET.get('producto')
        estado = request.GET.get('estado')
        lote = request.GET.get('lote')

        if fecha_ini:
            producciones = producciones.filter(fecha_creacion__gte=fecha_ini)
        if fecha_fin:
            producciones = producciones.filter(fecha_creacion__lte=fecha_fin)
        if producto_id:
            producciones = producciones.filter(producto_id=producto_id)
        if estado:
            producciones = producciones.filter(estado=estado)
        if lote:
            producciones = producciones.filter(lote__icontains=lote)

        data = []
        for prod in producciones[:100]:  # Limitar a 100 resultados
            data.append({
                'id': prod.id,
                'producto': prod.producto.nombre,
                'cantidad': float(prod.cantidad_producida),
                'lote': prod.lote or '',
                'estado': prod.get_estado_display(),
                'creado_por': prod.creado_por.username if prod.creado_por else 'N/A',
                'fecha_creacion': prod.fecha_creacion.isoformat(),
                'fecha_aplicacion': prod.fecha_aplicacion.isoformat() if prod.fecha_aplicacion else None
            })

        return Response({
            'success': True,
            'producciones': data,
            'total': len(data)
        })

    except Exception as e:
        logger.exception("Error al listar producciones")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)