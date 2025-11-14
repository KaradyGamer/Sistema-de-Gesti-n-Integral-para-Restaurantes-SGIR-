import logging
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.urls import reverse, NoReverseMatch
from django.apps import apps
from django.views.decorators.csrf import csrf_protect
from datetime import date
import json

from app.usuarios.models import Usuario
from app.usuarios.decorators import admin_requerido
from app.productos.models import Producto, Categoria
from app.mesas.models import Mesa
from app.pedidos.models import Pedido
from app.reservas.models import Reserva
from app.caja.models import JornadaLaboral, Transaccion
from .forms import UsuarioForm, ProductoForm, CategoriaForm, MesaForm, ReservaForm

logger = logging.getLogger("app.adminux")


def staff_required(user):
    """Verifica que el usuario esté autenticado y tenga permisos de staff."""
    return user.is_authenticated and user.is_staff


def safe_get_model(app_label, model_name):
    """
    Carga un modelo de forma segura.
    Retorna None si el modelo no existe en lugar de lanzar excepción.
    """
    try:
        return apps.get_model(app_label, model_name)
    except Exception as e:
        logger.debug(f"Model {app_label}.{model_name} not found: {e}")
        return None


def admin_url_for(model_cls, action="changelist"):
    """
    Genera URL del admin de Django para un modelo.
    Retorna '#' si el modelo no está registrado en el admin (evita NoReverseMatch).
    """
    if model_cls is None:
        return "#"
    try:
        app_label = model_cls._meta.app_label
        model_name = model_cls._meta.model_name
        return reverse(f"admin:{app_label}_{model_name}_{action}")
    except NoReverseMatch:
        logger.debug(f"Admin URL not found for {model_cls.__name__} - action: {action}")
        return "#"
    except Exception as e:
        logger.debug(f"Error generating admin URL for {model_cls.__name__}: {e}")
        return "#"


def safe_count(qs, **filters):
    """Evita crasheos si el campo no existe en el modelo."""
    try:
        return qs.filter(**filters).count()
    except Exception as e:
        logger.debug(f"safe_count fallback for {qs.model.__name__}: {e}")
        return qs.count()


# ══════════════════════════════════════════════
# 🔐 LOGIN DEL PERSONAL
# ══════════════════════════════════════════════

@csrf_protect
def staff_login(request):
    """
    Login unificado para el personal del restaurante.

    Comportamiento según tipo de usuario:
    - superuser → redirige a /admin/ (admin nativo Django)
    - staff (no superuser) → redirige a /adminux/ (panel moderno)
    - usuario normal → redirige a / (puede ajustarse)

    Respeta el parámetro ?next= si apunta a /adminux/
    """
    # Si ya está autenticado, redirigir según privilegios
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("/admin/")
        elif request.user.is_staff:
            return redirect("/adminux/")
        return redirect("/")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        # Autenticar usuario
        user = authenticate(request, username=username, password=password)

        if not user:
            logger.warning(f"Login fallido: usuario '{username}' no existe o credenciales inválidas")
            return render(request, "adminux/login.html", {
                "error": "Usuario o contraseña incorrectos",
                "next": request.POST.get("next", "")
            })

        if not user.is_active:
            logger.warning(f"Login fallido: usuario '{username}' está inactivo")
            return render(request, "adminux/login.html", {
                "error": "Tu cuenta está inactiva. Contacta al administrador.",
                "next": request.POST.get("next", "")
            })

        # Login exitoso
        login(request, user)
        logger.info(f"Login exitoso: {username} (is_staff={user.is_staff}, is_superuser={user.is_superuser})")

        # Determinar redirección
        next_url = request.POST.get("next") or request.GET.get("next") or ""

        # Si viene con ?next= hacia /adminux/, respetarlo
        if next_url.startswith("/adminux/"):
            return redirect(next_url)

        # Ruteo automático por privilegios
        if user.is_superuser:
            return redirect("/admin/")
        elif user.is_staff:
            return redirect("/adminux/")
        else:
            # Usuarios normales (clientes, etc.)
            return redirect("/")

    # GET request - mostrar formulario de login
    return render(request, "adminux/login.html", {
        "next": request.GET.get("next", "")
    })


# ══════════════════════════════════════════════
# 📊 DASHBOARD PRINCIPAL
# ══════════════════════════════════════════════

@login_required(login_url="/staff/login/")
@user_passes_test(staff_required, login_url="/staff/login/")
def adminux_dashboard(request):
    """
    Dashboard principal de AdminUX con estadísticas y enlaces al admin nativo.
    Solo accesible para usuarios is_staff.
    Versión mejorada con manejo robusto de errores NoReverseMatch.
    """
    # Cargar modelos dinámicamente (con manejo de errores)
    Mesa = safe_get_model("mesas", "Mesa")
    Producto = safe_get_model("productos", "Producto")
    Categoria = safe_get_model("productos", "Categoria")
    Pedido = safe_get_model("pedidos", "Pedido")
    Reserva = safe_get_model("reservas", "Reserva")
    Usuario = safe_get_model("usuarios", "Usuario")

    # Modelos de Caja (todos los registrados en admin)
    AlertaStock = safe_get_model("caja", "AlertaStock")
    CierreCaja = safe_get_model("caja", "CierreCaja")
    DetallePago = safe_get_model("caja", "DetallePago")
    HistMod = safe_get_model("caja", "HistorialModificaciones")
    JornadaLaboral = safe_get_model("caja", "JornadaLaboral")
    Transaccion = safe_get_model("caja", "Transaccion")

    # KPIs del sistema
    kpis = {
        "mesas": {
            "total": Mesa.objects.count() if Mesa else 0,
            "disponibles": safe_count(Mesa.objects, disponible=True) if Mesa else 0,
            "admin_list": admin_url_for(Mesa),
            "admin_add": admin_url_for(Mesa, "add"),
        },
        "productos": {
            "total": Producto.objects.count() if Producto else 0,
            "categorias": safe_count(Categoria.objects, activo=True) if Categoria else 0,
            "stock_bajo": safe_count(Producto.objects, activo=True, stock_actual__lte=10) if Producto and hasattr(Producto, 'stock_actual') else 0,
            "admin_list": admin_url_for(Producto),
            "admin_add": admin_url_for(Producto, "add"),
            "admin_categorias": admin_url_for(Categoria),
        },
        "pedidos": {
            "total": Pedido.objects.count() if Pedido else 0,
            "pendientes": safe_count(Pedido.objects, estado="pendiente") if Pedido else 0,
            "en_cocina": safe_count(Pedido.objects, estado__in=["en_preparacion", "en_cocina"]) if Pedido else 0,
            "listos": safe_count(Pedido.objects, estado="listo") if Pedido else 0,
            "admin_list": admin_url_for(Pedido),
            "admin_add": admin_url_for(Pedido, "add"),
        },
        "caja": {
            # Contadores
            "jornadas": JornadaLaboral.objects.count() if JornadaLaboral else 0,
            "transacciones": Transaccion.objects.count() if Transaccion else 0,
            "alertas_stock": AlertaStock.objects.count() if AlertaStock else 0,
            "cierres": CierreCaja.objects.count() if CierreCaja else 0,
            "jornada_activa": JornadaLaboral.hay_jornada_activa() if JornadaLaboral and hasattr(JornadaLaboral, 'hay_jornada_activa') else False,

            # Enlaces al admin (todos los modelos registrados)
            "alertas_list": admin_url_for(AlertaStock),
            "alertas_add": admin_url_for(AlertaStock, "add"),
            "cierres_list": admin_url_for(CierreCaja),
            "cierres_add": admin_url_for(CierreCaja, "add"),
            "detalles_pago_list": admin_url_for(DetallePago),
            "historial_list": admin_url_for(HistMod),
            "jornadas_list": admin_url_for(JornadaLaboral),
            "jornadas_add": admin_url_for(JornadaLaboral, "add"),
            "transacciones_list": admin_url_for(Transaccion),
            "transacciones_add": admin_url_for(Transaccion, "add"),
        },
        "reservas": {
            "total": Reserva.objects.count() if Reserva else 0,
            "activas": safe_count(Reserva.objects, estado__in=['pendiente', 'confirmada'], fecha_reserva__gte=timezone.now()) if Reserva else 0,
            "admin_list": admin_url_for(Reserva),
            "admin_add": admin_url_for(Reserva, "add"),
        },
        "usuarios": {
            "total": Usuario.objects.count() if Usuario else 0,
            "activos": safe_count(Usuario.objects, is_active=True, activo=True) if Usuario else 0,
            "admin_list": admin_url_for(Usuario),
            "admin_add": admin_url_for(Usuario, "add"),
        },
    }

    # Datos recientes
    recientes = {
        "pedidos": Pedido.objects.select_related('mesa').order_by("-id")[:8] if Pedido else [],
        "transacciones": Transaccion.objects.order_by("-id")[:8] if Transaccion else [],
        "reservas": Reserva.objects.order_by("-id")[:8] if Reserva else [],
    }

    # Datos para gráficas (Chart.js)
    labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    chart_orders = [5, 8, 3, 10, 6, 4, 7]
    chart_sales = [120, 340, 180, 500, 260, 210, 430]

    ctx = {
        "kpis": kpis,
        "recientes": recientes,
        "admin_home": reverse("admin:index"),
        "user": request.user,
        "chart_labels": json.dumps(labels),
        "chart_orders": json.dumps(chart_orders),
        "chart_sales": json.dumps(chart_sales),
    }

    logger.info(f"AdminUX dashboard renderizado correctamente - Usuario: {request.user.username}")
    return render(request, "html/adminux/dashboard.html", ctx)


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
    """✅ SEGURO: Crear nuevo usuario con Django Forms"""
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            try:
                usuario = form.save()
                messages.success(request, f'✅ Usuario {usuario.username} creado exitosamente')
                logger.info(f"AdminUX: Usuario {usuario.username} creado por {request.user.username}")
                return redirect('adminux:usuarios')
            except Exception as e:
                logger.exception(f"AdminUX: Error al crear usuario - {e}")
                messages.error(request, f'❌ Error al crear usuario: {str(e)}')
        else:
            # Mostrar errores de validación
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UsuarioForm()

    return render(request, 'html/adminux/usuarios/form.html', {'form': form})


@admin_requerido
def usuarios_editar(request, pk):
    """✅ SEGURO: Editar usuario existente con Django Forms"""
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            try:
                usuario = form.save()
                messages.success(request, f'✅ Usuario {usuario.username} actualizado exitosamente')
                logger.info(f"AdminUX: Usuario {usuario.username} editado por {request.user.username}")
                return redirect('adminux:usuarios')
            except Exception as e:
                logger.exception(f"AdminUX: Error al editar usuario - {e}")
                messages.error(request, f'❌ Error al actualizar usuario: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UsuarioForm(instance=usuario)

    context = {'form': form, 'usuario': usuario}
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
    categorias = Categoria.objects.filter(activo=True)
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
    categorias = Categoria.objects.filter(activo=True)
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
    categorias = Categoria.objects.filter(activo=True)
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
    categorias = Categoria.objects.filter(activo=True).annotate(
        total_productos=Count('productos', filter=Q(productos__activo=True))
    ).order_by('nombre')
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
