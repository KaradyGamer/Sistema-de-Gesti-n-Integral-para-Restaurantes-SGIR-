from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
import logging

logger = logging.getLogger('app.reportes')

from .models import ReporteVentas
from app.pedidos.models import Pedido, DetallePedido

@staff_member_required
def dashboard_reportes(request):
    """Panel principal de reportes con gráficos"""
    return render(request, 'admin/reportes/dashboard.html')

@staff_member_required
def datos_ventas_semanales(request):
    """API para obtener datos de ventas de la última semana"""
    try:
        hoy = timezone.now().date()
        
        # ✅ SOLUCIONADO: Calcular semana actual correctamente
        dias_desde_lunes = hoy.weekday()  # 0=Lunes, 6=Domingo
        inicio_semana = hoy - timedelta(days=dias_desde_lunes)
        fin_semana = inicio_semana + timedelta(days=6)
        
        # ✅ SOLUCIONADO: Debug para verificar fechas
        logger.info("📊 DASHBOARD DEBUG:")
        logger.info(f"📊 Hoy: {hoy}")
        logger.info(f"📊 Inicio semana: {inicio_semana}")
        logger.info(f"📊 Fin semana: {fin_semana}")
        
        # ✅ SOLUCIONADO: Incluir TODOS los pedidos no-cancelados (usando constantes válidas)
        from app.pedidos.models import Pedido as PedidoModel
        estados_ventas = [
            PedidoModel.ESTADO_CREADO,
            PedidoModel.ESTADO_CONFIRMADO,
            PedidoModel.ESTADO_EN_PREPARACION,
            PedidoModel.ESTADO_LISTO,
            PedidoModel.ESTADO_ENTREGADO,
            PedidoModel.ESTADO_CERRADO  # cerrado también cuenta como venta
        ]
        
        # Debug: Contar todos los pedidos
        total_pedidos_bd = Pedido.objects.all().count()
        pedidos_semana = Pedido.objects.filter(
            fecha__date__gte=inicio_semana,
            fecha__date__lte=fin_semana
        )
        
        logger.info(f"📊 Total pedidos en BD: {total_pedidos_bd}")
        logger.info(f"📊 Pedidos en semana actual: {pedidos_semana.count()}")
        
        # Datos por día de la semana
        ventas_por_dia = []
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        for i in range(7):
            fecha = inicio_semana + timedelta(days=i)
            
            # ✅ SOLUCIONADO: Incluir todos los estados de ventas
            ventas_dia = Pedido.objects.filter(
                fecha__date=fecha,
                estado__in=estados_ventas  # ✅ CAMBIADO: Todos los estados
            ).aggregate(total=Sum('total'))['total'] or 0
            
            pedidos_dia = Pedido.objects.filter(
                fecha__date=fecha,
                estado__in=estados_ventas  # ✅ CAMBIADO: Todos los estados
            ).count()
            
            logger.info(f"📊 {dias_semana[i]} ({fecha}): {pedidos_dia} pedidos, Bs/ {ventas_dia}")
            
            ventas_por_dia.append({
                'dia': dias_semana[i],
                'fecha': fecha.strftime('%d/%m'),
                'ventas': float(ventas_dia),
                'pedidos': pedidos_dia
            })
        
        total_semana = sum(dia['ventas'] for dia in ventas_por_dia)
        total_pedidos_semana = sum(dia['pedidos'] for dia in ventas_por_dia)
        
        logger.info("📊 RESULTADO FINAL:")
        logger.info(f"📊 Total ventas semana: Bs/ {total_semana}")
        logger.info(f"📊 Total pedidos semana: {total_pedidos_semana}")
        
        return JsonResponse({
            'ventas_por_dia': ventas_por_dia,
            'total_semana': total_semana,
            'total_pedidos': total_pedidos_semana
        })
        
    except Exception as e:
        logger.info(f"❌ Error en datos_ventas_semanales: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@staff_member_required
def datos_productos_top(request):
    """API para obtener los productos más vendidos"""
    try:
        hoy = timezone.now().date()
        
        # ✅ SOLUCIONADO: Usar semana actual
        dias_desde_lunes = hoy.weekday()
        inicio_semana = hoy - timedelta(days=dias_desde_lunes)
        
        logger.info(f"📊 PRODUCTOS TOP - Inicio semana: {inicio_semana}")
        
        # ✅ SOLUCIONADO: Incluir todos los estados de ventas (usando constantes válidas)
        from app.pedidos.models import Pedido as PedidoModel
        estados_ventas = [
            PedidoModel.ESTADO_CREADO,
            PedidoModel.ESTADO_CONFIRMADO,
            PedidoModel.ESTADO_EN_PREPARACION,
            PedidoModel.ESTADO_LISTO,
            PedidoModel.ESTADO_ENTREGADO,
            PedidoModel.ESTADO_CERRADO
        ]
        
        productos_top = DetallePedido.objects.filter(
            pedido__fecha__date__gte=inicio_semana,
            pedido__estado__in=estados_ventas  # ✅ CAMBIADO: Todos los estados
        ).values(
            'producto__nombre'
        ).annotate(
            cantidad_vendida=Sum('cantidad'),
            ingresos=Sum('subtotal')
        ).order_by('-cantidad_vendida')[:10]
        
        logger.info(f"📊 Productos encontrados: {productos_top.count()}")
        
        productos_data = []
        for producto in productos_top:
            logger.info(f"📊 Producto: {producto['producto__nombre']} - Cantidad: {producto['cantidad_vendida']}")
            productos_data.append({
                'nombre': producto['producto__nombre'],
                'cantidad': producto['cantidad_vendida'],
                'ingresos': float(producto['ingresos'])
            })
        
        return JsonResponse({
            'productos_top': productos_data
        })
        
    except Exception as e:
        logger.info(f"❌ Error en datos_productos_top: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

def generar_reporte_pdf(request):
    """Generar reporte básico en HTML (alternativa a PDF)"""
    try:
        # ✅ SOLUCIONADO: Generar un solo reporte semanal
        reporte = ReporteVentas.generar_reporte_semanal()
        
        hoy = timezone.now().date()
        dias_desde_lunes = hoy.weekday()
        inicio_semana = hoy - timedelta(days=dias_desde_lunes)

        # ✅ SOLUCIONADO: Incluir todos los estados de ventas (usando constantes válidas)
        from app.pedidos.models import Pedido as PedidoModel
        estados_ventas = [
            PedidoModel.ESTADO_CREADO,
            PedidoModel.ESTADO_CONFIRMADO,
            PedidoModel.ESTADO_EN_PREPARACION,
            PedidoModel.ESTADO_LISTO,
            PedidoModel.ESTADO_ENTREGADO,
            PedidoModel.ESTADO_CERRADO
        ]
        
        ventas = DetallePedido.objects.filter(
            pedido__fecha__date__gte=inicio_semana,
            pedido__estado__in=estados_ventas  # ✅ CAMBIADO: Todos los estados
        )

        resumen = ventas.values('producto__nombre').annotate(
            cantidad=Sum('cantidad'),
            total=Sum('subtotal')
        ).order_by('-cantidad')

        total_general = resumen.aggregate(Sum('total'))['total__sum'] or 0
        total_pedidos = Pedido.objects.filter(
            fecha__date__gte=inicio_semana,
            estado__in=estados_ventas  # ✅ CAMBIADO: Todos los estados
        ).count()
        
        context = {
            'inicio_semana': inicio_semana,
            'hoy': hoy,
            'resumen': resumen,
            'total_general': total_general,
            'total_pedidos': total_pedidos,
            'promedio': total_general / total_pedidos if total_pedidos > 0 else 0,
            'reporte': reporte
        }
        
        return render(request, 'admin/reportes/pdf_report.html', context)
        
    except Exception as e:
        return HttpResponse(f'Error generando reporte: {str(e)}', status=500)