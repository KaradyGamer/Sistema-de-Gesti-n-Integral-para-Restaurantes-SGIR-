/**
 * ADMINUX - PANEL DE ADMINISTRACIÓN MODERNO
 * JavaScript principal con animaciones e interactividad
 */

// ============================================
// VARIABLES GLOBALES
// ============================================
const sidebar = document.getElementById('sidebar');
const toggleBtn = document.getElementById('toggleSidebar');
const mobileToggle = document.getElementById('mobileToggle');
const userDropdownBtn = document.getElementById('userDropdownBtn');
const userDropdownMenu = document.getElementById('userDropdownMenu');
const globalSearch = document.getElementById('globalSearch');

// ============================================
// TOGGLE SIDEBAR
// ============================================
if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
}

if (mobileToggle) {
    mobileToggle.addEventListener('click', () => {
        sidebar.classList.toggle('active');
    });
}

// Restaurar estado del sidebar
if (localStorage.getItem('sidebarCollapsed') === 'true') {
    sidebar.classList.add('collapsed');
}

// Cerrar sidebar en móvil al hacer clic fuera
document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768) {
        if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target)) {
            sidebar.classList.remove('active');
        }
    }
});

// ============================================
// DROPDOWN MENU
// ============================================
if (userDropdownBtn) {
    userDropdownBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        userDropdownMenu.classList.toggle('active');
    });

    // Cerrar dropdown al hacer clic fuera
    document.addEventListener('click', () => {
        userDropdownMenu.classList.remove('active');
    });
}

// ============================================
// BÚSQUEDA GLOBAL
// ============================================
if (globalSearch) {
    let searchTimeout;

    globalSearch.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);

        searchTimeout = setTimeout(() => {
            const query = e.target.value.trim();
            if (query.length >= 3) {
                realizarBusqueda(query);
            }
        }, 500);
    });

    globalSearch.addEventListener('focus', () => {
        globalSearch.parentElement.style.width = '300px';
    });

    globalSearch.addEventListener('blur', () => {
        if (!globalSearch.value) {
            globalSearch.parentElement.style.width = '200px';
        }
    });
}

function realizarBusqueda(query) {
    console.log('Buscando:', query);
    // Aquí iría la lógica de búsqueda con fetch
}

// ============================================
// ANIMACIONES DE ENTRADA
// ============================================
function animateOnScroll() {
    const elements = document.querySelectorAll('.stat-card, .card, .quick-action-card');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateY(20px)';

                setTimeout(() => {
                    entry.target.style.transition = 'all 0.5s ease-out';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, 100);

                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });

    elements.forEach(el => observer.observe(el));
}

// Ejecutar animaciones al cargar
window.addEventListener('load', () => {
    animateOnScroll();
});

// ============================================
// NOTIFICACIONES
// ============================================
const notificationsBtn = document.getElementById('notificationsBtn');

if (notificationsBtn) {
    notificationsBtn.addEventListener('click', () => {
        mostrarNotificacion('No tienes notificaciones nuevas', 'info');
    });
}

function mostrarNotificacion(mensaje, tipo = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${tipo}`;
    notification.innerHTML = `
        <i class='bx ${getIconoTipo(tipo)}'></i>
        <span>${mensaje}</span>
    `;

    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${getColorTipo(tipo)};
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 12px;
        animation: slideInRight 0.3s ease-out;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function getIconoTipo(tipo) {
    const iconos = {
        success: 'bx-check-circle',
        error: 'bx-error-circle',
        warning: 'bx-error',
        info: 'bx-info-circle'
    };
    return iconos[tipo] || iconos.info;
}

function getColorTipo(tipo) {
    const colores = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    };
    return colores[tipo] || colores.info;
}

// ============================================
// CONFIGURACIÓN
// ============================================
const settingsBtn = document.getElementById('settingsBtn');

if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
        window.location.href = '/adminux/configuracion/';
    });
}

// ============================================
// TOOLTIPS
// ============================================
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[title]');

    tooltipElements.forEach(el => {
        el.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = el.getAttribute('title');
            tooltip.style.cssText = `
                position: absolute;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 0.85em;
                z-index: 10000;
                pointer-events: none;
                white-space: nowrap;
            `;

            document.body.appendChild(tooltip);

            const rect = el.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 8}px`;
            tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)}px`;

            el._tooltip = tooltip;
        });

        el.addEventListener('mouseleave', () => {
            if (el._tooltip) {
                el._tooltip.remove();
                delete el._tooltip;
            }
        });
    });
}

// Inicializar tooltips
initTooltips();

// ============================================
// CONFIRMACIONES DE ELIMINACIÓN
// ============================================
function confirmarEliminacion(mensaje = '¿Estás seguro de eliminar este elemento?') {
    return new Promise((resolve) => {
        const confirmed = confirm(mensaje);
        resolve(confirmed);
    });
}

// Agregar event listeners a botones de eliminación
document.querySelectorAll('[data-action="delete"]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
        e.preventDefault();

        const confirmed = await confirmarEliminacion();
        if (confirmed) {
            window.location.href = btn.getAttribute('href');
        }
    });
});

// ============================================
// ANIMACIONES CSS
// ============================================
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
`;
document.head.appendChild(style);

// ============================================
// UTILIDADES
// ============================================
function formatCurrency(amount) {
    return `Bs/ ${parseFloat(amount).toFixed(2)}`;
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('es-BO');
}

// ============================================
// AUTO-REFRESH (opcional)
// ============================================
let autoRefreshInterval;

function enableAutoRefresh(seconds = 60) {
    autoRefreshInterval = setInterval(() => {
        console.log('Auto-refresh activado');
        // Aquí puedes agregar lógica para actualizar datos
    }, seconds * 1000);
}

function disableAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
}

// ============================================
// INICIALIZACIÓN
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎨 AdminUX cargado correctamente');

    // Agregar efectos hover a tarjetas
    document.querySelectorAll('.stat-card, .card, .quick-action-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
});

// Exponer funciones globalmente
window.adminUX = {
    mostrarNotificacion,
    confirmarEliminacion,
    enableAutoRefresh,
    disableAutoRefresh,
    formatCurrency,
    formatDate
};

console.log('✅ AdminUX JS cargado y listo');
