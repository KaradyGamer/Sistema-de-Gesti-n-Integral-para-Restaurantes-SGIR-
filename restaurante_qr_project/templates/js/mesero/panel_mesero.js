// CONFIGURACIÓN
        const CONFIG = {
            autoUpdateInterval: 30000, // 30 segundos
            notificationDuration: 3000 // 3 segundos
        };

        let autoUpdateTimer;
        let lastUpdateTime = Date.now();

        // CAMBIO DE PESTAÑAS
        function switchTab(tabName) {
            // Actualizar pestañas
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.closest('.tab').classList.add('active');

            // Actualizar contenido
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabName + '-content').classList.add('active');

            // Cargar datos específicos
            if (tabName === 'pedidos') {
                loadPedidos();
            } else if (tabName === 'reservas') {
                loadReservas();
            }
        }

        // ✅ CARGAR PEDIDOS CON URL CORREGIDA
        async function loadPedidos() {
            try {
                console.log('🔄 Cargando pedidos del mesero...');
                showNotification('🔄 Actualizando pedidos...', 'info');
                
                const response = await fetch('/api/pedidos/mesero/pedidos/', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    }
                });
                
                console.log('📡 Respuesta pedidos:', response.status, response.statusText);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('📦 Datos pedidos recibidos:', data);
                
                if (data.success) {
                    renderPedidosListos(data.pedidos_listos || []);
                    renderPedidosEntregados(data.pedidos_entregados || []);
                    updateCounters('pedidos', data.pedidos_listos?.length || 0);
                    showNotification('✅ Pedidos actualizados', 'success');
                } else {
                    throw new Error(data.error || 'Error desconocido en pedidos');
                }
                
            } catch (error) {
                console.error('❌ Error loading pedidos:', error);
                showNotification('❌ Error al cargar pedidos: ' + error.message, 'error');
                
                // Mostrar mensaje de error en lugar de datos de ejemplo
                document.getElementById('pedidos-listos').innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">❌</div>
                        <h3>Error al cargar pedidos</h3>
                        <p>${error.message}</p>
                        <button class="btn btn-info" onclick="loadPedidos()">🔄 Reintentar</button>
                    </div>
                `;
                document.getElementById('pedidos-entregados').innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">❌</div>
                        <h3>Error al cargar pedidos entregados</h3>
                    </div>
                `;
            }
        }

        // ✅ CARGAR RESERVAS CON URL CORREGIDA
        async function loadReservas() {
            try {
                console.log('🔄 Cargando reservas del mesero...');
                showNotification('🔄 Actualizando reservas...', 'info');
                
                const response = await fetch('/api/pedidos/mesero/reservas/', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    }
                });
                
                console.log('📡 Respuesta reservas:', response.status, response.statusText);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('📅 Datos reservas recibidos:', data);
                
                if (data.success) {
                    renderReservasHoy(data.reservas_hoy || []);
                    renderReservasProximas(data.reservas_proximas || []);
                    updateCounters('reservas', data.reservas_hoy?.length || 0);
                    showNotification('✅ Reservas actualizadas', 'success');
                } else {
                    throw new Error(data.error || 'Error desconocido en reservas');
                }
                
            } catch (error) {
                console.error('❌ Error loading reservas:', error);
                showNotification('❌ Error al cargar reservas: ' + error.message, 'error');
                
                // Mostrar mensaje de error
                document.getElementById('reservas-hoy').innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">❌</div>
                        <h3>Error al cargar reservas</h3>
                        <p>${error.message}</p>
                        <button class="btn btn-info" onclick="loadReservas()">🔄 Reintentar</button>
                    </div>
                `;
                document.getElementById('reservas-proximas').innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">❌</div>
                        <h3>Error al cargar próximas reservas</h3>
                    </div>
                `;
            }
        }

        // RENDER FUNCTIONS
        function renderPedidosListos(pedidos) {
            const container = document.getElementById('pedidos-listos');
            
            if (pedidos.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🍽️</div>
                        <h3>No hay pedidos listos</h3>
                        <p>Los pedidos aparecerán aquí cuando estén listos para entregar</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = pedidos.map(pedido => `
                <div class="item">
                    <div class="item-header">
                        <div class="item-title">Mesa ${pedido.mesa}</div>
                        <div class="item-time">${pedido.tiempo}</div>
                    </div>
                    <div class="item-details">
                        <div class="detail-item">
                            <span class="detail-label">🍕 Productos:</span>
                            <span class="detail-value">${pedido.productos?.join(', ') || 'N/A'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">💰 Total:</span>
                            <span class="detail-value">${pedido.total}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">💳 Pago:</span>
                            <span class="detail-value">${pedido.forma_pago || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="actions">
                        <button class="btn btn-success" onclick="entregarPedido(${pedido.id})">
                            ✅ Entregar
                        </button>
                        <button class="btn btn-info" onclick="verDetalles(${pedido.id})">
                            👁️ Ver Detalles
                        </button>
                    </div>
                </div>
            `).join('');

            document.getElementById('listos-count').textContent = pedidos.length;
        }

        function renderPedidosEntregados(pedidos) {
            const container = document.getElementById('pedidos-entregados');
            
            if (pedidos.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">✅</div>
                        <h3>No hay pedidos entregados</h3>
                        <p>Los pedidos entregados aparecerán aquí</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = pedidos.map(pedido => `
                <div class="item" style="opacity: 0.8;">
                    <div class="item-header">
                        <div class="item-title">Mesa ${pedido.mesa}</div>
                        <div class="item-time">✅ ${pedido.tiempo}</div>
                    </div>
                    <div class="item-details">
                        <div class="detail-item">
                            <span class="detail-label">🍕 Productos:</span>
                            <span class="detail-value">${pedido.productos?.join(', ') || 'N/A'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">💰 Total:</span>
                            <span class="detail-value">${pedido.total}</span>
                        </div>
                    </div>
                </div>
            `).join('');

            document.getElementById('entregados-count').textContent = pedidos.length;
        }

        function renderReservasHoy(reservas) {
            const container = document.getElementById('reservas-hoy');
            
            if (reservas.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📅</div>
                        <h3>No hay reservas hoy</h3>
                        <p>Las reservas de hoy aparecerán aquí</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = reservas.map(reserva => `
                <div class="item">
                    <div class="item-header">
                        <div class="item-title">${reserva.nombre}</div>
                        <div class="status-badge status-${reserva.estado_color || reserva.estado}">${reserva.estado_texto || reserva.estado}</div>
                    </div>
                    <div class="item-details">
                        <div class="detail-item">
                            <span class="detail-label">🕐 Hora:</span>
                            <span class="detail-value">${reserva.hora}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">👥 Personas:</span>
                            <span class="detail-value">${reserva.personas}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">🍽️ Mesa:</span>
                            <span class="detail-value">${reserva.mesa || 'Sin asignar'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">📱 Teléfono:</span>
                            <span class="detail-value">${reserva.telefono}</span>
                        </div>
                    </div>
                    <div class="actions">
                        ${reserva.estado === 'pendiente' ? `
                            <button class="btn btn-success" onclick="confirmarReserva(${reserva.id})">
                                ✅ Confirmar
                            </button>
                        ` : ''}
                        ${!reserva.mesa ? `
                            <button class="btn btn-warning" onclick="asignarMesa(${reserva.id})">
                                🍽️ Asignar Mesa
                            </button>
                        ` : ''}
                    </div>
                </div>
            `).join('');

            document.getElementById('reservas-hoy-count').textContent = reservas.length;
        }

        function renderReservasProximas(reservas) {
            const container = document.getElementById('reservas-proximas');
            
            if (reservas.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🔜</div>
                        <h3>No hay próximas reservas</h3>
                        <p>Las próximas reservas aparecerán aquí</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = reservas.map(reserva => `
                <div class="item">
                    <div class="item-header">
                        <div class="item-title">${reserva.nombre}</div>
                        <div class="status-badge status-${reserva.estado}">${reserva.estado}</div>
                    </div>
                    <div class="item-details">
                        <div class="detail-item">
                            <span class="detail-label">📅 Fecha:</span>
                            <span class="detail-value">${reserva.fecha}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">🕐 Hora:</span>
                            <span class="detail-value">${reserva.hora}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">👥 Personas:</span>
                            <span class="detail-value">${reserva.personas}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">📱 Teléfono:</span>
                            <span class="detail-value">${reserva.telefono}</span>
                        </div>
                    </div>
                </div>
            `).join('');

            document.getElementById('proximas-count').textContent = reservas.length;
        }

        // UTILIDADES
        function updateCounters(type, count) {
            document.getElementById(`${type}-counter`).textContent = count;
        }

        function showNotification(message, type = 'info') {
            const notification = document.getElementById('notification');
            const text = document.getElementById('notification-text');
            
            text.textContent = message;
            notification.className = `notification show ${type}`;
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, CONFIG.notificationDuration);
        }

        function getCsrfToken() {
            const cookieValue = document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='))
                ?.split('=')[1];
            return cookieValue || '';
        }

        // ✅ ACCIONES CON URLs CORREGIDAS
        async function entregarPedido(id) {
            if (!confirm('¿Confirmas que el pedido ha sido entregado?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/pedidos/mesero/entregar/${id}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification('✅ Pedido marcado como entregado', 'success');
                    loadPedidos(); // Recargar datos
                } else {
                    showNotification(`❌ Error: ${data.error}`, 'error');
                }
                
            } catch (error) {
                console.error('Error entregando pedido:', error);
                showNotification('❌ Error al entregar pedido', 'error');
            }
        }

        function verDetalles(id) {
            alert(`Ver detalles del pedido ${id}\n(Esta funcionalidad se puede expandir con un modal)`);
        }

        async function confirmarReserva(id) {
            if (!confirm('¿Confirmar esta reserva?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/pedidos/mesero/confirmar-reserva/${id}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification('✅ Reserva confirmada', 'success');
                    loadReservas(); // Recargar datos
                } else {
                    showNotification(`❌ Error: ${data.error}`, 'error');
                }
                
            } catch (error) {
                console.error('Error confirmando reserva:', error);
                showNotification('❌ Error al confirmar reserva', 'error');
            }
        }

        async function asignarMesa(id) {
            const mesa = prompt('Número de mesa a asignar:');
            if (!mesa) {
                return;
            }
            
            try {
                const response = await fetch(`/api/pedidos/mesero/asignar-mesa/${id}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        mesa_numero: mesa
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification(`🍽️ Mesa ${mesa} asignada`, 'success');
                    loadReservas(); // Recargar datos
                } else {
                    showNotification(`❌ Error: ${data.error}`, 'error');
                }
                
            } catch (error) {
                console.error('Error asignando mesa:', error);
                showNotification('❌ Error al asignar mesa', 'error');
            }
        }

        // AUTO-ACTUALIZACIÓN
        function startAutoUpdate() {
            autoUpdateTimer = setInterval(() => {
                const activeTab = document.querySelector('.tab.active').textContent.includes('Pedidos') ? 'pedidos' : 'reservas';
                
                if (activeTab === 'pedidos') {
                    loadPedidos();
                } else {
                    loadReservas();
                }
                
                lastUpdateTime = Date.now();
                console.log(`🔄 Auto-actualización: ${activeTab} - ${new Date().toLocaleTimeString()}`);
            }, CONFIG.autoUpdateInterval);
        }

        function stopAutoUpdate() {
            if (autoUpdateTimer) {
                clearInterval(autoUpdateTimer);
            }
        }

        // INICIALIZACIÓN
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🧾 Panel Mesero iniciado');
            console.log('🔧 URLs de las APIs:');
            console.log('  - Pedidos: /api/pedidos/mesero/pedidos/');
            console.log('  - Reservas: /api/pedidos/mesero/reservas/');
            
            // Cargar datos iniciales
            loadPedidos();
            
            // Iniciar auto-actualización
            startAutoUpdate();
            
            // Detener auto-actualización cuando la página no esté visible
            document.addEventListener('visibilitychange', function() {
                if (document.hidden) {
                    stopAutoUpdate();
                    console.log('🔄 Auto-actualización pausada (página oculta)');
                } else {
                    startAutoUpdate();
                    console.log('🔄 Auto-actualización reanudada');
                }
            });
        });

        // Cleanup al salir
        window.addEventListener('beforeunload', function() {
            stopAutoUpdate();
        });