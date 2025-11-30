/**
 * Loader de AdminUX - Solo animación de carga entre páginas
 * NO incluye lógica SPA
 */

(function() {
  const loader = document.getElementById('adminuxLoader');

  if (!loader) return;

  // Ocultar loader cuando la página carga completamente
  window.addEventListener('load', function() {
    loader.classList.add('loader-hide');
  });

  // Mostrar loader antes de navegar a otra página
  window.addEventListener('beforeunload', function() {
    loader.classList.remove('loader-hide');
  });

  // Para navegación con enlaces (opcional, mejora UX)
  document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll('a:not([target="_blank"]):not([href^="#"])');

    links.forEach(function(link) {
      link.addEventListener('click', function(e) {
        // Solo mostrar loader si es navegación interna
        const href = this.getAttribute('href');
        if (href && !href.startsWith('http') && !href.startsWith('//')) {
          loader.classList.remove('loader-hide');
        }
      });
    });
  });
})();
