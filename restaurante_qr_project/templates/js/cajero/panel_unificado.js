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

        // Actualizar badges
        document.getElementById('badgePedidos').textContent = stats.pedidos_pendientes || 0;

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
        const response = await fetch('/api/caja/pedidos-pendientes/', {
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
        container.innerHTML = data.pedidos.map(pedido => `
            <div class="pedido-card">
                <div class="pedido-header">
                    <h3>Pedido #${pedido.id}</h3>
                    <span class="pedido-badge">Mesa ${pedido.mesa}</span>
                </div>
                <div class="pedido-body">
                    <p><strong>🕐 Hora:</strong> ${pedido.fecha}</p>
                    <p><strong>👥 Personas:</strong> ${pedido.numero_personas || 1}</p>
                    <p><strong>👨‍🍳 Mesero:</strong> ${pedido.mesero || 'Cliente directo'}</p>
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
        `).join('');

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

function verDetallePedido(id) {
    window.open(`/caja/detalle/${id}/`, '_blank');
}

function cobrarPedido(id) {
    window.location.href = `/caja/procesar-pago/${id}/`;
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
