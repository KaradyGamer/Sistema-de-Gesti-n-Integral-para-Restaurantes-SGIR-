from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import date, datetime, timedelta
import logging

from .models import Pedido, DetallePedido
from .serializers import PedidoSerializer
from app.mesas.models import Mesa
from app.productos.models import Producto
from app.usuarios.utils import rol_requerido
from app.usuarios.permisos import EsCocinero, EsMesero
from app.reservas.models import Reserva

from django.contrib.auth.decorators import login_required

# ✅ Configurar logger
logger = logging.getLogger('app.pedidos')

# ──────────────────────────────────────────────
# 🔓 Cliente – Plantillas públicas
# ──────────────────────────────────────────────

def formulario_cliente(request):
    return render(request, 'cliente/formulario.html')

def menu_cliente(request):
    return render(request, 'cliente/formulario.html')

def vista_exito(request):
    return render(request, 'cliente/exito.html')

def confirmacion_pedido(request):
    return render(request, 'cliente/confirmacion.html')

# ✅ FUNCIÓN CORREGIDA PARA CREAR PEDIDOS DEL CLIENTE
@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic  # ✅ Garantiza atomicidad de la transacción
def crear_pedido_cliente(request):
    """
    Crear pedido desde el cliente - VERSIÓN CORREGIDA PARA COMPATIBILIDAD
    """
    try:
        logger.info("Creando pedido del cliente")
        logger.debug(f"Datos recibidos: {request.data}")
        logger.debug(f"Método: {request.method}, Content-Type: {request.content_type}")
        
        # ✅ CORREGIDO: Obtener datos con múltiples nombres posibles
        mesa_id = (
            request.data.get('mesa_id') or 
            request.data.get('mesa') or 
            request.data.get('numero_mesa')
        )
        
        productos_data = (
            request.data.get('productos') or 
            request.data.get('detalles') or 
            []
        )
        
        forma_pago = request.data.get('forma_pago', 'efectivo')
        total_enviado = request.data.get('total', 0)

        logger.debug(f"Mesa ID: {mesa_id}, Productos: {len(productos_data)}, Forma pago: {forma_pago}, Total: {total_enviado}")

        # ✅ Validaciones básicas
        if not mesa_id:
            return Response({
                'error': 'El número de mesa es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not productos_data or len(productos_data) == 0:
            return Response({
                'error': 'Debe incluir al menos un producto en el pedido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ CORREGIDO: Buscar la mesa por número, no por ID
        try:
            # Intentar primero por número (más común)
            mesa = Mesa.objects.get(numero=mesa_id)
            logger.debug(f"Mesa encontrada por número: {mesa}")
        except Mesa.DoesNotExist:
            try:
                # Fallback: intentar por ID
                mesa = Mesa.objects.get(id=mesa_id)
                logger.debug(f"Mesa encontrada por ID: {mesa}")
            except Mesa.DoesNotExist:
                logger.warning(f"Mesa {mesa_id} no encontrada")
                return Response({
                    'error': f'Mesa {mesa_id} no encontrada'
                }, status=status.HTTP_404_NOT_FOUND)

        # ✅ Crear el pedido
        pedido = Pedido.objects.create(
            mesa=mesa,
            fecha=timezone.now(),
            forma_pago=forma_pago,
            estado='pendiente'
        )
        logger.info(f"Pedido #{pedido.id} creado para mesa {mesa.numero}")

        total_calculado = 0
        detalles_creados = []
        
        # ✅ CORREGIDO: Procesar productos con múltiples formatos
        for item in productos_data:
            # Obtener ID del producto con múltiples nombres posibles
            producto_id = (
                item.get('producto_id') or
                item.get('producto') or
                item.get('id')
            )

            cantidad = int(item.get('cantidad', 1))

            if not producto_id:
                logger.warning(f"Item sin producto ID: {item}")
                continue

            try:
                producto = Producto.objects.get(id=producto_id)
                subtotal = producto.precio * cantidad
                total_calculado += subtotal

                # Crear detalle del pedido
                detalle = DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad,
                    subtotal=subtotal
                )

                detalles_creados.append({
                    'producto': producto.nombre,
                    'cantidad': cantidad,
                    'precio_unitario': float(producto.precio),
                    'subtotal': float(subtotal)
                })

                logger.debug(f"Detalle: {cantidad}x {producto.nombre} = Bs/ {subtotal}")

            except Producto.DoesNotExist:
                logger.error(f"Producto ID {producto_id} no encontrado")
                # Continuar con los otros productos en lugar de fallar completamente
                continue

        # ✅ Verificar que se crearon detalles
        if not detalles_creados:
            pedido.delete()  # Limpiar pedido sin detalles
            return Response({
                'error': 'No se pudieron procesar los productos del pedido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Actualizar total del pedido
        pedido.total = total_calculado
        pedido.save()

        logger.info(f"Pedido #{pedido.id} completado - Mesa {mesa.numero} - Total: Bs/ {total_calculado}")

        return Response({
            'success': True,
            'mensaje': 'Pedido creado exitosamente',
            'pedido_id': pedido.id,
            'mesa': mesa.numero,
            'total': float(total_calculado),
            'detalles': detalles_creados,
            'estado': pedido.estado
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.exception(f"Error grave creando pedido: {str(e)}")

        return Response({
            'error': f'Error interno del servidor: {str(e)}',
            'debug': 'Ver consola del servidor para detalles'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ──────────────────────────────────────────────
# 👨‍🍳 Cocinero – Vistas HTML
# ──────────────────────────────────────────────

# 🔓 Login cocinero (público)
def login_cocinero(request):
    return render(request, 'login.html')

# 🔐 Panel cocinero (requiere autenticación y rol)
def panel_cocina(request):
    """Panel del cocinero - Sin decoradores Django"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para acceder al panel de cocina.')
        return redirect('/login/')
    
    return render(request, 'cocinero/panel_cocina.html', {
        'title': 'Panel del Cocinero',
        'user_role': 'cocinero',
        'user': request.user,
        'nombre_usuario': request.user.first_name or request.user.username,
    })

# ──────────────────────────────────────────────
# 🧾 Mesero – Vistas HTML protegidas MEJORADAS
# ──────────────────────────────────────────────

# 🔓 Login mesero (público)
def login_mesero(request):
    return render(request, 'login.html')

# 🔐 Panel mesero MEJORADO con pestañas y auto-actualización
def panel_mesero(request):
    """Panel mesero mejorado con pestañas de pedidos y reservas"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para acceder al panel de mesero.')
        return redirect('/login/')
    
    context = {
        'user': request.user,
        'nombre_usuario': request.user.first_name or request.user.username,
        'title': 'Panel del Mesero',
        'user_role': 'mesero'
    }
    return render(request, 'mesero/panel_mesero.html', context)

# ✅ FUNCIÓN 1 CORREGIDA: api_pedidos_mesero
@login_required
def api_pedidos_mesero(request):
    """API para obtener pedidos del mesero (listos y entregados) - DJANGO AUTH"""
    try:
        print(f"🧾 API Pedidos Mesero - Usuario: {request.user}")
        print(f"🧾 Usuario autenticado: {request.user.is_authenticated}")
        
        fecha_hoy = date.today()
        
        # ✅ SOLUCIONADO: Usar 'detalles' en lugar de 'detallepedido_set'
        pedidos_listos = Pedido.objects.filter(
            estado='listo',
            fecha__date=fecha_hoy
        ).select_related('mesa').prefetch_related('detalles__producto').order_by('-fecha')
        
        pedidos_entregados = Pedido.objects.filter(
            estado='entregado',
            fecha__date=fecha_hoy
        ).select_related('mesa').prefetch_related('detalles__producto').order_by('-fecha')
        
        print(f"🧾 Pedidos listos encontrados: {pedidos_listos.count()}")
        print(f"🧾 Pedidos entregados encontrados: {pedidos_entregados.count()}")
        
        # Serializar pedidos listos
        pedidos_listos_data = []
        for pedido in pedidos_listos:
            try:
                # ✅ SOLUCIONADO: Usar 'detalles' en lugar de 'detallepedido_set'
                productos = [detalle.producto.nombre for detalle in pedido.detalles.all()]
            except:
                productos = [f'Pedido Mesa {pedido.mesa.numero if pedido.mesa else "N/A"}']
                
            pedidos_listos_data.append({
                'id': pedido.id,
                'mesa': pedido.mesa.numero if pedido.mesa else 'Sin mesa',
                'tiempo': pedido.fecha.strftime('%H:%M'),
                'productos': productos,
                'total': f'Bs/ {pedido.total:.2f}',
                'forma_pago': pedido.forma_pago,
                'observaciones': getattr(pedido, 'observaciones', '') or ''
            })
        
        # Serializar pedidos entregados
        pedidos_entregados_data = []
        for pedido in pedidos_entregados:
            try:
                # ✅ SOLUCIONADO: Usar 'detalles' en lugar de 'detallepedido_set'
                productos = [detalle.producto.nombre for detalle in pedido.detalles.all()]
            except:
                productos = [f'Pedido Mesa {pedido.mesa.numero if pedido.mesa else "N/A"}']
                
            pedidos_entregados_data.append({
                'id': pedido.id,
                'mesa': pedido.mesa.numero if pedido.mesa else 'Sin mesa',
                'tiempo': pedido.fecha.strftime('%H:%M'),
                'productos': productos,
                'total': f'Bs/ {pedido.total:.2f}',
                'forma_pago': pedido.forma_pago
            })
        
        response_data = {
            'success': True,
            'pedidos_listos': pedidos_listos_data,
            'pedidos_entregados': pedidos_entregados_data,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Enviando {len(pedidos_listos_data)} pedidos listos y {len(pedidos_entregados_data)} entregados")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ Error en api_pedidos_mesero: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ✅ FUNCIÓN 2 CORREGIDA: api_reservas_mesero
@login_required
def api_reservas_mesero(request):
    """API para obtener reservas del día para el mesero - DJANGO AUTH"""
    try:
        print("=" * 50)
        print(f"📅 API RESERVAS MESERO - Usuario: {request.user}")
        print(f"📅 Usuario autenticado: {request.user.is_authenticated}")
        print("=" * 50)
        
        # Obtener fecha actual
        fecha_hoy = timezone.now().date()
        fecha_manana = fecha_hoy + timedelta(days=1)
        
        print(f"📅 Fecha hoy: {fecha_hoy}")
        print(f"📅 Fecha mañana: {fecha_manana}")
        
        # Obtener TODAS las reservas para debug
        todas_reservas = Reserva.objects.all()
        print(f"📊 TOTAL reservas en BD: {todas_reservas.count()}")
        
        for reserva in todas_reservas:
            print(f"  📋 Reserva #{reserva.id}: {reserva.nombre_completo} | {reserva.fecha_reserva} | {reserva.estado}")
        
        # Obtener reservas de hoy
        reservas_hoy = Reserva.objects.filter(
            fecha_reserva=fecha_hoy
        ).order_by('hora_reserva')
        
        print(f"📅 Reservas encontradas para HOY ({fecha_hoy}): {reservas_hoy.count()}")
        
        # Debug detallado de reservas de hoy
        for reserva in reservas_hoy:
            print(f"  ✅ Reserva HOY #{reserva.id}: {reserva.nombre_completo}, {reserva.hora_reserva}, Estado: {reserva.estado}")
        
        # Próximas reservas (mañana en adelante)
        reservas_proximas = Reserva.objects.filter(
            fecha_reserva__gte=fecha_manana
        ).order_by('fecha_reserva', 'hora_reserva')[:10]
        
        print(f"📅 Próximas reservas encontradas: {reservas_proximas.count()}")
        
        # Debug próximas reservas
        for reserva in reservas_proximas:
            print(f"  🔜 Reserva PRÓXIMA #{reserva.id}: {reserva.nombre_completo}, {reserva.fecha_reserva}, {reserva.hora_reserva}")
        
        # Serializar reservas de hoy
        reservas_hoy_data = []
        for reserva in reservas_hoy:
            estado_info = {
                'pendiente': {'texto': 'Pendiente', 'color': 'warning'},
                'confirmada': {'texto': 'Confirmada', 'color': 'success'}, 
                'en_uso': {'texto': 'En Uso', 'color': 'primary'},
                'completada': {'texto': 'Completada', 'color': 'secondary'},
                'cancelada': {'texto': 'Cancelada', 'color': 'danger'}
            }
            
            estado_actual = estado_info.get(reserva.estado, {'texto': reserva.estado, 'color': 'secondary'})
            
            reserva_data = {
                'id': reserva.id,
                'numero_carnet': reserva.numero_carnet,
                'nombre': reserva.nombre_completo,
                'hora': reserva.hora_reserva.strftime('%H:%M'),
                'personas': reserva.numero_personas,
                'mesa': reserva.mesa.numero if reserva.mesa else None,
                'telefono': reserva.telefono or 'No disponible',
                'email': reserva.email or 'No disponible',
                'estado': reserva.estado,
                'estado_texto': estado_actual['texto'],
                'estado_color': estado_actual['color'],
                'observaciones': reserva.observaciones or '',
                'fecha_creacion': reserva.fecha_creacion.strftime('%H:%M') if reserva.fecha_creacion else ''
            }
            
            reservas_hoy_data.append(reserva_data)
            print(f"  ✅ Serializada reserva HOY: {reserva.nombre_completo} - {reserva.estado}")
        
        # Serializar próximas reservas
        reservas_proximas_data = []
        for reserva in reservas_proximas:
            reserva_data = {
                'id': reserva.id,
                'numero_carnet': reserva.numero_carnet,
                'nombre': reserva.nombre_completo,
                'fecha': reserva.fecha_reserva.strftime('%d/%m/%Y'),
                'hora': reserva.hora_reserva.strftime('%H:%M'),
                'personas': reserva.numero_personas,
                'estado': reserva.estado,
                'telefono': reserva.telefono or 'No disponible',
                'mesa': reserva.mesa.numero if reserva.mesa else None
            }
            reservas_proximas_data.append(reserva_data)
            print(f"  ✅ Serializada reserva PRÓXIMA: {reserva.nombre_completo}")
        
        response_data = {
            'success': True,
            'reservas_hoy': reservas_hoy_data,
            'reservas_proximas': reservas_proximas_data,
            'timestamp': datetime.now().isoformat(),
            'total_hoy': len(reservas_hoy_data),
            'total_proximas': len(reservas_proximas_data),
            'debug_info': {
                'total_reservas_bd': todas_reservas.count(),
                'fecha_consultada': str(fecha_hoy),
                'usuario': str(request.user)
            }
        }
        
        print(f"📅 RESPUESTA FINAL:")
        print(f"  - Reservas HOY: {len(reservas_hoy_data)}")
        print(f"  - Reservas PRÓXIMAS: {len(reservas_proximas_data)}")
        print("=" * 50)
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ ERROR GRAVE en api_reservas_mesero: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': str(e),
            'mensaje': 'Error al obtener las reservas'
        }, status=500)

# ✅ FUNCIÓN 3 CORREGIDA: api_entregar_pedido
@login_required  
def api_entregar_pedido(request, pedido_id):
    """API para marcar un pedido como entregado - DJANGO AUTH"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        
        if pedido.estado != 'listo':
            return JsonResponse({
                'success': False,
                'error': 'Solo se pueden entregar pedidos que están listos'
            }, status=400)
        
        pedido.estado = 'entregado'
        pedido.save()
        
        print(f"✅ Pedido #{pedido_id} marcado como entregado por {request.user}")
        
        return JsonResponse({
            'success': True,
            'message': f'Pedido #{pedido_id} marcado como entregado',
            'pedido_id': pedido_id
        })
        
    except Pedido.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Pedido no encontrado'
        }, status=404)
    except Exception as e:
        print(f"❌ Error en api_entregar_pedido: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ✅ FUNCIÓN 4 CORREGIDA: api_confirmar_reserva
@login_required
def api_confirmar_reserva(request, reserva_id):
    """API para confirmar una reserva - DJANGO AUTH"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        
    try:
        reserva = Reserva.objects.get(id=reserva_id)
        
        if reserva.estado not in ['pendiente']:
            return JsonResponse({
                'success': False,
                'error': 'Solo se pueden confirmar reservas pendientes'
            }, status=400)
        
        reserva.estado = 'confirmada'
        reserva.save()
        
        print(f"✅ Reserva #{reserva_id} confirmada por {request.user}")
        
        return JsonResponse({
            'success': True,
            'message': f'Reserva #{reserva_id} confirmada',
            'reserva_id': reserva_id,
            'nuevo_estado': 'confirmada'
        })
        
    except Reserva.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Reserva no encontrada'
        }, status=404)
    except Exception as e:
        print(f"❌ Error en api_confirmar_reserva: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ✅ FUNCIÓN 5 CORREGIDA: api_cambiar_estado_reserva
@login_required
def api_cambiar_estado_reserva(request, reserva_id):
    """API para cambiar el estado de una reserva - DJANGO AUTH"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        nuevo_estado = data.get('estado')
        
        if not nuevo_estado:
            return JsonResponse({
                'success': False,
                'error': 'Estado requerido'
            }, status=400)
        
        estados_validos = ['pendiente', 'confirmada', 'en_uso', 'completada', 'cancelada']
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'success': False,
                'error': f'Estado inválido. Estados válidos: {", ".join(estados_validos)}'
            }, status=400)
        
        reserva = Reserva.objects.get(id=reserva_id)
        estado_anterior = reserva.estado
        reserva.estado = nuevo_estado
        reserva.save()
        
        print(f"✅ Reserva #{reserva_id} cambiada de '{estado_anterior}' a '{nuevo_estado}' por {request.user}")
        
        return JsonResponse({
            'success': True,
            'message': f'Reserva #{reserva_id} actualizada a {nuevo_estado}',
            'reserva_id': reserva_id,
            'estado_anterior': estado_anterior,
            'nuevo_estado': nuevo_estado
        })
        
    except Reserva.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Reserva no encontrada'
        }, status=404)
    except Exception as e:
        print(f"❌ Error en api_cambiar_estado_reserva: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ✅ FUNCIÓN 6 CORREGIDA: api_asignar_mesa_reserva
@login_required
def api_asignar_mesa_reserva(request, reserva_id):
    """API para asignar mesa a una reserva - DJANGO AUTH"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        mesa_numero = data.get('mesa_numero')
        
        if not mesa_numero:
            return JsonResponse({
                'success': False,
                'error': 'Número de mesa requerido'
            }, status=400)
        
        reserva = Reserva.objects.get(id=reserva_id)
        
        try:
            mesa = Mesa.objects.get(numero=mesa_numero)
        except Mesa.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Mesa {mesa_numero} no encontrada'
            }, status=404)
        
        mesa_anterior = reserva.mesa.numero if reserva.mesa else None
        reserva.mesa = mesa
        reserva.save()
        
        print(f"✅ Mesa {mesa_numero} asignada a reserva #{reserva_id} por {request.user}")
        
        return JsonResponse({
            'success': True,
            'message': f'Mesa {mesa_numero} asignada a la reserva',
            'reserva_id': reserva_id,
            'mesa_anterior': mesa_anterior,
            'mesa_nueva': mesa_numero
        })
        
    except Reserva.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Reserva no encontrada'
        }, status=404)
    except Exception as e:
        print(f"❌ Error en api_asignar_mesa_reserva: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ──────────────────────────────────────────────
# 🔐 APIs COCINA CORREGIDAS - DJANGO AUTH
# ──────────────────────────────────────────────

# ✅ NUEVA FUNCIÓN PARA REEMPLAZAR PedidosEnCocinaAPIView
@login_required
def pedidos_en_cocina_api(request):
    """API para obtener todos los pedidos para la cocina - DJANGO AUTH"""
    try:
        # ✅ Debug: Verificar el usuario y rol
        print(f"🔍 API Cocina - Usuario autenticado: {request.user}")
        print(f"🔍 Username: {request.user.username}")
        
        # ✅ CORREGIDO: Solo mostrar pedidos que el cocinero necesita trabajar
        # Excluir 'listo' y 'entregado' porque ya no son responsabilidad del cocinero
        pedidos = Pedido.objects.filter(
            estado__in=['pendiente', 'en preparacion']  # ✅ SOLO ESTOS ESTADOS
        ).order_by('-fecha')
        
        print(f"✅ Pedidos encontrados para cocina: {pedidos.count()}")
        
        pedidos_data = []
        for pedido in pedidos:
            print(f"📦 Procesando pedido ID: {pedido.id}, Mesa: {pedido.mesa}, Estado: {pedido.estado}")
            
            # ✅ SOLUCIONADO: Usar 'detalles' en lugar de 'detallepedido_set'
            try:
                detalles = pedido.detalles.all()  # ✅ CORREGIDO
                if detalles.exists():
                    detalles_data = []
                    for detalle in detalles:
                        detalles_data.append({
                            'cantidad': detalle.cantidad,
                            'producto': detalle.producto.nombre if detalle.producto else 'Producto',
                            'subtotal': float(detalle.subtotal)
                        })
                    print(f"  📋 Detalles encontrados: {len(detalles_data)}")
                else:
                    # Si no hay detalles, crear uno genérico
                    detalles_data = [
                        {
                            'cantidad': 1,
                            'producto': f'Pedido para mesa {pedido.mesa.numero if pedido.mesa else "N/A"}',
                            'subtotal': float(pedido.total)
                        }
                    ]
                    print(f"  📋 No hay detalles, creando genérico")
            except Exception as e:
                print(f"  ❌ Error obteniendo detalles: {str(e)}")
                # Fallback: usar datos básicos
                detalles_data = [
                    {
                        'cantidad': 1,
                        'producto': f'Producto para mesa {pedido.mesa.numero if pedido.mesa else "N/A"}',
                        'subtotal': float(pedido.total)
                    }
                ]
            
            pedidos_data.append({
                'id': pedido.id,
                'mesa': pedido.mesa.numero if pedido.mesa else 'N/A',
                'estado': pedido.estado,
                'total': float(pedido.total),
                'fecha': pedido.fecha.isoformat(),
                'detalles': detalles_data
            })
        
        print(f"✅ Enviando {len(pedidos_data)} pedidos al frontend (solo pendientes y en preparación)")
        return JsonResponse(pedidos_data, safe=False)
        
    except Exception as e:
        print(f"❌ ERROR GRAVE en pedidos_en_cocina_api: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f'Error al obtener pedidos: {str(e)}',
            'mensaje_debug': 'Ver consola del servidor para detalles'
        }, status=500)

# ✅ FUNCIÓN CORREGIDA: actualizar_estado_pedido
@login_required
def actualizar_estado_pedido(request, pedido_id):
    """Actualizar estado del pedido - DJANGO AUTH"""
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        
        print(f"🔄 Actualizando pedido {pedido_id}, usuario: {request.user}")
        print(f"🔄 Datos recibidos: {data}")
        
        # Buscar el pedido
        pedido = Pedido.objects.get(id=pedido_id)
        print(f"🔄 Pedido encontrado: {pedido}")
        
        # Obtener el nuevo estado del request
        nuevo_estado = data.get('estado')
        print(f"🔄 Nuevo estado solicitado: {nuevo_estado}")
        
        # Validar que se envió un estado
        if not nuevo_estado:
            return JsonResponse({
                'error': 'El campo "estado" es requerido'
            }, status=400)
        
        # Validar que el estado es válido
        estados_validos = ['pendiente', 'en preparacion', 'listo', 'entregado']
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'error': f'Estado inválido. Estados válidos: {", ".join(estados_validos)}'
            }, status=400)
        
        # Actualizar el estado
        estado_anterior = pedido.estado
        pedido.estado = nuevo_estado
        pedido.save()
        
        print(f"✅ Pedido {pedido_id} actualizado de '{estado_anterior}' a '{nuevo_estado}'")
        
        return JsonResponse({
            'mensaje': f'Pedido #{pedido_id} actualizado correctamente',
            'pedido_id': pedido.id,
            'estado_anterior': estado_anterior,
            'estado_nuevo': nuevo_estado
        })

    except Pedido.DoesNotExist:
        print(f"❌ Pedido {pedido_id} no encontrado")
        return JsonResponse({
            'error': f'Pedido con ID {pedido_id} no encontrado'
        }, status=404)
    
    except Exception as e:
        print(f"❌ Error al actualizar pedido {pedido_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)

# ──────────────────────────────────────────────
# 🔐 APIs RESTANTES (MANTENER ORIGINALES)
# ──────────────────────────────────────────────

# Función para obtener pedidos por mesa (para meseros)
@api_view(['GET'])
@permission_classes([IsAuthenticated])  # ✅ Temporalmente sin EsMesero
def pedidos_por_mesa(request):
    """API para que el mesero vea pedidos por mesa"""
    try:
        print(f"🧾 Mesero solicitando pedidos por mesa: {request.user}")
        
        # Obtener todas las mesas con pedidos activos
        pedidos = Pedido.objects.exclude(estado='entregado').select_related('mesa').order_by('-fecha')
        print(f"🧾 Pedidos activos encontrados: {pedidos.count()}")
        
        # Agrupar por mesa
        mesas_data = {}
        for pedido in pedidos:
            mesa_numero = pedido.mesa.numero if pedido.mesa else 'Sin mesa'
            
            if mesa_numero not in mesas_data:
                mesas_data[mesa_numero] = {
                    'numero': mesa_numero,
                    'pedidos': []
                }
            
            mesas_data[mesa_numero]['pedidos'].append({
                'id': pedido.id,
                'estado': pedido.estado,
                'total': float(pedido.total),
                'fecha': pedido.fecha.isoformat()
            })
        
        print(f"🧾 Enviando datos de {len(mesas_data)} mesas")
        return Response(list(mesas_data.values()), status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"❌ Error en pedidos_por_mesa: {str(e)}")
        return Response({
            'error': f'Error al obtener pedidos por mesa: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Función para marcar pedido como entregado (para meseros) - FUNCIÓN ORIGINAL
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])  # ✅ Temporalmente sin EsMesero
def marcar_entregado(request, pedido_id):
    """Marcar pedido como entregado"""
    try:
        print(f"📦 Marcando pedido {pedido_id} como entregado, usuario: {request.user}")
        
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.estado = 'entregado'
        pedido.save()
        
        print(f"✅ Pedido {pedido_id} marcado como entregado")
        
        return Response({
            'mensaje': f'Pedido #{pedido_id} marcado como entregado'
        }, status=status.HTTP_200_OK)
        
    except Pedido.DoesNotExist:
        print(f"❌ Pedido {pedido_id} no encontrado para marcar como entregado")
        return Response({
            'error': f'Pedido con ID {pedido_id} no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"❌ Error al marcar como entregado: {str(e)}")
        return Response({
            'error': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 🔄 CRUD completo (opcional si usas routers)
class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all().order_by('-fecha')
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]