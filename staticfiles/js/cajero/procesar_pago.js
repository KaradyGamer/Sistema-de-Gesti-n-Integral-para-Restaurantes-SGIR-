const pedidoTotal = parseFloat('{{ pedido.total }}');
        let totalFinal = pedidoTotal;

        // Manejo de métodos de pago
        document.querySelectorAll('.payment-method').forEach(method => {
            method.addEventListener('click', function() {
                document.querySelectorAll('.payment-method').forEach(m => m.classList.remove('active'));
                this.classList.add('active');
                this.querySelector('input[type="radio"]').checked = true;

                const metodoPago = this.querySelector('input[type="radio"]').value;
                const montoRecibidoGroup = document.getElementById('monto-recibido-group');
                const cambioDisplay = document.getElementById('cambio-display');

                if (metodoPago === 'efectivo') {
                    montoRecibidoGroup.style.display = 'flex';
                } else {
                    montoRecibidoGroup.style.display = 'none';
                    cambioDisplay.style.display = 'none';
                }
            });
        });

        // Calcular totales
        function calcularTotales() {
            const descuentoPorcentaje = parseFloat(document.getElementById('descuento').value) || 0;
            const propina = parseFloat(document.getElementById('propina').value) || 0;

            const descuentoMonto = (pedidoTotal * descuentoPorcentaje) / 100;
            totalFinal = pedidoTotal - descuentoMonto + propina;

            document.getElementById('descuento-display').textContent = 'Bs/ ' + descuentoMonto.toFixed(2);
            document.getElementById('propina-display').textContent = 'Bs/ ' + propina.toFixed(2);
            document.getElementById('total-final').textContent = 'Bs/ ' + totalFinal.toFixed(2);

            calcularCambio();
        }

        // Calcular cambio
        function calcularCambio() {
            const montoRecibido = parseFloat(document.getElementById('monto_recibido').value) || 0;
            const cambio = montoRecibido - totalFinal;

            const cambioDisplay = document.getElementById('cambio-display');
            const cambioAmount = document.getElementById('cambio-amount');

            if (montoRecibido > 0 && cambio >= 0) {
                cambioAmount.textContent = cambio.toFixed(2);
                cambioDisplay.style.display = 'block';
            } else {
                cambioDisplay.style.display = 'none';
            }
        }

        // Event listeners
        document.getElementById('descuento').addEventListener('input', calcularTotales);
        document.getElementById('propina').addEventListener('input', calcularTotales);
        document.getElementById('monto_recibido').addEventListener('input', calcularCambio);

        // Submit del formulario
        document.getElementById('payment-form').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const metodoPago = formData.get('metodo_pago');
            const montoRecibido = parseFloat(formData.get('monto_recibido')) || 0;

            // Validar monto recibido para efectivo
            if (metodoPago === 'efectivo' && montoRecibido < totalFinal) {
                alert('El monto recibido debe ser mayor o igual al total a pagar.');
                return;
            }

            const data = {
                pedido_id: {{ pedido.id }},
                metodo_pago: metodoPago,
                monto_total: totalFinal.toFixed(2),
                monto_recibido: montoRecibido.toFixed(2),  // ✅ Agregado para la API
                descuento_porcentaje: parseFloat(formData.get('descuento')) || 0,
                propina: parseFloat(formData.get('propina')) || 0,
                referencia: formData.get('referencia'),
                observaciones: formData.get('observaciones')
            };

            try {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                const response = await fetch('/api/caja/pago/simple/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (response.ok) {
                    alert('✓ Pago procesado exitosamente\nFactura: ' + result.numero_factura);
                    window.location.href = '/caja/';
                } else {
                    alert('Error: ' + (result.error || 'No se pudo procesar el pago'));
                }
            } catch (error) {
                alert('Error de conexión: ' + error.message);
            }
        });