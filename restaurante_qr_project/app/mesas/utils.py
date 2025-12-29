"""
Utilidades para gestión de mesas
"""
import logging
from django.db import transaction
from .models import Mesa

logger = logging.getLogger('app.mesas')


@transaction.atomic  # ✅ NUEVO: Garantiza atomicidad y permite select_for_update
def asignar_mesa_automatica(numero_personas, fecha_reserva=None, hora_reserva=None):
    """
    Asigna automáticamente una mesa o combinación de mesas según el número de personas.
    Usa select_for_update() para prevenir condiciones de carrera.

    Args:
        numero_personas (int): Número de personas que necesitan mesa
        fecha_reserva (date, optional): Fecha de la reserva para verificar disponibilidad
        hora_reserva (time, optional): Hora de la reserva

    Returns:
        dict: {
            'success': bool,
            'mesa': Mesa or None,
            'mesas_combinadas': list of Mesa or None,
            'capacidad_total': int,
            'mensaje': str
        }
    """
    logger.info(f"Buscando mesa para {numero_personas} personas")

    # 1. Buscar mesa individual con capacidad suficiente
    # ✅ NUEVO: Usar select_for_update() para evitar condiciones de carrera
    mesa_individual = Mesa.objects.select_for_update().filter(
        disponible=True,
        capacidad__gte=numero_personas,
        estado='disponible',
        es_combinada=False
    ).order_by('capacidad').first()  # Ordenar por capacidad para asignar la más pequeña que sirva

    if mesa_individual:
        logger.info(f"Mesa {mesa_individual.numero} asignada (capacidad: {mesa_individual.capacidad})")
        return {
            'success': True,
            'mesa': mesa_individual,
            'mesas_combinadas': None,
            'capacidad_total': mesa_individual.capacidad,
            'mensaje': f'Mesa {mesa_individual.numero} asignada (capacidad: {mesa_individual.capacidad} personas)'
        }

    # 2. Si no hay mesa individual, buscar combinación de mesas
    logger.info("No hay mesa individual suficiente, buscando combinación de mesas")
    # ✅ NUEVO: Usar select_for_update() para bloquear todas las mesas candidatas
    mesas_disponibles = Mesa.objects.select_for_update().filter(
        disponible=True,
        estado='disponible',
        es_combinada=False
    ).order_by('numero')

    # Intentar combinar 2 mesas
    for i, mesa1 in enumerate(mesas_disponibles):
        for mesa2 in mesas_disponibles[i+1:]:
            capacidad_total = mesa1.capacidad + mesa2.capacidad
            if capacidad_total >= numero_personas:
                logger.info(f"Combinación encontrada: Mesa {mesa1.numero} + Mesa {mesa2.numero} (capacidad: {capacidad_total})")
                return {
                    'success': True,
                    'mesa': mesa1,  # Mesa principal
                    'mesas_combinadas': [mesa1, mesa2],
                    'capacidad_total': capacidad_total,
                    'mensaje': f'Mesas {mesa1.numero}+{mesa2.numero} combinadas (capacidad: {capacidad_total} personas)'
                }

    # Intentar combinar 3 mesas (para grupos muy grandes)
    for i, mesa1 in enumerate(mesas_disponibles):
        for j, mesa2 in enumerate(mesas_disponibles[i+1:], start=i+1):
            for mesa3 in mesas_disponibles[j+1:]:
                capacidad_total = mesa1.capacidad + mesa2.capacidad + mesa3.capacidad
                if capacidad_total >= numero_personas:
                    logger.info(f"Combinación de 3 mesas encontrada: {mesa1.numero}+{mesa2.numero}+{mesa3.numero}")
                    return {
                        'success': True,
                        'mesa': mesa1,
                        'mesas_combinadas': [mesa1, mesa2, mesa3],
                        'capacidad_total': capacidad_total,
                        'mensaje': f'Mesas {mesa1.numero}+{mesa2.numero}+{mesa3.numero} combinadas (capacidad: {capacidad_total} personas)'
                    }

    # 3. No hay mesas disponibles
    logger.warning(f"No hay mesas disponibles para {numero_personas} personas")
    return {
        'success': False,
        'mesa': None,
        'mesas_combinadas': None,
        'capacidad_total': 0,
        'mensaje': f'No hay mesas disponibles para {numero_personas} personas. Por favor, contacte al restaurante.'
    }


def combinar_mesas(mesas_list, estado='reservada'):
    """
    Combina físicamente las mesas en el sistema.

    Args:
        mesas_list (list): Lista de objetos Mesa a combinar
        estado (str): Estado a asignar ('reservada' u 'ocupada')

    Returns:
        Mesa: Mesa principal con las demás combinadas
    """
    if not mesas_list or len(mesas_list) < 2:
        logger.error("Se necesitan al menos 2 mesas para combinar")
        return None

    # Mesa principal (la primera)
    mesa_principal = mesas_list[0]

    # Números de todas las mesas
    numeros_mesas = [str(m.numero) for m in mesas_list]
    mesas_combinadas_str = ','.join(numeros_mesas)

    # Capacidad total
    capacidad_total = sum(m.capacidad for m in mesas_list)

    # Actualizar todas las mesas
    for mesa in mesas_list:
        mesa.es_combinada = True
        mesa.mesas_combinadas = mesas_combinadas_str
        mesa.capacidad_combinada = capacidad_total
        mesa.estado = estado
        mesa.save()

    logger.info(f"Mesas {mesas_combinadas_str} combinadas. Capacidad total: {capacidad_total}")

    return mesa_principal


def separar_mesas(mesa):
    """
    Separa mesas que estaban combinadas y las vuelve a estado disponible.

    Args:
        mesa (Mesa): Cualquier mesa del grupo combinado
    """
    if not mesa.es_combinada:
        logger.info(f"Mesa {mesa.numero} no está combinada")
        return

    # Obtener todas las mesas del grupo
    numeros_mesas = mesa.mesas_combinadas.split(',')
    mesas_grupo = Mesa.objects.filter(numero__in=numeros_mesas)

    # Separar cada una
    for m in mesas_grupo:
        m.es_combinada = False
        m.mesas_combinadas = None
        m.capacidad_combinada = 0
        m.estado = 'disponible'
        m.save()

    logger.info(f"Mesas {mesa.mesas_combinadas} separadas y liberadas")


def obtener_info_mesa_completa(mesa):
    """
    Obtiene información completa de una mesa incluyendo si está combinada.

    Args:
        mesa (Mesa): Mesa a consultar

    Returns:
        dict: Información completa de la mesa
    """
    info = {
        'numero': mesa.numero,
        'estado': mesa.estado,
        'capacidad': mesa.capacidad,
        'disponible': mesa.disponible,
        'es_combinada': mesa.es_combinada,
    }

    if mesa.es_combinada and mesa.mesas_combinadas:
        info['mesas_combinadas'] = mesa.mesas_combinadas
        info['capacidad_total'] = mesa.capacidad_combinada
        info['display'] = f"Mesa {mesa.mesas_combinadas.replace(',', '+')} (combinada)"
    else:
        info['mesas_combinadas'] = None
        info['capacidad_total'] = mesa.capacidad
        info['display'] = f"Mesa {mesa.numero}"

    return info


def liberar_mesa(mesa):
    """
    Libera una mesa o grupo de mesas combinadas después del pago.

    Args:
        mesa (Mesa): Mesa a liberar
    """
    if mesa.es_combinada:
        # Si está combinada, liberar todo el grupo
        separar_mesas(mesa)
        logger.info(f"Grupo de mesas {mesa.mesas_combinadas} liberado")
    else:
        # Mesa individual
        mesa.estado = 'disponible'
        mesa.save()
        logger.info(f"Mesa {mesa.numero} liberada")
