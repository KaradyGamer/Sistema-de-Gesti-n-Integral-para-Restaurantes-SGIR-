"""
Utilidades para gestión de pedidos con control de inventario
"""
from django.db import transaction
from .models import Pedido, DetallePedido
from app.productos.models import Producto
import logging

logger = logging.getLogger('app.pedidos')


@transaction.atomic
def modificar_pedido_con_stock(pedido_id, productos_nuevos, usuario=None):
    """
    Modifica un pedido existente restaurando stock de productos eliminados
    y descontando stock de productos nuevos/aumentados.

    Args:
        pedido_id: ID del pedido a modificar
        productos_nuevos: Dict con formato {producto_id: cantidad_nueva}
        usuario: Usuario que realiza la modificación (opcional)

    Returns:
        dict: {'success': True/False, 'mensaje': str, 'pedido': Pedido}

    Raises:
        ValueError: Si hay stock insuficiente o el pedido no existe
    """
    try:
        # 1. Obtener el pedido
        pedido = Pedido.objects.get(id=pedido_id)

        # Guardar estado anterior para el historial
        detalle_anterior = {
            'total': float(pedido.total),
            'productos': [
                {
                    'producto_id': d.producto.id,
                    'nombre': d.producto.nombre,
                    'cantidad': d.cantidad,
                    'precio_unitario': float(d.precio_unitario)
                }
                for d in pedido.detalles.all()
            ]
        }

        # 2. Validar que el pedido se pueda modificar
        if pedido.estado in ['pagado', 'cancelado']:
            raise ValueError(f"No se puede modificar un pedido en estado '{pedido.get_estado_display()}'")

        # 3. Obtener detalles actuales
        detalles_actuales = {
            d.producto.id: d
            for d in pedido.detalles.select_related('producto').all()
        }

        logger.info(f"Modificando pedido #{pedido_id}. Detalles actuales: {list(detalles_actuales.keys())}")
        logger.info(f"Productos nuevos: {productos_nuevos}")

        # 4. Restaurar stock de productos eliminados o reducidos
        for producto_id, detalle_actual in detalles_actuales.items():
            if producto_id not in productos_nuevos:
                # Producto eliminado completamente - restaurar todo el stock
                cantidad_a_restaurar = detalle_actual.cantidad - detalle_actual.cantidad_pagada

                if cantidad_a_restaurar > 0:
                    detalle_actual.producto.agregar_stock(cantidad_a_restaurar)
                    logger.info(
                        f"  [OK] Producto '{detalle_actual.producto.nombre}' eliminado - "
                        f"Stock restaurado: {cantidad_a_restaurar} unidades"
                    )

                # Eliminar el detalle
                detalle_actual.delete()

            elif productos_nuevos[producto_id] < detalle_actual.cantidad:
                # Cantidad reducida - restaurar diferencia (solo lo no pagado)
                diferencia = detalle_actual.cantidad - productos_nuevos[producto_id]
                cantidad_a_restaurar = min(diferencia, detalle_actual.cantidad_pendiente)

                if cantidad_a_restaurar > 0:
                    detalle_actual.producto.agregar_stock(cantidad_a_restaurar)
                    logger.info(
                        f"  [OK] Cantidad reducida de '{detalle_actual.producto.nombre}' - "
                        f"Stock restaurado: {cantidad_a_restaurar} unidades"
                    )

        # 5. Descontar stock de productos nuevos o aumentados
        errores_stock = []

        for producto_id, cantidad_nueva in productos_nuevos.items():
            try:
                producto = Producto.objects.get(id=producto_id, activo=True)
            except Producto.DoesNotExist:
                raise ValueError(f"Producto con ID {producto_id} no encontrado o no está disponible")

            if producto_id not in detalles_actuales:
                # Producto NUEVO - descontar todo el stock
                if not producto.descontar_stock(cantidad_nueva):
                    errores_stock.append(
                        f"{producto.nombre}: Stock insuficiente "
                        f"(Disponible: {producto.stock_actual}, Solicitado: {cantidad_nueva})"
                    )
                else:
                    logger.info(
                        f"  [OK] Producto nuevo '{producto.nombre}' agregado - "
                        f"Stock descontado: {cantidad_nueva} unidades"
                    )

                    # Crear nuevo detalle
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=producto,
                        cantidad=cantidad_nueva,
                        precio_unitario=producto.precio,
                        subtotal=producto.precio * cantidad_nueva
                    )

            elif cantidad_nueva > detalles_actuales[producto_id].cantidad:
                # Cantidad AUMENTADA - descontar solo la diferencia
                diferencia = cantidad_nueva - detalles_actuales[producto_id].cantidad

                if not producto.descontar_stock(diferencia):
                    errores_stock.append(
                        f"{producto.nombre}: Stock insuficiente para aumentar cantidad "
                        f"(Disponible: {producto.stock_actual}, Adicional: {diferencia})"
                    )
                else:
                    logger.info(
                        f"  [OK] Cantidad aumentada de '{producto.nombre}' - "
                        f"Stock descontado: {diferencia} unidades"
                    )

                    # Actualizar detalle existente
                    detalle = detalles_actuales[producto_id]
                    detalle.cantidad = cantidad_nueva
                    detalle.subtotal = detalle.precio_unitario * cantidad_nueva
                    detalle.save()

            else:
                # Cantidad sin cambios - no hacer nada con el stock
                logger.info(f"  [INFO] Producto '{producto.nombre}' sin cambios de cantidad")

        # 6. Si hubo errores de stock, hacer rollback
        if errores_stock:
            raise ValueError("Errores de stock:\n" + "\n".join(errores_stock))

        # 7. Recalcular total del pedido
        pedido.total = pedido.calcular_total()
        pedido.modificado = True  # Marcar como modificado
        pedido.save()

        # 8. Guardar historial de modificación
        if usuario:
            try:
                from app.caja.models import HistorialModificacion

                detalle_nuevo = {
                    'total': float(pedido.total),
                    'productos': [
                        {
                            'producto_id': d.producto.id,
                            'nombre': d.producto.nombre,
                            'cantidad': d.cantidad,
                            'precio_unitario': float(d.precio_unitario)
                        }
                        for d in pedido.detalles.all()
                    ]
                }

                HistorialModificacion.objects.create(
                    pedido=pedido,
                    usuario=usuario,
                    tipo_cambio='modificar_cantidad',
                    detalle_anterior=detalle_anterior,
                    detalle_nuevo=detalle_nuevo,
                    motivo='Modificación de productos desde panel de caja'
                )
                logger.info(f"Historial de modificación registrado para pedido #{pedido_id}")
            except Exception as e:
                logger.warning(f"No se pudo guardar historial de modificación: {e}")

        logger.info(f"[OK] Pedido #{pedido_id} modificado exitosamente. Nuevo total: Bs/ {pedido.total}")

        return {
            'success': True,
            'mensaje': f'Pedido #{pedido_id} modificado exitosamente',
            'pedido': pedido,
            'nuevo_total': float(pedido.total)
        }

    except Pedido.DoesNotExist:
        logger.error(f"Pedido #{pedido_id} no encontrado")
        raise ValueError(f"Pedido #{pedido_id} no encontrado")

    except Producto.DoesNotExist as e:
        logger.error(f"Producto no encontrado al modificar pedido: {e}")
        raise ValueError(f"Producto no encontrado: {e}")

    except Exception as e:
        logger.exception(f"Error modificando pedido #{pedido_id}: {str(e)}")
        raise


@transaction.atomic
def eliminar_producto_de_pedido(pedido_id, producto_id):
    """
    Elimina un producto específico de un pedido y restaura su stock.
    Solo permite eliminar productos que NO han sido pagados.

    Args:
        pedido_id: ID del pedido
        producto_id: ID del producto a eliminar

    Returns:
        dict: {'success': True/False, 'mensaje': str}
    """
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        detalle = DetallePedido.objects.get(pedido=pedido, producto_id=producto_id)

        # Verificar que no esté completamente pagado
        if detalle.esta_pagado_completo:
            raise ValueError(
                f"No se puede eliminar '{detalle.producto.nombre}' porque ya fue pagado completamente"
            )

        # Restaurar stock solo de la cantidad NO pagada
        cantidad_a_restaurar = detalle.cantidad_pendiente

        if cantidad_a_restaurar > 0:
            detalle.producto.agregar_stock(cantidad_a_restaurar)
            logger.info(
                f"Stock restaurado: {cantidad_a_restaurar} unidades de '{detalle.producto.nombre}'"
            )

        # Si tiene cantidad pagada, solo reducir cantidad total
        if detalle.cantidad_pagada > 0:
            detalle.cantidad = detalle.cantidad_pagada
            detalle.subtotal = detalle.precio_unitario * detalle.cantidad_pagada
            detalle.save()

            mensaje = (
                f"Cantidad pendiente de '{detalle.producto.nombre}' eliminada. "
                f"Cantidad pagada ({detalle.cantidad_pagada}) se mantiene en el pedido."
            )
        else:
            # Si no tiene nada pagado, eliminar completamente
            producto_nombre = detalle.producto.nombre
            detalle.delete()
            mensaje = f"Producto '{producto_nombre}' eliminado completamente del pedido"

        # Recalcular total
        pedido.total = pedido.calcular_total()
        pedido.modificado = True
        pedido.save()

        logger.info(f"[OK] {mensaje}. Nuevo total: Bs/ {pedido.total}")

        return {
            'success': True,
            'mensaje': mensaje,
            'nuevo_total': float(pedido.total)
        }

    except Pedido.DoesNotExist:
        raise ValueError(f"Pedido #{pedido_id} no encontrado")
    except DetallePedido.DoesNotExist:
        raise ValueError(f"Producto no encontrado en el pedido #{pedido_id}")
    except Exception as e:
        logger.exception(f"Error eliminando producto de pedido: {str(e)}")
        raise


def obtener_resumen_modificacion(pedido_id):
    """
    Obtiene un resumen del pedido indicando qué productos pueden ser modificados.

    Args:
        pedido_id: ID del pedido

    Returns:
        dict: Información detallada del pedido y sus productos
    """
    try:
        pedido = Pedido.objects.select_related('mesa').prefetch_related(
            'detalles__producto'
        ).get(id=pedido_id)

        productos = []
        for detalle in pedido.detalles.all():
            productos.append({
                'producto_id': detalle.producto.id,
                'nombre': detalle.producto.nombre,
                'cantidad_total': detalle.cantidad,
                'cantidad_pagada': detalle.cantidad_pagada,
                'cantidad_pendiente': detalle.cantidad_pendiente,
                'precio_unitario': float(detalle.precio_unitario),
                'subtotal_total': float(detalle.subtotal),
                'subtotal_pendiente': float(detalle.precio_unitario * detalle.cantidad_pendiente),
                'puede_modificar': not detalle.esta_pagado_completo,
                'stock_disponible': detalle.producto.stock_actual if detalle.producto.requiere_inventario else None
            })

        return {
            'pedido_id': pedido.id,
            'mesa': pedido.mesa.numero if pedido.mesa else None,
            'estado': pedido.estado,
            'total': float(pedido.total),
            'puede_modificar': pedido.estado not in ['pagado', 'cancelado'],
            'productos': productos,
            'productos_pendientes': pedido.productos_pendientes_pago()
        }

    except Pedido.DoesNotExist:
        raise ValueError(f"Pedido #{pedido_id} no encontrado")
