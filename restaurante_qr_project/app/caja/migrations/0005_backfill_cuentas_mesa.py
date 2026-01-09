# Generated manually for SGIR v40.4.0 - Backfill de CuentaMesa
# Este script migra datos existentes sin perder información

from django.db import migrations
from django.utils import timezone
from decimal import Decimal


def backfill_cuentas_mesa(apps, schema_editor):
    """
    Crea CuentaMesa para todos los pedidos existentes que no tienen cuenta.
    Agrupa pedidos por mesa y fecha para crear cuentas coherentes.
    """
    Pedido = apps.get_model('pedidos', 'Pedido')
    CuentaMesa = apps.get_model('caja', 'CuentaMesa')
    Transaccion = apps.get_model('caja', 'Transaccion')
    Usuario = apps.get_model('usuarios', 'Usuario')

    # Verificar si el campo 'cuenta' existe antes de intentar usarlo
    # (puede haber sido eliminado en migraciones posteriores)
    if not hasattr(Pedido, '_meta') or 'cuenta' not in [f.name for f in Pedido._meta.get_fields()]:
        print("\n[SKIP] Campo 'cuenta' no existe en Pedido - migracion ya no aplicable")
        return

    # Obtener un usuario por defecto para cuentas sin mesero
    usuario_sistema = Usuario.objects.filter(is_superuser=True).first()

    # Procesar pedidos sin cuenta
    pedidos_sin_cuenta = Pedido.objects.filter(cuenta__isnull=True).select_related('mesa', 'mesero_comanda')

    print(f"\n[MIGRACION] Migrando {pedidos_sin_cuenta.count()} pedidos a CuentaMesa...")

    # Agrupar pedidos por mesa y fecha (mismo día)
    pedidos_por_mesa = {}
    for pedido in pedidos_sin_cuenta:
        fecha_key = pedido.fecha.date() if hasattr(pedido.fecha, 'date') else pedido.fecha
        mesa_key = (pedido.mesa.id, fecha_key)

        if mesa_key not in pedidos_por_mesa:
            pedidos_por_mesa[mesa_key] = []
        pedidos_por_mesa[mesa_key].append(pedido)

    cuentas_creadas = 0
    pedidos_migrados = 0

    # Agrupar todas las cuentas por mesa (sin importar fecha) para manejar constraint único
    cuentas_por_mesa_id = {}
    for (mesa_id, fecha), pedidos_grupo in pedidos_por_mesa.items():
        if mesa_id not in cuentas_por_mesa_id:
            cuentas_por_mesa_id[mesa_id] = []
        cuentas_por_mesa_id[mesa_id].append((fecha, pedidos_grupo))

    # Crear CuentaMesa para cada mesa
    for mesa_id, grupos_fecha in cuentas_por_mesa_id.items():
        # Ordenar por fecha (más reciente primero)
        grupos_fecha.sort(key=lambda x: x[0], reverse=True)

        # Procesar grupos: el más reciente puede ser abierta, los demás cerrada/con_deuda
        for idx, (fecha, pedidos_grupo) in enumerate(grupos_fecha):
            es_mas_reciente = (idx == 0)

            # Determinar estado de la cuenta basándose en los pedidos
            todos_pagados = all(p.estado_pago == 'pagado' for p in pedidos_grupo)
            hay_activos = any(p.estado in ['pendiente', 'en preparacion', 'listo', 'entregado'] for p in pedidos_grupo)

            if hay_activos and es_mas_reciente:
                # Solo el grupo más reciente puede estar abierto
                estado_cuenta = 'abierta'
            elif todos_pagados:
                estado_cuenta = 'cerrada'
            else:
                estado_cuenta = 'con_deuda'

            # Calcular totales
            total_acumulado = sum(
                Decimal(str(p.total_final if p.total_final > 0 else p.total))
                for p in pedidos_grupo
                if p.estado != 'cancelado'
            )

            monto_pagado = sum(
                Decimal(str(p.monto_pagado or 0))
                for p in pedidos_grupo
                if p.estado != 'cancelado'
            )

            # Determinar quién abrió (primer mesero o usuario sistema)
            abierta_por = pedidos_grupo[0].mesero_comanda or usuario_sistema

            # Determinar quién cerró (cajero del último pedido pagado)
            cerrada_por = None
            fecha_cierre = None
            if estado_cuenta in ['cerrada', 'con_deuda']:
                pedidos_pagados = [p for p in pedidos_grupo if p.cajero_responsable]
                if pedidos_pagados:
                    ultimo_pagado = max(pedidos_pagados, key=lambda p: p.fecha_pago or p.fecha)
                    cerrada_por = ultimo_pagado.cajero_responsable
                    fecha_cierre = ultimo_pagado.fecha_pago

            # Crear CuentaMesa
            cuenta = CuentaMesa.objects.create(
                mesa_id=mesa_id,
                estado=estado_cuenta,
                total_acumulado=total_acumulado,
                monto_pagado=monto_pagado,
                fecha_apertura=pedidos_grupo[0].fecha,
                fecha_cierre=fecha_cierre,
                abierta_por=abierta_por,
                cerrada_por=cerrada_por,
                deuda_autorizada=(estado_cuenta == 'con_deuda'),
                observaciones=f"Cuenta migrada automaticamente de {len(pedidos_grupo)} pedido(s) legacy"
            )

            # Asociar todos los pedidos a esta cuenta
            for pedido in pedidos_grupo:
                pedido.cuenta = cuenta
                pedido.save(update_fields=['cuenta'])
                pedidos_migrados += 1

            cuentas_creadas += 1
            print(f"  [OK] Cuenta Mesa {cuenta.mesa.numero} - {estado_cuenta} - {len(pedidos_grupo)} pedidos - Bs/ {total_acumulado}")

    print(f"\n[OK] Migracion completada:")
    print(f"   - {cuentas_creadas} cuentas creadas")
    print(f"   - {pedidos_migrados} pedidos migrados")

    # Procesar transacciones sin cuenta
    # Verificar si el campo 'cuenta' existe en Transaccion
    if 'cuenta' not in [f.name for f in Transaccion._meta.get_fields()]:
        print("\n[SKIP] Campo 'cuenta' no existe en Transaccion - saltando migracion de transacciones")
        return

    transacciones_sin_cuenta = Transaccion.objects.filter(cuenta__isnull=True).select_related('pedido')

    print(f"\n[MIGRACION] Migrando {transacciones_sin_cuenta.count()} transacciones a CuentaMesa...")

    transacciones_migradas = 0
    for transaccion in transacciones_sin_cuenta:
        if transaccion.pedido and transaccion.pedido.cuenta:
            # Asociar a la cuenta del pedido
            transaccion.cuenta = transaccion.pedido.cuenta
            transaccion.save(update_fields=['cuenta'])
            transacciones_migradas += 1
        else:
            # Transacción huérfana (no debería pasar, pero por si acaso)
            print(f"  [ADVERTENCIA] Transaccion #{transaccion.id} sin pedido o sin cuenta - requiere revision manual")

    print(f"[OK] {transacciones_migradas} transacciones migradas\n")


def reverse_backfill(apps, schema_editor):
    """
    Reversa: Limpia las asociaciones de cuenta (deja null)
    """
    Pedido = apps.get_model('pedidos', 'Pedido')
    Transaccion = apps.get_model('caja', 'Transaccion')

    Pedido.objects.all().update(cuenta=None)
    Transaccion.objects.all().update(cuenta=None)


class Migration(migrations.Migration):

    dependencies = [
        ('caja', '0004_add_cuenta_mesa_model'),
        ('pedidos', '0008_add_cuenta_mesa_model'),
    ]

    operations = [
        migrations.RunPython(backfill_cuentas_mesa, reverse_backfill),
    ]
