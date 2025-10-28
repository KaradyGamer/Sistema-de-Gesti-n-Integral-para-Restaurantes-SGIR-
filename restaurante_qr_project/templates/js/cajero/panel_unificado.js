/**
 * PANEL UNIFICADO DE CAJA
 * Sistema de navegación SPA con sidebar
 */

// Esperar a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {

// ============================================
// VARIABLES GLOBALES
// ============================================
const sidebar = document.getElementById('sidebar');
const toggleBtn = document.getElementById('toggleSidebar');
const navItems = document.querySelectorAll('.nav-item');
const sections = document.querySelectorAll('.content-section');
const pageTitle = document.getElementById('pageTitle');
const pageSubtitle = document.getElementById('pageSubtitle');

// Títulos de secciones
const sectionTitles = {
    dashboard: { title: 'Inicio', subtitle: 'Resumen general del sistema' },
    pedidos: { title: 'Pedidos Pendientes', subtitle: 'Gestión de pedidos por cobrar' },
    cobrar: { title: 'Procesar Pagos', subtitle: 'Cobrar pedidos entregados' },
    mesas: { title: 'Mapa de Mesas', subtitle: 'Estado actual de las mesas' },
    historial: { title: 'Historial', subtitle: 'Transacciones realizadas' },
    stock: { title: 'Alertas de Stock', subtitle: 'Productos con stock bajo' },
    personal: { title: 'Gestión de Personal', subtitle: 'Empleados y turnos' },
    jornada: { title: 'Jornada Laboral', subtitle: 'Control de jornada laboral' }
};

// ============================================
// TOGGLE SIDEBAR
// ============================================
toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
});

// Restaurar estado del sidebar
if (localStorage.getItem('sidebarCollapsed') === 'true') {
    sidebar.classList.add('collapsed');
}

// Sidebar en móvil
if (window.innerWidth <= 768) {
    document.addEventListener('click', (e) => {
        if (!sidebar.contains(e.target) && sidebar.classList.contains('active')) {
            sidebar.classList.remove('active');
        }
    });
}

// ============================================
// NAVEGACIÓN ENTRE SECCIONES
// ============================================
function navigateTo(sectionName) {
    // Ocultar todas las secciones
    sections.forEach(section => section.classList.remove('active'));

    // Desactivar todos los nav items
    navItems.forEach(item => item.classList.remove('active'));

    // Activar sección seleccionada
    const targetSection = document.getElementById(`section-${sectionName}`);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // Activar nav item correspondiente
    const targetNav = document.querySelector(`[data-section="${sectionName}"]`);
    if (targetNav) {
        targetNav.classList.add('active');
    }

    // Actualizar título
    const titleInfo = sectionTitles[sectionName];
    if (titleInfo) {
        pageTitle.textContent = titleInfo.title;
        pageSubtitle.textContent = titleInfo.subtitle;
    }

    // Actualizar URL (sin recargar)
    history.pushState({ section: sectionName }, '', `#${sectionName}`);

    // Cerrar sidebar en móvil
    if (window.innerWidth <= 768) {
        sidebar.classList.remove('active');
    }

    // Cargar datos según sección
    if (sectionName === 'dashboard') {
        cargarDashboard();
    } else if (sectionName === 'pedidos') {
        cargarPedidos();
    } else if (sectionName === 'mesas') {
        cargarMapaMesas();
    } else if (sectionName === 'historial') {
        cargarHistorial();
    } else if (sectionName === 'stock') {
        cargarAlertasStock();
    } else if (sectionName === 'personal') {
        cargarPersonal();
    } else if (sectionName === 'jornada') {
        cargarJornada();
    }
}

// Event listeners para navegación
navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const section = item.dataset.section;
        navigateTo(section);
    });
});

// Manejar navegación con botones back/forward
window.addEventListener('popstate', (e) => {
    if (e.state && e.state.section) {
        navigateTo(e.state.section);
    }
});

// Navegación inicial desde URL hash
window.addEventListener('load', () => {
    const hash = window.location.hash.substring(1);
    if (hash && sectionTitles[hash]) {
        navigateTo(hash);
    } else {
        navigateTo('dashboard');
    }
});

// ============================================
// CARGAR DASHBOARD
// ============================================
async function cargarDashboard() {
    try {
        const response = await fetch('/api/caja/estadisticas/', {
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (!response.ok) throw new Error('Error al cargar estadísticas');

        const data = await response.json();
        const stats = data.estadisticas || {};

        // Actualizar estadísticas
        document.getElementById('totalVentas').textContent = parseFloat(stats.totales?.total || 0).toFixed(2);
        document.getElementById('totalPedidos').textContent = stats.total_pedidos || 0;
        document.getElementById('pedidosPagados').textContent = stats.pedidos_pagados || 0;
        document.getElementById('pedidosPendientes').textContent = stats.pedidos_pendientes || 0;

        // Cargar tablero Kanban
        await cargarKanban();

    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('Error al cargar dashboard', 'error');
    }
}

// ============================================
// CARGAR PEDIDOS
// ============================================
async function cargarPedidos() {
    const container = document.getElementById('pedidosList');
    container.innerHTML = '<div class="loading">Cargando pedidos...</div>';

    try {
        const response = await fetch('/api/caja/pedidos/pendientes/', {
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (!response.ok) throw new Error('Error al cargar pedidos');

        const data = await response.json();

        if (!data.pedidos || data.pedidos.length === 0) {
            container.innerHTML = `
                <div class="card" style="grid-column: 1/-1; text-align: center; padding: 60px;">
                    <i class='bx bx-check-circle' style="font-size: 4em; color: var(--success-color);"></i>
                    <h3 style="margin-top: 20px;">No hay pedidos pendientes</h3>
                    <p style="color: var(--text-secondary);">Todos los pedidos están pagados</p>
                </div>
            `;
            return;
        }

        // Renderizar pedidos
        container.innerHTML = data.pedidos.map(pedido => {
            // Determinar badge de estado
            let estadoBadge = '';
            let estadoColor = '';
            switch(pedido.estado) {
                case 'pendiente':
                    estadoBadge = '⏳ Pendiente';
                    estadoColor = '#ffc107';
                    break;
                case 'en_preparacion':
                    estadoBadge = '🍳 En Preparación';
                    estadoColor = '#17a2b8';
                    break;
                case 'listo':
                    estadoBadge = '✅ Listo';
                    estadoColor = '#28a745';
                    break;
                case 'entregado':
                    estadoBadge = '🍽️ Entregado';
                    estadoColor = '#6c757d';
                    break;
                default:
                    estadoBadge = pedido.estado;
                    estadoColor = '#6c757d';
            }

            return `
            <div class="pedido-card">
                <div class="pedido-header">
                    <h3>Pedido #${pedido.id}</h3>
                    <div style="display: flex; gap: 8px;">
                        <span class="pedido-badge" style="background: ${estadoColor};">${estadoBadge}</span>
                        <span class="pedido-badge">Mesa ${pedido.mesa}</span>
                    </div>
                </div>
                <div class="pedido-body">
                    <p><strong>🕐 Hora:</strong> ${pedido.fecha}</p>
                    <p><strong>👥 Personas:</strong> ${pedido.numero_personas || 1}</p>
                    <p><strong>👨‍🍳 Mesero:</strong> ${pedido.mesero || 'Cliente directo'}</p>
                    ${pedido.modificado && pedido.modificado_por ? `
                        <div style="background: #fff3cd; border-left: 3px solid #ffc107; padding: 8px 12px; margin: 8px 0; border-radius: 4px;">
                            <small><i class='bx bx-edit'></i> <strong>Modificado por:</strong> ${pedido.modificado_por}</small>
                        </div>
                    ` : ''}
                    <p><strong>Productos:</strong></p>
                    <ul style="margin-left: 20px; margin-top: 8px;">
                        ${pedido.productos.map(p => `
                            <li style="margin-bottom: 5px;">${p.cantidad}x ${p.nombre} - Bs/ ${p.subtotal.toFixed(2)}</li>
                        `).join('')}
                    </ul>
                </div>
                <div class="pedido-total">
                    Total: Bs/ ${pedido.total_final.toFixed(2)}
                </div>
                <div class="pedido-actions">
                    <button class="btn btn-primary" onclick="verDetallePedido(${pedido.id})">
                        <i class='bx bx-show'></i> Ver Detalle
                    </button>
                    <button class="btn btn-success" onclick="cobrarPedido(${pedido.id})">
                        <i class='bx bx-money'></i> Cobrar
                    </button>
                </div>
            </div>
        `;
        }).join('');

    } catch (error) {
        console.error('Error:', error);
        container.innerHTML = `
            <div class="card" style="grid-column: 1/-1; text-align: center; padding: 40px;">
                <p style="color: var(--danger-color);">❌ Error al cargar pedidos</p>
                <button class="btn btn-primary" onclick="cargarPedidos()" style="margin-top: 20px;">
                    <i class='bx bx-refresh'></i> Reintentar
                </button>
            </div>
        `;
    }
}

// ============================================
// ACCIONES
// ============================================
function recargarPedidos() {
    cargarPedidos();
    mostrarNotificacion('Pedidos actualizados', 'success');
}

async function verDetallePedido(id) {
    const modal = document.getElementById('modalDetallePedido');
    const modalBody = document.getElementById('modalBody');

    modalBody.innerHTML = '<div class="loading">Cargando detalle...</div>';
    modal.style.display = 'flex';

    try {
        const response = await fetch(`/api/caja/pedidos/${id}/`, {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        if (!response.ok) throw new Error('Error al cargar pedido');

        const data = await response.json();
        const pedido = data.pedido;

        modalBody.innerHTML = `
            <div class="pedido-detalle">
                <div class="detalle-header">
                    <h3>Pedido #${pedido.id} - Mesa ${pedido.mesa}</h3>
                    <span class="badge" style="background: #ffc107;">${pedido.estado}</span>
                </div>

                <div class="detalle-info">
                    <p><strong>🕐 Fecha:</strong> ${pedido.fecha}</p>
                    <p><strong>👥 Personas:</strong> ${pedido.numero_personas || 1}</p>
                    <p><strong>👨‍🍳 Mesero:</strong> ${pedido.mesero || 'Cliente directo'}</p>
                </div>

                <div class="detalle-productos">
                    <h4>Productos</h4>
                    <table style="width: 100%; margin-top: 10px;">
                        <thead>
                            <tr>
                                <th>Producto</th>
                                <th>Cantidad</th>
                                <th>Precio Unit.</th>
                                <th>Subtotal</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${pedido.productos.map(p => `
                                <tr>
                                    <td>${p.nombre}</td>
                                    <td>${p.cantidad}</td>
                                    <td>Bs/ ${p.precio_unitario.toFixed(2)}</td>
                                    <td>Bs/ ${p.subtotal.toFixed(2)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>

                <div class="detalle-totales">
                    <p><strong>Subtotal:</strong> Bs/ ${pedido.subtotal.toFixed(2)}</p>
                    ${pedido.descuento > 0 ? `<p><strong>Descuento:</strong> -Bs/ ${pedido.descuento.toFixed(2)}</p>` : ''}
                    ${pedido.propina > 0 ? `<p><strong>Propina:</strong> +Bs/ ${pedido.propina.toFixed(2)}</p>` : ''}
                    <h3><strong>TOTAL:</strong> Bs/ ${pedido.total_final.toFixed(2)}</h3>
                </div>

                <div class="detalle-acciones">
                    <button class="btn btn-warning" onclick="modificarPedido(${id}, ${JSON.stringify(pedido).replace(/"/g, '&quot;')})">
                        <i class='bx bx-edit'></i> Modificar Pedido
                    </button>
                    <button class="btn btn-success btn-lg" onclick="procesarPago(${id}, ${pedido.total_final})">
                        <i class='bx bx-money'></i> Procesar Pago
                    </button>
                    <button class="btn btn-secondary" onclick="cerrarModal()">
                        <i class='bx bx-x'></i> Cerrar
                    </button>
                </div>
            </div>
        `;

    } catch (error) {
        modalBody.innerHTML = `
            <p style="color: red; text-align: center;">Error al cargar el pedido</p>
            <button class="btn btn-primary" onclick="cerrarModal()">Cerrar</button>
        `;
    }
}

function cerrarModal() {
    document.getElementById('modalDetallePedido').style.display = 'none';
}

async function procesarPago(id, totalPedido) {
    // Mostrar formulario de pago en el modal
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div class="form-pago">
            <h3>Procesar Pago - Pedido #${id}</h3>

            <div class="total-a-pagar">
                <h2>Total a Pagar: <span style="color: var(--primary-color);">Bs/ ${totalPedido.toFixed(2)}</span></h2>
            </div>

            <div class="form-group">
                <label>Método de Pago:</label>
                <select id="metodoPago" class="form-control">
                    <option value="efectivo">💵 Efectivo</option>
                    <option value="tarjeta">💳 Tarjeta</option>
                    <option value="qr">📱 QR</option>
                    <option value="mixto">🔀 Mixto</option>
                </select>
            </div>

            <div class="form-group">
                <label>Monto Recibido:</label>
                <input type="number" id="montoRecibido" class="form-control" step="0.01" min="0"
                       placeholder="Ingrese el monto" oninput="calcularCambio(${totalPedido})">
            </div>

            <div id="mensajeCambio" class="mensaje-cambio"></div>

            <div class="form-actions">
                <button class="btn btn-success btn-lg" onclick="confirmarPago(${id}, ${totalPedido})">
                    <i class='bx bx-check'></i> Confirmar Pago
                </button>
                <button class="btn btn-secondary" onclick="verDetallePedido(${id})">
                    <i class='bx bx-arrow-back'></i> Volver
                </button>
            </div>
        </div>
    `;
}

function calcularCambio(totalPedido) {
    const montoRecibido = parseFloat(document.getElementById('montoRecibido').value) || 0;
    const mensajeDiv = document.getElementById('mensajeCambio');

    if (montoRecibido === 0) {
        mensajeDiv.innerHTML = '';
        return;
    }

    if (montoRecibido < totalPedido) {
        const faltante = totalPedido - montoRecibido;
        mensajeDiv.innerHTML = `
            <div class="alerta alerta-error">
                <i class='bx bx-error-circle'></i>
                <div>
                    <h3>❌ MONTO INSUFICIENTE</h3>
                    <p>Faltan: <strong>Bs/ ${faltante.toFixed(2)}</strong></p>
                </div>
            </div>
        `;
        mensajeDiv.className = 'mensaje-cambio error';
    } else if (montoRecibido > totalPedido) {
        const cambio = montoRecibido - totalPedido;
        mensajeDiv.innerHTML = `
            <div class="alerta alerta-success">
                <i class='bx bx-check-circle'></i>
                <div>
                    <h3>✅ CAMBIO A ENTREGAR</h3>
                    <p class="cambio-grande">Bs/ ${cambio.toFixed(2)}</p>
                </div>
            </div>
        `;
        mensajeDiv.className = 'mensaje-cambio success';
    } else {
        mensajeDiv.innerHTML = `
            <div class="alerta alerta-exact">
                <i class='bx bx-check-circle'></i>
                <div>
                    <h3>✅ MONTO EXACTO</h3>
                    <p>Sin cambio</p>
                </div>
            </div>
        `;
        mensajeDiv.className = 'mensaje-cambio exact';
    }
}

async function confirmarPago(id, totalPedido) {
    const metodo = document.getElementById('metodoPago').value;
    const monto = parseFloat(document.getElementById('montoRecibido').value);

    if (!monto || monto <= 0) {
        mostrarNotificacion('❌ Ingrese un monto válido', 'error');
        return;
    }

    if (monto < totalPedido) {
        const faltante = totalPedido - monto;
        mostrarNotificacion(`❌ Monto insuficiente. Faltan Bs/ ${faltante.toFixed(2)}`, 'error');
        return;
    }

    try {
        const response = await fetch('/api/caja/pago/simple/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                pedido_id: id,
                metodo_pago: metodo,
                monto_recibido: monto
            })
        });

        const data = await response.json();

        if (data.success) {
            mostrarNotificacion('✅ Pago procesado correctamente', 'success');
            cerrarModal();
            cargarPedidos(); // Recargar lista
            cargarDashboard(); // Actualizar dashboard
            cargarMapaMesas(); // ✅ NUEVO: Actualizar mapa de mesas en tiempo real
        } else {
            mostrarNotificacion('❌ Error: ' + (data.error || 'Error al procesar pago'), 'error');
        }

    } catch (error) {
        mostrarNotificacion('❌ Error al procesar pago', 'error');
    }
}

function cobrarPedido(id) {
    verDetallePedido(id);
}

async function modificarPedido(id, pedidoData) {
    const modalBody = document.getElementById('modalBody');

    // Obtener todos los productos disponibles
    try {
        const response = await fetch('/api/productos/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        const data = await response.json();
        const todosProductos = data.productos || [];

        // DEBUG: Ver que productos devuelve la API
        console.log('=== DEBUG: Productos de la API ===');
        console.log('Total productos:', todosProductos.length);
        todosProductos.forEach(p => {
            console.log(`ID: ${p.id}, Nombre: ${p.nombre}, Categoria: ${p.categoria_nombre}`);
        });

        // Agrupar productos por categoría
        const productosPorCategoria = {};
        todosProductos.forEach(p => {
            const cat = p.categoria_nombre || 'Sin Categoría';
            if (!productosPorCategoria[cat]) {
                productosPorCategoria[cat] = [];
            }
            productosPorCategoria[cat].push(p);
        });

        // Calcular total actual
        const totalActual = pedidoData.productos.reduce((sum, p) => {
            const subtotal = parseFloat(p.subtotal) || 0;
            return sum + subtotal;
        }, 0);

        modalBody.innerHTML = `
            <div class="modificar-pedido">
                <h3>Modificar Pedido #${id}</h3>

                <div class="productos-actuales">
                    <h4>Productos en el Pedido</h4>
                    <div id="listaProductosPedido">
                        ${pedidoData.productos.map((p, index) => {
                            const precioUnit = parseFloat(p.precio_unitario) || 0;
                            let cantidad = parseInt(p.cantidad) || 1;

                            // Validar que la cantidad sea >= 1
                            if (cantidad < 1) cantidad = 1;

                            const subtotal = precioUnit * cantidad;

                            return `
                            <div class="producto-item" id="producto-${index}">
                                <span>${p.nombre}</span>
                                <div class="cantidad-controls">
                                    <button onclick="cambiarCantidad(${index}, -1)" class="btn-cantidad">-</button>
                                    <input type="number" id="cant-${index}" value="${cantidad}" min="1" step="1"
                                           class="input-cantidad"
                                           oninput="validarCantidadInput(${index})"
                                           onblur="validarCantidadInput(${index})">
                                    <button onclick="cambiarCantidad(${index}, 1)" class="btn-cantidad">+</button>
                                </div>
                                <span class="precio" id="subtotal-${index}">Bs/ ${subtotal.toFixed(2)}</span>
                                <button onclick="eliminarProducto(${index})" class="btn-eliminar">
                                    <i class='bx bx-trash'></i>
                                </button>
                            </div>
                        `;
                        }).join('')}
                    </div>
                </div>

                <div class="agregar-producto">
                    <h4><i class='bx bx-plus-circle'></i> Agregar Producto</h4>

                    <!-- Buscador -->
                    <div class="buscador-productos">
                        <i class='bx bx-search'></i>
                        <input type="text" id="buscarProducto" placeholder="Buscar producto..."
                               onkeyup="filtrarProductos()" class="input-buscar">
                    </div>

                    <!-- Lista simple de productos -->
                    <div class="lista-productos-menu" id="listaProductosMenu">
                        ${Object.keys(productosPorCategoria).map(categoria => `
                            <div class="categoria-grupo">
                                <div class="categoria-header" onclick="toggleCategoria('${categoria.replace(/\s+/g, '_')}')">
                                    <i class='bx bx-folder'></i>
                                    <span>${categoria}</span>
                                    <span class="badge-count">${productosPorCategoria[categoria].length}</span>
                                    <i class='bx bx-chevron-down toggle-icon'></i>
                                </div>
                                <div class="categoria-items" id="cat_${categoria.replace(/\s+/g, '_')}">
                                    ${productosPorCategoria[categoria].map(p => {
                                        const precio = parseFloat(p.precio) || 0;
                                        return `
                                        <div class="producto-simple-item"
                                             data-producto-id="${p.id}"
                                             data-producto-precio="${precio}"
                                             data-buscar="${p.nombre.toLowerCase()}">
                                            <span class="nombre-producto">${p.nombre}</span>
                                            <span class="precio-producto">Bs/ ${precio.toFixed(2)}</span>
                                        </div>
                                        `;
                                    }).join('')}
                                </div>
                            </div>
                        `).join('')}
                        <div id="noResultados" style="display: none; text-align: center; padding: 20px; color: #666;">
                            <i class='bx bx-search-alt' style='font-size: 48px;'></i>
                            <p>No se encontraron productos</p>
                        </div>
                    </div>
                </div>

                <div class="total-modificado">
                    <h3>Total: <span id="totalModificado">Bs/ ${totalActual.toFixed(2)}</span></h3>
                </div>

                <div class="form-actions">
                    <button class="btn btn-success btn-lg" onclick="guardarModificacion(${id})">
                        <i class='bx bx-save'></i> Guardar Cambios
                    </button>
                    <button class="btn btn-secondary" onclick="verDetallePedido(${id})">
                        <i class='bx bx-arrow-back'></i> Cancelar
                    </button>
                </div>
            </div>
        `;

        // Guardar datos del pedido en variable global temporal
        window.pedidoEnModificacion = {
            id: id,
            productos: [...pedidoData.productos]
        };

        // Agregar event listener para clicks en productos usando delegacion de eventos
        const listaProductosMenu = document.getElementById('listaProductosMenu');
        if (listaProductosMenu) {
            // Remover listeners anteriores si existen
            listaProductosMenu.replaceWith(listaProductosMenu.cloneNode(true));
            const listaActualizada = document.getElementById('listaProductosMenu');

            listaActualizada.addEventListener('click', function(e) {
                const item = e.target.closest('.producto-simple-item');
                if (item) {
                    const productoId = parseInt(item.dataset.productoId);
                    const productoPrecio = parseFloat(item.dataset.productoPrecio);
                    const productoNombre = item.querySelector('.nombre-producto')?.textContent || 'Producto';

                    console.log('=== DEBUG: Click en producto ===');
                    console.log('ID:', productoId, 'Nombre:', productoNombre, 'Precio:', productoPrecio);

                    seleccionarProductoMenu(productoId, productoNombre, productoPrecio);
                }
            });
        }

    } catch (error) {
        console.error('=== ERROR al cargar productos ===', error);
        mostrarNotificacion('Error al cargar productos: ' + error.message, 'error');
    }
}

function cambiarCantidad(index, delta) {
    const input = document.getElementById(`cant-${index}`);
    let cantidad = parseInt(input.value) + delta;

    // Validar que sea un número positivo
    if (isNaN(cantidad)) cantidad = 1;
    cantidad = Math.abs(cantidad); // Convertir negativos a positivos
    if (cantidad < 1) cantidad = 1;

    input.value = cantidad;

    // Actualizar en el pedido temporal
    window.pedidoEnModificacion.productos[index].cantidad = cantidad;
    actualizarTotal();
}

// Validar cantidad cuando se escribe manualmente
function validarCantidadInput(index) {
    const input = document.getElementById(`cant-${index}`);
    let cantidad = parseInt(input.value);

    // Validar y corregir
    if (isNaN(cantidad)) cantidad = 1;
    cantidad = Math.abs(cantidad); // Convertir negativos a positivos
    if (cantidad < 1) cantidad = 1;

    input.value = cantidad;
    window.pedidoEnModificacion.productos[index].cantidad = cantidad;
    actualizarTotal();
}

function eliminarProducto(index) {
    if (confirm('¿Eliminar este producto del pedido?')) {
        document.getElementById(`producto-${index}`).remove();
        window.pedidoEnModificacion.productos.splice(index, 1);
        actualizarTotal();
    }
}

// Toggle categoría (expandir/colapsar)
function toggleCategoria(categoriaId) {
    const items = document.getElementById(`cat_${categoriaId}`);
    const header = items.previousElementSibling;
    const icon = header.querySelector('.toggle-icon');

    if (items.style.display === 'none' || items.style.display === '') {
        items.style.display = 'grid';
        icon.style.transform = 'rotate(0deg)';
    } else {
        items.style.display = 'none';
        icon.style.transform = 'rotate(-90deg)';
    }
}

// Filtrar productos por búsqueda
function filtrarProductos() {
    const busqueda = document.getElementById('buscarProducto').value.toLowerCase().trim();
    const items = document.querySelectorAll('.producto-simple-item');
    const categorias = document.querySelectorAll('.categoria-grupo');

    let hayResultados = false;

    items.forEach(item => {
        const textoBuscar = item.dataset.buscar || '';

        if (textoBuscar.includes(busqueda)) {
            item.style.display = 'flex';
            hayResultados = true;
        } else {
            item.style.display = 'none';
        }
    });

    // Si hay búsqueda, expandir todas las categorías que tengan resultados
    if (busqueda.length > 0) {
        categorias.forEach(cat => {
            const itemsVisibles = cat.querySelectorAll('.producto-simple-item:not([style*="display: none"])');
            const catItems = cat.querySelector('.categoria-items');
            const icon = cat.querySelector('.toggle-icon');

            if (itemsVisibles.length > 0) {
                catItems.style.display = 'grid';
                icon.style.transform = 'rotate(0deg)';
            } else {
                catItems.style.display = 'none';
            }
        });

        // Mostrar mensaje si no hay resultados
        const noResultados = document.getElementById('noResultados');
        if (noResultados) {
            noResultados.style.display = hayResultados ? 'none' : 'block';
        }
    } else {
        // Sin búsqueda, mostrar todo
        const noResultados = document.getElementById('noResultados');
        if (noResultados) {
            noResultados.style.display = 'none';
        }
    }
}

// Seleccionar producto del menú
function seleccionarProductoMenu(id, nombre, precio) {
    // DEBUG: Ver que valores llegan a la funcion
    console.log('=== DEBUG: seleccionarProductoMenu ===');
    console.log('ID recibido:', id, 'Tipo:', typeof id);
    console.log('Nombre recibido:', nombre);
    console.log('Precio recibido:', precio);

    // Agregar al array temporal
    const nuevoProducto = {
        id: id,
        nombre: nombre,
        cantidad: 1,
        precio_unitario: precio,
        subtotal: precio
    };

    console.log('Producto a agregar:', nuevoProducto);
    window.pedidoEnModificacion.productos.push(nuevoProducto);

    // Recargar la vista de modificación
    modificarPedido(window.pedidoEnModificacion.id, window.pedidoEnModificacion);
    mostrarNotificacion(`✅ ${nombre} agregado`, 'success');
}

function actualizarTotal() {
    let total = 0;
    window.pedidoEnModificacion.productos.forEach((p, i) => {
        const input = document.getElementById(`cant-${i}`);
        let cantidad = parseInt(input?.value || p.cantidad);

        // Validar cantidad (debe ser >= 1)
        if (isNaN(cantidad) || cantidad < 1) {
            cantidad = 1;
            if (input) input.value = 1;
        }

        // Actualizar cantidad en el objeto
        p.cantidad = cantidad;

        // Calcular subtotal
        const subtotal = p.precio_unitario * cantidad;
        total += subtotal;

        // Actualizar subtotal en la interfaz
        const subtotalElement = document.getElementById(`subtotal-${i}`);
        if (subtotalElement) {
            subtotalElement.textContent = `Bs/ ${subtotal.toFixed(2)}`;
        }
    });

    document.getElementById('totalModificado').textContent = `Bs/ ${total.toFixed(2)}`;
}

async function guardarModificacion(id) {
  try {
    // Actualizar cantidades desde los inputs antes de enviar
    (window.pedidoEnModificacion.productos || []).forEach((p, index) => {
      const input = document.getElementById(`cant-${index}`);
      if (input) {
        let cantidad = parseInt(input.value);
        // Validar y convertir negativos a positivos
        if (isNaN(cantidad)) cantidad = 1;
        cantidad = Math.abs(cantidad);
        if (cantidad < 1) cantidad = 1;
        p.cantidad = cantidad;
      }
    });

    // Armar el payload con las cantidades actualizadas
    const productosMap = {};
    (window.pedidoEnModificacion.productos || []).forEach(p => {
      // Usar producto_id si existe (productos del pedido existente), sino usar id (productos recien agregados)
      const productoId = p.producto_id || p.id;
      productosMap[productoId] = parseInt(p.cantidad) || 1;
    });

    // DEBUG: Ver que se va a enviar al backend
    console.log('=== DEBUG: guardarModificacion ===');
    console.log('Productos en modificacion:', window.pedidoEnModificacion.productos);
    console.log('productosMap a enviar:', productosMap);

    const resp = await fetch(`/api/pedidos/${id}/modificar/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ productos: productosMap })
    });

    if (!resp.ok) {
      const errorData = await resp.json();
      throw new Error(errorData.error || 'Error al guardar modificaciones');
    }

    const data = await resp.json();

    mostrarNotificacion('Pedido modificado correctamente', 'success');
    cerrarModal();
    cargarPedidos(); // refresca la lista
    cargarDashboard(); // actualizar dashboard
  } catch (e) {
    console.error(e);
    mostrarNotificacion('Error: ' + e.message, 'error');
  }
}

function abrirTurno() {
    window.location.href = '/caja/abrir/';
}

function cerrarCaja() {
    if (confirm('¿Está seguro de cerrar la caja? Esto cerrará el turno actual.')) {
        window.location.href = '/caja/cierre/';
    }
}

// ============================================
// UTILIDADES
// ============================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function mostrarNotificacion(mensaje, tipo = 'info') {
    // Crear notificación toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    toast.textContent = mensaje;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${tipo === 'success' ? 'var(--success-color)' : tipo === 'error' ? 'var(--danger-color)' : 'var(--primary-color)'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// CARGAR MAPA DE MESAS
// ============================================
async function cargarMapaMesas() {
    const container = document.getElementById('mapaMesasContainer');
    container.innerHTML = '<div class="loading">Cargando mapa de mesas...</div>';

    try {
        const response = await fetch('/api/caja/mapa-mesas/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        if (!response.ok) throw new Error('Error al cargar mapa');

        const data = await response.json();

        if (!data.mesas || data.mesas.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class='bx bx-table'></i>
                    <h3>No hay mesas registradas</h3>
                    <p>Contacta al administrador para crear mesas</p>
                </div>
            `;
            return;
        }

        // Renderizar el mapa de mesas
        let html = `
            <div class="mapa-header">
                <div class="mapa-leyenda">
                    <span class="leyenda-item"><div class="color-box verde"></div> Disponible</span>
                    <span class="leyenda-item"><div class="color-box amarillo"></div> Reservada</span>
                    <span class="leyenda-item"><div class="color-box rojo"></div> Ocupada</span>
                    <span class="leyenda-item"><div class="color-box azul"></div> Pagando</span>
                </div>
            </div>
            <div class="mapa-grid">
        `;

        data.mesas.forEach(mesa => {
            const estadoTexto = {
                'disponible': 'Disponible',
                'ocupada': 'Ocupada',
                'reservada': 'Reservada',
                'pagando': 'Procesando Pago'
            };

            // Renderizar lista de productos
            let productosHTML = '';
            if (mesa.productos && mesa.productos.length > 0) {
                productosHTML = `
                    <div class="mesa-productos-lista">
                        <div class="productos-titulo">Productos:</div>
                        ${mesa.productos.map(p => `
                            <div class="producto-item-mesa">
                                • ${p.nombre} x${p.cantidad}
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            // Determinar si la mesa es clickeable
            const esClickeable = mesa.pedidos_activos > 0;
            const cursorStyle = esClickeable ? 'cursor: pointer;' : '';
            const onclickAttr = esClickeable ? `onclick="expandirMesa(${mesa.id})"` : '';

            html += `
                <div class="mesa-card ${mesa.color} ${esClickeable ? 'mesa-clickeable' : ''}"
                     data-mesa-id="${mesa.id}"
                     ${onclickAttr}
                     style="${cursorStyle}">
                    <div class="mesa-numero">Mesa ${mesa.numero}</div>
                    <div class="mesa-info">
                        <span class="mesa-capacidad">
                            <i class='bx bx-group'></i> ${mesa.capacidad}
                        </span>
                        <span class="mesa-estado">${estadoTexto[mesa.estado] || mesa.estado}</span>
                    </div>
                    ${mesa.pedidos_activos > 0 ? `
                        <div class="mesa-resumen">
                            <span><i class='bx bx-receipt'></i> ${mesa.pedidos_activos} pedido(s)</span>
                            <span class="mesa-total">Bs/ ${parseFloat(mesa.total_pendiente).toFixed(2)}</span>
                        </div>
                        ${productosHTML}
                    ` : ''}
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;

    } catch (error) {
        console.error('[DEBUG] Error cargando mapa de mesas:', error);
        container.innerHTML = '<p style="color: red;">Error al cargar mapa de mesas</p>';
    }
}


// ============================================
// PANEL LATERAL DE MESA
// ============================================
let pedidoActualData = null;
let productosDisponibles = [];

async function expandirMesa(mesaId) {
    try {
        // Obtener pedidos pendientes
        const response = await fetch(`/api/caja/pedidos/pendientes/`, {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        if (!response.ok) throw new Error('Error al cargar pedidos');

        const data = await response.json();

        // Buscar pedido de esta mesa
        const pedidoMesa = data.pedidos.find(p => p.mesa_id === mesaId);

        if (!pedidoMesa) {
            mostrarNotificacion('No hay pedidos activos en esta mesa', 'warning');
            return;
        }

        // Obtener detalle completo del pedido (incluye detalle_id)
        const detalleResponse = await fetch(`/api/caja/pedidos/${pedidoMesa.id}/`, {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        const detalleData = await detalleResponse.json();

        // Obtener productos disponibles
        const productosResponse = await fetch(`/api/productos/`, {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        const productosData = await productosResponse.json();
        productosDisponibles = productosData.productos || [];

        // Guardar datos del pedido con detalle_id
        pedidoActualData = {
            id: pedidoMesa.id,
            mesaId: mesaId,
            mesaNumero: pedidoMesa.mesa,
            productos: detalleData.pedido.productos.map(p => ({
                detalle_id: p.id,
                producto_id: p.producto_id,
                nombre: p.nombre,
                cantidad: p.cantidad,
                precio_unitario: p.precio_unitario,
                subtotal: p.subtotal
            })),
            total: pedidoMesa.total_final
        };

        abrirPanelLateralMesa();

    } catch (error) {
        console.error('Error abriendo panel de mesa:', error);
        mostrarNotificacion('Error al cargar datos de mesa', 'error');
    }
}

function abrirPanelLateralMesa() {
    // Cerrar panel anterior si existe
    const panelAnterior = document.getElementById('panelLateralMesa');
    if (panelAnterior) {
        panelAnterior.remove();
    }

    // Agrupar productos disponibles por categoría
    const productosPorCategoria = {};
    productosDisponibles.forEach(p => {
        const categoria = p.categoria_nombre || 'Sin Categoría';
        if (!productosPorCategoria[categoria]) {
            productosPorCategoria[categoria] = [];
        }
        productosPorCategoria[categoria].push(p);
    });

    const total = calcularTotalPedidoActual();

    const panelHTML = `
        <div class="panel-lateral-overlay" id="panelLateralOverlay" onclick="cerrarPanelLateralMesa()"></div>
        <div class="panel-lateral-mesa" id="panelLateralMesa">
            <!-- Header -->
            <div class="panel-lateral-header">
                <div>
                    <h2>Detalle del Pedido</h2>
                    <p class="panel-subtitle">Modificar Pedido #${pedidoActualData.id}</p>
                </div>
                <button type="button" class="panel-close-btn" onclick="cerrarPanelLateralMesa()">
                    <i class='bx bx-x'></i>
                </button>
            </div>

            <!-- Body con scroll -->
            <div class="panel-lateral-body">
                <!-- Productos en el Pedido -->
                <div class="panel-seccion">
                    <h3 class="panel-seccion-titulo">Productos en el Pedido</h3>
                    <div id="listaProductosPedido" class="productos-pedido-lista">
                        ${renderizarProductosPedido()}
                    </div>
                </div>

                <!-- Agregar Producto -->
                <div class="panel-seccion">
                    <h3 class="panel-seccion-titulo">
                        <i class='bx bx-plus-circle'></i> Agregar Producto
                    </h3>

                    <!-- Buscador -->
                    <div class="buscador-producto">
                        <i class='bx bx-search'></i>
                        <input
                            type="text"
                            id="buscadorProducto"
                            placeholder="Buscar producto..."
                            onkeyup="filtrarProductos(this.value)"
                        >
                    </div>

                    <!-- Categorías y productos -->
                    <div id="listaCategorias" class="categorias-lista">
                        ${Object.entries(productosPorCategoria).map(([categoria, productos]) => `
                            <div class="categoria-grupo">
                                <div class="categoria-header" onclick="toggleCategoria('${categoria.replace(/\s/g, '_')}')">
                                    <i class='bx bx-folder'></i>
                                    <span>${categoria}</span>
                                    <i class='bx bx-chevron-down categoria-arrow'></i>
                                </div>
                                <div class="categoria-productos" id="cat_${categoria.replace(/\s/g, '_')}">
                                    ${productos.map(p => `
                                        <div class="producto-item-seleccionable" data-nombre="${p.nombre.toLowerCase()}">
                                            <div class="producto-item-info">
                                                <span class="producto-nombre">${p.nombre}</span>
                                                <span class="producto-precio">Bs/ ${parseFloat(p.precio).toFixed(2)}</span>
                                            </div>
                                            <button type="button" class="btn-agregar-producto"
                                                    data-producto-id="${p.id}"
                                                    data-producto-nombre="${p.nombre}"
                                                    data-producto-precio="${p.precio}"
                                                    onclick="agregarProductoAlPedido(this.dataset.productoId, this.dataset.productoNombre, this.dataset.productoPrecio)">
                                                <i class='bx bx-plus'></i>
                                            </button>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>

            <!-- Footer fijo con total y botones -->
            <div class="panel-lateral-footer">
                <div class="panel-total">
                    <span class="panel-total-label">Total:</span>
                    <span class="panel-total-valor" id="totalPedidoActual">Bs/ ${total.toFixed(2)}</span>
                </div>

                <div class="panel-botones-grid">
                    <button type="button" class="btn-panel btn-pagar" onclick="cerrarPanelLateralMesa(); abrirModalPago(${pedidoActualData.mesaId}, false);">
                        <i class='bx bx-money'></i>
                        Pagar Todo
                    </button>
                    <button type="button" class="btn-panel btn-pago-separado" onclick="cerrarPanelLateralMesa(); abrirModalPago(${pedidoActualData.mesaId}, true);">
                        <i class='bx bx-cut'></i>
                        Pago Separado
                    </button>
                    <button type="button" class="btn-panel btn-cambiar-mesa" onclick="cerrarPanelLateralMesa(); abrirModalCambiarMesa(${pedidoActualData.mesaId});">
                        <i class='bx bx-transfer'></i>
                        Cambiar Mesa
                    </button>
                </div>

                <button type="button" class="btn-panel btn-guardar-principal" onclick="guardarCambiosPedido()">
                    <i class='bx bx-save'></i>
                    Guardar Cambios
                </button>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', panelHTML);

    // Animación de entrada
    setTimeout(() => {
        document.getElementById('panelLateralMesa').classList.add('abierto');
        document.getElementById('panelLateralOverlay').classList.add('visible');
    }, 10);
}

function renderizarProductosPedido() {
    if (!pedidoActualData.productos || pedidoActualData.productos.length === 0) {
        return '<div class="empty-productos">No hay productos en este pedido</div>';
    }

    return pedidoActualData.productos.map((producto, index) => `
        <div class="producto-pedido-item">
            <div class="producto-pedido-info">
                <span class="producto-pedido-nombre">${producto.nombre}</span>
                <span class="producto-pedido-precio">Bs/ ${parseFloat(producto.precio_unitario).toFixed(2)} c/u</span>
            </div>
            <div class="producto-pedido-controles">
                <button type="button" class="btn-cantidad btn-menos" onclick="modificarCantidadPedido(${index}, -1)">
                    <i class='bx bx-minus'></i>
                </button>
                <span class="cantidad-display">${producto.cantidad}</span>
                <button type="button" class="btn-cantidad btn-mas" onclick="modificarCantidadPedido(${index}, 1)">
                    <i class='bx bx-plus'></i>
                </button>
                <button type="button" class="btn-eliminar-producto" onclick="eliminarProductoDePedido(${index})" title="Eliminar">
                    <i class='bx bx-trash'></i>
                </button>
            </div>
            <div class="producto-pedido-subtotal">
                Bs/ ${(parseFloat(producto.precio_unitario) * producto.cantidad).toFixed(2)}
            </div>
        </div>
    `).join('');
}

function toggleCategoria(categoriaId) {
    const categoriaElement = document.getElementById(`cat_${categoriaId}`);
    if (categoriaElement) {
        categoriaElement.classList.toggle('expandida');
        const header = categoriaElement.previousElementSibling;
        if (header) {
            header.classList.toggle('abierta');
        }
    }
}

function filtrarProductos(termino) {
    const terminoLower = termino.toLowerCase().trim();
    const productos = document.querySelectorAll('.producto-item-seleccionable');

    productos.forEach(producto => {
        const nombre = producto.getAttribute('data-nombre');
        if (nombre.includes(terminoLower)) {
            producto.style.display = 'flex';
        } else {
            producto.style.display = 'none';
        }
    });

    // Si hay búsqueda, expandir todas las categorías
    if (terminoLower.length > 0) {
        document.querySelectorAll('.categoria-productos').forEach(cat => {
            cat.classList.add('expandida');
        });
    }
}

async function modificarCantidadPedido(index, cambio) {
    const producto = pedidoActualData.productos[index];
    const nuevaCantidad = producto.cantidad + cambio;

    if (nuevaCantidad < 1) {
        mostrarNotificacion('La cantidad mínima es 1. Usa el botón eliminar para quitar el producto.', 'warning');
        return;
    }

    // Actualizar localmente primero para UI responsive
    const cantidadAnterior = producto.cantidad;
    producto.cantidad = nuevaCantidad;
    actualizarVistaPanelLateral();

    // Guardar en backend (si tiene detalle_id del backend)
    if (producto.detalle_id) {
        try {
            const response = await fetch(`/api/caja/pedidos/detalle/${producto.detalle_id}/cantidad/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ cantidad: nuevaCantidad })
            });

            const data = await response.json();
            if (!data.success) {
                // Revertir si falla
                producto.cantidad = cantidadAnterior;
                actualizarVistaPanelLateral();
                mostrarNotificacion(data.error || 'Error al modificar cantidad', 'error');
            }
        } catch (error) {
            producto.cantidad = cantidadAnterior;
            actualizarVistaPanelLateral();
            mostrarNotificacion('Error al guardar cambio', 'error');
        }
    }
}

async function eliminarProductoDePedido(index) {
    if (pedidoActualData.productos.length === 1) {
        mostrarNotificacion('No puedes eliminar el único producto del pedido.', 'warning');
        return;
    }

    const producto = pedidoActualData.productos[index];

    if (!confirm(`¿Eliminar ${producto.nombre} del pedido?`)) {
        return;
    }

    // Guardar referencia para posible restauración
    const productoEliminado = { ...producto };
    const indexEliminado = index;

    // Eliminar localmente primero para UI responsive
    pedidoActualData.productos.splice(index, 1);
    actualizarVistaPanelLateral();
    mostrarNotificacion('Producto eliminado', 'success');

    // Eliminar en backend (si tiene detalle_id)
    if (producto.detalle_id) {
        try {
            const response = await fetch(`/api/caja/pedidos/detalle/${producto.detalle_id}/eliminar/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ motivo: 'Eliminado desde panel de caja' })
            });

            const data = await response.json();
            if (!data.success) {
                // Restaurar si falla
                pedidoActualData.productos.splice(indexEliminado, 0, productoEliminado);
                actualizarVistaPanelLateral();
                mostrarNotificacion(data.error || 'Error al eliminar producto', 'error');
            }
        } catch (error) {
            pedidoActualData.productos.splice(indexEliminado, 0, productoEliminado);
            actualizarVistaPanelLateral();
            mostrarNotificacion('Error al eliminar producto', 'error');
        }
    }
}

async function agregarProductoAlPedido(productoId, nombre, precio) {
    // Verificar si ya existe
    const productoExistente = pedidoActualData.productos.find(p => p.producto_id === productoId);

    if (productoExistente) {
        // Si existe, aumentar cantidad usando la función de modificar
        const index = pedidoActualData.productos.indexOf(productoExistente);
        await modificarCantidadPedido(index, 1);
        mostrarNotificacion(`Cantidad de ${nombre} aumentada`, 'success');
        return;
    }

    // Agregar localmente primero
    const nuevoProducto = {
        nombre: nombre,
        cantidad: 1,
        precio_unitario: parseFloat(precio),
        subtotal: parseFloat(precio),
        producto_id: productoId
    };

    pedidoActualData.productos.push(nuevoProducto);
    actualizarVistaPanelLateral();
    mostrarNotificacion(`${nombre} agregado`, 'success');

    // Guardar en backend
    try {
        const response = await fetch('/api/caja/pedidos/agregar-producto/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                pedido_id: pedidoActualData.id,
                producto_id: productoId,
                cantidad: 1
            })
        });

        const data = await response.json();
        if (data.success) {
            // Guardar el detalle_id para futuras modificaciones
            nuevoProducto.detalle_id = data.detalle.id;
        } else {
            // Eliminar si falla
            const index = pedidoActualData.productos.indexOf(nuevoProducto);
            pedidoActualData.productos.splice(index, 1);
            actualizarVistaPanelLateral();
            mostrarNotificacion(data.error || 'Error al agregar producto', 'error');
        }
    } catch (error) {
        const index = pedidoActualData.productos.indexOf(nuevoProducto);
        pedidoActualData.productos.splice(index, 1);
        actualizarVistaPanelLateral();
        mostrarNotificacion('Error al agregar producto', 'error');
    }
}

function calcularTotalPedidoActual() {
    if (!pedidoActualData || !pedidoActualData.productos) return 0;

    return pedidoActualData.productos.reduce((total, producto) => {
        return total + (parseFloat(producto.precio_unitario) * producto.cantidad);
    }, 0);
}

function actualizarVistaPanelLateral() {
    const listaContainer = document.getElementById('listaProductosPedido');
    const totalContainer = document.getElementById('totalPedidoActual');

    if (listaContainer) {
        listaContainer.innerHTML = renderizarProductosPedido();
    }

    if (totalContainer) {
        const total = calcularTotalPedidoActual();
        totalContainer.textContent = `Bs/ ${total.toFixed(2)}`;
    }
}

async function guardarCambiosPedido() {
    try {
        mostrarNotificacion('Cambios aplicados correctamente', 'success');
        cerrarPanelLateralMesa();
        cargarMapaMesas();
    } catch (error) {
        console.error('Error guardando cambios:', error);
        mostrarNotificacion('Error al guardar cambios', 'error');
    }
}

function cerrarPanelLateralMesa() {
    const panel = document.getElementById('panelLateralMesa');
    const overlay = document.getElementById('panelLateralOverlay');

    if (panel) {
        panel.classList.remove('abierto');
        setTimeout(() => panel.remove(), 300);
    }

    if (overlay) {
        overlay.classList.remove('visible');
        setTimeout(() => overlay.remove(), 300);
    }

    pedidoActualData = null;
}



// ============================================
// CARGAR HISTORIAL
// ============================================
async function cargarHistorial() {
    const container = document.getElementById('historialContainer');
    container.innerHTML = '<div class="loading">Cargando historial...</div>';

    try {
        const response = await fetch('/api/caja/pedidos/pagados/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        if (!response.ok) throw new Error('Error al cargar historial');

        const data = await response.json();
        const pedidosPagados = data.pedidos || [];

        if (pedidosPagados.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class='bx bx-history'></i>
                    <h3>No hay transacciones registradas</h3>
                    <p>Los pedidos pagados aparecerán aquí</p>
                </div>
            `;
            return;
        }

        // Renderizar historial
        let html = `
            <div class="historial-header">
                <h3>Historial de Transacciones</h3>
                <p class="historial-count">Total: ${pedidosPagados.length} transacciones</p>
            </div>
            <div class="historial-lista">
        `;

        pedidosPagados.forEach(pedido => {
            const fecha = new Date(pedido.fecha_pago);
            const fechaFormateada = fecha.toLocaleDateString('es-BO', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
            const horaFormateada = fecha.toLocaleTimeString('es-BO', {
                hour: '2-digit',
                minute: '2-digit'
            });

            html += `
                <div class="historial-item">
                    <div class="historial-icon">
                        <i class='bx bx-check-circle'></i>
                    </div>
                    <div class="historial-info">
                        <div class="historial-titulo">
                            <strong>Pedido #${pedido.id}</strong>
                            <span class="historial-mesa">Mesa ${pedido.mesa}</span>
                        </div>
                        <div class="historial-detalles">
                            <span><i class='bx bx-calendar'></i> ${fechaFormateada}</span>
                            <span><i class='bx bx-time'></i> ${horaFormateada}</span>
                            <span><i class='bx bx-credit-card'></i> ${pedido.forma_pago || 'N/A'}</span>
                            <span><i class='bx bx-user'></i> ${pedido.cajero || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="historial-total">
                        Bs/ ${parseFloat(pedido.total_final).toFixed(2)}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;

    } catch (error) {
        console.error('Error cargando historial:', error);
        container.innerHTML = '<p style="color: red;">Error al cargar historial</p>';
    }
}

async function cargarAlertasStock() {
    const container = document.getElementById('alertasStockContainer');
    container.innerHTML = '<div class="loading">Cargando alertas de stock...</div>';

    try {
        const response = await fetch('/api/caja/alertas-stock/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        if (!response.ok) throw new Error('Error al cargar alertas de stock');

        const data = await response.json();

        if (!data.alertas || data.alertas.length === 0) {
            container.innerHTML = `
                <div class="card" style="text-align: center; padding: 60px;">
                    <i class='bx bx-check-circle' style="font-size: 4em; color: var(--success);"></i>
                    <h3 style="margin-top: 20px;">No hay alertas de stock</h3>
                    <p style="color: var(--text-secondary);">Todos los productos tienen stock suficiente</p>
                </div>
            `;
            // Actualizar badge del sidebar
            const badge = document.getElementById('badgeStock');
            if (badge) badge.textContent = '0';
            return;
        }

        // Actualizar badge del sidebar
        const badge = document.getElementById('badgeStock');
        if (badge) badge.textContent = data.total_alertas;

        // Renderizar alertas
        let html = '<div class="alertas-grid">';

        data.alertas.forEach(alerta => {
            const tipoIcon = alerta.tipo_alerta === 'agotado' ? 'bx-x-circle' : 'bx-error';
            const tipoColor = alerta.tipo_alerta === 'agotado' ? 'var(--danger)' : 'var(--warning)';
            const tipoTexto = alerta.tipo_alerta === 'agotado' ? 'Agotado' : 'Stock Bajo';

            html += `
                <div class="card alerta-card" data-alerta-id="${alerta.id}">
                    <div class="alerta-header">
                        <i class='bx ${tipoIcon}' style="font-size: 2em; color: ${tipoColor};"></i>
                        <span class="badge" style="background: ${tipoColor};">${tipoTexto}</span>
                    </div>
                    <div class="alerta-body">
                        <h3>${alerta.producto}</h3>
                        <div class="alerta-stats">
                            <div class="stat">
                                <span class="label">Stock Actual:</span>
                                <span class="value" style="color: ${tipoColor}; font-weight: bold;">
                                    ${alerta.stock_actual}
                                </span>
                            </div>
                            <div class="stat">
                                <span class="label">Stock Mínimo:</span>
                                <span class="value">${alerta.stock_minimo}</span>
                            </div>
                        </div>
                        <p class="alerta-fecha">
                            <i class='bx bx-time-five'></i>
                            ${new Date(alerta.fecha_creacion).toLocaleString('es-ES')}
                        </p>
                    </div>
                    <div class="alerta-actions">
                        <button class="btn btn-primary" onclick="resolverAlerta(${alerta.id})">
                            <i class='bx bx-check'></i> Resolver
                        </button>
                        <button class="btn btn-outline" onclick="verProducto(${alerta.producto_id})">
                            <i class='bx bx-info-circle'></i> Ver Producto
                        </button>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;

    } catch (error) {
        console.error('Error al cargar alertas de stock:', error);
        container.innerHTML = `
            <div class="card error">
                <i class='bx bx-error-circle'></i>
                <p>Error al cargar alertas de stock</p>
                <button class="btn btn-primary" onclick="cargarAlertasStock()">
                    <i class='bx bx-refresh'></i> Reintentar
                </button>
            </div>
        `;
    }
}

async function resolverAlerta(alertaId) {
    if (!confirm('¿Marcar esta alerta como resuelta? Esto indica que ya se ha tomado acción sobre el stock.')) {
        return;
    }

    try {
        const response = await fetch(`/api/caja/alertas-stock/${alertaId}/resolver/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        const data = await response.json();

        if (data.success) {
            mostrarNotificacion('Alerta marcada como resuelta', 'success');
            cargarAlertasStock(); // Recargar lista
        } else {
            mostrarNotificacion(data.error || 'Error al resolver alerta', 'error');
        }

    } catch (error) {
        console.error('Error al resolver alerta:', error);
        mostrarNotificacion('Error de conexión al resolver alerta', 'error');
    }
}

function verProducto(productoId) {
    mostrarNotificacion('Funcionalidad de ver producto en desarrollo', 'info');
    // TODO: Implementar modal con detalles del producto
}

async function cargarPersonal() {
    const container = document.getElementById('personalContainer');
    container.innerHTML = '<div class="loading">Cargando empleados...</div>';

    try {
        const response = await fetch('/api/caja/empleados/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        if (!response.ok) throw new Error('Error al cargar empleados');

        const data = await response.json();

        if (!data.empleados || data.empleados.length === 0) {
            container.innerHTML = `
                <div class="card" style="text-align: center; padding: 60px;">
                    <i class='bx bx-user' style="font-size: 4em; color: var(--text-secondary);"></i>
                    <h3 style="margin-top: 20px;">No hay empleados registrados</h3>
                    <p style="color: var(--text-secondary);">Contacta al administrador para crear empleados</p>
                </div>
            `;
            return;
        }

        // Filtrar solo empleados que necesitan QR (NO cajeros)
        const empleadosConQR = data.empleados.filter(emp => emp.rol.toLowerCase() !== 'cajero');

        if (empleadosConQR.length === 0) {
            container.innerHTML = `
                <div class="card" style="text-align: center; padding: 60px;">
                    <i class='bx bx-qr-scan' style="font-size: 4em; color: var(--text-secondary);"></i>
                    <h3 style="margin-top: 20px;">No hay personal con acceso QR</h3>
                    <p style="color: var(--text-secondary);">Los empleados con QR aparecerán aquí</p>
                </div>
            `;
            return;
        }

        // Renderizar empleados sin agrupar por rol
        let html = `
            <div class="personal-qr-container">
                <div class="personal-qr-header">
                    <i class='bx bx-qr-scan' style="font-size: 32px; color: var(--primary-color);"></i>
                    <div>
                        <h3>Personal - Generar QR</h3>
                        <p>${empleadosConQR.length} empleado${empleadosConQR.length !== 1 ? 's' : ''} con acceso QR</p>
                    </div>
                </div>
                <div class="empleados-qr-grid">
                    ${empleadosConQR.map(emp => `
                        <div class="empleado-qr-card">
                            <div class="empleado-avatar">
                                <i class='bx bx-user-circle'></i>
                            </div>
                            <div class="empleado-nombre">
                                <h4>${emp.nombre_completo}</h4>
                                <p class="empleado-username">@${emp.username}</p>
                            </div>
                            <button class="btn-generar-qr-simple" onclick="generarQREmpleado(${emp.id}, '${emp.nombre_completo}')">
                                <i class='bx bx-qr-scan'></i>
                                Generar QR
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        container.innerHTML = html;

    } catch (error) {
        console.error('Error:', error);
        container.innerHTML = `
            <div class="card" style="text-align: center; padding: 40px;">
                <p style="color: var(--danger-color);">Error al cargar empleados</p>
                <button class="btn btn-primary" onclick="cargarPersonal()" style="margin-top: 20px;">
                    <i class='bx bx-refresh'></i> Reintentar
                </button>
            </div>
        `;
    }
}

// ✅ NUEVO: Generar QR para empleado
async function generarQREmpleado(empleadoId, nombreEmpleado) {
    try {
        const response = await fetch('/usuarios/generar-qr/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                empleado_id: empleadoId
            })
        });

        const data = await response.json();

        if (!data.success) {
            mostrarNotificacion(data.error || 'Error al generar QR', 'error');
            return;
        }

        // Mostrar QR en un modal
        mostrarModalQR(data.qr_url, nombreEmpleado, data.empleado.rol);
        mostrarNotificacion(data.message, 'success');

    } catch (error) {
        console.error('[ERROR] Error al generar QR:', error);
        mostrarNotificacion('Error al generar código QR', 'error');
    }
}

function mostrarModalQR(qrUrl, nombreEmpleado, rol) {
    const modalBody = document.getElementById('modalBody');

    modalBody.innerHTML = `
        <div class="qr-modal-content">
            <div class="qr-modal-header">
                <i class='bx bx-qr-scan' style="font-size: 48px; color: var(--primary-color);"></i>
                <h2>Código QR Generado</h2>
                <p class="qr-modal-subtitle">${nombreEmpleado} - ${rol}</p>
            </div>

            <div class="qr-modal-body">
                <div class="qr-container-modal" id="qrCodeContainer"></div>
                <div class="qr-instrucciones">
                    <div class="qr-instruccion-item">
                        <i class='bx bx-check-circle'></i>
                        <span>El código QR ha sido generado exitosamente</span>
                    </div>
                    <div class="qr-instruccion-item">
                        <i class='bx bx-mobile'></i>
                        <span>Escanea con tu dispositivo móvil para iniciar sesión</span>
                    </div>
                    <div class="qr-instruccion-item">
                        <i class='bx bx-refresh'></i>
                        <span>Al escanear, este QR se invalidará y se generará uno nuevo</span>
                    </div>
                </div>
            </div>

            <div class="qr-modal-footer">
                <button class="btn btn-secondary" onclick="cerrarModal()">
                    <i class='bx bx-x'></i>
                    Cerrar
                </button>
            </div>
        </div>
    `;

    // Mostrar modal primero
    const modalElement = document.getElementById('modalDetallePedido');
    if (modalElement) {
        modalElement.style.display = 'flex';
    }

    // Generar QR después de que el modal esté visible
    setTimeout(() => {
        const qrContainer = document.getElementById('qrCodeContainer');
        if (qrContainer) {
            new QRCode(qrContainer, {
                text: qrUrl,
                width: 256,
                height: 256,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });
        }
    }, 100);
}

async function cargarJornada() {
    const container = document.getElementById('jornadaContainer');
    container.innerHTML = '<div class="loading">Cargando jornada...</div>';

    try {
        const response = await fetch('/api/caja/jornada/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        if (!response.ok) throw new Error('Error al cargar jornada');

        const data = await response.json();

        if (data.hay_jornada_activa) {
            // Hay jornada activa - mostrar información y botón de finalizar
            container.innerHTML = `
                <div class="jornada-activa">
                    <div class="jornada-header">
                        <div class="jornada-status activo">
                            <i class='bx bx-time-five'></i>
                            <span>JORNADA ACTIVA</span>
                        </div>
                    </div>

                    <div class="jornada-info-grid">
                        <div class="jornada-info-item">
                            <div class="jornada-icon calendar">
                                <i class='bx bx-calendar'></i>
                            </div>
                            <div class="jornada-info-content">
                                <label>Fecha</label>
                                <span>${formatearFecha(data.jornada.fecha)}</span>
                            </div>
                        </div>

                        <div class="jornada-info-item">
                            <div class="jornada-icon time">
                                <i class='bx bx-time'></i>
                            </div>
                            <div class="jornada-info-content">
                                <label>Hora de Inicio</label>
                                <span>${data.jornada.hora_inicio}</span>
                            </div>
                        </div>

                        <div class="jornada-info-item">
                            <div class="jornada-icon timer">
                                <i class='bx bx-timer'></i>
                            </div>
                            <div class="jornada-info-content">
                                <label>Duracion</label>
                                <span>${data.jornada.duracion}</span>
                            </div>
                        </div>

                        <div class="jornada-info-item">
                            <div class="jornada-icon user">
                                <i class='bx bx-user'></i>
                            </div>
                            <div class="jornada-info-content">
                                <label>Iniciado por</label>
                                <span>${data.jornada.cajero}</span>
                            </div>
                        </div>
                    </div>

                    ${data.jornada.observaciones_apertura ? `
                        <div class="jornada-observaciones">
                            <label><i class='bx bx-note'></i> Observaciones de Apertura:</label>
                            <p>${data.jornada.observaciones_apertura}</p>
                        </div>
                    ` : ''}

                    <div class="jornada-acciones">
                        <button class="btn btn-danger btn-lg" onclick="abrirModalFinalizarJornada()">
                            <i class='bx bx-stop-circle'></i>
                            Finalizar Jornada
                        </button>
                    </div>
                </div>
            `;
        } else {
            // No hay jornada activa - mostrar botón de iniciar
            container.innerHTML = `
                <div class="jornada-inactiva">
                    <div class="jornada-empty-state">
                        <i class='bx bx-calendar-x'></i>
                        <h3>No hay jornada laboral activa</h3>
                        <p>Inicia una nueva jornada para comenzar a trabajar</p>
                    </div>

                    <div class="jornada-acciones">
                        <button class="btn btn-success btn-lg" onclick="abrirModalIniciarJornada()">
                            <i class='bx bx-play-circle'></i>
                            Iniciar Jornada
                        </button>
                    </div>
                </div>
            `;
        }

    } catch (error) {
        console.error('Error cargando jornada:', error);
        container.innerHTML = `
            <div class="error-container">
                <i class='bx bx-error-circle'></i>
                <p style="color: var(--danger-color);">Error al cargar jornada</p>
                <button class="btn btn-primary" onclick="cargarJornada()" style="margin-top: 20px;">
                    <i class='bx bx-refresh'></i> Reintentar
                </button>
            </div>
        `;
    }
}

function formatearFecha(fechaStr) {
    const fecha = new Date(fechaStr + 'T00:00:00');
    const dias = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

    return `${dias[fecha.getDay()]}, ${fecha.getDate()} de ${meses[fecha.getMonth()]} ${fecha.getFullYear()}`;
}

function abrirModalIniciarJornada() {
    // Eliminar modal existente si hay
    const modalExistente = document.getElementById('modalIniciarJornada');
    if (modalExistente) {
        modalExistente.remove();
    }

    const modalHTML = `
        <div class="modal" id="modalIniciarJornada" style="display: flex;" onclick="cerrarModalJornada(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h2><i class='bx bx-play-circle'></i> Iniciar Jornada Laboral</h2>
                    <button class="modal-close" onclick="cerrarModalJornada()">&times;</button>
                </div>
                <div class="modal-body">
                    <p style="margin-bottom: 20px;">¿Estás seguro que deseas iniciar una nueva jornada laboral?</p>

                    <div class="form-group">
                        <label>Observaciones (opcional)</label>
                        <textarea
                            id="observacionesInicioJornada"
                            class="form-control"
                            rows="3"
                            placeholder="Ej: Inicio de turno mañana..."></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="cerrarModalJornada()">
                        <i class='bx bx-x'></i> Cancelar
                    </button>
                    <button class="btn btn-success" onclick="iniciarJornada()">
                        <i class='bx bx-play-circle'></i> Iniciar Jornada
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function abrirModalFinalizarJornada() {
    // Eliminar modal existente si hay
    const modalExistente = document.getElementById('modalFinalizarJornada');
    if (modalExistente) {
        modalExistente.remove();
    }

    const modalHTML = `
        <div class="modal" id="modalFinalizarJornada" style="display: flex;" onclick="cerrarModalJornada(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h2><i class='bx bx-stop-circle'></i> Finalizar Jornada Laboral</h2>
                    <button class="modal-close" onclick="cerrarModalJornada()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="alerta-warning">
                        <i class='bx bx-info-circle'></i>
                        <p>Al finalizar la jornada, se verificará que no haya pedidos pendientes de pago.</p>
                    </div>

                    <div class="form-group" style="margin-top: 20px;">
                        <label>Observaciones de Cierre (opcional)</label>
                        <textarea
                            id="observacionesCierreJornada"
                            class="form-control"
                            rows="3"
                            placeholder="Ej: Sin novedades, todo en orden..."></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="cerrarModalJornada()">
                        <i class='bx bx-x'></i> Cancelar
                    </button>
                    <button class="btn btn-danger" onclick="finalizarJornada()">
                        <i class='bx bx-stop-circle'></i> Finalizar Jornada
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function cerrarModalJornada(event) {
    if (event && event.target !== event.currentTarget) return;

    const modales = document.querySelectorAll('#modalIniciarJornada, #modalFinalizarJornada');
    modales.forEach(modal => modal.remove());
}

async function iniciarJornada() {
    try {
        const observaciones = document.getElementById('observacionesInicioJornada').value.trim();

        const response = await fetch('/api/caja/jornada/iniciar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ observaciones })
        });

        const data = await response.json();

        if (data.success) {
            mostrarNotificacion(data.message, 'success');
            cerrarModalJornada();
            cargarJornada();
        } else {
            mostrarNotificacion(data.error, 'error');
        }

    } catch (error) {
        console.error('Error iniciando jornada:', error);
        mostrarNotificacion('Error al iniciar jornada', 'error');
    }
}

async function finalizarJornada() {
    try {
        const observaciones = document.getElementById('observacionesCierreJornada').value.trim();

        const response = await fetch('/api/caja/jornada/finalizar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ observaciones })
        });

        const data = await response.json();

        if (data.success) {
            mostrarNotificacion(data.message, 'success');
            cerrarModalJornada();
            cargarJornada();
        } else {
            mostrarNotificacion(data.error, 'error');
        }

    } catch (error) {
        console.error('Error finalizando jornada:', error);
        mostrarNotificacion('Error al finalizar jornada', 'error');
    }
}

// ============================================
// TURNO DE CAJA (CierreCaja)
// ============================================

function abrirModalTurno() {
    // Eliminar modal existente si hay
    const modalExistente = document.getElementById('modalAbrirTurno');
    if (modalExistente) {
        modalExistente.remove();
    }

    const modalHTML = `
        <div class="modal" id="modalAbrirTurno" style="display: flex;" onclick="cerrarModalTurno(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h2><i class='bx bx-store-alt'></i> Abrir Turno de Caja</h2>
                    <button class="modal-close" onclick="cerrarModalTurno()">&times;</button>
                </div>
                <div class="modal-body">
                    <p style="margin-bottom: 20px;">Selecciona el turno y registra el efectivo inicial</p>

                    <div class="form-group">
                        <label>Tipo de Turno *</label>
                        <select id="tipoTurno" class="form-control">
                            <option value="manana">Mañana (06:00 - 14:00)</option>
                            <option value="tarde">Tarde (14:00 - 22:00)</option>
                            <option value="noche">Noche (22:00 - 06:00)</option>
                            <option value="completo">Día Completo</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Efectivo Inicial (Bs/)</label>
                        <input
                            type="number"
                            id="efectivoInicial"
                            class="form-control"
                            placeholder="0.00"
                            step="0.01"
                            min="0"
                            value="0">
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="cerrarModalTurno()">
                        <i class='bx bx-x'></i> Cancelar
                    </button>
                    <button class="btn btn-success" onclick="confirmarAbrirTurno()">
                        <i class='bx bx-check-circle'></i> Abrir Turno
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function cerrarModalTurno(event) {
    if (event && event.target !== event.currentTarget) return;

    const modal = document.getElementById('modalAbrirTurno');
    if (modal) {
        modal.remove();
    }
}

async function confirmarAbrirTurno() {
    try {
        const tipoTurno = document.getElementById('tipoTurno').value;
        const efectivoInicial = document.getElementById('efectivoInicial').value || '0';

        const response = await fetch('/api/caja/turno/abrir/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                turno: tipoTurno,
                efectivo_inicial: parseFloat(efectivoInicial)
            })
        });

        const data = await response.json();

        if (data.success) {
            mostrarNotificacion(data.message, 'success');
            cerrarModalTurno();
            // Recargar página para actualizar header
            location.reload();
        } else {
            mostrarNotificacion(data.error, 'error');
        }

    } catch (error) {
        console.error('Error abriendo turno:', error);
        mostrarNotificacion('Error al abrir turno', 'error');
    }
}

// Auto-actualización cada 30 segundos
setInterval(() => {
    const currentSection = document.querySelector('.content-section.active');
    if (currentSection && currentSection.id === 'section-dashboard') {
        cargarDashboard();
    } else if (currentSection && currentSection.id === 'section-pedidos') {
        cargarPedidos();
    }
}, 30000);

// Cargar datos iniciales
cargarDashboard();

console.log('✅ Panel Unificado de Caja cargado correctamente');

// ============================================
// TABLERO KANBAN - ESTADO DE PEDIDOS
// ============================================
let kanbanTimerInterval = null;

async function cargarKanban() {
    try {
        const response = await fetch('/api/caja/pedidos/kanban/', {
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (!response.ok) throw new Error('Error al cargar kanban');

        const data = await response.json();

        // Actualizar cada columna
        ['pedido', 'preparando', 'listo', 'entregado'].forEach(estado => {
            const pedidos = data[estado] || [];
            renderizarColumnaKanban(estado, pedidos);
        });

        // ✅ NUEVO: Iniciar actualización del temporizador cada segundo
        iniciarTimerKanban();

    } catch (error) {
        console.error('[DEBUG] Error al cargar kanban:', error);
        mostrarNotificacion('Error al cargar estado de pedidos', 'error');
    }
}

// ✅ NUEVO: Función para actualizar temporizadores en tiempo real
function iniciarTimerKanban() {
    // Limpiar intervalo anterior si existe
    if (kanbanTimerInterval) {
        clearInterval(kanbanTimerInterval);
    }

    // Actualizar cada segundo (excepto ENTREGADO que ya no cuenta)
    kanbanTimerInterval = setInterval(() => {
        const tarjetas = document.querySelectorAll('.kanban-card[data-estado]:not([data-estado="entregado"])');

        tarjetas.forEach(tarjeta => {
            const tiempoTotal = parseInt(tarjeta.dataset.tiempoTotal || 0);
            const nuevoTiempo = tiempoTotal + 1;

            // Actualizar data attribute
            tarjeta.dataset.tiempoTotal = nuevoTiempo;

            // Calcular minutos y segundos
            const minutos = Math.floor(nuevoTiempo / 60);
            const segundos = nuevoTiempo % 60;

            // Actualizar display
            const timerElement = tarjeta.querySelector('.kanban-timer-valor');
            if (timerElement) {
                timerElement.textContent = `${minutos}:${segundos.toString().padStart(2, '0')}`;
            }

            // Agregar alerta si pasa 20 minutos
            const timerContainer = tarjeta.querySelector('.kanban-timer');
            if (timerContainer && minutos >= 20) {
                timerContainer.classList.add('kanban-timer-alerta');
            }
        });
    }, 1000);
}

function renderizarColumnaKanban(estado, pedidos) {
    const container = document.getElementById(`items-${estado}`);
    const countElement = document.getElementById(`count-${estado}`);

    // Actualizar contador
    countElement.textContent = pedidos.length;

    if (pedidos.length === 0) {
        container.innerHTML = `
            <div class="empty">
                <i class='bx bx-package'></i>
                <p>Sin pedidos</p>
            </div>
        `;
        return;
    }

    // Ordenar: PEDIDO, PREPARANDO, LISTO usan FIFO (más antiguo primero)
    // ENTREGADO usa LIFO (más reciente primero)
    if (estado === 'entregado') {
        pedidos.reverse(); // Invertir para LIFO
    }

    container.innerHTML = pedidos.map(pedido => crearTarjetaKanban(pedido, estado)).join('');
}

function crearTarjetaKanban(pedido, estado) {
    // Agrupar productos por categoría
    const productosPorCategoria = {};

    pedido.productos.forEach(p => {
        const categoria = p.categoria || 'Sin Categoría';
        if (!productosPorCategoria[categoria]) {
            productosPorCategoria[categoria] = [];
        }
        productosPorCategoria[categoria].push(p);
    });

    // Iconos por categoría (puedes personalizarlos)
    const iconosCategoria = {
        'Bebidas': '🥤',
        'Comidas': '🍽️',
        'Postres': '🍰',
        'Entradas': '🥗',
        'Platos Principales': '🍲',
        'Sin Categoría': '📦'
    };

    // Generar HTML de productos agrupados
    const productosHTML = Object.entries(productosPorCategoria).map(([categoria, productos]) => `
        <div class="kanban-categoria">
            <div class="kanban-categoria-titulo">
                <span>${iconosCategoria[categoria] || '📦'}</span>
                <span>${categoria.toUpperCase()}</span>
            </div>
            ${productos.map(p => `
                <div class="kanban-producto-item">• ${p.nombre} x${p.cantidad}</div>
            `).join('')}
        </div>
    `).join('');

    // ✅ NUEVO: Calcular y formatear temporizador
    const minutos = pedido.tiempo_minutos || 0;
    const segundos = pedido.tiempo_segundos || 0;
    const tiempoFormateado = `${minutos}:${segundos.toString().padStart(2, '0')}`;
    const claseAlerta = pedido.alerta_20min ? 'kanban-timer-alerta' : '';

    // ✅ NUEVO: Solo avanzar, nunca retroceder
    const puedeAvanzar = estado !== 'entregado';

    const botonesHTML = puedeAvanzar ? `
        <div class="kanban-card-actions">
            <button class="kanban-btn kanban-btn-next"
                    onclick="cambiarEstadoKanban(${pedido.id}, '${estado}', 'next')">
                <i class='bx bx-chevron-right'></i>
            </button>
        </div>
    ` : '';

    return `
        <div class="kanban-card" data-pedido-id="${pedido.id}" data-estado="${estado}" data-tiempo-total="${pedido.tiempo_total_segundos || 0}">
            <div class="kanban-card-header">
                <span class="kanban-card-mesa">Mesa ${pedido.mesa || 'N/A'}</span>
                <span class="kanban-card-total">Bs/ ${parseFloat(pedido.total).toFixed(2)}</span>
            </div>
            <div class="kanban-card-productos">
                ${productosHTML}
            </div>
            <div class="kanban-card-footer">
                <div class="kanban-mesero">
                    <i class='bx bx-user'></i>
                    <span>${pedido.mesero || 'N/A'}</span>
                </div>
                <div class="kanban-timer ${claseAlerta}" data-pedido-id="${pedido.id}">
                    <i class='bx bx-timer'></i>
                    <span class="kanban-timer-valor">${tiempoFormateado}</span>
                </div>
            </div>
            ${botonesHTML}
        </div>
    `;
}

async function cambiarEstadoKanban(pedidoId, estadoActual, direccion) {
    const estados = ['pedido', 'preparando', 'listo', 'entregado'];
    const indexActual = estados.indexOf(estadoActual);

    // ✅ NUEVO: Solo permitir avanzar (next), nunca retroceder (prev)
    if (direccion === 'prev') {
        mostrarNotificacion('No se puede retroceder el estado de un pedido', 'error');
        return;
    }

    const nuevoIndex = Math.min(estados.length - 1, indexActual + 1);
    const nuevoEstado = estados[nuevoIndex];

    if (nuevoEstado === estadoActual) return;

    try {
        const response = await fetch(`/api/caja/pedidos/${pedidoId}/cambiar-estado/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ estado: nuevoEstado })
        });

        if (!response.ok) throw new Error('Error al cambiar estado');

        // Recargar kanban
        await cargarKanban();
        mostrarNotificacion(`Pedido movido a ${nuevoEstado.toUpperCase()}`, 'success');

    } catch (error) {
        console.error('[DEBUG] Error al cambiar estado:', error);
        mostrarNotificacion('Error al cambiar estado del pedido', 'error');
    }
}

// ============================================
// FUNCIONES DE MAPA DE MESAS
// ============================================

async function abrirModalPago(mesaId, pagoSeparado) {
    try {
        // Obtener pedido pendiente de la mesa
        const response = await fetch('/api/caja/pedidos/pendientes/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        const data = await response.json();
        if (!data.success) {
            mostrarNotificacion('Error al cargar pedido', 'error');
            return;
        }

        const pedido = data.pedidos.find(p => p.mesa_id === mesaId);
        if (!pedido) {
            mostrarNotificacion('No hay pedido pendiente en esta mesa', 'error');
            return;
        }

        if (pagoSeparado) {
            // Pago separado - mostrar productos para seleccionar
            abrirModalPagoSeparado(pedido);
        } else {
            // Pago total - mostrar formulario de pago directo
            document.getElementById('modalDetallePedido').style.display = 'flex';
            await procesarPago(pedido.id, pedido.total_final);
        }
    } catch (error) {
        console.error('Error al abrir modal de pago:', error);
        mostrarNotificacion('Error al procesar pago', 'error');
    }
}

async function abrirModalPagoSeparado(pedido) {
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div class="pago-separado-container">
            <h3>Pago Separado - Pedido #${pedido.id} - Mesa ${pedido.mesa}</h3>
            <p class="subtitle">Selecciona los productos y cantidad a pagar</p>

            <div class="productos-separado-lista">
                ${pedido.productos.map((producto, index) => `
                    <div class="producto-separado-item">
                        <div class="producto-info">
                            <span class="producto-nombre">${producto.nombre}</span>
                            <span class="producto-precio-unit">Bs/ ${producto.precio_unitario.toFixed(2)} c/u</span>
                        </div>
                        <div class="cantidad-selector">
                            <button class="btn-cantidad" onclick="cambiarCantidadSeparado(${index}, -1, ${producto.cantidad}, ${producto.precio_unitario})">
                                <i class='bx bx-minus'></i>
                            </button>
                            <input type="number"
                                   id="cant_${index}"
                                   class="cantidad-input"
                                   value="0"
                                   min="0"
                                   max="${producto.cantidad}"
                                   data-precio-unit="${producto.precio_unitario}"
                                   data-max="${producto.cantidad}"
                                   onchange="validarCantidadSeparado(${index}, ${producto.cantidad})"
                                   readonly>
                            <span class="cantidad-max">/ ${producto.cantidad}</span>
                            <button class="btn-cantidad" onclick="cambiarCantidadSeparado(${index}, 1, ${producto.cantidad}, ${producto.precio_unitario})">
                                <i class='bx bx-plus'></i>
                            </button>
                        </div>
                        <div class="producto-subtotal">
                            <span id="subtotal_${index}">Bs/ 0.00</span>
                        </div>
                    </div>
                `).join('')}
            </div>

            <div class="total-separado">
                <h3>Total Seleccionado: <span id="totalSeparado">Bs/ 0.00</span></h3>
            </div>

            <div class="form-actions">
                <button class="btn btn-success btn-lg" onclick="continuarPagoSeparado(${pedido.id})">
                    <i class='bx bx-check'></i> Continuar al Pago
                </button>
                <button class="btn btn-secondary" onclick="cerrarModal()">
                    <i class='bx bx-x'></i> Cancelar
                </button>
            </div>
        </div>
    `;

    document.getElementById('modalDetallePedido').style.display = 'flex';
}

function cambiarCantidadSeparado(index, cambio, maxCantidad, precioUnitario) {
    const input = document.getElementById(`cant_${index}`);
    let cantidad = parseInt(input.value) || 0;

    cantidad += cambio;

    // Validar límites
    if (cantidad < 0) cantidad = 0;
    if (cantidad > maxCantidad) cantidad = maxCantidad;

    input.value = cantidad;

    // Actualizar subtotal del producto
    const subtotal = cantidad * precioUnitario;
    document.getElementById(`subtotal_${index}`).textContent = `Bs/ ${subtotal.toFixed(2)}`;

    // Actualizar total general
    actualizarTotalSeparado();
}

function validarCantidadSeparado(index, maxCantidad) {
    const input = document.getElementById(`cant_${index}`);
    let cantidad = parseInt(input.value) || 0;

    if (cantidad < 0) cantidad = 0;
    if (cantidad > maxCantidad) cantidad = maxCantidad;

    input.value = cantidad;
    actualizarTotalSeparado();
}

function actualizarTotalSeparado() {
    const inputs = document.querySelectorAll('.cantidad-input');
    let total = 0;

    inputs.forEach(input => {
        const cantidad = parseInt(input.value) || 0;
        const precioUnit = parseFloat(input.dataset.precioUnit) || 0;
        total += cantidad * precioUnit;
    });

    document.getElementById('totalSeparado').textContent = `Bs/ ${total.toFixed(2)}`;
}

async function continuarPagoSeparado(pedidoId) {
    const inputs = document.querySelectorAll('.cantidad-input');
    let total = 0;
    let hayProductos = false;

    inputs.forEach(input => {
        const cantidad = parseInt(input.value) || 0;
        if (cantidad > 0) {
            hayProductos = true;
            const precioUnit = parseFloat(input.dataset.precioUnit) || 0;
            total += cantidad * precioUnit;
        }
    });

    if (!hayProductos) {
        mostrarNotificacion('Selecciona al menos un producto con cantidad mayor a 0', 'error');
        return;
    }

    // Mostrar formulario de pago con el total calculado
    await procesarPago(pedidoId, total);
}

async function abrirModalCambiarMesa(mesaIdActual) {
    try {
        // Obtener todas las mesas disponibles
        const response = await fetch('/api/caja/mapa-mesas/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        const data = await response.json();
        if (!data.success) {
            mostrarNotificacion('Error al cargar mesas', 'error');
            return;
        }

        // Obtener pedido de la mesa actual
        const pedidosResponse = await fetch('/api/caja/pedidos/pendientes/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        const pedidosData = await pedidosResponse.json();
        const pedido = pedidosData.pedidos.find(p => p.mesa_id === mesaIdActual);

        if (!pedido) {
            mostrarNotificacion('No hay pedido en esta mesa', 'error');
            return;
        }

        // Filtrar solo mesas disponibles
        const mesasDisponibles = data.mesas.filter(m =>
            m.estado === 'disponible' && m.id !== mesaIdActual
        );

        const modalBody = document.getElementById('modalBody');
        modalBody.innerHTML = `
            <div class="cambiar-mesa-container">
                <h3>Cambiar Mesa - Pedido #${pedido.id}</h3>
                <p class="subtitle">Mesa actual: <strong>Mesa ${pedido.mesa}</strong></p>
                <p>Selecciona la nueva mesa:</p>

                <div class="mesas-grid">
                    ${mesasDisponibles.map(mesa => `
                        <button class="mesa-option"
                                data-pedido-id="${pedido.id}"
                                data-mesa-actual-id="${mesaIdActual}"
                                data-mesa-nueva-id="${mesa.id}"
                                data-mesa-numero="${mesa.numero}"
                                onclick="confirmarCambioMesa(this.dataset.pedidoId, this.dataset.mesaActualId, this.dataset.mesaNuevaId, this.dataset.mesaNumero)">
                            <i class='bx bx-table'></i>
                            <span>Mesa ${mesa.numero}</span>
                            <small>Capacidad: ${mesa.capacidad}</small>
                        </button>
                    `).join('')}
                </div>

                ${mesasDisponibles.length === 0 ? `
                    <div class="empty-state">
                        <i class='bx bx-error'></i>
                        <p>No hay mesas disponibles</p>
                    </div>
                ` : ''}

                <div class="form-actions">
                    <button class="btn btn-secondary" onclick="cerrarModal()">
                        <i class='bx bx-x'></i> Cancelar
                    </button>
                </div>
            </div>
        `;

        document.getElementById('modalDetallePedido').style.display = 'flex';
    } catch (error) {
        console.error('Error al abrir modal cambiar mesa:', error);
        mostrarNotificacion('Error al cargar mesas', 'error');
    }
}

async function confirmarCambioMesa(pedidoId, mesaActualId, mesaNuevaId, mesaNuevoNumero) {
    try {
        const response = await fetch('/api/caja/pedidos/reasignar-mesa/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                pedido_id: pedidoId,
                mesa_id: mesaNuevaId,
                motivo: 'Cambio solicitado desde panel de caja'
            })
        });

        const data = await response.json();

        if (data.success) {
            mostrarNotificacion(`Pedido reasignado a Mesa ${mesaNuevoNumero}`, 'success');
            cerrarModal();
            cerrarPanelLateralMesa();
            cargarMapaMesas(); // Recargar mapa
        } else {
            mostrarNotificacion(data.error || 'Error al cambiar mesa', 'error');
        }
    } catch (error) {
        console.error('Error al cambiar mesa:', error);
        mostrarNotificacion('Error al cambiar mesa', 'error');
    }
}

// ============================================
// EXPONER FUNCIONES AL SCOPE GLOBAL
// ============================================
// Las funciones usadas en onclick deben estar en window
window.navigateTo = navigateTo;
window.expandirMesa = expandirMesa;
window.abrirModalPago = abrirModalPago;
window.abrirModalCambiarMesa = abrirModalCambiarMesa;
window.cerrarPanelLateralMesa = cerrarPanelLateralMesa;
window.modificarCantidadPedido = modificarCantidadPedido;
window.eliminarProductoDePedido = eliminarProductoDePedido;
window.agregarProductoAlPedido = agregarProductoAlPedido;
window.guardarCambiosPedido = guardarCambiosPedido;
window.toggleCategoria = toggleCategoria;
window.filtrarProductos = filtrarProductos;
window.cambiarCantidadSeparado = cambiarCantidadSeparado;
window.validarCantidadSeparado = validarCantidadSeparado;
window.actualizarTotalSeparado = actualizarTotalSeparado;
window.continuarPagoSeparado = continuarPagoSeparado;
window.confirmarCambioMesa = confirmarCambioMesa;
window.verDetallePedido = verDetallePedido;
window.procesarPago = procesarPago;
window.confirmarPago = confirmarPago;
window.calcularCambio = calcularCambio;
window.cerrarModal = cerrarModal;
window.mostrarNotificacion = mostrarNotificacion;
window.cargarDashboard = cargarDashboard;
window.cargarPedidos = cargarPedidos;
window.cargarMapaMesas = cargarMapaMesas;
window.cargarHistorial = cargarHistorial;
window.cargarPersonal = cargarPersonal;
window.generarQREmpleado = generarQREmpleado;
window.cargarJornada = cargarJornada;
window.abrirModalIniciarJornada = abrirModalIniciarJornada;
window.abrirModalFinalizarJornada = abrirModalFinalizarJornada;
window.cerrarModalJornada = cerrarModalJornada;
window.iniciarJornada = iniciarJornada;
window.finalizarJornada = finalizarJornada;
// ✅ NUEVO: Funciones de Turno de Caja (diferente de Jornada Laboral)
window.abrirTurno = abrirModalTurno;
window.abrirModalTurno = abrirModalTurno;
window.cerrarModalTurno = cerrarModalTurno;
window.confirmarAbrirTurno = confirmarAbrirTurno;
window.cargarKanban = cargarKanban;
window.cambiarEstadoKanban = cambiarEstadoKanban;

// Fin del event listener DOMContentLoaded
});
