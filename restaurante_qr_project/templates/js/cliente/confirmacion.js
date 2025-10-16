// Sistema de Confirmación de Pedidos
class OrderConfirmation {
            constructor() {
                this.orderData = null;
                this.init();
            }

            init() {
                // Obtener datos del pedido desde localStorage o URL params
                this.loadOrderData();
            }

            // Obtener CSRF token desde el DOM
            getCSRFToken() {
                // Buscar en input oculto
                const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
                if (tokenInput) {
                    return tokenInput.value;
                }

                // Buscar en meta tag
                const tokenMeta = document.querySelector('meta[name="csrf-token"]');
                if (tokenMeta) {
                    return tokenMeta.content;
                }

                // Buscar en cookies
                const cookies = document.cookie.split(';');
                for (let cookie of cookies) {
                    const [name, value] = cookie.trim().split('=');
                    if (name === 'csrftoken') {
                        return value;
                    }
                }

                console.error('❌ No se encontró el CSRF token');
                return '';
            }

            loadOrderData() {
                try {
                    // Obtener datos del pedido desde localStorage
                    const orderData = localStorage.getItem('pendingOrder');
                    
                    if (orderData) {
                        this.orderData = JSON.parse(orderData);
                        this.renderOrderSummary();
                    } else {
                        // Si no hay datos, redirigir al formulario
                        window.location.href = '/';
                    }
                } catch (error) {
                    console.error('Error cargando datos del pedido:', error);
                    this.showError('Error cargando los datos del pedido');
                }
            }

            renderOrderSummary() {
                const orderContent = document.getElementById('orderContent');
                const actionButtons = document.getElementById('actionButtons');

                if (!this.orderData || !this.orderData.productos || this.orderData.productos.length === 0) {
                    orderContent.innerHTML = '<div class="error">❌ No hay productos en el pedido</div>';
                    return;
                }

                let html = `
                    <div class="mesa-info">
                        <div class="mesa-number">Mesa ${this.orderData.mesa}</div>
                        <div>Tu mesa de servicio</div>
                    </div>

                    <div class="payment-info">
                        <div class="payment-method">${this.getPaymentMethodName(this.orderData.forma_pago)}</div>
                        <div>Método de pago seleccionado</div>
                    </div>

                    <div class="order-summary">
                        <h3>📋 Resumen del Pedido</h3>
                `;

                // Agregar cada producto
                this.orderData.productos.forEach(product => {
                    const subtotal = product.precio * product.cantidad;
                    html += `
                        <div class="order-item">
                            <div class="item-info">
                                <div class="item-name">${product.nombre}</div>
                                <div class="item-quantity">Cantidad: ${product.cantidad}</div>
                            </div>
                            <div class="item-price">Bs ${subtotal.toFixed(2)}</div>
                        </div>
                    `;
                });

                html += '</div>';

                // Total
                html += `
                    <div class="total-section">
                        <div class="total-amount">Bs ${parseFloat(this.orderData.total).toFixed(2)}</div>
                        <div class="total-items">Total: ${this.orderData.productos.reduce((sum, p) => sum + p.cantidad, 0)} productos</div>
                    </div>
                `;

                orderContent.innerHTML = html;
                actionButtons.style.display = 'flex';
            }

            getPaymentMethodName(method) {
                const methods = {
                    'efectivo': '💵 Efectivo',
                    'qr': '📱 Código QR',
                    'tarjeta': '💳 Tarjeta'
                };
                return methods[method] || method;
            }

            async confirmOrder() {
                const confirmBtn = document.getElementById('confirmBtn');
                const originalText = confirmBtn.textContent;
                
                // Mostrar loading
                confirmBtn.textContent = '⏳ Enviando...';
                confirmBtn.disabled = true;

                try {
                    console.log('🚀 Enviando pedido confirmado:', this.orderData);
                    
                    const response = await fetch('/api/pedidos/cliente/crear/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCSRFToken(),
                            'Accept': 'application/json',
                        },
                        credentials: 'same-origin',
                        body: JSON.stringify(this.orderData)
                    });

                    console.log('📥 Response status:', response.status);
                    
                    if (response.ok) {
                        const result = await response.json();
                        console.log('✅ Pedido enviado exitosamente:', result);
                        
                        // Limpiar datos temporales
                        localStorage.removeItem('pendingOrder');
                        
                        // Redirigir a página de éxito
                        window.location.href = '/exito/';
                        
                    } else {
                        let errorMessage = `Error ${response.status}`;
                        try {
                            const errorData = await response.json();
                            console.error('❌ Error del servidor:', errorData);
                            errorMessage = errorData.error || errorData.detail || errorMessage;
                        } catch (e) {
                            console.error('❌ Error parseando respuesta de error');
                        }
                        throw new Error(errorMessage);
                    }
                    
                } catch (error) {
                    console.error('❌ Error enviando pedido:', error);
                    this.showError(`❌ Error al enviar el pedido: ${error.message}`);
                } finally {
                    // Restaurar botón
                    confirmBtn.textContent = originalText;
                    confirmBtn.disabled = false;
                }
            }

            editOrder() {
                // No preguntar confirmación, solo regresar a editar
                console.log('🔄 Regresando al formulario para editar pedido');
                
                // Mantener los datos en localStorage para que se conserven
                // No eliminar: localStorage.removeItem('pendingOrder');
                
                // Regresar al formulario
                window.location.href = '/';
            }

            showError(message) {
                const container = document.querySelector('.container');
                const alert = document.createElement('div');
                alert.className = 'error';
                alert.textContent = message;
                container.insertBefore(alert, container.firstChild);
                
                setTimeout(() => {
                    alert.remove();
                }, 5000);
            }

            showSuccess(message) {
                const container = document.querySelector('.container');
                const alert = document.createElement('div');
                alert.className = 'success';
                alert.innerHTML = message;
                container.insertBefore(alert, container.firstChild);
                
                setTimeout(() => {
                    alert.remove();
                }, 5000);
            }
        }

        // Funciones globales para los botones
        let orderConfirmation;

        function confirmOrder() {
            if (orderConfirmation) {
                orderConfirmation.confirmOrder();
            }
        }

        function editOrder() {
            if (orderConfirmation) {
                orderConfirmation.editOrder();
            }
        }

        // Inicializar cuando se carga la página
        document.addEventListener('DOMContentLoaded', () => {
            orderConfirmation = new OrderConfirmation();
        });