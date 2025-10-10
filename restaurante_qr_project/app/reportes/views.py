from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
import json
import csv
from io import StringIO

from .models import ReporteVentas
from app.pedidos.models import Pedido, DetallePedido
from app.productos.models import Producto

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
        print(f"📊 DASHBOARD DEBUG:")
        print(f"📊 Hoy: {hoy}")
        print(f"📊 Inicio semana: {inicio_semana}")
        print(f"📊 Fin semana: {fin_semana}")
        
        # ✅ SOLUCIONADO: Incluir TODOS los pedidos (no solo entregados)
        estados_ventas = ['pendiente', 'en preparacion', 'listo', 'entregado']
        
        # Debug: Contar todos los pedidos
        total_pedidos_bd = Pedido.objects.all().count()
        pedidos_semana = Pedido.objects.filter(
            fecha__date__gte=inicio_semana,
            fecha__date__lte=fin_semana
        )
        
        print(f"📊 Total pedidos en BD: {total_pedidos_bd}")
        print(f"📊 Pedidos en semana actual: {pedidos_semana.count()}")
        
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
            
            print(f"📊 {dias_semana[i]} ({fecha}): {pedidos_dia} pedidos, Bs/ {ventas_dia}")
            
            ventas_por_dia.append({
                'dia': dias_semana[i],
                'fecha': fecha.strftime('%d/%m'),
                'ventas': float(ventas_dia),
                'pedidos': pedidos_dia
            })
        
        total_semana = sum(dia['ventas'] for dia in ventas_por_dia)
        total_pedidos_semana = sum(dia['pedidos'] for dia in ventas_por_dia)
        
        print(f"📊 RESULTADO FINAL:")
        print(f"📊 Total ventas semana: Bs/ {total_semana}")
        print(f"📊 Total pedidos semana: {total_pedidos_semana}")
        
        return JsonResponse({
            'ventas_por_dia': ventas_por_dia,
            'total_semana': total_semana,
            'total_pedidos': total_pedidos_semana
        })
        
    except Exception as e:
        print(f"❌ Error en datos_ventas_semanales: {str(e)}")
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
        
        print(f"📊 PRODUCTOS TOP - Inicio semana: {inicio_semana}")
        
        # ✅ SOLUCIONADO: Incluir todos los estados de ventas
        estados_ventas = ['pendiente', 'en preparacion', 'listo', 'entregado']
        
        productos_top = DetallePedido.objects.filter(
            pedido__fecha__date__gte=inicio_semana,
            pedido__estado__in=estados_ventas  # ✅ CAMBIADO: Todos los estados
        ).values(
            'producto__nombre'
        ).annotate(
            cantidad_vendida=Sum('cantidad'),
            ingresos=Sum('subtotal')
        ).order_by('-cantidad_vendida')[:10]
        
        print(f"📊 Productos encontrados: {productos_top.count()}")
        
        productos_data = []
        for producto in productos_top:
            print(f"📊 Producto: {producto['producto__nombre']} - Cantidad: {producto['cantidad_vendida']}")
            productos_data.append({
                'nombre': producto['producto__nombre'],
                'cantidad': producto['cantidad_vendida'],
                'ingresos': float(producto['ingresos'])
            })
        
        return JsonResponse({
            'productos_top': productos_data
        })
        
    except Exception as e:
        print(f"❌ Error en datos_productos_top: {str(e)}")
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

        # ✅ SOLUCIONADO: Incluir todos los estados de ventas
        estados_ventas = ['pendiente', 'en preparacion', 'listo', 'entregado']
        
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