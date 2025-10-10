// Sugerir turno basado en la hora actual
        window.addEventListener('DOMContentLoaded', function() {
            const turnoSelect = document.getElementById('turno');
            const ahora = new Date();
            const hora = ahora.getHours();

            let turnoSugerido = '';
            if (hora >= 6 && hora < 14) {
                turnoSugerido = 'manana';
            } else if (hora >= 14 && hora < 22) {
                turnoSugerido = 'tarde';
            } else {
                turnoSugerido = 'noche';
            }

            turnoSelect.value = turnoSugerido;
        });

        // Validación del formulario
        document.getElementById('abrir-caja-form')?.addEventListener('submit', function(e) {
            const efectivo = parseFloat(document.getElementById('efectivo_inicial').value);
            const turno = document.getElementById('turno').value;

            if (!turno) {
                e.preventDefault();
                alert('⚠️ Por favor selecciona un turno');
                return;
            }

            if (isNaN(efectivo) || efectivo < 0) {
                e.preventDefault();
                alert('⚠️ Por favor ingresa un monto válido');
                return;
            }

            if (efectivo === 0) {
                if (!confirm('¿Estás seguro de abrir la caja con Bs/ 0.00?')) {
                    e.preventDefault();
                    return;
                }
            }

            // Confirmación final
            if (!confirm(`¿Confirmar apertura de caja?\n\nTurno: ${turno.toUpperCase()}\nEfectivo Inicial: Bs/ ${efectivo.toFixed(2)}`)) {
                e.preventDefault();
            }
        });