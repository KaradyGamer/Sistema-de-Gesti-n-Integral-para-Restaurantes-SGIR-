from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from app.usuarios.decorators import admin_requerido
from .models import CategoriaInsumo, Insumo, MovimientoInsumo
from .forms import CategoriaInsumoForm, InsumoForm, AjusteStockForm
import logging

logger = logging.getLogger(__name__)


# ==================== CATEGORÍAS DE INSUMOS ====================

@login_required
@admin_requerido
def categorias_insumo_list(request):
    """Lista de categorías de insumos"""
    search = request.GET.get('search', '')

    categorias = CategoriaInsumo.objects.all()

    if search:
        categorias = categorias.filter(
            Q(nombre__icontains=search) |
            Q(descripcion__icontains=search)
        )

    context = {
        'categorias': categorias,
        'search': search,
        'total': categorias.count(),
    }
    return render(request, 'html/adminux/inventario/categorias_list.html', context)


@login_required
@admin_requerido
def categorias_insumo_crear(request):
    """Crear nueva categoría de insumo"""
    if request.method == 'POST':
        form = CategoriaInsumoForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" creada exitosamente.')
            logger.info(f"Categoría de insumo creada: {categoria.nombre} por {request.user.username}")
            return redirect('inventario:categorias_insumo')
        else:
            messages.error(request, 'Error al crear la categoría. Verifica los datos.')
    else:
        form = CategoriaInsumoForm()

    context = {
        'form': form,
        'title': 'Crear Categoría de Insumo',
        'back_url': 'inventario:categorias_insumo',
    }
    return render(request, 'html/adminux/inventario/categorias_form.html', context)


@login_required
@admin_requerido
def categorias_insumo_editar(request, pk):
    """Editar categoría de insumo"""
    categoria = get_object_or_404(CategoriaInsumo, pk=pk)

    if request.method == 'POST':
        form = CategoriaInsumoForm(request.POST, instance=categoria)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" actualizada exitosamente.')
            logger.info(f"Categoría de insumo actualizada: {categoria.nombre} por {request.user.username}")
            return redirect('inventario:categorias_insumo')
        else:
            messages.error(request, 'Error al actualizar la categoría.')
    else:
        form = CategoriaInsumoForm(instance=categoria)

    context = {
        'form': form,
        'title': f'Editar Categoría: {categoria.nombre}',
        'back_url': 'inventario:categorias_insumo',
        'categoria': categoria,
    }
    return render(request, 'html/adminux/inventario/categorias_form.html', context)


@login_required
@admin_requerido
def categorias_insumo_eliminar(request, pk):
    """Eliminar (desactivar) categoría de insumo"""
    categoria = get_object_or_404(CategoriaInsumo, pk=pk)

    categoria.activo = False
    categoria.save()

    messages.success(request, f'Categoría "{categoria.nombre}" desactivada exitosamente.')
    logger.info(f"Categoría de insumo desactivada: {categoria.nombre} por {request.user.username}")

    return redirect('inventario:categorias_insumo')


# ==================== INSUMOS ====================

@login_required
@admin_requerido
def insumos_list(request):
    """Lista de insumos con filtros"""
    search = request.GET.get('search', '')
    categoria_id = request.GET.get('categoria', '')
    estado = request.GET.get('estado', '')  # ok, bajo, agotado

    insumos = Insumo.objects.select_related('categoria').filter(activo=True)

    # Filtro por búsqueda
    if search:
        insumos = insumos.filter(
            Q(nombre__icontains=search) |
            Q(nota__icontains=search)
        )

    # Filtro por categoría
    if categoria_id:
        insumos = insumos.filter(categoria_id=categoria_id)

    # Filtro por estado de stock
    if estado == 'bajo':
        insumos = [i for i in insumos if i.stock_bajo]
    elif estado == 'agotado':
        insumos = [i for i in insumos if i.agotado]
    elif estado == 'ok':
        insumos = [i for i in insumos if not i.stock_bajo and not i.agotado]

    categorias = CategoriaInsumo.objects.filter(activo=True)

    context = {
        'insumos': insumos,
        'categorias': categorias,
        'search': search,
        'categoria_id': categoria_id,
        'estado': estado,
        'total': len(insumos) if isinstance(insumos, list) else insumos.count(),
    }
    return render(request, 'html/adminux/inventario/insumos_list.html', context)


@login_required
@admin_requerido
def insumos_crear(request):
    """Crear nuevo insumo"""
    if request.method == 'POST':
        form = InsumoForm(request.POST)
        if form.is_valid():
            insumo = form.save()
            messages.success(request, f'Insumo "{insumo.nombre}" creado exitosamente.')
            logger.info(f"Insumo creado: {insumo.nombre} por {request.user.username}")
            return redirect('inventario:insumos')
        else:
            messages.error(request, 'Error al crear el insumo. Verifica los datos.')
    else:
        form = InsumoForm()

    context = {
        'form': form,
        'title': 'Crear Insumo',
        'back_url': 'inventario:insumos',
    }
    return render(request, 'html/adminux/inventario/insumos_form.html', context)


@login_required
@admin_requerido
def insumos_editar(request, pk):
    """Editar insumo existente"""
    insumo = get_object_or_404(Insumo, pk=pk)

    if request.method == 'POST':
        form = InsumoForm(request.POST, instance=insumo)
        if form.is_valid():
            insumo = form.save()
            messages.success(request, f'Insumo "{insumo.nombre}" actualizado exitosamente.')
            logger.info(f"Insumo actualizado: {insumo.nombre} por {request.user.username}")
            return redirect('inventario:insumos')
        else:
            messages.error(request, 'Error al actualizar el insumo.')
    else:
        form = InsumoForm(instance=insumo)

    context = {
        'form': form,
        'title': f'Editar Insumo: {insumo.nombre}',
        'back_url': 'inventario:insumos',
        'insumo': insumo,
    }
    return render(request, 'html/adminux/inventario/insumos_form.html', context)


@login_required
@admin_requerido
def insumos_eliminar(request, pk):
    """Eliminar (desactivar) insumo"""
    insumo = get_object_or_404(Insumo, pk=pk)

    insumo.activo = False
    insumo.save()

    messages.success(request, f'Insumo "{insumo.nombre}" desactivado exitosamente.')
    logger.info(f"Insumo desactivado: {insumo.nombre} por {request.user.username}")

    return redirect('inventario:insumos')


@login_required
@admin_requerido
def insumos_ajustar_stock(request, pk):
    """Ajustar stock de un insumo"""
    insumo = get_object_or_404(Insumo, pk=pk)

    if request.method == 'POST':
        form = AjusteStockForm(request.POST)
        if form.is_valid():
            cantidad_nueva = form.cleaned_data['cantidad_nueva']
            motivo = form.cleaned_data['motivo']

            try:
                insumo.ajustar_stock(
                    cantidad_nueva=cantidad_nueva,
                    motivo=motivo,
                    usuario=request.user
                )
                messages.success(
                    request,
                    f'Stock de "{insumo.nombre}" ajustado a {cantidad_nueva} {insumo.unidad}.'
                )
                logger.info(f"Stock ajustado: {insumo.nombre} a {cantidad_nueva} por {request.user.username}")
                return redirect('inventario:insumos')

            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Error en el formulario de ajuste.')
    else:
        form = AjusteStockForm(initial={'cantidad_nueva': insumo.stock_actual})

    context = {
        'form': form,
        'title': f'Ajustar Stock: {insumo.nombre}',
        'back_url': 'inventario:insumos',
        'insumo': insumo,
    }
    return render(request, 'html/adminux/inventario/insumos_ajustar.html', context)


# ==================== MOVIMIENTOS ====================

@login_required
@admin_requerido
def movimientos_list(request):
    """Historial de movimientos de inventario"""
    insumo_id = request.GET.get('insumo', '')
    tipo = request.GET.get('tipo', '')

    movimientos = MovimientoInsumo.objects.select_related('insumo', 'creado_por').all()

    # Filtro por insumo
    if insumo_id:
        movimientos = movimientos.filter(insumo_id=insumo_id)

    # Filtro por tipo
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)

    insumos = Insumo.objects.filter(activo=True)

    context = {
        'movimientos': movimientos[:100],  # Últimos 100 movimientos
        'insumos': insumos,
        'insumo_id': insumo_id,
        'tipo': tipo,
        'total': movimientos.count(),
    }
    return render(request, 'html/adminux/inventario/movimientos_list.html', context)
