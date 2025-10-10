from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg
from app.pedidos.models import Pedido, DetallePedido
from app.productos.models import Producto

class ReporteVentas(models.Model):
    """
    Modelo para almacenar reportes de ventas generados
    """
    TIPOS_REPORTE = [
        ('diario', 'Reporte Diario'),
        ('semanal', 'Reporte Semanal'),
        ('mensual', 'Reporte Mensual'),
        ('personalizado', 'Periodo Personalizado'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPOS_REPORTE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_pedidos = models.IntegerField(default=0)
    promedio_por_pedido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    producto_mas_vendido = models.CharField(max_length=200, blank=True)
    dia_mas_ventas = models.CharField(max_length=50, blank=True)
    observaciones = models.TextField(blank=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    archivo_excel = models.FileField(upload_to='reportes/excel/', blank=True, null=True)
    archivo_pdf = models.FileField(upload_to='reportes/pdf/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Reporte de Ventas"
        verbose_name_plural = "Reportes de Ventas"
        ordering = ['-fecha_generacion']
        # ✅ SOLUCIONADO: Evitar reportes duplicados para el mismo periodo
        unique_together = ['tipo', 'fecha_inicio', 'fecha_fin']
    
    def __str__(self):
        return f"Reporte {self.tipo} - {self.fecha_inicio} a {self.fecha_fin}"
    
    @classmethod
    def generar_reporte_semanal(cls):
        """Genera un reporte de la última semana - EVITA DUPLICADOS"""
        hoy = timezone.now().date()
        
        # ✅ SOLUCIONADO: Calcular inicio de semana correctamente
        dias_desde_lunes = hoy.weekday()  # 0=Lunes, 6=Domingo
        inicio_semana = hoy - timedelta(days=dias_desde_lunes)
        fin_semana = inicio_semana + timedelta(days=6)
        
        # ✅ SOLUCIONADO: Verificar si ya existe el reporte para esta semana
        reporte_existente = cls.objects.filter(
            tipo='semanal',
            fecha_inicio=inicio_semana,
            fecha_fin=fin_semana
        ).first()
        
        if reporte_existente:
            return reporte_existente  # Retornar el existente en lugar de crear duplicado
        
        # Calcular estadísticas
        pedidos = Pedido.objects.filter(
            fecha__date__gte=inicio_semana,
            fecha__date__lte=fin_semana,
            estado='entregado'
        )
        
        total_ventas = pedidos.aggregate(Sum('total'))['total__sum'] or 0
        total_pedidos = pedidos.count()
        promedio = total_ventas / total_pedidos if total_pedidos > 0 else 0
        
        # Producto más vendido
        producto_top = DetallePedido.objects.filter(
            pedido__in=pedidos
        ).values('producto__nombre').annotate(
            total_vendido=Sum('cantidad')
        ).order_by('-total_vendido').first()
        
        producto_mas_vendido = producto_top['producto__nombre'] if producto_top else "N/A"
        
        # Día con más ventas
        ventas_por_dia = pedidos.extra(
            select={'dia': 'date(fecha)'}
        ).values('dia').annotate(
            total_dia=Sum('total')
        ).order_by('-total_dia').first()
        
        dia_mas_ventas = ""
        if ventas_por_dia:
            fecha_dia = datetime.strptime(ventas_por_dia['dia'], '%Y-%m-%d').date()
            dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            dia_mas_ventas = f"{dias_semana[fecha_dia.weekday()]} ({fecha_dia.strftime('%d/%m')})"
        
        # Generar observaciones automáticas
        observaciones = cls.generar_observaciones_inteligentes(
            total_ventas, total_pedidos, promedio, producto_mas_vendido, dia_mas_ventas
        )
        
        # Crear el reporte
        reporte = cls.objects.create(
            tipo='semanal',
            fecha_inicio=inicio_semana,
            fecha_fin=fin_semana,
            total_ventas=total_ventas,
            total_pedidos=total_pedidos,
            promedio_por_pedido=promedio,
            producto_mas_vendido=producto_mas_vendido,
            dia_mas_ventas=dia_mas_ventas,
            observaciones=observaciones
        )
        
        return reporte
    
    @staticmethod
    def generar_observaciones_inteligentes(total_ventas, total_pedidos, promedio, producto_top, dia_top):
        """Genera comentarios automáticos sobre las tendencias"""
        observaciones = []
        
        # ✅ SOLUCIONADO: Cambiar moneda a Bs/
        # Análisis de ventas
        if total_ventas > 1000:
            observaciones.append(f"📈 Excelente semana con Bs/ {total_ventas:.2f} en ventas totales.")
        elif total_ventas > 500:
            observaciones.append(f"📊 Semana promedio con Bs/ {total_ventas:.2f} en ventas.")
        else:
            observaciones.append(f"📉 Semana baja con Bs/ {total_ventas:.2f} en ventas. Considerar promociones.")
        
        # Análisis de pedidos
        if total_pedidos > 50:
            observaciones.append(f"🎯 Alto volumen de pedidos ({total_pedidos}). Excelente flujo de clientes.")
        elif total_pedidos > 20:
            observaciones.append(f"📋 Volumen moderado de pedidos ({total_pedidos}).")
        else:
            observaciones.append(f"⚠️ Bajo volumen de pedidos ({total_pedidos}). Revisar estrategias de marketing.")
        
        # Análisis de promedio
        if promedio > 20:
            observaciones.append(f"💰 Excelente ticket promedio de Bs/ {promedio:.2f}.")
        elif promedio > 15:
            observaciones.append(f"💵 Ticket promedio saludable de Bs/ {promedio:.2f}.")
        else:
            observaciones.append(f"💸 Ticket promedio bajo (Bs/ {promedio:.2f}). Considerar upselling.")
        
        # Producto estrella
        if producto_top and producto_top != "N/A":
            observaciones.append(f"⭐ Producto estrella: '{producto_top}'. Mantener en stock y promocionar.")
        
        # Día pico
        if dia_top:
            observaciones.append(f"🔥 Día pico: {dia_top}. Asegurar personal suficiente estos días.")
        
        return " ".join(observaciones)

class AnalisisProducto(models.Model):
    """
    Análisis detallado por producto
    """
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='analisis')
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    cantidad_vendida = models.IntegerField(default=0)
    ingresos_generados = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promedio_diario = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ranking_ventas = models.IntegerField(default=0)  # Posición en ranking de ventas
    fecha_analisis = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Análisis de Producto"
        verbose_name_plural = "Análisis de Productos"
        unique_together = ['producto', 'periodo_inicio', 'periodo_fin']
    
    def __str__(self):
        return f"Análisis {self.producto.nombre} - {self.periodo_inicio} a {self.periodo_fin}"