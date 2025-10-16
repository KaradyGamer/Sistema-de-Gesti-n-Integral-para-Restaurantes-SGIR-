// Establecer fecha actual como predeterminada si no hay filtros
        window.addEventListener('DOMContentLoaded', function() {
            const fechaInicio = document.querySelector('input[name="fecha_inicio"]');
            const fechaFin = document.querySelector('input[name="fecha_fin"]');

            if (!fechaInicio.value && !fechaFin.value) {
                const hoy = new Date().toISOString().split('T')[0];
                fechaFin.value = hoy;
            }
        });