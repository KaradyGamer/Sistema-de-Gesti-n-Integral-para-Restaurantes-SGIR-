// ========================================
// SGIR - Responsive Tables Handler
// Envuelve tablas automáticamente en contenedores responsive
// ========================================

(function() {
    'use strict';

    /**
     * Envuelve todas las tablas sin wrapper en un contenedor .table-responsive
     */
    function wrapTables() {
        const tables = document.querySelectorAll('table');
        let wrappedCount = 0;

        tables.forEach(table => {
            // Verificar si la tabla ya está dentro de un wrapper responsive
            if (!table.closest('.table-responsive')) {
                // Crear wrapper
                const wrapper = document.createElement('div');
                wrapper.className = 'table-responsive';

                // Insertar wrapper antes de la tabla
                table.parentNode.insertBefore(wrapper, table);

                // Mover tabla dentro del wrapper
                wrapper.appendChild(table);

                wrappedCount++;
            }
        });

        if (wrappedCount > 0) {
            console.log(`[Responsive Tables] ${wrappedCount} tabla(s) envuelta(s) en contenedores responsive`);
        }
    }

    /**
     * Añade clases responsive a elementos comunes
     */
    function addResponsiveClasses() {
        // Añadir .img-fluid a imágenes sin clase
        document.querySelectorAll('img:not([class*="fluid"])').forEach(img => {
            if (!img.classList.contains('img-fluid') && !img.closest('.no-responsive')) {
                img.classList.add('img-fluid');
            }
        });

        // Añadir .container-fluid a contenedores principales
        document.querySelectorAll('.main-content > div:first-child').forEach(div => {
            if (!div.classList.contains('container-fluid') && !div.closest('.no-responsive')) {
                div.classList.add('container-fluid');
            }
        });
    }

    /**
     * Maneja el overflow de tablas grandes
     */
    function handleTableOverflow() {
        const tables = document.querySelectorAll('.table-responsive table');

        tables.forEach(table => {
            const wrapper = table.closest('.table-responsive');
            if (wrapper && table.offsetWidth > wrapper.offsetWidth) {
                wrapper.classList.add('has-overflow');

                // Añadir indicador visual de scroll
                if (!wrapper.querySelector('.scroll-indicator')) {
                    const indicator = document.createElement('div');
                    indicator.className = 'scroll-indicator';
                    indicator.innerHTML = '← Desliza para ver más →';
                    indicator.style.cssText = 'text-align:center; padding:5px; font-size:0.875rem; color:#666; background:#f0f0f0; border-radius:0 0 8px 8px;';
                    wrapper.appendChild(indicator);

                    // Remover indicador cuando se hace scroll
                    wrapper.addEventListener('scroll', function() {
                        if (this.scrollLeft > 10) {
                            indicator.style.display = 'none';
                        }
                    }, { once: true });
                }
            }
        });
    }

    /**
     * Detecta orientación del dispositivo y ajusta layout
     */
    function handleOrientation() {
        const orientation = window.innerWidth > window.innerHeight ? 'landscape' : 'portrait';
        document.body.setAttribute('data-orientation', orientation);
    }

    /**
     * Inicializa todas las funciones responsive
     */
    function init() {
        wrapTables();
        addResponsiveClasses();
        handleTableOverflow();
        handleOrientation();

        // Observar cambios en el DOM para tablas dinámicas
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.addedNodes.length) {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1) { // Element node
                            if (node.tagName === 'TABLE') {
                                wrapTables();
                                handleTableOverflow();
                            } else if (node.querySelector && node.querySelector('table')) {
                                wrapTables();
                                handleTableOverflow();
                            }
                        }
                    });
                }
            });
        });

        // Observar cambios en el body
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Manejar cambios de orientación
        window.addEventListener('resize', () => {
            handleOrientation();
            handleTableOverflow();
        });

        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                handleOrientation();
                handleTableOverflow();
            }, 100);
        });
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
