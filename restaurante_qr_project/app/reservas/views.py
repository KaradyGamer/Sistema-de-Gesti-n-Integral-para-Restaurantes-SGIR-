from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Reserva
from .forms import ReservaForm
from app.mesas.models import Mesa
from app.mesas.utils import asignar_mesa_automatica, combinar_mesas
from datetime import datetime, date, timedelta
import json
import logging

logger = logging.getLogger('app.reservas')

def reservar_mesa(request):
    """Formulario principal para hacer reservas con asignación automática de mesa"""
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)  # No guardar todavía

            # ✅ NUEVO: Asignación automática de mesa según número de personas
            numero_personas = reserva.numero_personas
            resultado_asignacion = asignar_mesa_automatica(
                numero_personas=numero_personas,
                fecha_reserva=reserva.fecha_reserva,
                hora_reserva=reserva.hora_reserva
            )

            if resultado_asignacion['success']:
                # Asignar mesa principal
                reserva.mesa = resultado_asignacion['mesa']
                reserva.save()  # Guardar la reserva

                # Si hay mesas combinadas, combinarlas
                if resultado_asignacion['mesas_combinadas']:
                    combinar_mesas(resultado_asignacion['mesas_combinadas'], estado='reservada')
                    messages.info(request, resultado_asignacion['mensaje'])
                else:
                    # Mesa individual
                    reserva.mesa.estado = 'reservada'
                    reserva.mesa.save()
                    messages.info(request, resultado_asignacion['mensaje'])

                messages.success(request, f'¡Reserva confirmada para {reserva.nombre_completo}!')
                logger.info(f"Reserva creada: {reserva.nombre_completo} - Mesa {reserva.mesa.numero} - {numero_personas} personas")
                return redirect('confirmacion_reserva', reserva_id=reserva.id)
            else:
                # No hay mesas disponibles
                messages.error(request, resultado_asignacion['mensaje'])
                logger.warning(f"No hay mesas disponibles para {numero_personas} personas")
    else:
        form = ReservaForm()

    return render(request, 'reservas/reservar.html', {'form': form})

def confirmacion_reserva(request, reserva_id):
    """Página de confirmación de reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    return render(request, 'reservas/confirmacion.html', {'reserva': reserva})

def consultar_reserva(request):
    """Consultar todas las reservas por carnet"""
    reservas = []
    carnet_buscado = None
    
    if request.method == 'POST':
        carnet = request.POST.get('numero_carnet')
        if carnet:
            carnet_buscado = carnet
            try:
                # ✅ SOLUCIONADO: Filtrar solo reservas actuales/futuras
                ahora = timezone.now()
                fecha_hoy = ahora.date()
                hora_actual = ahora.time()
                
                # Buscar reservas activas que NO hayan pasado
                reservas = Reserva.objects.filter(
                    numero_carnet=carnet,
                    estado__in=['pendiente', 'confirmada', 'en_uso']
                ).filter(
                    # Fecha futura O (fecha de hoy pero hora futura)
                    models.Q(fecha_reserva__gt=fecha_hoy) |
                    models.Q(fecha_reserva=fecha_hoy, hora_reserva__gt=hora_actual)
                ).order_by('-fecha_creacion')
                
                if not reservas.exists():
                    messages.error(request, 'No se encontraron reservas activas pendientes con ese número de carnet.')
            except Exception as e:
                messages.error(request, 'Error al buscar las reservas. Inténtalo de nuevo.')
        else:
            messages.error(request, 'Por favor, ingresa tu número de carnet.')
    
    return render(request, 'reservas/consultar.html', {
        'reservas': reservas,
        'carnet_buscado': carnet_buscado
    })

def editar_reserva(request, reserva_id):
    """Editar una reserva existente"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificar que la reserva puede ser editada
    if not reserva.puede_cancelar():
        messages.error(request, 'Esta reserva ya no puede ser editada porque está muy cerca de la fecha programada.')
        return redirect('consultar_reserva')
    
    if reserva.estado not in ['pendiente', 'confirmada']:
        messages.error(request, 'Solo se pueden editar reservas pendientes o confirmadas.')
        return redirect('consultar_reserva')
    
    if request.method == 'POST':
        form = ReservaForm(request.POST, instance=reserva)
        if form.is_valid():
            reserva_actualizada = form.save()
            messages.success(request, f'¡Reserva actualizada exitosamente para {reserva_actualizada.nombre_completo}!')
            return redirect('confirmacion_reserva', reserva_id=reserva_actualizada.id)
    else:
        form = ReservaForm(instance=reserva)
    
    return render(request, 'reservas/editar.html', {
        'form': form, 
        'reserva': reserva
    })

def panel_reservas(request):
    """Panel para administrar todas las reservas"""
    fecha_hoy = date.today()
    reservas_hoy = Reserva.objects.filter(fecha_reserva=fecha_hoy).order_by('hora_reserva')
    reservas_futuras = Reserva.objects.filter(
        fecha_reserva__gt=fecha_hoy,
        estado__in=['pendiente', 'confirmada']
    ).order_by('fecha_reserva', 'hora_reserva')
    
    context = {
        'reservas_hoy': reservas_hoy,
        'reservas_futuras': reservas_futuras,
        'fecha_hoy': fecha_hoy
    }
    return render(request, 'reservas/panel.html', context)

# APIs REST
@api_view(['GET'])
@permission_classes([AllowAny])  # ✅ AGREGADO: Acceso público para mesas disponibles
def mesas_disponibles(request):
    """API para obtener mesas disponibles según fecha, hora y personas"""
    fecha = request.GET.get('fecha')
    hora = request.GET.get('hora')
    personas = request.GET.get('personas')
    
    if not all([fecha, hora, personas]):
        return Response({'error': 'Faltan parámetros'}, status=400)
    
    try:
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        hora_obj = datetime.strptime(hora, '%H:%M').time()
        personas_int = int(personas)
    except ValueError:
        return Response({'error': 'Formato de datos inválido'}, status=400)
    
    # Buscar mesas con capacidad suficiente
    mesas_adecuadas = Mesa.objects.filter(
        capacidad__gte=personas_int,
        disponible=True
    )
    
    # Filtrar mesas ya reservadas en esa fecha/hora
    reservas_existentes = Reserva.objects.filter(
        fecha_reserva=fecha_obj,
        hora_reserva=hora_obj,
        estado__in=['pendiente', 'confirmada', 'en_uso']
    ).values_list('mesa_id', flat=True)
    
    mesas_disponibles = mesas_adecuadas.exclude(id__in=reservas_existentes)
    
    mesas_data = [{
        'id': mesa.id,
        'numero': mesa.numero,
        'capacidad': mesa.capacidad
    } for mesa in mesas_disponibles]
    
    return Response({'mesas': mesas_data})

# ✅ SOLUCIONADO: Agregar permiso público para cancelar reserva
@api_view(['POST'])
@permission_classes([AllowAny])  # ✅ PERMITE ACCESO SIN AUTENTICACIÓN
def cancelar_reserva(request, reserva_id):
    """API para cancelar una reserva - ACCESO PÚBLICO"""
    try:
        reserva = Reserva.objects.get(id=reserva_id)
        
        # Verificar que la reserva puede ser cancelada
        if not reserva.puede_cancelar():
            return Response({
                'success': False,
                'error': 'Esta reserva ya no puede ser cancelada porque está muy cerca de la fecha programada.'
            }, status=400)
        
        if reserva.estado not in ['pendiente', 'confirmada']:
            return Response({
                'success': False,
                'error': 'Solo se pueden cancelar reservas pendientes o confirmadas.'
            }, status=400)
        
        reserva.estado = 'cancelada'
        reserva.save()
        
        return Response({
            'success': True,
            'message': 'Reserva cancelada exitosamente.'
        })
        
    except Reserva.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Reserva no encontrada.'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Error interno del servidor.'
        }, status=500)

@api_view(['POST'])
def cambiar_estado_reserva(request, reserva_id):
    """API para cambiar el estado de una reserva"""
    try:
        reserva = Reserva.objects.get(id=reserva_id)
        nuevo_estado = request.data.get('estado')
        
        if nuevo_estado in dict(Reserva.ESTADO_CHOICES):
            reserva.estado = nuevo_estado
            reserva.save()
            return Response({'message': 'Estado actualizado correctamente'})
        else:
            return Response({'error': 'Estado inválido'}, status=400)
    except Reserva.DoesNotExist:
        return Response({'error': 'Reserva no encontrada'}, status=404)