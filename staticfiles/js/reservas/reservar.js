// Verificar disponibilidad de mesas en tiempo real
        function verificarDisponibilidad() {
            const fecha = document.getElementById('id_fecha_reserva').value;
            const hora = document.getElementById('id_hora_reserva').value;
            const personas = document.getElementById('id_numero_personas').value;

            if (fecha && hora && personas) {
                fetch(`/reservas/api/mesas-disponibles/?fecha=${fecha}&hora=${hora}&personas=${personas}`)
                    .then(response => response.json())
                    .then(data => {
                        const mesasDiv = document.getElementById('mesasDisponibles');
                        const listaMesas = document.getElementById('listaMesas');
                        
                        if (data.mesas && data.mesas.length > 0) {
                            listaMesas.innerHTML = data.mesas.map(mesa => 
                                `<span class="mesa-item">Mesa ${mesa.numero} (${mesa.capacidad} personas)</span>`
                            ).join('');
                            mesasDiv.style.display = 'block';
                        } else {
                            listaMesas.innerHTML = '<span style="color: red;">⚠️ No hay mesas disponibles para esta fecha y hora</span>';
                            mesasDiv.style.display = 'block';
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('mesasDisponibles').style.display = 'none';
                    });
            } else {
                document.getElementById('mesasDisponibles').style.display = 'none';
            }
        }

        // Event listeners
        document.getElementById('id_fecha_reserva').addEventListener('change', verificarDisponibilidad);
        document.getElementById('id_hora_reserva').addEventListener('change', verificarDisponibilidad);
        document.getElementById('id_numero_personas').addEventListener('change', verificarDisponibilidad);

        // Configurar fecha mínima como hoy
        document.getElementById('id_fecha_reserva').setAttribute('min', new Date().toISOString().split('T')[0]);