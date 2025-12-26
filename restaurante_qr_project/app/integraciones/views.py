"""
SGIR - Endpoints de integración para n8n
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
import os

from app.inventario.models import Insumo
from app.caja.models import CierreCaja
from app.pedidos.models import Pedido
from app.productos.models import Producto


def check_api_key(request):
    """Validar API KEY desde header"""
    api_key = request.META.get('HTTP_X_API_KEY')
    expected = os.getenv('N8N_API_KEY', 'cambiar-en-env')
    return api_key == expected


@api_view(['GET'])
def health_check(request):
    """GET /api/integraciones/health/"""
    return Response({'status': 'ok', 'timestamp': timezone.now().isoformat()})


@api_view(['GET'])
def inventario_stock_bajo(request):
    """GET /api/integraciones/inventario/stock-bajo/ + Header X-API-KEY"""
    if not check_api_key(request):
        return Response({'error': 'API KEY inválida'}, status=403)

    criticos = Insumo.objects.filter(activo=True, stock_actual=0).values(
        'id', 'nombre', 'unidad', 'stock_actual', 'stock_minimo'
    )
    bajos = Insumo.objects.filter(
        activo=True, stock_actual__gt=0, stock_actual__lte=F('stock_minimo')
    ).values('id', 'nombre', 'unidad', 'stock_actual', 'stock_minimo')

    return Response({
        'total': criticos.count() + bajos.count(),
        'criticos': list(criticos),
        'bajos': list(bajos),
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
def caja_resumen_cierres(request):
    """GET /api/integraciones/caja/resumen-cierres/?fecha=2025-12-26 + Header X-API-KEY"""
    if not check_api_key(request):
        return Response({'error': 'API KEY inválida'}, status=403)

    fecha_str = request.GET.get('fecha')
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else timezone.now().date()

    cierres = CierreCaja.objects.filter(fecha=fecha, estado='cerrado')
    resumen = cierres.aggregate(
        total_efectivo=Sum('total_efectivo'),
        total_tarjeta=Sum('total_tarjeta'),
        total_general=Sum('total_general')
    )

    for key, value in resumen.items():
        if isinstance(value, Decimal):
            resumen[key] = float(value)
        elif value is None:
            resumen[key] = 0.0

    return Response({
        'fecha': fecha.isoformat(),
        'total_cierres': cierres.count(),
        **resumen,
        'timestamp': timezone.now().isoformat()
    })
