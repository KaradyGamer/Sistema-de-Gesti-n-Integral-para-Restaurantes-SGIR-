// CONFIGURACIÓN
        const CONFIG = {
            autoUpdateInterval: 15000, // 15 segundos
            notificationDuration: 3000
        };

        let autoUpdateTimer;

        // CARGAR PEDIDOS DE LA COCINA
        async function cargarPedidos() {
            try {
                console.log('🍳 Cargando pedidos de la cocina...');
                mostrarNotificacion('🔄 Actualizando pedidos...', 'info');
                
                const response = await fetch('/api/pedidos/cocina/', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    }
                });
                
                console.log('📡 Respuesta del servidor:', response.status, response.statusText);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const pedidos = await response.json();
                console.log('📦 Pedidos recibidos:', pedidos);
                
                renderizarPedidos(pedidos);
                mostrarNotificacion('✅ Pedidos actualizados', 'success');
                
            } catch (error) {
                console.error('❌ Error cargando pedidos:', error);
                mostrarNotificacion('❌ Error al cargar pedidos: ' + error.message, 'error');
                
                // Mostrar mensaje de error
                document.getElementById('pedidos-container').innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">❌</div>
                        <h3>Error al cargar pedidos</h3>
                        <p>${error.message}</p>
                        <button class="btn btn-primary" onclick="cargarPedidos()">🔄 Reintentar</button>
                    </div>
                `;
            }
        }

        // RENDERIZAR PEDIDOS
        function renderizarPedidos(pedidos) {
            const container = document.getElementById('pedidos-container');
            
            if (!pedidos || pedidos.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">🍽️</div>
                        <h3>No hay pedidos pendientes</h3>
                        <p>Los nuevos pedidos aparecerán aquí automáticamente</p>
                    </div>
                `;
                document.getElementById('pedidos-count').textContent = '0';
                return;
            }

            const pedidosHTML = pedidos.map(pedido => {
                const estadoClass = `estado-${pedido.estado.replace(' ', '-')}`;
                const estadoTexto = pedido.estado.toUpperCase();
                
                // Renderizar productos
                const productosHTML = pedido.detalles?.map(detalle => `
                    <div class="producto-item">
                        <span class="producto-nombre">${detalle.producto}</span>
                        <span class="producto-cantidad">${detalle.cantidad}x</span>
                    </div>
                `).join('') || '<div class="producto-item"><span>Sin detalles</span></div>';
                
                // Botones según el estado
                let botonesHTML = '';
                if (pedido.estado === 'pendiente') {
                    botonesHTML = `
                        <button onclick="cambiarEstado(${pedido.id}, 'en preparacion')" class="btn btn-primary">
                            🔥 Comenzar Preparación
                        </button>
                    `;
                } else if (pedido.estado === 'en preparacion') {
                    botonesHTML = `
                        <button onclick="cambiarEstado(${pedido.id}, 'listo')" class="btn btn-success">
                            ✅ Marcar como Listo
                        </button>
                    `;
                }
                
                return `
                    <div class="pedido-card" data-pedido-id="${pedido.id}">
                        <div class="pedido-header">
                            <div class="mesa-numero">Mesa ${pedido.mesa}</div>
                            <div class="pedido-tiempo">${new Date(pedido.fecha).toLocaleTimeString()}</div>
                        </div>
                        
                        <div class="estado-badge ${estadoClass}">${estadoTexto}</div>
                        
                        <div class="productos-lista">
                            ${productosHTML}
                        </div>
                        
                        <div class="pedido-total">
                            Total: Bs. ${pedido.total}
                        </div>
                        
                        <div class="pedido-actions">
                            ${botonesHTML}
                        </div>
                    </div>
                `;
            }).join('');

            container.innerHTML = `<div class="pedidos-grid">${pedidosHTML}</div>`;
            document.getElementById('pedidos-count').textContent = pedidos.length;
        }

        // CAMBIAR ESTADO DEL PEDIDO
        async function cambiarEstado(pedidoId, nuevoEstado) {
            try {
                console.log(`🔄 Cambiando pedido ${pedidoId} a estado: ${nuevoEstado}`);
                
                const response = await fetch(`/api/pedidos/${pedidoId}/actualizar/`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        estado: nuevoEstado
                    })
                });
                
                const data = await response.json();
                
                if (response.ok && data.mensaje) {
                    mostrarNotificacion(`✅ ${data.mensaje}`, 'success');
                    cargarPedidos(); // Recargar pedidos
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
                
            } catch (error) {
                console.error('❌ Error cambiando estado:', error);
                mostrarNotificacion('❌ Error al actualizar pedido: ' + error.message, 'error');
            }
        }

        // FUNCIÓN PÚBLICA PARA EL BOTÓN
        function actualizarPedidos() {
            cargarPedidos();
        }

        // UTILIDADES
        function getCsrfToken() {
            const cookieValue = document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='))
                ?.split('=')[1];
            return cookieValue || '';
        }

        function mostrarNotificacion(mensaje, tipo = 'info') {
            const notification = document.getElementById('notification');
            const text = document.getElementById('notification-text');
            
            text.textContent = mensaje;
            notification.className = `notification show ${tipo}`;
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, CONFIG.notificationDuration);
        }

        // AUTO-ACTUALIZACIÓN
        function iniciarAutoActualizacion() {
            autoUpdateTimer = setInterval(() => {
                cargarPedidos();
                console.log(`🔄 Auto-actualización: ${new Date().toLocaleTimeString()}`);
            }, CONFIG.autoUpdateInterval);
        }

        function detenerAutoActualizacion() {
            if (autoUpdateTimer) {
                clearInterval(autoUpdateTimer);
            }
        }

        // INICIALIZACIÓN
        document.addEventListener('DOMContentLoaded', function() {
            console.log('👨‍🍳 Panel de Cocina iniciado');
            console.log('🔧 API URL: /api/pedidos/cocina/');
            
            // Cargar pedidos iniciales
            cargarPedidos();
            
            // Iniciar auto-actualización
            iniciarAutoActualizacion();
            
            // Pausar auto-actualización cuando la página no esté visible
            document.addEventListener('visibilitychange', function() {
                if (document.hidden) {
                    detenerAutoActualizacion();
                    console.log('⏸️ Auto-actualización pausada');
                } else {
                    iniciarAutoActualizacion();
                    console.log('▶️ Auto-actualización reanudada');
                }
            });
        });

        // Cleanup al salir
        window.addEventListener('beforeunload', function() {
            detenerAutoActualizacion();
        });