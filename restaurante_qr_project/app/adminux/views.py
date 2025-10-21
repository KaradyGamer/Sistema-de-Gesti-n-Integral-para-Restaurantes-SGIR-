from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import date

from app.usuarios.models import Usuario
from app.usuarios.decorators import admin_requerido
from app.productos.models import Producto, Categoria
from app.mesas.models import Mesa
from app.pedidos.models import Pedido
from app.reservas.models import Reserva


# ══════════════════════════════════════════════
# 📊 DASHBOARD PRINCIPAL
# ══════════════════════════════════════════════

@admin_requerido
def dashboard(request):
    """Dashboard principal de AdminUX con estadísticas"""

    # Estadísticas generales
    total_usuarios = Usuario.objects.filter(activo=True).count()
    total_productos = Producto.objects.filter(activo=True).count()
    total_mesas = Mesa.objects.count()

    # Pedidos del día
    hoy = date.today()
    pedidos_hoy = Pedido.objects.filter(fecha__date=hoy)
    total_pedidos_hoy = pedidos_hoy.count()
    ventas_hoy = pedidos_hoy.filter(estado_pago='pagado').aggregate(Sum('total'))['total__sum'] or 0

    # Reservas activas
    reservas_activas = Reserva.objects.filter(
        estado__in=['pendiente', 'confirmada'],
        fecha_reserva__gte=hoy
    ).count()

    # Productos con stock bajo
    productos_stock_bajo = Producto.objects.filter(
        activo=True,
        stock__lte=10
    ).count()

    # Últimos pedidos
    ultimos_pedidos = Pedido.objects.select_related('mesa').order_by('-fecha')[:5]

    # Últimas reservas
    ultimas_reservas = Reserva.objects.select_related('mesa').order_by('-fecha_creacion')[:5]

    context = {
        'total_usuarios': total_usuarios,
        'total_productos': total_productos,
        'total_mesas': total_mesas,
        'total_pedidos_hoy': total_pedidos_hoy,
        'ventas_hoy': ventas_hoy,
        'reservas_activas': reservas_activas,
        'productos_stock_bajo': productos_stock_bajo,
        'ultimos_pedidos': ultimos_pedidos,
        'ultimas_reservas': ultimas_reservas,
    }

    return render(request, 'html/adminux/dashboard.html', context)


# ══════════════════════════════════════════════
# 👥 GESTIÓN DE USUARIOS
# ══════════════════════════════════════════════

@admin_requerido
def usuarios_list(request):
    """Lista de todos los usuarios"""
    usuarios = Usuario.objects.filter(activo=True).order_by('-date_joined')
    context = {'usuarios': usuarios}
    return render(request, 'adminux/usuarios/list.html', context)


@admin_requerido
def usuarios_crear(request):
    """Crear nuevo usuario"""
    if request.method == 'POST':
        try:
            usuario = Usuario.objects.create_user(
                username=request.POST['username'],
                email=request.POST.get('email', ''),
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                password=request.POST['password'],
                rol=request.POST['rol'],
                is_active=request.POST.get('is_active') == 'on'
            )
            messages.success(request, f'✅ Usuario {usuario.username} creado exitosamente')
            return redirect('adminux:usuarios')
        except Exception as e:
            messages.error(request, f'❌ Error al crear usuario: {str(e)}')
    return render(request, 'html/adminux/usuarios/form.html')


@admin_requerido
def usuarios_editar(request, pk):
    """Editar usuario existente"""
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        try:
            usuario.email = request.POST.get('email', '')
            usuario.first_name = request.POST['first_name']
            usuario.last_name = request.POST['last_name']
            usuario.rol = request.POST['rol']
            usuario.is_active = request.POST.get('is_active') == 'on'

            # Cambiar contraseña solo si se proporciona una nueva
            password = request.POST.get('password', '').strip()
            if password:
                usuario.set_password(password)

            usuario.save()
            messages.success(request, f'✅ Usuario {usuario.username} actualizado exitosamente')
            return redirect('adminux:usuarios')
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar usuario: {str(e)}')
    context = {'usuario': usuario}
    return render(request, 'html/adminux/usuarios/form.html', context)


@admin_requerido
def usuarios_eliminar(request, pk):
    """Eliminar usuario (soft delete)"""
    usuario = get_object_or_404(Usuario, pk=pk)
    usuario.is_active = False
    usuario.save()
    messages.success(request, f'✅ Usuario {usuario.username} eliminado exitosamente')
    return redirect('adminux:usuarios')


# ══════════════════════════════════════════════
# 🍕 GESTIÓN DE PRODUCTOS
# ══════════════════════════════════════════════

@admin_requerido
def productos_list(request):
    """Lista de todos los productos"""
    productos = Producto.objects.filter(activo=True).select_related('categoria').order_by('categoria', 'nombre')
    categorias = Categoria.objects.filter(activa=True)
    context = {'productos': productos, 'categorias': categorias}
    return render(request, 'html/adminux/productos/list.html', context)


@admin_requerido
def productos_crear(request):
    """Crear nuevo producto"""
    if request.method == 'POST':
        try:
            producto = Producto.objects.create(
                nombre=request.POST['nombre'],
                descripcion=request.POST.get('descripcion', ''),
                categoria_id=request.POST['categoria'],
                precio=request.POST['precio'],
                stock=request.POST['stock'],
                disponible=request.POST.get('disponible') == 'on',
                imagen=request.FILES.get('imagen')
            )
            messages.success(request, f'✅ Producto {producto.nombre} creado exitosamente')
            return redirect('adminux:productos')
        except Exception as e:
            messages.error(request, f'❌ Error al crear producto: {str(e)}')
    categorias = Categoria.objects.filter(activa=True)
    context = {'categorias': categorias}
    return render(request, 'html/adminux/productos/form.html', context)


@admin_requerido
def productos_editar(request, pk):
    """Editar producto existente"""
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        try:
            producto.nombre = request.POST['nombre']
            producto.descripcion = request.POST.get('descripcion', '')
            producto.categoria_id = request.POST['categoria']
            producto.precio = request.POST['precio']
            producto.stock = request.POST['stock']
            producto.disponible = request.POST.get('disponible') == 'on'

            # Actualizar imagen solo si se sube una nueva
            if 'imagen' in request.FILES:
                producto.imagen = request.FILES['imagen']

            producto.save()
            messages.success(request, f'✅ Producto {producto.nombre} actualizado exitosamente')
            return redirect('adminux:productos')
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar producto: {str(e)}')
    categorias = Categoria.objects.filter(activa=True)
    context = {'producto': producto, 'categorias': categorias}
    return render(request, 'html/adminux/productos/form.html', context)


@admin_requerido
def productos_eliminar(request, pk):
    """Eliminar producto (soft delete)"""
    producto = get_object_or_404(Producto, pk=pk)
    producto.activo = False
    producto.save()
    messages.success(request, f'✅ Producto {producto.nombre} eliminado exitosamente')
    return redirect('adminux:productos')


# ══════════════════════════════════════════════
# 📁 GESTIÓN DE CATEGORÍAS
# ══════════════════════════════════════════════

@admin_requerido
def categorias_list(request):
    """Lista de todas las categorías"""
    categorias = Categoria.objects.filter(activa=True).annotate(
        total_productos=Count('productos', filter=Q(productos__activo=True))
    ).order_by('orden', 'nombre')
    context = {'categorias': categorias}
    return render(request, 'html/adminux/categorias/list.html', context)


@admin_requerido
def categorias_crear(request):
    """Crear nueva categoría"""
    if request.method == 'POST':
        try:
            categoria = Categoria.objects.create(
                nombre=request.POST['nombre'],
                descripcion=request.POST.get('descripcion', ''),
                orden=request.POST.get('orden', 0)
            )
            messages.success(request, f'✅ Categoría {categoria.nombre} creada exitosamente')
            return redirect('adminux:categorias')
        except Exception as e:
            messages.error(request, f'❌ Error al crear categoría: {str(e)}')
    return render(request, 'html/adminux/categorias/form.html')


@admin_requerido
def categorias_editar(request, pk):
    """Editar categoría existente"""
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        try:
            categoria.nombre = request.POST['nombre']
            categoria.descripcion = request.POST.get('descripcion', '')
            categoria.orden = request.POST.get('orden', 0)
            categoria.save()
            messages.success(request, f'✅ Categoría {categoria.nombre} actualizada exitosamente')
            return redirect('adminux:categorias')
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar categoría: {str(e)}')
    context = {'categoria': categoria}
    return render(request, 'html/adminux/categorias/form.html', context)


@admin_requerido
def categorias_eliminar(request, pk):
    """Eliminar categoría (soft delete)"""
    categoria = get_object_or_404(Categoria, pk=pk)
    # Verificar que no tenga productos activos
    if categoria.productos.filter(activo=True).exists():
        messages.error(request, '❌ No se puede eliminar: la categoría tiene productos asociados')
        return redirect('adminux:categorias')
    categoria.activa = False
    categoria.save()
    messages.success(request, f'✅ Categoría {categoria.nombre} eliminada exitosamente')
    return redirect('adminux:categorias')


# ══════════════════════════════════════════════
# 🪑 GESTIÓN DE MESAS
# ══════════════════════════════════════════════

@admin_requerido
def mesas_list(request):
    """Lista de todas las mesas"""
    mesas = Mesa.objects.all().order_by('numero')
    context = {'mesas': mesas}
    return render(request, 'html/adminux/mesas/list.html', context)


@admin_requerido
def mesas_crear(request):
    """Crear nueva mesa"""
    if request.method == 'POST':
        try:
            mesa = Mesa.objects.create(
                numero=request.POST['numero'],
                capacidad=request.POST['capacidad'],
                estado=request.POST['estado'],
                ubicacion=request.POST.get('ubicacion', '')
            )
            messages.success(request, f'✅ Mesa {mesa.numero} creada exitosamente')
            return redirect('adminux:mesas')
        except Exception as e:
            messages.error(request, f'❌ Error al crear mesa: {str(e)}')
    return render(request, 'html/adminux/mesas/form.html')


@admin_requerido
def mesas_editar(request, pk):
    """Editar mesa existente"""
    mesa = get_object_or_404(Mesa, pk=pk)
    if request.method == 'POST':
        try:
            mesa.capacidad = request.POST['capacidad']
            mesa.estado = request.POST['estado']
            mesa.ubicacion = request.POST.get('ubicacion', '')
            mesa.save()
            messages.success(request, f'✅ Mesa {mesa.numero} actualizada exitosamente')
            return redirect('adminux:mesas')
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar mesa: {str(e)}')
    context = {'mesa': mesa}
    return render(request, 'html/adminux/mesas/form.html', context)


@admin_requerido
def mesas_eliminar(request, pk):
    """Eliminar mesa"""
    mesa = get_object_or_404(Mesa, pk=pk)
    numero = mesa.numero
    mesa.delete()
    messages.success(request, f'✅ Mesa {numero} eliminada exitosamente')
    return redirect('adminux:mesas')


# ══════════════════════════════════════════════
# 📋 GESTIÓN DE PEDIDOS
# ══════════════════════════════════════════════

@admin_requerido
def pedidos_list(request):
    """Lista de todos los pedidos"""
    pedidos = Pedido.objects.select_related('mesa').order_by('-fecha')[:100]
    mesas = Mesa.objects.all().order_by('numero')
    context = {'pedidos': pedidos, 'mesas': mesas}
    return render(request, 'html/adminux/pedidos/list.html', context)


@admin_requerido
def pedidos_detalle(request, pk):
    """Detalle de un pedido"""
    pedido = get_object_or_404(Pedido.objects.prefetch_related('items__producto'), pk=pk)
    context = {'pedido': pedido}
    return render(request, 'html/adminux/pedidos/detalle.html', context)


# ══════════════════════════════════════════════
# 📅 GESTIÓN DE RESERVAS
# ══════════════════════════════════════════════

@admin_requerido
def reservas_list(request):
    """Lista de todas las reservas"""
    reservas = Reserva.objects.select_related('mesa').order_by('-fecha_reserva')[:100]
    context = {'reservas': reservas}
    return render(request, 'html/adminux/reservas/list.html', context)

@admin_requerido
def reservas_crear(request):
    """Crear nueva reserva"""
    if request.method == 'POST':
        try:
            from datetime import datetime
            fecha_hora = f"{request.POST['fecha_reserva']} {request.POST['hora_reserva']}"
            reserva = Reserva.objects.create(
                nombre_cliente=request.POST['nombre_cliente'],
                telefono=request.POST['telefono'],
                email=request.POST.get('email', ''),
                numero_personas=request.POST['numero_personas'],
                fecha_reserva=datetime.strptime(fecha_hora, '%Y-%m-%d %H:%M'),
                mesa_id=request.POST['mesa'],
                estado=request.POST['estado'],
                observaciones=request.POST.get('observaciones', '')
            )
            messages.success(request, f'✅ Reserva para {reserva.nombre_cliente} creada exitosamente')
            return redirect('adminux:reservas')
        except Exception as e:
            messages.error(request, f'❌ Error al crear reserva: {str(e)}')
    mesas = Mesa.objects.all().order_by('numero')
    context = {'mesas': mesas}
    return render(request, 'html/adminux/reservas/form.html', context)


@admin_requerido
def reservas_editar(request, pk):
    """Editar reserva existente"""
    reserva = get_object_or_404(Reserva, pk=pk)
    if request.method == 'POST':
        try:
            from datetime import datetime
            fecha_hora = f"{request.POST['fecha_reserva']} {request.POST['hora_reserva']}"
            reserva.nombre_cliente = request.POST['nombre_cliente']
            reserva.telefono = request.POST['telefono']
            reserva.email = request.POST.get('email', '')
            reserva.numero_personas = request.POST['numero_personas']
            reserva.fecha_reserva = datetime.strptime(fecha_hora, '%Y-%m-%d %H:%M')
            reserva.mesa_id = request.POST['mesa']
            reserva.estado = request.POST['estado']
            reserva.observaciones = request.POST.get('observaciones', '')
            reserva.save()
            messages.success(request, f'✅ Reserva de {reserva.nombre_cliente} actualizada exitosamente')
            return redirect('adminux:reservas')
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar reserva: {str(e)}')
    mesas = Mesa.objects.all().order_by('numero')
    context = {'reserva': reserva, 'mesas': mesas}
    return render(request, 'html/adminux/reservas/form.html', context)


@admin_requerido
def reservas_eliminar(request, pk):
    """Eliminar reserva"""
    reserva = get_object_or_404(Reserva, pk=pk)
    nombre = reserva.nombre_cliente
    reserva.delete()
    messages.success(request, f'✅ Reserva de {nombre} eliminada exitosamente')
    return redirect('adminux:reservas')


# ══════════════════════════════════════════════
# 📊 REPORTES Y ESTADÍSTICAS
# ══════════════════════════════════════════════

@admin_requerido
def reportes(request):
    """Panel de reportes"""
    return render(request, 'adminux/reportes/index.html')


@admin_requerido
def reportes_ventas(request):
    """Reporte de ventas"""
    return render(request, 'adminux/reportes/ventas.html')


@admin_requerido
def reportes_productos(request):
    """Reporte de productos más vendidos"""
    return render(request, 'adminux/reportes/productos.html')


# ══════════════════════════════════════════════
# ⚙️ CONFIGURACIÓN
# ══════════════════════════════════════════════

@admin_requerido
def configuracion(request):
    """Configuración del sistema"""
    return render(request, 'adminux/configuracion.html')
