const pedidoId = {{ pedido.id }};
        const totalOriginal = parseFloat('{{ pedido.total }}');
        let cambios = {
            modificados: [],
            eliminados: [],
            agregados: []
        };

        function cambiarCantidad(itemId, delta) {
            const input = document.getElementById(`cantidad-${itemId}`);
            let nuevaCantidad = parseInt(input.value) + delta;
            if (nuevaCantidad < 0) nuevaCantidad = 0;
            input.value = nuevaCantidad;
            actualizarSubtotal(itemId);
        }

        function actualizarSubtotal(itemId) {
            const input = document.getElementById(`cantidad-${itemId}`);
            const cantidad = parseInt(input.value) || 0;
            const precio = parseFloat(input.dataset.precio);
            const cantidadOriginal = parseInt(input.dataset.original);
            const subtotal = cantidad * precio;

            document.getElementById(`subtotal-${itemId}`).textContent = `Bs/ ${subtotal.toFixed(2)}`;

            // Marcar como eliminado si cantidad = 0
            const item = document.querySelector(`[data-item-id="${itemId}"]`);
            if (cantidad === 0) {
                item.classList.add('deleted');
            } else {
                item.classList.remove('deleted');
            }

            // Registrar cambio
            if (cantidad !== cantidadOriginal) {
                const index = cambios.modificados.findIndex(c => c.item_id === itemId);
                if (index >= 0) {
                    if (cantidad === 0) {
                        cambios.modificados.splice(index, 1);
                        if (!cambios.eliminados.includes(itemId)) {
                            cambios.eliminados.push(itemId);
                        }
                    } else {
                        cambios.modificados[index].nueva_cantidad = cantidad;
                    }
                } else if (cantidad > 0) {
                    cambios.modificados.push({
                        item_id: itemId,
                        nueva_cantidad: cantidad,
                        cantidad_original: cantidadOriginal
                    });
                }
            }

            calcularNuevoTotal();
        }

        function eliminarItem(itemId) {
            if (confirm('¿Estás seguro de eliminar este item?')) {
                document.getElementById(`cantidad-${itemId}`).value = 0;
                actualizarSubtotal(itemId);
            }
        }

        function agregarProducto(productoId, nombre, precio) {
            // Verificar si ya existe en el pedido
            const existente = document.querySelector(`[data-producto-id="${productoId}"]`);
            if (existente) {
                const itemId = existente.dataset.itemId;
                const input = document.getElementById(`cantidad-${itemId}`);
                input.value = parseInt(input.value) + 1;
                actualizarSubtotal(itemId);
            } else {
                // Agregar a la lista de nuevos
                const existe = cambios.agregados.find(p => p.producto_id === productoId);
                if (existe) {
                    existe.cantidad++;
                } else {
                    cambios.agregados.push({
                        producto_id: productoId,
                        nombre: nombre,
                        precio: precio,
                        cantidad: 1
                    });
                }
            }
            calcularNuevoTotal();
        }

        function calcularNuevoTotal() {
            let total = 0;

            // Sumar items existentes
            document.querySelectorAll('.item').forEach(item => {
                const itemId = item.dataset.itemId;
                const cantidad = parseInt(document.getElementById(`cantidad-${itemId}`).value) || 0;
                const precio = parseFloat(document.getElementById(`cantidad-${itemId}`).dataset.precio);
                total += cantidad * precio;
            });

            // Sumar items nuevos
            cambios.agregados.forEach(item => {
                total += item.cantidad * item.precio;
            });

            document.getElementById('nuevo-total').textContent = `Bs/ ${total.toFixed(2)}`;

            // Mostrar resumen de cambios
            mostrarResumenCambios();
        }

        function mostrarResumenCambios() {
            const hayCambios = cambios.modificados.length > 0 || cambios.eliminados.length > 0 || cambios.agregados.length > 0;

            if (hayCambios) {
                document.getElementById('cambios-resumen').style.display = 'block';
                const lista = document.getElementById('lista-cambios');
                lista.innerHTML = '';

                cambios.modificados.forEach(c => {
                    const li = document.createElement('li');
                    li.textContent = `Cantidad modificada (Item #${c.item_id})`;
                    lista.appendChild(li);
                });

                cambios.eliminados.forEach(id => {
                    const li = document.createElement('li');
                    li.textContent = `Item eliminado (#${id})`;
                    lista.appendChild(li);
                });

                cambios.agregados.forEach(p => {
                    const li = document.createElement('li');
                    li.textContent = `Agregado: ${p.nombre} (x${p.cantidad})`;
                    lista.appendChild(li);
                });
            } else {
                document.getElementById('cambios-resumen').style.display = 'none';
            }
        }

        function buscarProductos() {
            const search = document.getElementById('search-product').value.toLowerCase();
            document.querySelectorAll('.product-item').forEach(item => {
                const nombre = item.dataset.nombre;
                if (nombre.includes(search)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        }

        async function guardarCambios() {
            const motivo = document.getElementById('motivo').value.trim();

            if (!motivo) {
                alert('⚠️ Debes ingresar un motivo para la modificación');
                return;
            }

            const hayCambios = cambios.modificados.length > 0 || cambios.eliminados.length > 0 || cambios.agregados.length > 0;
            if (!hayCambios) {
                alert('⚠️ No hay cambios para guardar');
                return;
            }

            if (!confirm('¿Confirmar modificación del pedido?')) {
                return;
            }

            try {
                const response = await fetch(`/api/caja/pedido/${pedidoId}/modificar/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': '{{ csrf_token }}'
                    },
                    body: JSON.stringify({
                        modificados: cambios.modificados,
                        eliminados: cambios.eliminados,
                        agregados: cambios.agregados,
                        motivo: motivo
                    })
                });

                const result = await response.json();

                if (response.ok) {
                    alert('✓ Pedido modificado exitosamente');
                    window.location.href = `/caja/pedido/${pedidoId}/`;
                } else {
                    alert('Error: ' + (result.error || 'No se pudo modificar el pedido'));
                }
            } catch (error) {
                alert('Error de conexión: ' + error.message);
            }
        }