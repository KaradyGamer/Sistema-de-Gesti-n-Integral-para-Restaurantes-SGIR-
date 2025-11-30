/**
 * AdminUX SPA - Single Page Application Navigation
 * Maneja la navegación entre secciones sin recargar la página
 */

// ===== NAVEGACIÓN SPA =====
document.addEventListener('DOMContentLoaded', function() {
  // Ocultar loader después de cargar
  setTimeout(() => {
    const loader = document.getElementById('loader');
    if (loader) {
      loader.classList.add('hidden');
    }
  }, 500);

  // Navegación del sidebar
  const navItems = document.querySelectorAll('.nav-item');
  const sections = document.querySelectorAll('.page-section');

  navItems.forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();

      const target = this.dataset.target;
      if (!target) return;

      // Actualizar navegación activa
      navItems.forEach(nav => nav.classList.remove('active'));
      this.classList.add('active');

      // Mostrar sección correspondiente
      sections.forEach(section => {
        if (section.dataset.section === target) {
          section.classList.add('active');
        } else {
          section.classList.remove('active');
        }
      });

      // Actualizar título del topbar
      const topbarTitle = document.querySelector('.topbar-title');
      if (topbarTitle) {
        topbarTitle.textContent = this.querySelector('.nav-text').textContent;
      }

      // Scroll to top suavemente
      document.querySelector('.adminux-main-inner').scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  });
});

// ===== NOTIFICACIONES =====
const notifBell = document.getElementById('notifBell');
const notifDropdown = document.getElementById('notifDropdown');
const notifClear = document.getElementById('notifClear');
const notifList = document.getElementById('notifList');
const notifBadge = document.getElementById('notifBadge');

if (notifBell && notifDropdown) {
  notifBell.addEventListener('click', function(e) {
    e.stopPropagation();
    notifDropdown.classList.toggle('hidden');
  });

  // Cerrar dropdown al hacer clic fuera
  document.addEventListener('click', function(e) {
    if (!notifDropdown.contains(e.target) && e.target !== notifBell) {
      notifDropdown.classList.add('hidden');
    }
  });

  // Limpiar notificaciones
  if (notifClear) {
    notifClear.addEventListener('click', function() {
      notifList.innerHTML = '<li class="notif-empty">No hay notificaciones</li>';
      notifBadge.classList.add('hidden');
      notifBadge.textContent = '0';
    });
  }
}

// ===== FUNCIÓN PARA AGREGAR NOTIFICACIONES =====
function agregarNotificacion(titulo, mensaje, tipo = 'info') {
  const notifItem = document.createElement('li');
  notifItem.className = `notif-item notif-${tipo}`;
  notifItem.innerHTML = `
    <div class="notif-content">
      <strong>${titulo}</strong>
      <p>${mensaje}</p>
    </div>
    <button class="notif-remove">&times;</button>
  `;

  // Remover mensaje de "no hay notificaciones"
  const emptyMsg = notifList.querySelector('.notif-empty');
  if (emptyMsg) {
    emptyMsg.remove();
  }

  notifList.insertBefore(notifItem, notifList.firstChild);

  // Actualizar badge
  const count = notifList.querySelectorAll('.notif-item').length;
  notifBadge.textContent = count;
  notifBadge.classList.remove('hidden');

  // Event listener para remover
  notifItem.querySelector('.notif-remove').addEventListener('click', function() {
    notifItem.remove();
    const newCount = notifList.querySelectorAll('.notif-item').length;
    notifBadge.textContent = newCount;
    if (newCount === 0) {
      notifBadge.classList.add('hidden');
      notifList.innerHTML = '<li class="notif-empty">No hay notificaciones</li>';
    }
  });
}

// Exponer función globalmente
window.agregarNotificacion = agregarNotificacion;

// ===== BURGER MENU (Mobile) =====
const burgerToggle = document.getElementById('burgerToggle');
const sidebar = document.querySelector('.sidebar');

if (burgerToggle && sidebar) {
  burgerToggle.addEventListener('change', function() {
    if (this.checked) {
      sidebar.classList.add('sidebar--mobile-open');
    } else {
      sidebar.classList.remove('sidebar--mobile-open');
    }
  });

  // Cerrar sidebar al hacer clic en un nav-item en mobile
  navItems.forEach(item => {
    item.addEventListener('click', function() {
      if (window.innerWidth <= 768) {
        burgerToggle.checked = false;
        sidebar.classList.remove('sidebar--mobile-open');
      }
    });
  });
}

console.log('✅ AdminUX SPA inicializado correctamente');
