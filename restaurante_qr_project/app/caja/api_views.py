from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import date, datetime
import json
import logging

from app.pedidos.models import Pedido, DetallePedido
from app.mesas.models import Mesa
from app.mesas.utils import liberar_mesa
from app.productos.models import Producto
from .models import Transaccion, DetallePago, CierreCaja, HistorialModificacion, AlertaStock
from .utils import (
    generar_numero_factura,
    calcular_cambio,
    validar_stock_pedido,
    descontar_stock_pedido,
    calcular_totales_caja,
    crear_historial_modificacion,
    verificar_alertas_stock,
    aplicar_descuento_porcentaje,
    aplicar_propina,
    calcular_total_con_descuento_propina,
    obtener_estadisticas_caja_dia
)

# ✅ Configurar logger
logger = logging.getLogger('app.caja')


# ══════════════════════════════════════════════
# 🛒 APIS DE PEDIDOS
# ══════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_pedidos_pendientes_pago(request):
    """
    Obtiene todos los pedidos pendientes de pago
    """
    try:
        print(f"[DEBUG] API Pedidos Pendientes - Usuario: {request.user}")

        # Mostrar pedidos pendientes de pago (cualquier estado excepto cancelado)
        pedidos = Pedido.objects.filter(
            estado_pago='pendiente'
        ).exclude(
            estado='cancelado'
        ).select_related('mesa').prefetch_related('detalles__producto').order_by('fecha')

        pedidos_data = []
        for pedido in pedidos:
            # Calcular total final
            total_final = pedido.total_final if pedido.total_final > 0 else pedido.total

            # Obtener productos
            productos = []
            for detalle in pedido.detalles.all():
                productos.append({
                    'nombre': detalle.producto.nombre,
                    'cantidad': detalle.cantidad,
                    'precio_unitario': float(detalle.producto.precio),
                    'subtotal': float(detalle.subtotal)
                })

            # ✅ NUEVO: Información del mesero que comandó
            mesero_nombre = "Cliente directo"
            if pedido.mesero_comanda:
                mesero_nombre = f"{pedido.mesero_comanda.first_name} {pedido.mesero_comanda.last_name}".strip() or pedido.mesero_comanda.username

            # ✅ NUEVO: Información de quién modificó el pedido
            modificado_por = None
            if pedido.modificado:
                ultima_modificacion = pedido.historial_modificaciones.order_by('-fecha_hora').first()
                if ultima_modificacion and ultima_modificacion.usuario:
                    modificado_por = f"{ultima_modificacion.usuario.first_name} {ultima_modificacion.usuario.last_name}".strip() or ultima_modificacion.usuario.username

            pedidos_data.append({
                'id': pedido.id,
                'mesa': pedido.mesa.numero if pedido.mesa else 'N/A',
                'mesa_id': pedido.mesa.id if pedido.mesa else None,
                'fecha': pedido.fecha.strftime('%H:%M'),
                'estado': pedido.estado,  # ✅ Agregado: Estado del pedido
                'estado_pago': pedido.estado_pago,  # ✅ Agregado: Estado del pago
                'productos': productos,
                'subtotal': float(pedido.total),
                'descuento': float(pedido.descuento),
                'propina': float(pedido.propina),
                'total_final': float(total_final),
                'forma_pago': pedido.forma_pago,
                'observaciones': pedido.observaciones or '',
                'numero_personas': pedido.numero_personas,
                'mesero': mesero_nombre,
                'modificado': pedido.modificado,
                'modificado_por': modificado_por
            })

        return Response({
            'success': True,
            'pedidos': pedidos_data,
            'total_pedidos': len(pedidos_data)
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_pedidos_pendientes_pago: {str(e)}")
        import traceback
        traceback.print_exc()

        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_detalle_pedido(request, pedido_id):
    """
    Obtiene el detalle completo de un pedido específico
    """
    try:
        pedido = get_object_or_404(
            Pedido.objects.select_related('mesa').prefetch_related('detalles__producto'),
            id=pedido_id
        )

        # Productos del pedido
        productos = []
        for detalle in pedido.detalles.all():
            productos.append({
                'id': detalle.id,
                'producto_id': detalle.producto.id,
                'nombre': detalle.producto.nombre,
                'cantidad': detalle.cantidad,
                'precio_unitario': float(detalle.producto.precio),
                'subtotal': float(detalle.subtotal),
                'stock_disponible': detalle.producto.stock_actual if detalle.producto.requiere_inventario else None
            })

        # Calcular total final
        total_final = pedido.total_final if pedido.total_final > 0 else pedido.total

        return Response({
            'success': True,
            'pedido': {
                'id': pedido.id,
                'mesa': pedido.mesa.numero if pedido.mesa else 'N/A',
                'estado': pedido.estado,
                'estado_pago': pedido.estado_pago,
                'fecha': pedido.fecha.isoformat(),
                'productos': productos,
                'subtotal': float(pedido.total),
                'descuento': float(pedido.descuento),
                'descuento_porcentaje': float(pedido.descuento_porcentaje),
                'propina': float(pedido.propina),
                'total_final': float(total_final),
                'forma_pago': pedido.forma_pago,
                'observaciones': pedido.observaciones or '',
                'observaciones_caja': pedido.observaciones_caja or '',
                'modificado': pedido.modificado,
                'reasignado': pedido.reasignado
            }
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_detalle_pedido: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ══════════════════════════════════════════════
# 💰 APIS DE PAGOS
# ══════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def api_procesar_pago_simple(request):
    """
    Procesa un pago simple con un solo método de pago
    """
    try:
        pedido_id = request.data.get('pedido_id')
        metodo_pago = request.data.get('metodo_pago')
        monto_recibido = request.data.get('monto_recibido')
        referencia = request.data.get('referencia', '')

        logger.info(f"Procesando pago simple - Pedido: {pedido_id}, Método: {metodo_pago}")

        # Validaciones
        if not all([pedido_id, metodo_pago]):
            return Response({
                'success': False,
                'error': 'Faltan datos requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener pedido
        pedido = get_object_or_404(Pedido, id=pedido_id)

        # Verificar que no esté pagado
        if pedido.estado_pago == 'pagado':
            return Response({
                'success': False,
                'error': 'Este pedido ya ha sido pagado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar stock
        es_valido, productos_sin_stock = validar_stock_pedido(pedido)
        if not es_valido:
            return Response({
                'success': False,
                'error': 'Productos sin stock suficiente',
                'productos_sin_stock': productos_sin_stock
            }, status=status.HTTP_400_BAD_REQUEST)

        # Calcular total final
        total_final = calcular_total_con_descuento_propina(pedido)
        pedido.total_final = total_final

        # Calcular cambio (si es efectivo)
        cambio = 0
        if metodo_pago == 'efectivo' and monto_recibido:
            cambio = calcular_cambio(total_final, monto_recibido)

        # Crear transacción
        numero_factura = generar_numero_factura()
        transaccion = Transaccion.objects.create(
            pedido=pedido,
            cajero=request.user,
            monto_total=total_final,
            metodo_pago=metodo_pago,
            estado='procesado',
            numero_factura=numero_factura,
            referencia=referencia
        )

        # Actualizar pedido
        pedido.estado_pago = 'pagado'
        pedido.fecha_pago = timezone.now()
        pedido.cajero_responsable = request.user
        pedido.monto_pagado = total_final
        pedido.forma_pago = metodo_pago
        pedido.save()

        # Descontar stock
        descontar_stock_pedido(pedido)

        # ✅ MEJORADO: Liberar mesa (incluso si está combinada)
        if pedido.mesa:
            liberar_mesa(pedido.mesa)
            logger.info(f"Mesa {pedido.mesa.numero} liberada después del pago")

        # Verificar alertas de stock
        verificar_alertas_stock()

        logger.info(f"Pago procesado exitosamente - Factura: {numero_factura}, Total: Bs/ {total_final}")

        return Response({
            'success': True,
            'message': 'Pago procesado exitosamente',
            'transaccion_id': transaccion.id,
            'numero_factura': numero_factura,
            'total_pagado': float(total_final),
            'cambio': float(cambio) if cambio > 0 else 0,
            'metodo_pago': metodo_pago
        })

    except Exception as e:
        logger.exception(f"Error en api_procesar_pago_simple: {str(e)}")

        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def api_procesar_pago_mixto(request):
    """
    Procesa un pago mixto con múltiples métodos de pago
    """
    try:
        pedido_id = request.data.get('pedido_id')
        detalles_pago = request.data.get('detalles_pago', [])  # Lista de {metodo, monto, referencia}

        print(f"[DEBUG] Procesando pago mixto - Pedido: {pedido_id}")

        # Validaciones
        if not pedido_id or not detalles_pago:
            return Response({
                'success': False,
                'error': 'Faltan datos requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener pedido
        pedido = get_object_or_404(Pedido, id=pedido_id)

        # Verificar que no esté pagado
        if pedido.estado_pago == 'pagado':
            return Response({
                'success': False,
                'error': 'Este pedido ya ha sido pagado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Calcular total final
        total_final = calcular_total_con_descuento_propina(pedido)
        pedido.total_final = total_final

        # Validar que la suma de pagos coincida con el total
        suma_pagos = sum(Decimal(str(d.get('monto', 0))) for d in detalles_pago)
        if suma_pagos != total_final:
            return Response({
                'success': False,
                'error': f'La suma de pagos (Bs/ {suma_pagos}) no coincide con el total (Bs/ {total_final})'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar stock
        es_valido, productos_sin_stock = validar_stock_pedido(pedido)
        if not es_valido:
            return Response({
                'success': False,
                'error': 'Productos sin stock suficiente',
                'productos_sin_stock': productos_sin_stock
            }, status=status.HTTP_400_BAD_REQUEST)

        # Crear transacción principal
        numero_factura = generar_numero_factura()
        transaccion = Transaccion.objects.create(
            pedido=pedido,
            cajero=request.user,
            monto_total=total_final,
            metodo_pago='mixto',
            estado='procesado',
            numero_factura=numero_factura
        )

        # Crear detalles de pago
        for detalle in detalles_pago:
            DetallePago.objects.create(
                transaccion=transaccion,
                metodo_pago=detalle.get('metodo'),
                monto=Decimal(str(detalle.get('monto'))),
                referencia=detalle.get('referencia', '')
            )

        # Actualizar pedido
        pedido.estado_pago = 'pagado'
        pedido.fecha_pago = timezone.now()
        pedido.cajero_responsable = request.user
        pedido.monto_pagado = total_final
        pedido.forma_pago = 'mixto'
        pedido.save()

        # Descontar stock
        descontar_stock_pedido(pedido)

        # ✅ MEJORADO: Liberar mesa (incluso si está combinada)
        if pedido.mesa:
            liberar_mesa(pedido.mesa)
            logger.info(f"Mesa {pedido.mesa.numero} liberada después del pago")

        # Verificar alertas de stock
        verificar_alertas_stock()

        print(f"[DEBUG] Pago mixto procesado - Factura: {numero_factura}")

        return Response({
            'success': True,
            'message': 'Pago mixto procesado exitosamente',
            'transaccion_id': transaccion.id,
            'numero_factura': numero_factura,
            'total_pagado': float(total_final),
            'detalles_pago': [
                {
                    'metodo': d.get('metodo'),
                    'monto': float(d.get('monto'))
                } for d in detalles_pago
            ]
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_procesar_pago_mixto: {str(e)}")
        import traceback
        traceback.print_exc()

        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ══════════════════════════════════════════════
# ✏️ APIS DE MODIFICACIÓN DE PEDIDOS
# ══════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def api_aplicar_descuento(request):
    """
    Aplica un descuento por porcentaje a un pedido
    """
    try:
        pedido_id = request.data.get('pedido_id')
        porcentaje = request.data.get('porcentaje')
        motivo = request.data.get('motivo', '')

        # Validaciones
        if not pedido_id or porcentaje is None:
            return Response({
                'success': False,
                'error': 'Faltan datos requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        porcentaje = float(porcentaje)

        # Obtener pedido
        pedido = get_object_or_404(Pedido, id=pedido_id)

        # Verificar que no esté pagado
        if pedido.estado_pago == 'pagado':
            return Response({
                'success': False,
                'error': 'No se puede modificar un pedido ya pagado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Aplicar descuento
        pedido_actualizado = aplicar_descuento_porcentaje(
            pedido=pedido,
            porcentaje=porcentaje,
            usuario=request.user,
            motivo=motivo
        )

        return Response({
            'success': True,
            'message': f'Descuento del {porcentaje}% aplicado',
            'pedido': {
                'id': pedido_actualizado.id,
                'subtotal': float(pedido_actualizado.total),
                'descuento': float(pedido_actualizado.descuento),
                'descuento_porcentaje': float(pedido_actualizado.descuento_porcentaje),
                'total_final': float(pedido_actualizado.total_final)
            }
        })

    except ValueError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"[DEBUG] Error en api_aplicar_descuento: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def api_aplicar_propina(request):
    """
    Aplica propina a un pedido
    """
    try:
        pedido_id = request.data.get('pedido_id')
        monto_propina = request.data.get('monto_propina')

        # Validaciones
        if not pedido_id or monto_propina is None:
            return Response({
                'success': False,
                'error': 'Faltan datos requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener pedido
        pedido = get_object_or_404(Pedido, id=pedido_id)

        # Verificar que no esté pagado
        if pedido.estado_pago == 'pagado':
            return Response({
                'success': False,
                'error': 'No se puede modificar un pedido ya pagado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Aplicar propina
        pedido_actualizado = aplicar_propina(
            pedido=pedido,
            monto_propina=monto_propina,
            usuario=request.user
        )

        return Response({
            'success': True,
            'message': f'Propina de Bs/ {monto_propina} aplicada',
            'pedido': {
                'id': pedido_actualizado.id,
                'subtotal': float(pedido_actualizado.total),
                'propina': float(pedido_actualizado.propina),
                'total_final': float(pedido_actualizado.total_final)
            }
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_aplicar_propina: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def api_agregar_producto_pedido(request):
    """
    Agrega un producto a un pedido existente
    """
    try:
        pedido_id = request.data.get('pedido_id')
        producto_id = request.data.get('producto_id')
        cantidad = request.data.get('cantidad', 1)

        # Validaciones
        if not all([pedido_id, producto_id]):
            return Response({
                'success': False,
                'error': 'Faltan datos requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        cantidad = int(cantidad)

        # Obtener pedido y producto
        pedido = get_object_or_404(Pedido, id=pedido_id)
        producto = get_object_or_404(Producto, id=producto_id)

        # Verificar que no esté pagado
        if pedido.estado_pago == 'pagado':
            return Response({
                'success': False,
                'error': 'No se puede modificar un pedido ya pagado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar stock
        if producto.requiere_inventario and producto.stock_actual < cantidad:
            return Response({
                'success': False,
                'error': f'Stock insuficiente. Disponible: {producto.stock_actual}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Calcular subtotal
        subtotal = producto.precio * cantidad

        # Guardar estado anterior
        detalles_anteriores = list(pedido.detalles.all().values('producto__nombre', 'cantidad'))

        # Agregar producto
        detalle = DetallePedido.objects.create(
            pedido=pedido,
            producto=producto,
            cantidad=cantidad,
            subtotal=subtotal
        )

        # Recalcular total del pedido
        pedido.total = pedido.detalles.aggregate(Sum('subtotal'))['subtotal__sum'] or 0
        pedido.total_final = calcular_total_con_descuento_propina(pedido)
        pedido.modificado = True
        pedido.save()

        # Guardar estado nuevo
        detalles_nuevos = list(pedido.detalles.all().values('producto__nombre', 'cantidad'))

        # Crear historial
        crear_historial_modificacion(
            pedido=pedido,
            usuario=request.user,
            tipo_cambio='agregar_producto',
            detalle_anterior={'productos': detalles_anteriores, 'total': float(pedido.total - subtotal)},
            detalle_nuevo={'productos': detalles_nuevos, 'total': float(pedido.total)},
            motivo=f'Agregado: {cantidad}x {producto.nombre}'
        )

        return Response({
            'success': True,
            'message': f'Producto agregado: {cantidad}x {producto.nombre}',
            'pedido': {
                'id': pedido.id,
                'total': float(pedido.total),
                'total_final': float(pedido.total_final)
            },
            'detalle': {
                'id': detalle.id,
                'producto': producto.nombre,
                'cantidad': cantidad,
                'subtotal': float(subtotal)
            }
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_agregar_producto_pedido: {str(e)}")
        import traceback
        traceback.print_exc()

        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def api_eliminar_producto_pedido(request, detalle_id):
    """
    Elimina un producto de un pedido
    """
    try:
        motivo = request.data.get('motivo', 'Sin motivo especificado')

        # Obtener detalle
        detalle = get_object_or_404(DetallePedido, id=detalle_id)
        pedido = detalle.pedido

        # Verificar que no esté pagado
        if pedido.estado_pago == 'pagado':
            return Response({
                'success': False,
                'error': 'No se puede modificar un pedido ya pagado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar que el pedido tenga más de un producto
        if pedido.detalles.count() <= 1:
            return Response({
                'success': False,
                'error': 'No se puede eliminar el único producto del pedido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Guardar información antes de eliminar
        producto_nombre = detalle.producto.nombre
        cantidad_eliminada = detalle.cantidad
        subtotal_eliminado = detalle.subtotal

        detalles_anteriores = list(pedido.detalles.all().values('producto__nombre', 'cantidad'))

        # Eliminar detalle
        detalle.delete()

        # Recalcular total
        pedido.total = pedido.detalles.aggregate(Sum('subtotal'))['subtotal__sum'] or 0
        pedido.total_final = calcular_total_con_descuento_propina(pedido)
        pedido.modificado = True
        pedido.save()

        detalles_nuevos = list(pedido.detalles.all().values('producto__nombre', 'cantidad'))

        # Crear historial
        crear_historial_modificacion(
            pedido=pedido,
            usuario=request.user,
            tipo_cambio='eliminar_producto',
            detalle_anterior={'productos': detalles_anteriores, 'total': float(pedido.total + subtotal_eliminado)},
            detalle_nuevo={'productos': detalles_nuevos, 'total': float(pedido.total)},
            motivo=f'Eliminado: {cantidad_eliminada}x {producto_nombre}. Motivo: {motivo}'
        )

        return Response({
            'success': True,
            'message': f'Producto eliminado: {cantidad_eliminada}x {producto_nombre}',
            'pedido': {
                'id': pedido.id,
                'total': float(pedido.total),
                'total_final': float(pedido.total_final)
            }
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_eliminar_producto_pedido: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def api_modificar_cantidad_producto(request, detalle_id):
    """
    Modifica la cantidad de un producto en el pedido
    """
    try:
        nueva_cantidad = request.data.get('cantidad')

        if not nueva_cantidad or int(nueva_cantidad) < 1:
            return Response({
                'success': False,
                'error': 'Cantidad inválida'
            }, status=status.HTTP_400_BAD_REQUEST)

        nueva_cantidad = int(nueva_cantidad)

        # Obtener detalle
        detalle = get_object_or_404(DetallePedido, id=detalle_id)
        pedido = detalle.pedido
        producto = detalle.producto

        # Verificar que no esté pagado
        if pedido.estado_pago == 'pagado':
            return Response({
                'success': False,
                'error': 'No se puede modificar un pedido ya pagado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar stock
        if producto.requiere_inventario and producto.stock_actual < nueva_cantidad:
            return Response({
                'success': False,
                'error': f'Stock insuficiente. Disponible: {producto.stock_actual}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Guardar estado anterior
        cantidad_anterior = detalle.cantidad
        detalles_anteriores = list(pedido.detalles.all().values('producto__nombre', 'cantidad'))

        # Modificar cantidad
        detalle.cantidad = nueva_cantidad
        detalle.subtotal = producto.precio * nueva_cantidad
        detalle.save()

        # Recalcular total
        pedido.total = pedido.detalles.aggregate(Sum('subtotal'))['subtotal__sum'] or 0
        pedido.total_final = calcular_total_con_descuento_propina(pedido)
        pedido.modificado = True
        pedido.save()

        detalles_nuevos = list(pedido.detalles.all().values('producto__nombre', 'cantidad'))

        # Crear historial
        crear_historial_modificacion(
            pedido=pedido,
            usuario=request.user,
            tipo_cambio='modificar_cantidad',
            detalle_anterior={'productos': detalles_anteriores},
            detalle_nuevo={'productos': detalles_nuevos},
            motivo=f'{producto.nombre}: {cantidad_anterior} → {nueva_cantidad}'
        )

        return Response({
            'success': True,
            'message': f'Cantidad actualizada: {producto.nombre}',
            'detalle': {
                'id': detalle.id,
                'cantidad_anterior': cantidad_anterior,
                'cantidad_nueva': nueva_cantidad,
                'subtotal': float(detalle.subtotal)
            },
            'pedido': {
                'id': pedido.id,
                'total': float(pedido.total),
                'total_final': float(pedido.total_final)
            }
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_modificar_cantidad_producto: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def api_reasignar_pedido_mesa(request):
    """
    Reasigna un pedido a otra mesa
    """
    try:
        pedido_id = request.data.get('pedido_id')
        nueva_mesa_id = request.data.get('mesa_id')
        motivo = request.data.get('motivo', 'Cambio de mesa solicitado')

        # Validaciones
        if not all([pedido_id, nueva_mesa_id]):
            return Response({
                'success': False,
                'error': 'Faltan datos requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener pedido y mesa
        pedido = get_object_or_404(Pedido, id=pedido_id)
        nueva_mesa = get_object_or_404(Mesa, id=nueva_mesa_id)

        # Verificar que no esté pagado
        if pedido.estado_pago == 'pagado':
            return Response({
                'success': False,
                'error': 'No se puede reasignar un pedido ya pagado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Guardar mesa anterior
        mesa_anterior = pedido.mesa
        mesa_anterior_numero = mesa_anterior.numero if mesa_anterior else 'Sin mesa'

        # Liberar mesa anterior
        if mesa_anterior:
            mesa_anterior.estado = 'disponible'
            mesa_anterior.save()

        # Asignar nueva mesa
        pedido.mesa = nueva_mesa
        pedido.reasignado = True
        pedido.save()

        # Ocupar nueva mesa
        nueva_mesa.estado = 'ocupada'
        nueva_mesa.save()

        # Crear historial
        crear_historial_modificacion(
            pedido=pedido,
            usuario=request.user,
            tipo_cambio='reasignar_mesa',
            detalle_anterior={'mesa': mesa_anterior_numero},
            detalle_nuevo={'mesa': nueva_mesa.numero},
            motivo=motivo
        )

        return Response({
            'success': True,
            'message': f'Pedido reasignado de Mesa {mesa_anterior_numero} a Mesa {nueva_mesa.numero}',
            'pedido': {
                'id': pedido.id,
                'mesa_anterior': mesa_anterior_numero,
                'mesa_nueva': nueva_mesa.numero
            }
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_reasignar_pedido_mesa: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ══════════════════════════════════════════════
# 💼 APIS DE CAJA (TURNOS)
# ══════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def api_abrir_caja(request):
    """
    Abre un turno de caja
    """
    try:
        efectivo_inicial = request.data.get('efectivo_inicial', 0)
        turno = request.data.get('turno', 'completo')

        # Verificar si ya hay un turno abierto
        turno_existente = CierreCaja.objects.filter(
            cajero=request.user,
            estado='abierto',
            fecha=date.today()
        ).first()

        if turno_existente:
            return Response({
                'success': False,
                'error': 'Ya tienes un turno abierto'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Crear cierre de caja
        cierre = CierreCaja.objects.create(
            cajero=request.user,
            fecha=date.today(),
            turno=turno,
            estado='abierto',
            efectivo_inicial=Decimal(str(efectivo_inicial)),
            efectivo_esperado=Decimal(str(efectivo_inicial))
        )

        print(f"[DEBUG] Caja abierta - Cajero: {request.user}, Turno: {turno}")

        return Response({
            'success': True,
            'message': f'Caja abierta - Turno {turno}',
            'turno': {
                'id': cierre.id,
                'cajero': request.user.username,
                'fecha': cierre.fecha.isoformat(),
                'turno': cierre.turno,
                'efectivo_inicial': float(cierre.efectivo_inicial),
                'hora_apertura': cierre.hora_apertura.isoformat()
            }
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_abrir_caja: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def api_cerrar_caja(request):
    """
    Cierra el turno de caja y hace el cuadre
    """
    try:
        efectivo_real = request.data.get('efectivo_real')
        observaciones = request.data.get('observaciones', '')

        if efectivo_real is None:
            return Response({
                'success': False,
                'error': 'Debe especificar el efectivo real contado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener turno abierto
        turno = CierreCaja.objects.filter(
            cajero=request.user,
            estado='abierto',
            fecha=date.today()
        ).first()

        if not turno:
            return Response({
                'success': False,
                'error': 'No tienes un turno abierto para cerrar'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener transacciones del turno
        transacciones = Transaccion.objects.filter(
            cajero=request.user,
            fecha_hora__date=date.today(),
            fecha_hora__gte=turno.hora_apertura,
            estado='procesado'
        )

        # Calcular totales por método
        totales = calcular_totales_caja(transacciones)

        # Obtener pedidos del turno
        pedidos = Pedido.objects.filter(
            cajero_responsable=request.user,
            fecha_pago__date=date.today(),
            fecha_pago__gte=turno.hora_apertura
        )

        # Calcular descuentos y propinas
        total_descuentos = pedidos.aggregate(Sum('descuento'))['descuento__sum'] or Decimal('0')
        total_propinas = pedidos.aggregate(Sum('propina'))['propina__sum'] or Decimal('0')

        # Actualizar datos del cierre
        turno.total_efectivo = totales['efectivo']
        turno.total_tarjeta = totales['tarjeta']
        turno.total_qr = totales['qr']
        turno.total_movil = totales['movil']
        turno.total_ventas = totales['total']
        turno.efectivo_esperado = turno.efectivo_inicial + totales['efectivo']
        turno.total_descuentos = total_descuentos
        turno.total_propinas = total_propinas
        turno.numero_pedidos = pedidos.count()

        # Cerrar caja
        turno.cerrar_caja(
            efectivo_real=Decimal(str(efectivo_real)),
            observaciones=observaciones
        )

        print(f"[DEBUG] Caja cerrada - Cajero: {request.user}, Diferencia: {turno.diferencia}")

        return Response({
            'success': True,
            'message': 'Caja cerrada exitosamente',
            'cierre': {
                'id': turno.id,
                'fecha': turno.fecha.isoformat(),
                'turno': turno.turno,
                'efectivo_inicial': float(turno.efectivo_inicial),
                'efectivo_esperado': float(turno.efectivo_esperado),
                'efectivo_real': float(turno.efectivo_real),
                'diferencia': float(turno.diferencia),
                'total_ventas': float(turno.total_ventas),
                'total_efectivo': float(turno.total_efectivo),
                'total_tarjeta': float(turno.total_tarjeta),
                'total_qr': float(turno.total_qr),
                'total_movil': float(turno.total_movil),
                'total_descuentos': float(turno.total_descuentos),
                'total_propinas': float(turno.total_propinas),
                'numero_pedidos': turno.numero_pedidos,
                'hora_cierre': turno.hora_cierre.isoformat()
            }
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_cerrar_caja: {str(e)}")
        import traceback
        traceback.print_exc()

        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ══════════════════════════════════════════════
# 📊 APIS DE CONSULTA
# ══════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_mapa_mesas(request):
    """
    Obtiene el estado de todas las mesas para el mapa digital
    ✅ ACTUALIZADO: Muestra TODOS los productos de cada mesa
    """
    try:
        # Obtener TODAS las mesas
        mesas = Mesa.objects.all().order_by('numero')

        mesas_data = []
        for mesa in mesas:
            # Buscar pedidos activos
            pedidos_activos = Pedido.objects.filter(
                mesa=mesa,
                estado_pago='pendiente'
            ).exclude(estado='cancelado').prefetch_related('detalles__producto')

            total_pendiente = sum(
                p.total_final if p.total_final > 0 else p.total
                for p in pedidos_activos
            )

            # Obtener TODOS los productos de esta mesa
            productos_mesa = []
            for pedido in pedidos_activos:
                for detalle in pedido.detalles.all():
                    productos_mesa.append({
                        'nombre': detalle.producto.nombre,
                        'cantidad': detalle.cantidad,
                        'precio_unitario': float(detalle.precio_unitario),
                        'subtotal': float(detalle.subtotal)
                    })

            # Determinar color según estado
            if pedidos_activos.exists():
                if mesa.estado == 'pagando':
                    color = 'azul'  # En proceso de pago
                else:
                    color = 'rojo'  # Ocupada
            elif mesa.estado == 'reservada':
                color = 'amarillo'  # Reservada
            else:
                color = 'verde'  # Disponible

            mesas_data.append({
                'id': mesa.id,
                'numero': mesa.numero,
                'estado': mesa.estado,
                'capacidad': mesa.capacidad,
                'color': color,
                'pedidos_activos': pedidos_activos.count(),
                'total_pendiente': float(total_pendiente),
                'productos': productos_mesa,  # ✅ NUEVO: Lista de todos los productos
                'posicion_x': mesa.posicion_x,
                'posicion_y': mesa.posicion_y
            })

        return Response({
            'success': True,
            'mesas': mesas_data
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_mapa_mesas: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_estadisticas_dia(request):
    """
    Obtiene estadísticas de caja del día
    """
    try:
        fecha_str = request.GET.get('fecha')

        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                fecha = date.today()
        else:
            fecha = date.today()

        estadisticas = obtener_estadisticas_caja_dia(fecha)

        return Response({
            'success': True,
            'estadisticas': estadisticas
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_estadisticas_dia: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_alertas_stock(request):
    """
    Obtiene las alertas de stock activas
    """
    try:
        alertas = AlertaStock.objects.filter(
            estado='activa'
        ).select_related('producto').order_by('-fecha_creacion')

        alertas_data = []
        for alerta in alertas:
            alertas_data.append({
                'id': alerta.id,
                'producto': alerta.producto.nombre,
                'producto_id': alerta.producto.id,
                'tipo_alerta': alerta.tipo_alerta,
                'stock_actual': alerta.stock_actual,
                'stock_minimo': alerta.producto.stock_minimo,
                'fecha_creacion': alerta.fecha_creacion.isoformat()
            })

        return Response({
            'success': True,
            'alertas': alertas_data,
            'total_alertas': len(alertas_data)
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_alertas_stock: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def api_resolver_alerta_stock(request, alerta_id):
    """
    Marca una alerta de stock como resuelta
    """
    try:
        observaciones = request.data.get('observaciones', '')

        alerta = get_object_or_404(AlertaStock, id=alerta_id)
        alerta.resolver(request.user, observaciones)

        return Response({
            'success': True,
            'message': f'Alerta resuelta: {alerta.producto.nombre}'
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_resolver_alerta_stock: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_historial_modificaciones(request, pedido_id):
    """
    Obtiene el historial de modificaciones de un pedido
    """
    try:
        historial = HistorialModificacion.objects.filter(
            pedido_id=pedido_id
        ).select_related('usuario').order_by('-fecha_hora')

        historial_data = []
        for registro in historial:
            historial_data.append({
                'id': registro.id,
                'tipo_cambio': registro.tipo_cambio,
                'usuario': registro.usuario.username if registro.usuario else 'Sistema',
                'fecha_hora': registro.fecha_hora.isoformat(),
                'motivo': registro.motivo or '',
                'detalle_anterior': registro.detalle_anterior,
                'detalle_nuevo': registro.detalle_nuevo
            })

        return Response({
            'success': True,
            'historial': historial_data
        })

    except Exception as e:
        print(f"[ERROR] Error en api_historial_modificaciones: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_lista_empleados(request):
    """
    Obtiene la lista de empleados (meseros, cocineros, cajeros) con sus QR codes
    """
    try:
        from app.usuarios.models import Usuario
        from django.conf import settings
        from pathlib import Path

        print(f"[API] Obteniendo lista de empleados - Usuario: {request.user}")

        # Obtener empleados activos (meseros, cocineros, cajeros)
        empleados = Usuario.objects.filter(
            rol__in=['mesero', 'cocinero', 'cajero'],
            activo=True
        ).order_by('rol', 'username')

        empleados_data = []
        for empleado in empleados:
            # Ruta al QR code del empleado
            qr_filename = f"{empleado.rol}-{empleado.username}-qr.png"
            qr_path = Path(settings.MEDIA_ROOT) / 'qr_empleados' / qr_filename

            # URL del QR code
            qr_url = None
            if qr_path.exists():
                qr_url = f"{settings.MEDIA_URL}qr_empleados/{qr_filename}"

            # Token QR
            qr_token = empleado.qr_token if empleado.qr_token else None

            empleados_data.append({
                'id': empleado.id,
                'username': empleado.username,
                'nombre_completo': f"{empleado.first_name} {empleado.last_name}".strip() or empleado.username,
                'rol': empleado.rol,
                'rol_display': empleado.get_rol_display(),
                'qr_url': qr_url,
                'qr_token': str(qr_token) if qr_token else None,
                'activo': empleado.activo,
                'areas_permitidas': empleado.areas_permitidas
            })

        return Response({
            'success': True,
            'empleados': empleados_data,
            'total': len(empleados_data)
        })

    except Exception as e:
        print(f"[ERROR] Error en api_lista_empleados: {str(e)}")
        import traceback
        traceback.print_exc()

        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ══════════════════════════════════════════════
# 🎯 API TABLERO KANBAN
# ══════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_pedidos_kanban(request):
    """
    Obtiene pedidos agrupados por estado para el tablero Kanban
    Estados: pedido, preparando, listo, entregado
    """
    try:
        # Mapeo de estados del modelo a estados del Kanban
        mapeo_estados = {
            'pendiente': 'pedido',
            'en preparacion': 'preparando',
            'listo': 'listo',
            'entregado': 'entregado'
        }

        # Inicializar respuesta
        resultado = {
            'pedido': [],
            'preparando': [],
            'listo': [],
            'entregado': []
        }

        # Obtener pedidos pendientes de pago (exceptuando cancelados)
        pedidos = Pedido.objects.filter(
            estado_pago='pendiente'
        ).exclude(
            estado='cancelado'
        ).select_related('mesa', 'mesero_comanda').prefetch_related(
            'detalles__producto__categoria'
        ).order_by('fecha')

        for pedido in pedidos:
            # Mapear estado del modelo al estado del Kanban
            estado_modelo = pedido.estado
            estado_kanban = mapeo_estados.get(estado_modelo, 'pedido')

            # Preparar productos agrupados por categoría
            productos = []
            for detalle in pedido.detalles.all():
                categoria_nombre = detalle.producto.categoria.nombre if detalle.producto.categoria else 'Sin Categoría'
                productos.append({
                    'nombre': detalle.producto.nombre,
                    'cantidad': detalle.cantidad,
                    'categoria': categoria_nombre
                })

            # Obtener información del mesero
            mesero_nombre = "N/A"
            if pedido.mesero_comanda:
                mesero_nombre = f"{pedido.mesero_comanda.first_name} {pedido.mesero_comanda.last_name}".strip()
                if not mesero_nombre:
                    mesero_nombre = pedido.mesero_comanda.username

            # Calcular total
            total = pedido.total_final if pedido.total_final > 0 else pedido.total

            # Agregar pedido al estado correspondiente
            resultado[estado_kanban].append({
                'id': pedido.id,
                'mesa': pedido.mesa.numero if pedido.mesa else 'N/A',
                'mesa_id': pedido.mesa.id if pedido.mesa else None,
                'productos': productos,
                'total': float(total),
                'mesero': mesero_nombre,
                'hora': pedido.fecha.strftime('%H:%M'),
                'estado_actual': estado_modelo
            })

        return Response({
            'success': True,
            'pedido': resultado['pedido'],
            'preparando': resultado['preparando'],
            'listo': resultado['listo'],
            'entregado': resultado['entregado']
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_pedidos_kanban: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_cambiar_estado_pedido(request, pedido_id):
    """
    Cambia el estado de un pedido en el tablero Kanban
    """
    try:
        pedido = get_object_or_404(Pedido, id=pedido_id)

        nuevo_estado_kanban = request.data.get('estado')

        # Mapeo inverso: de estado Kanban a estado del modelo
        mapeo_kanban_a_modelo = {
            'pedido': 'pendiente',
            'preparando': 'en preparacion',
            'listo': 'listo',
            'entregado': 'entregado'
        }

        nuevo_estado_modelo = mapeo_kanban_a_modelo.get(nuevo_estado_kanban)

        if not nuevo_estado_modelo:
            return Response({
                'success': False,
                'error': 'Estado inválido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Actualizar estado
        pedido.estado = nuevo_estado_modelo
        pedido.save()

        return Response({
            'success': True,
            'message': f'Estado cambiado a {nuevo_estado_kanban}'
        })

    except Exception as e:
        print(f"[DEBUG] Error en api_cambiar_estado_pedido: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
