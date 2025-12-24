"""
SGIR v40.5.0 - Services de Producción
Lógica de negocio atómica para recetario y producción
"""
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import logging

from .models import Receta, RecetaItem, Produccion, ProduccionDetalle
from app.productos.models import Producto
from app.inventario.models import Insumo, MovimientoInsumo

logger = logging.getLogger('app.produccion')


@transaction.atomic
def crear_receta(producto, items, usuario):
    """
    Crea una receta nueva para un producto fabricable.

    Args:
        producto: Producto instance
        items: Lista de dicts [{'insumo_id': int, 'cantidad': Decimal, 'merma_pct': Decimal}]
        usuario: Usuario que crea la receta

    Returns:
        Receta instance

    Raises:
        ValidationError
    """
    # Validar producto fabricable
    if not getattr(producto, 'es_fabricable', False):
        raise ValidationError('El producto debe tener es_fabricable=True')

    # Validar items no vacío
    if not items or len(items) == 0:
        raise ValidationError('La receta debe tener al menos un insumo')

    # Validar insumos sin duplicados
    insumo_ids = [item['insumo_id'] for item in items]
    if len(insumo_ids) != len(set(insumo_ids)):
        raise ValidationError('No se permiten insumos duplicados en la receta')

    # Verificar si ya existe receta
    if hasattr(producto, 'receta'):
        raise ValidationError('Ya existe una receta para este producto. Use actualizar_receta()')

    # Crear receta
    receta = Receta.objects.create(
        producto=producto,
        activo=True,
        version=1,
        creado_por=usuario
    )

    # Crear items
    for item_data in items:
        insumo = Insumo.objects.get(id=item_data['insumo_id'])
        RecetaItem.objects.create(
            receta=receta,
            insumo=insumo,
            cantidad=Decimal(str(item_data['cantidad'])),
            merma_pct=Decimal(str(item_data.get('merma_pct', 0)))
        )

    logger.info(f"Receta creada: {producto.nombre} con {len(items)} insumos por {usuario.username}")
    return receta


@transaction.atomic
def actualizar_receta(producto, items, usuario):
    """
    Actualiza receta existente incrementando versión.

    Args:
        producto: Producto instance
        items: Lista de dicts [{'insumo_id': int, 'cantidad': Decimal, 'merma_pct': Decimal}]
        usuario: Usuario

    Returns:
        Receta instance actualizada
    """
    if not hasattr(producto, 'receta'):
        raise ValidationError('No existe receta para este producto. Use crear_receta()')

    receta = producto.receta

    # Incrementar versión
    receta.version += 1
    receta.creado_por = usuario
    receta.save()

    # Eliminar items antiguos
    receta.items.all().delete()

    # Crear items nuevos
    for item_data in items:
        insumo = Insumo.objects.get(id=item_data['insumo_id'])
        RecetaItem.objects.create(
            receta=receta,
            insumo=insumo,
            cantidad=Decimal(str(item_data['cantidad'])),
            merma_pct=Decimal(str(item_data.get('merma_pct', 0)))
        )

    logger.info(f"Receta actualizada: {producto.nombre} v{receta.version} por {usuario.username}")
    return receta


@transaction.atomic
def registrar_produccion(producto, cantidad, lote, notas, usuario):
    """
    Registra intención de producir (estado='registrada').
    No modifica stock todavía.

    Args:
        producto: Producto instance
        cantidad: Decimal, cantidad a producir
        lote: str opcional
        notas: str opcional
        usuario: Usuario

    Returns:
        Produccion instance
    """
    # Validar producto fabricable
    if not getattr(producto, 'es_fabricable', False):
        raise ValidationError('Solo productos fabricables pueden ser producidos')

    # Validar receta existe y está activa
    if not hasattr(producto, 'receta'):
        raise ValidationError(f'El producto {producto.nombre} no tiene receta configurada')

    receta = producto.receta
    if not receta.activo:
        raise ValidationError(f'La receta del producto {producto.nombre} está inactiva')

    # Crear producción en estado registrada
    produccion = Produccion.objects.create(
        producto=producto,
        receta=receta,
        cantidad_producida=Decimal(str(cantidad)),
        lote=lote or '',
        estado='registrada',
        notas=notas or '',
        creado_por=usuario
    )

    logger.info(f"Producción registrada: {producto.nombre} x{cantidad} (ID: {produccion.id}) por {usuario.username}")
    return produccion


@transaction.atomic
def aplicar_produccion(produccion_id, usuario):
    """
    Aplica producción: descuenta insumos y aumenta stock del producto.
    ATOMICO con FAIL-FAST: valida TODO antes de modificar NADA.

    Args:
        produccion_id: int
        usuario: Usuario que aplica

    Returns:
        Produccion instance aplicada

    Raises:
        ValidationError si falta stock o estado inválido
    """
    # Obtener producción
    produccion = Produccion.objects.select_for_update().get(id=produccion_id)

    # Validar estado
    if produccion.estado != 'registrada':
        raise ValidationError(f'Solo se pueden aplicar producciones en estado "registrada". Estado actual: {produccion.get_estado_display()}')

    # Validar receta activa
    if not produccion.receta.activo:
        raise ValidationError('La receta utilizada está inactiva')

    # Calcular consumos requeridos
    consumos = []
    for item in produccion.receta.items.all():
        cantidad_total = item.cantidad_con_merma * produccion.cantidad_producida
        consumos.append({
            'insumo': item.insumo,
            'cantidad': cantidad_total,
            'receta_item': item
        })

    # FAIL-FAST: Validar stock de TODOS los insumos ANTES de descontar
    insumos_a_bloquear = [c['insumo'] for c in consumos]
    insumos_bloqueados = list(Insumo.objects.select_for_update().filter(
        id__in=[ins.id for ins in insumos_a_bloquear]
    ))

    faltantes = []
    for consumo in consumos:
        insumo = next(ins for ins in insumos_bloqueados if ins.id == consumo['insumo'].id)
        if insumo.stock_actual < consumo['cantidad']:
            faltantes.append({
                'insumo': insumo.nombre,
                'requerido': float(consumo['cantidad']),
                'disponible': float(insumo.stock_actual),
                'unidad': insumo.unidad
            })

    if faltantes:
        mensaje = 'Stock insuficiente para aplicar producción:\n'
        for f in faltantes:
            mensaje += f"  - {f['insumo']}: necesita {f['requerido']:.3f} {f['unidad']}, disponible {f['disponible']:.3f}\n"
        raise ValidationError(mensaje)

    # Descontar insumos y crear snapshots
    for consumo in consumos:
        insumo = next(ins for ins in insumos_bloqueados if ins.id == consumo['insumo'].id)
        cantidad_descontar = consumo['cantidad']

        # Snapshot ANTES
        stock_antes = insumo.stock_actual

        # Descontar con update condicional (por seguridad adicional)
        updated = Insumo.objects.filter(
            id=insumo.id,
            stock_actual__gte=cantidad_descontar
        ).update(stock_actual=F('stock_actual') - cantidad_descontar)

        if updated == 0:
            raise ValidationError(f'No se pudo descontar {insumo.nombre}: stock insuficiente al momento de aplicar')

        # Refresh para obtener stock actualizado
        insumo.refresh_from_db()
        stock_despues = insumo.stock_actual

        # Crear MovimientoInsumo
        MovimientoInsumo.objects.create(
            insumo=insumo,
            tipo='salida',
            cantidad=int(cantidad_descontar) if insumo.unidad == 'unidad' else int(cantidad_descontar),
            motivo=f'Producción #{produccion.id} - {produccion.producto.nombre} x{produccion.cantidad_producida}',
            creado_por=usuario
        )

        # Crear ProduccionDetalle (snapshot)
        ProduccionDetalle.objects.create(
            produccion=produccion,
            insumo=insumo,
            cantidad_calculada=cantidad_descontar,
            unidad_snapshot=insumo.unidad,
            stock_insumo_antes=stock_antes,
            stock_insumo_despues=stock_despues
        )

    # Incrementar stock del producto terminado SIEMPRE
    Producto.objects.filter(id=produccion.producto.id).update(
        stock_actual=F('stock_actual') + int(produccion.cantidad_producida)
    )

    # Marcar producción como aplicada
    produccion.estado = 'aplicada'
    produccion.aplicado_por = usuario
    produccion.fecha_aplicacion = timezone.now()
    produccion.save()

    logger.info(f"Producción aplicada: {produccion.producto.nombre} x{produccion.cantidad_producida} (ID: {produccion.id}) por {usuario.username}")
    return produccion


@transaction.atomic
def anular_produccion(produccion_id, motivo, usuario, pin_secundario):
    """
    Anula producción aplicada: revierte insumos y decrementa stock del producto.
    REQUIERE PIN SECUNDARIO VÁLIDO.

    Args:
        produccion_id: int
        motivo: str
        usuario: Usuario
        pin_secundario: str (NO se guarda, solo se valida)

    Returns:
        Produccion instance anulada

    Raises:
        ValidationError
    """
    # Validar PIN secundario
    if not usuario.validar_pin_secundario(pin_secundario):
        raise ValidationError('PIN secundario inválido')

    # Obtener producción
    produccion = Produccion.objects.select_for_update().get(id=produccion_id)

    # Validar estado
    if produccion.estado != 'aplicada':
        raise ValidationError(f'Solo se pueden anular producciones en estado "aplicada". Estado actual: {produccion.get_estado_display()}')

    # Revertir: devolver insumos según snapshots
    for detalle in produccion.detalles.all():
        insumo = Insumo.objects.select_for_update().get(id=detalle.insumo.id)

        # Devolver cantidad exacta según snapshot
        cantidad_devolver = detalle.cantidad_calculada

        Insumo.objects.filter(id=insumo.id).update(
            stock_actual=F('stock_actual') + cantidad_devolver
        )

        # Registrar movimiento de ajuste/entrada
        MovimientoInsumo.objects.create(
            insumo=insumo,
            tipo='ajuste',
            cantidad=int(cantidad_devolver) if insumo.unidad == 'unidad' else int(cantidad_devolver),
            motivo=f'ANULACIÓN Producción #{produccion.id} - {motivo}',
            creado_por=usuario
        )

    # Decrementar stock del producto terminado
    producto_id = produccion.producto.id
    cantidad_decrementar = int(produccion.cantidad_producida)

    # Validar que no quede negativo
    producto_actual = Producto.objects.get(id=producto_id)
    if producto_actual.stock_actual < cantidad_decrementar:
        raise ValidationError(
            f'No se puede anular: el producto {producto_actual.nombre} solo tiene {producto_actual.stock_actual} unidades, '
            f'pero la producción agregó {cantidad_decrementar}'
        )

    Producto.objects.filter(id=producto_id).update(
        stock_actual=F('stock_actual') - cantidad_decrementar
    )

    # Marcar producción como anulada
    produccion.estado = 'anulada'
    produccion.motivo_anulacion = motivo
    produccion.anulado_por = usuario
    produccion.fecha_anulacion = timezone.now()
    produccion.pin_secundario_validado = True  # NO guardamos el PIN, solo que fue validado
    produccion.save()

    logger.critical(
        f"PRODUCCIÓN ANULADA: {produccion.producto.nombre} x{produccion.cantidad_producida} "
        f"(ID: {produccion.id}) por {usuario.username}. Motivo: {motivo}"
    )

    return produccion