/**
 * PANEL UNIFICADO DE CAJA
 * Sistema de navegación SPA con sidebar
 */

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
    dashboard: { title: 'Dashboard', subtitle: 'Resumen general del sistema' },
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
                <h3>Mapa de Mesas</h3>
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

            // Botones de acción
            let botonesHTML = '';
            if (mesa.pedidos_activos > 0) {
                botonesHTML = `
                    <div class="mesa-acciones">
                        <button class="btn-mesa btn-pagar" onclick="abrirModalPago(${mesa.id}, false)" title="Pagar todo">
                            <i class='bx bx-money'></i>
                        </button>
                        <button class="btn-mesa btn-separado" onclick="abrirModalPago(${mesa.id}, true)" title="Pago separado">
                            <i class='bx bx-cut'></i>
                        </button>
                        <button class="btn-mesa btn-modificar" onclick="modificarPedidoMesa(${mesa.id})" title="Modificar">
                            <i class='bx bx-edit'></i>
                        </button>
                        <button class="btn-mesa btn-cambiar" onclick="abrirModalCambiarMesa(${mesa.id})" title="Cambiar mesa">
                            <i class='bx bx-transfer'></i>
                        </button>
                    </div>
                `;
            }

            html += `
                <div class="mesa-card ${mesa.color}" data-mesa-id="${mesa.id}">
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
                        ${botonesHTML}
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
// CARGAR HISTORIAL
// ============================================
async function cargarHistorial() {
    const container = document.getElementById('historialContainer');
    container.innerHTML = '<div class="loading">Cargando historial...</div>';

    try {
        const response = await fetch('/api/caja/pedidos/pendientes/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        if (!response.ok) throw new Error('Error al cargar historial');

        const data = await response.json();

        // Filtrar solo pedidos pagados
        const pedidosPagados = (data.pedidos || []).filter(p => p.estado_pago === 'pagado');

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
            const fecha = new Date(pedido.fecha);
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
                            <span class="historial-mesa">Mesa ${pedido.mesa_numero}</span>
                        </div>
                        <div class="historial-detalles">
                            <span><i class='bx bx-calendar'></i> ${fechaFormateada}</span>
                            <span><i class='bx bx-time'></i> ${horaFormateada}</span>
                            <span><i class='bx bx-user'></i> ${pedido.mesero || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="historial-total">
                        Bs/ ${parseFloat(pedido.total_final || pedido.total).toFixed(2)}
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

function cargarAlertasStock() {
    document.getElementById('alertasStockContainer').innerHTML = '<p>⚠️ Alertas de stock próximamente</p>';
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

        // Agrupar empleados por rol
        const empleadosPorRol = {
            'cajero': [],
            'mesero': [],
            'cocinero': []
        };

        data.empleados.forEach(emp => {
            if (empleadosPorRol[emp.rol]) {
                empleadosPorRol[emp.rol].push(emp);
            }
        });

        // Renderizar empleados agrupados por rol
        let html = '<div class="empleados-grid">';

        for (const [rol, empleados] of Object.entries(empleadosPorRol)) {
            if (empleados.length === 0) continue;

            const iconos = {
                'cajero': 'bx-dollar',
                'mesero': 'bx-dish',
                'cocinero': 'bx-food-menu'
            };

            const colores = {
                'cajero': '#10b981',
                'mesero': '#6366f1',
                'cocinero': '#f59e0b'
            };

            html += `
                <div class="rol-grupo">
                    <h3 class="rol-titulo" style="color: ${colores[rol]};">
                        <i class='bx ${iconos[rol]}'></i>
                        ${empleados[0].rol_display}s (${empleados.length})
                    </h3>
                    <div class="empleados-rol-grid">
                        ${empleados.map(emp => `
                            <div class="empleado-card">
                                <div class="empleado-header">
                                    <i class='bx ${iconos[rol]}' style="font-size: 24px; color: ${colores[rol]};"></i>
                                    <div class="empleado-info">
                                        <h4>${emp.nombre_completo}</h4>
                                        <p class="empleado-username">@${emp.username}</p>
                                    </div>
                                </div>
                                <div class="empleado-qr">
                                    ${emp.qr_url ? `
                                        <img src="${emp.qr_url}" alt="QR ${emp.username}" class="qr-image">
                                        <p class="qr-instruccion">Escanea para iniciar sesion</p>
                                    ` : `
                                        <div class="qr-placeholder">
                                            <i class='bx bx-qr' style="font-size: 48px; color: #ccc;"></i>
                                            <p>QR no disponible</p>
                                        </div>
                                    `}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        html += '</div>';
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

function cargarJornada() {
    document.getElementById('jornadaContainer').innerHTML = '<p>📅 Jornada laboral próximamente</p>';
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

    } catch (error) {
        console.error('[DEBUG] Error al cargar kanban:', error);
        mostrarNotificacion('Error al cargar estado de pedidos', 'error');
    }
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

    // Botones de navegación
    const puedeRetroceder = estado !== 'pedido';
    const puedeAvanzar = estado !== 'entregado';

    const botonesHTML = `
        <div class="kanban-card-actions">
            <button class="kanban-btn kanban-btn-prev"
                    onclick="cambiarEstadoKanban(${pedido.id}, '${estado}', 'prev')"
                    ${!puedeRetroceder ? 'disabled' : ''}>
                <i class='bx bx-chevron-left'></i>
            </button>
            <button class="kanban-btn kanban-btn-next"
                    onclick="cambiarEstadoKanban(${pedido.id}, '${estado}', 'next')"
                    ${!puedeAvanzar ? 'disabled' : ''}>
                <i class='bx bx-chevron-right'></i>
            </button>
        </div>
    `;

    return `
        <div class="kanban-card" data-pedido-id="${pedido.id}" data-estado="${estado}">
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
                <div class="kanban-hora">
                    <i class='bx bx-time'></i>
                    <span>${pedido.hora || ''}</span>
                </div>
            </div>
            ${botonesHTML}
        </div>
    `;
}

async function cambiarEstadoKanban(pedidoId, estadoActual, direccion) {
    const estados = ['pedido', 'preparando', 'listo', 'entregado'];
    const indexActual = estados.indexOf(estadoActual);

    let nuevoIndex;
    if (direccion === 'prev') {
        nuevoIndex = Math.max(0, indexActual - 1);
    } else {
        nuevoIndex = Math.min(estados.length - 1, indexActual + 1);
    }

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

function abrirModalPago(mesaId, pagoSeparado) {
    if (pagoSeparado) {
        mostrarNotificacion('Función "Pago Separado" en desarrollo', 'info');
        // TODO: Implementar modal de pago separado
    } else {
        mostrarNotificacion('Función "Pagar Todo" en desarrollo', 'info');
        // TODO: Implementar pago completo
    }
}

function modificarPedidoMesa(mesaId) {
    mostrarNotificacion('Función "Modificar Pedido" en desarrollo', 'info');
    // TODO: Implementar modificación de pedido
}

function abrirModalCambiarMesa(mesaId) {
    mostrarNotificacion('Función "Cambiar Mesa" en desarrollo', 'info');
    // TODO: Implementar cambio de mesa
}
