from django.utils import timezone
from django.db.models import Sum, Count
from decimal import Decimal
from datetime import datetime, date
import uuid


def generar_numero_factura():
    """
    Genera un número de factura único
    Formato: FACT-YYYYMMDD-XXXXX
    """
    fecha_str = timezone.now().strftime('%Y%m%d')
    uuid_str = str(uuid.uuid4())[:8].upper()
    return f"FACT-{fecha_str}-{uuid_str}"


def calcular_cambio(total, monto_recibido):
    """
    Calcula el cambio a devolver
    """
    cambio = Decimal(str(monto_recibido)) - Decimal(str(total))
    return max(cambio, Decimal('0'))


def validar_stock_pedido(pedido):
    """
    Valida que todos los productos del pedido tengan stock disponible
    Retorna: (es_valido, productos_sin_stock)
    """
    productos_sin_stock = []

    for detalle in pedido.detalles.all():
        producto = detalle.producto

        # Solo validar si el producto requiere inventario
        if producto.requiere_inventario:
            if producto.stock_actual < detalle.cantidad:
                productos_sin_stock.append({
                    'producto': producto.nombre,
                    'solicitado': detalle.cantidad,
                    'disponible': producto.stock_actual
                })

    es_valido = len(productos_sin_stock) == 0
    return es_valido, productos_sin_stock


def descontar_stock_pedido(pedido):
    """
    Descuenta el stock de todos los productos del pedido
    """
    for detalle in pedido.detalles.all():
        producto = detalle.producto
        if producto.requiere_inventario:
            producto.descontar_stock(detalle.cantidad)


def calcular_totales_caja(transacciones):
    """
    Calcula los totales por método de pago de una lista de transacciones
    """
    totales = {
        'efectivo': Decimal('0'),
        'tarjeta': Decimal('0'),
        'qr': Decimal('0'),
        'movil': Decimal('0'),
        'total': Decimal('0'),
    }

    for transaccion in transacciones:
        # Si es pago simple
        if transaccion.metodo_pago in totales:
            totales[transaccion.metodo_pago] += transaccion.monto_total

        # Si es pago mixto, sumar los detalles
        for detalle in transaccion.detalles_pago.all():
            if detalle.metodo_pago in totales:
                totales[detalle.metodo_pago] += detalle.monto

        totales['total'] += transaccion.monto_total

    return totales


def crear_historial_modificacion(pedido, usuario, tipo_cambio, detalle_anterior, detalle_nuevo, motivo=None):
    """
    Crea un registro en el historial de modificaciones
    """
    from .models import HistorialModificacion

    historial = HistorialModificacion.objects.create(
        pedido=pedido,
        usuario=usuario,
        tipo_cambio=tipo_cambio,
        detalle_anterior=detalle_anterior,
        detalle_nuevo=detalle_nuevo,
        motivo=motivo
    )

    return historial


def verificar_alertas_stock():
    """
    Verifica y crea alertas para productos con stock bajo o agotado
    """
    from app.productos.models import Producto
    from .models import AlertaStock

    productos = Producto.objects.filter(requiere_inventario=True)
    alertas_creadas = []

    for producto in productos:
        # Verificar si ya existe una alerta activa
        alerta_existente = AlertaStock.objects.filter(
            producto=producto,
            estado='activa'
        ).exists()

        if alerta_existente:
            continue

        # Crear alerta si está agotado
        if producto.agotado:
            alerta = AlertaStock.objects.create(
                producto=producto,
                tipo_alerta='agotado',
                stock_actual=producto.stock_actual
            )
            alertas_creadas.append(alerta)

        # Crear alerta si el stock está bajo
        elif producto.stock_bajo:
            alerta = AlertaStock.objects.create(
                producto=producto,
                tipo_alerta='stock_bajo',
                stock_actual=producto.stock_actual
            )
            alertas_creadas.append(alerta)

    return alertas_creadas


def obtener_pedidos_pendientes_pago():
    """
    Obtiene todos los pedidos que están listos pero pendientes de pago
    """
    from app.pedidos.models import Pedido

    return Pedido.objects.filter(
        estado='entregado',
        estado_pago='pendiente'
    ).select_related('mesa', 'cajero_responsable').prefetch_related('detalles__producto')


def calcular_total_con_descuento_propina(pedido):
    """
    Calcula el total final de un pedido con descuento y propina
    """
    subtotal = pedido.total
    descuento = pedido.descuento if pedido.descuento else Decimal('0')
    propina = pedido.propina if pedido.propina else Decimal('0')

    total_con_descuento = subtotal - descuento
    total_final = total_con_descuento + propina

    return max(total_final, Decimal('0'))  # No puede ser negativo


def aplicar_descuento_porcentaje(pedido, porcentaje, usuario, motivo=None):
    """
    Aplica un descuento por porcentaje a un pedido
    """
    if porcentaje < 0 or porcentaje > 100:
        raise ValueError("El porcentaje debe estar entre 0 y 100")

    # Calcular el descuento
    descuento_decimal = Decimal(str(porcentaje)) / Decimal('100')
    monto_descuento = pedido.total * descuento_decimal

    # Guardar estado anterior
    detalle_anterior = {
        'total': float(pedido.total),
        'descuento': float(pedido.descuento),
        'descuento_porcentaje': float(pedido.descuento_porcentaje),
        'total_final': float(pedido.total_final)
    }

    # Aplicar descuento
    pedido.descuento = monto_descuento
    pedido.descuento_porcentaje = Decimal(str(porcentaje))
    pedido.total_final = calcular_total_con_descuento_propina(pedido)
    pedido.modificado = True
    pedido.save()

    # Guardar estado nuevo
    detalle_nuevo = {
        'total': float(pedido.total),
        'descuento': float(pedido.descuento),
        'descuento_porcentaje': float(pedido.descuento_porcentaje),
        'total_final': float(pedido.total_final)
    }

    # Crear historial
    crear_historial_modificacion(
        pedido=pedido,
        usuario=usuario,
        tipo_cambio='aplicar_descuento',
        detalle_anterior=detalle_anterior,
        detalle_nuevo=detalle_nuevo,
        motivo=motivo
    )

    return pedido


def aplicar_propina(pedido, monto_propina, usuario):
    """
    Aplica propina a un pedido
    """
    # Guardar estado anterior
    detalle_anterior = {
        'propina': float(pedido.propina),
        'total_final': float(pedido.total_final)
    }

    # Aplicar propina
    pedido.propina = Decimal(str(monto_propina))
    pedido.total_final = calcular_total_con_descuento_propina(pedido)
    pedido.modificado = True
    pedido.save()

    # Guardar estado nuevo
    detalle_nuevo = {
        'propina': float(pedido.propina),
        'total_final': float(pedido.total_final)
    }

    # Crear historial
    crear_historial_modificacion(
        pedido=pedido,
        usuario=usuario,
        tipo_cambio='agregar_propina',
        detalle_anterior=detalle_anterior,
        detalle_nuevo=detalle_nuevo
    )

    return pedido


def obtener_estadisticas_caja_dia(fecha=None):
    """
    Obtiene estadísticas de caja para un día específico
    """
    from .models import Transaccion
    from app.pedidos.models import Pedido

    if fecha is None:
        fecha = timezone.now().date()

    # Transacciones del día
    transacciones = Transaccion.objects.filter(
        fecha_hora__date=fecha,
        estado='procesado'
    )

    # Pedidos del día
    pedidos = Pedido.objects.filter(
        fecha__date=fecha
    )

    # Calcular totales
    totales = calcular_totales_caja(transacciones)

    # Estadísticas de pedidos
    total_pedidos = pedidos.count()
    pedidos_pagados = pedidos.filter(estado_pago='pagado').count()
    pedidos_pendientes = pedidos.filter(estado_pago='pendiente').count()

    # Descuentos y propinas
    total_descuentos = pedidos.aggregate(Sum('descuento'))['descuento__sum'] or Decimal('0')
    total_propinas = pedidos.aggregate(Sum('propina'))['propina__sum'] or Decimal('0')

    return {
        'fecha': fecha,
        'totales': totales,
        'total_pedidos': total_pedidos,
        'pedidos_pagados': pedidos_pagados,
        'pedidos_pendientes': pedidos_pendientes,
        'total_descuentos': float(total_descuentos),
        'total_propinas': float(total_propinas),
        'promedio_por_pedido': float(totales['total'] / total_pedidos) if total_pedidos > 0 else 0,
    }