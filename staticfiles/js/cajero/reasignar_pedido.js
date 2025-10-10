let mesaSeleccionadaId = null;
        let mesaSeleccionadaNumero = null;

        function seleccionarMesa(mesaId, mesaNumero) {
            // Remover selección anterior
            document.querySelectorAll('.mesa-option').forEach(m => {
                m.classList.remove('selected');
            });

            // Seleccionar nueva mesa
            const mesa = document.querySelector(`[data-mesa-id="${mesaId}"]`);
            mesa.classList.add('selected');

            mesaSeleccionadaId = mesaId;
            mesaSeleccionadaNumero = mesaNumero;

            // Actualizar UI
            document.getElementById('nueva_mesa_id').value = mesaId;
            document.getElementById('mesa-seleccionada-texto').textContent = `Mesa ${mesaNumero}`;
            document.getElementById('selected-info').classList.add('show');
            document.getElementById('btn-confirmar').disabled = false;
        }

        document.getElementById('reasignar-form')?.addEventListener('submit', function(e) {
            e.preventDefault();

            const motivo = document.getElementById('motivo').value.trim();

            if (!mesaSeleccionadaId) {
                alert('⚠️ Debes seleccionar una mesa');
                return;
            }

            if (!motivo) {
                alert('⚠️ Debes ingresar un motivo para la reasignación');
                return;
            }

            const mesaActual = {{ pedido.mesa.numero }};
            if (!confirm(`¿Confirmar reasignación?\n\nMesa Actual: ${mesaActual}\nNueva Mesa: ${mesaSeleccionadaNumero}\n\nMotivo: ${motivo}`)) {
                return;
            }

            this.submit();
        });