// Sistema de Pedidos para Restaurante
class RestaurantOrderSystem {
            constructor() {
                this.products = {};
                this.cart = {};
                this.total = 0;
                this.activeTab = null;
                this.modalProduct = null;  // ✅ NUEVO: producto actual en modal
                this.modalQuantity = 1;    // ✅ NUEVO: cantidad en modal
                this.init();
            }

            init() {
                this.loadProducts();
                this.bindEvents();
                this.loadPendingOrder();
            }

            // ✅ NUEVA FUNCIÓN: Renderizar pestañas
            renderTabs() {
                const tabsHeader = document.getElementById('tabsHeader');
                const tabsContent = document.getElementById('tabsContent');
                
                if (Object.keys(this.products).length === 0) {
                    tabsHeader.innerHTML = '<div class="error">❌ No se encontraron categorías</div>';
                    tabsContent.innerHTML = '<div class="error">❌ No se encontraron productos</div>';
                    return;
                }

                // ✅ Renderizar botones de pestañas
                let tabsHTML = '';
                const categories = Object.keys(this.products);
                
                categories.forEach((category, index) => {
                    const isActive = index === 0 ? 'active' : '';
                    const categoryIcon = this.getCategoryIcon(category);

                    tabsHTML += `
                        <button type="button" class="tab-button ${isActive}"
                                onclick="orderSystem.switchTab('${category}')"
                                data-category="${category}">
                            <span class="tab-icon">${categoryIcon}</span>
                            <span class="tab-text">${category}</span>
                        </button>
                    `;
                });
                
                tabsHeader.innerHTML = tabsHTML;

                // ✅ Renderizar contenido de pestañas
                let contentHTML = '';
                
                categories.forEach((category, index) => {
                    const isActive = index === 0 ? 'active' : '';
                    const items = this.products[category];
                    
                    contentHTML += `
                        <div class="tab-content ${isActive}" data-category="${category}">
                            <div class="category-header">
                                <div class="category-title">
                                    ${this.getCategoryIcon(category)} ${category}
                                </div>
                                <div class="category-description">
                                    ${this.getCategoryDescription(category)}
                                </div>
                            </div>
                            <div class="product-grid">
                                ${this.renderCategoryProducts(items)}
                            </div>
                        </div>
                    `;
                });
                
                tabsContent.innerHTML = contentHTML;
                
                // Establecer pestaña activa
                if (categories.length > 0) {
                    this.activeTab = categories[0];
                }
            }

            // ✅ NUEVA FUNCIÓN: Cambiar pestaña
            switchTab(category) {
                // Remover active de todos los botones y contenidos
                document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                
                // Agregar active al botón y contenido seleccionado
                document.querySelector(`[data-category="${category}"]`).classList.add('active');
                document.querySelector(`.tab-content[data-category="${category}"]`).classList.add('active');
                
                this.activeTab = category;
                
                // Efecto suave de scroll hacia las pestañas
                document.getElementById('tabsContainer').scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            }

            // ✅ NUEVA FUNCIÓN: Iconos por categoría
            getCategoryIcon(category) {
                const icons = {
                    'Bebidas': '🥤',
                    'Platos Principales': '🍽️',
                    'Entradas': '🥗',
                    'Postres': '🍰',
                    'Sopas': '🍲',
                    'Ensaladas': '🥗',
                    'Desayunos': '🍳',
                    'Cenas': '🌙',
                    'Comida Rápida': '🍔',
                    'Mariscos': '🦐',
                    'Carnes': '🥩',
                    'Vegetariano': '🌱',
                    'Especialidades': '⭐'
                };
                
                return icons[category] || '🍴';
            }

            // ✅ NUEVA FUNCIÓN: Descripciones por categoría
            getCategoryDescription(category) {
                const descriptions = {
                    'Bebidas': 'Refrescantes bebidas para acompañar tu comida',
                    'Platos Principales': 'Deliciosos platos preparados con ingredientes frescos',
                    'Entradas': 'Perfectas para comenzar tu experiencia culinaria',
                    'Postres': 'Dulces momentos para culminar tu comida',
                    'Sopas': 'Caldos reconfortantes y nutritivos',
                    'Ensaladas': 'Frescas y saludables opciones',
                    'Desayunos': 'Energía para comenzar tu día',
                    'Cenas': 'Opciones especiales para la noche',
                    'Comida Rápida': 'Sabor rápido sin comprometer calidad',
                    'Mariscos': 'Frescos del mar para los amantes del océano',
                    'Carnes': 'Jugosas carnes preparadas a la perfección',
                    'Vegetariano': 'Opciones saludables libres de carne',
                    'Especialidades': 'Lo mejor de nuestra cocina'
                };
                
                return descriptions[category] || 'Deliciosas opciones para tu paladar';
            }

            // ✅ MODIFICADA: Renderizar productos de una categoría
            renderCategoryProducts(items) {
                let html = '';
                
                items.forEach(product => {
                    const quantity = this.cart[product.id] || 0;
                    
                    // Manejo de imágenes mejorado
                    let imageUrl = this.getProductImage(product);
                    
                    html += `
                        <div class="product-card" data-product-id="${product.id}">
                            <div class="product-image" onclick="orderSystem.openProductModal(${product.id})" style="cursor: pointer;">
                                <img src="${imageUrl}"
                                     alt="${product.nombre}"
                                     loading="lazy"
                                     onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=300&h=200&fit=crop&crop=center';">
                            </div>
                            <div class="product-info" onclick="orderSystem.openProductModal(${product.id})" style="cursor: pointer;">
                                <div class="product-name">${product.nombre}</div>
                                <div class="product-description">${product.descripcion || 'Delicioso producto preparado con ingredientes frescos'}</div>
                                <div class="product-price">Bs/ ${parseFloat(product.precio).toFixed(2)}</div>
                            </div>
                            <div class="quantity-control">
                                <button type="button" class="quantity-btn" onclick="orderSystem.decreaseQuantity(${product.id})" ${quantity <= 0 ? 'disabled' : ''}>−</button>
                                <span class="quantity-display">${quantity}</span>
                                <button type="button" class="quantity-btn" onclick="orderSystem.increaseQuantity(${product.id})">+</button>
                            </div>
                        </div>
                    `;
                });
                
                return html;
            }

            // ✅ NUEVA FUNCIÓN: Obtener imagen del producto
            getProductImage(product) {
                if (product.imagen && product.imagen.trim() !== '') {
                    if (product.imagen.startsWith('/media/')) {
                        return product.imagen;
                    } else if (product.imagen.startsWith('http')) {
                        return product.imagen;
                    } else {
                        return `/media/${product.imagen}`;
                    }
                } else {
                    // Imágenes por defecto según el nombre del producto
                    const productName = product.nombre.toLowerCase();
                    if (productName.includes('coca') || productName.includes('cola')) {
                        return 'https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=300&h=200&fit=crop&crop=center';
                    } else if (productName.includes('fanta') || productName.includes('naranja')) {
                        return 'https://images.unsplash.com/photo-1613478223719-2ab802602423?w=300&h=200&fit=crop&crop=center';
                    } else if (productName.includes('sprite') || productName.includes('spiter')) {
                        return 'https://images.unsplash.com/photo-1625772299848-391b6a87d7b3?w=300&h=200&fit=crop&crop=center';
                    } else if (productName.includes('sopa')) {
                        return 'https://images.unsplash.com/photo-1547592180-85f173990554?w=300&h=200&fit=crop&crop=center';
                    } else if (productName.includes('pollo')) {
                        return 'https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?w=300&h=200&fit=crop&crop=center';
                    } else if (productName.includes('pescado')) {
                        return 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=300&h=200&fit=crop&crop=center';
                    } else {
                        return 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=300&h=200&fit=crop&crop=center';
                    }
                }
            }

            // ✅ FUNCIÓN EXISTENTE MODIFICADA: Cargar pedido pendiente
            loadPendingOrder() {
                try {
                    // Obtener número de mesa desde URL (tiene prioridad)
                    const urlParams = new URLSearchParams(window.location.search);
                    const mesaFromUrl = urlParams.get('mesa');

                    const pendingOrder = localStorage.getItem('pendingOrder');
                    if (pendingOrder) {
                        const orderData = JSON.parse(pendingOrder);
                        console.log('🔄 Cargando pedido pendiente:', orderData);

                        // Si hay mesa en URL, usar esa; sino usar la del localStorage
                        if (mesaFromUrl) {
                            document.getElementById('tableNumber').value = mesaFromUrl;
                            console.log('✅ Número de mesa desde URL:', mesaFromUrl);
                        } else if (orderData.mesa || orderData.mesa_id) {
                            document.getElementById('tableNumber').value = orderData.mesa || orderData.mesa_id;
                        }


                        if (orderData.productos && Array.isArray(orderData.productos)) {
                            this.cart = {};
                            orderData.productos.forEach(producto => {
                                const id = producto.producto_id || producto.id;
                                const cantidad = producto.cantidad;
                                if (id && cantidad > 0) {
                                    this.cart[id] = cantidad;
                                }
                            });
                        }

                        setTimeout(() => {
                            this.renderTabs();
                            this.updateDisplay();
                        }, 500);
                    } else if (mesaFromUrl) {
                        // No hay pedido pendiente pero sí hay mesa en URL
                        document.getElementById('tableNumber').value = mesaFromUrl;
                        console.log('✅ Número de mesa desde URL (sin pedido previo):', mesaFromUrl);
                    }
                } catch (error) {
                    console.error('Error cargando pedido pendiente:', error);
                    localStorage.removeItem('pendingOrder');
                }
            }

            // ✅ FUNCIÓN EXISTENTE MODIFICADA: Cargar productos
            async loadProducts() {
                try {
                    console.log('🔄 Cargando productos...');
                    
                    const baseUrl = window.location.origin;
                    const apiUrl = `${baseUrl}/api/productos/agrupados/`;
                    
                    console.log('📡 Llamando a:', apiUrl);
                    
                    const response = await fetch(apiUrl, {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                        },
                        credentials: 'same-origin'
                    });
                    
                    console.log('📥 Response status:', response.status);
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    console.log('✅ Datos completos recibidos:', data);
                    
                    if (data.categorias && Array.isArray(data.categorias)) {
                        this.products = {};
                        
                        data.categorias.forEach(categoria => {
                            this.products[categoria.nombre] = categoria.productos;
                        });
                        
                        console.log('✅ Productos procesados:', this.products);
                        this.renderTabs(); // ✅ CAMBIADO: usar renderTabs en lugar de renderProducts
                        
                    } else if (data && typeof data === 'object') {
                        this.products = data;
                        this.renderTabs(); // ✅ CAMBIADO: usar renderTabs en lugar de renderProducts
                        
                    } else {
                        throw new Error('Formato de respuesta inválido');
                    }
                    
                } catch (error) {
                    console.warn('⚠️ Error cargando desde API:', error);
                    
                    const tabsHeader = document.getElementById('tabsHeader');
                    const tabsContent = document.getElementById('tabsContent');
                    
                    tabsHeader.innerHTML = `
                        <div class="error">
                            ❌ Error cargando categorías: ${error.message}
                        </div>
                    `;
                    
                    tabsContent.innerHTML = `
                        <div class="error">
                            ❌ Error cargando productos: ${error.message}<br>
                            <small>Verifica que el servidor esté corriendo en ${window.location.origin}</small><br>
                            <button onclick="orderSystem.loadProducts()" style="margin-top: 10px; padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer;">🔄 Reintentar</button>
                        </div>
                    `;
                }
            }

            // ✅ RESTO DE FUNCIONES EXISTENTES (sin cambios)
            increaseQuantity(productId) {
                this.cart[productId] = (this.cart[productId] || 0) + 1;
                this.updateDisplay();
                this.updateQuantityButton(productId);
            }

            decreaseQuantity(productId) {
                if (this.cart[productId] > 0) {
                    this.cart[productId]--;
                    if (this.cart[productId] === 0) {
                        delete this.cart[productId];
                    }
                    this.updateDisplay();
                    this.updateQuantityButton(productId);
                }
            }

            updateQuantityButton(productId) {
                const productCard = document.querySelector(`[data-product-id="${productId}"]`);
                if (productCard) {
                    const quantityDisplay = productCard.querySelector('.quantity-display');
                    const decreaseBtn = productCard.querySelector('.quantity-btn:first-child');
                    const quantity = this.cart[productId] || 0;
                    
                    quantityDisplay.textContent = quantity;
                    decreaseBtn.disabled = quantity <= 0;
                }
            }

            updateDisplay() {
                this.calculateTotal();
                document.getElementById('totalAmount').textContent = this.total.toFixed(2);
                document.getElementById('totalItems').textContent = Object.values(this.cart).reduce((sum, qty) => sum + qty, 0);

                const submitBtn = document.getElementById('submitBtn');
                const hasItems = Object.keys(this.cart).length > 0;
                const hasTable = document.getElementById('tableNumber').value.trim() !== '';
                // ✅ NUEVO: Verificar número de personas
                const numberOfPeopleInput = document.getElementById('numberOfPeople');
                const hasPeople = numberOfPeopleInput ? numberOfPeopleInput.value.trim() !== '' && parseInt(numberOfPeopleInput.value) > 0 : true;

                submitBtn.disabled = !(hasItems && hasTable && hasPeople);
            }

            calculateTotal() {
                this.total = 0;
                for (const [productId, quantity] of Object.entries(this.cart)) {
                    const product = this.findProductById(parseInt(productId));
                    if (product) {
                        this.total += parseFloat(product.precio) * quantity;
                    }
                }
            }

            findProductById(id) {
                for (const items of Object.values(this.products)) {
                    const product = items.find(p => p.id === id);
                    if (product) return product;
                }
                return null;
            }

            bindEvents() {
                document.getElementById('tableNumber').addEventListener('input', () => {
                    this.updateDisplay();
                });

                // ✅ NUEVO: Event listener para número de personas
                const numberOfPeopleInput = document.getElementById('numberOfPeople');
                if (numberOfPeopleInput) {
                    numberOfPeopleInput.addEventListener('input', () => {
                        this.updateDisplay();
                    });
                }

                document.getElementById('orderForm').addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.submitOrder();
                });

                // ✅ NUEVO: Cerrar modal al hacer clic fuera
                const modal = document.getElementById('productModal');
                if (modal) {
                    modal.addEventListener('click', (e) => {
                        if (e.target === modal) {
                            this.closeProductModal();
                        }
                    });
                }
            }

            async submitOrder() {
                const tableNumber = document.getElementById('tableNumber').value;
                // ✅ NUEVO: Capturar número de personas
                const numberOfPeople = document.getElementById('numberOfPeople')?.value;
                // ✅ NUEVO: Capturar ID del usuario (mesero)
                const userId = document.getElementById('userId')?.value;

                if (!tableNumber) {
                    alert('❌ Por favor completa el número de mesa');
                    return;
                }

                // ✅ NUEVO: Validar número de personas
                if (!numberOfPeople || numberOfPeople < 1) {
                    alert('❌ Por favor indica el número de personas');
                    return;
                }

                if (Object.keys(this.cart).length === 0) {
                    alert('❌ Por favor selecciona al menos un producto');
                    return;
                }

                const productosValidos = Object.entries(this.cart).filter(([id, cantidad]) => cantidad > 0);
                if (productosValidos.length === 0) {
                    alert('❌ Por favor selecciona al menos un producto con cantidad mayor a 0');
                    return;
                }

                const submitBtn = document.getElementById('submitBtn');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = '⏳ Preparando pedido...';
                submitBtn.disabled = true;

                try {
                    const productosDetallados = productosValidos.map(([id, cantidad]) => {
                        const product = this.findProductById(parseInt(id));
                        return {
                            producto_id: parseInt(id),
                            producto: parseInt(id),
                            id: parseInt(id),
                            cantidad: cantidad,
                            nombre: product?.nombre || 'Producto',
                            precio: product?.precio || 0
                        };
                    });

                    const orderData = {
                        mesa_id: parseInt(tableNumber),
                        mesa: parseInt(tableNumber),
                        numero_mesa: parseInt(tableNumber),
                        numero_personas: parseInt(numberOfPeople),  // ✅ NUEVO
                        productos: productosDetallados,
                        detalles: productosDetallados,
                        total: parseFloat(this.total.toFixed(2))
                    };

                    // ✅ NUEVO: Agregar mesero_id si existe
                    if (userId) {
                        orderData.mesero_id = parseInt(userId);
                        orderData.usuario_id = parseInt(userId);
                    }

                    console.log('📋 Preparando datos para confirmación:', orderData);

                    localStorage.setItem('pendingOrder', JSON.stringify(orderData));

                    this.showSuccess('📋 Preparando confirmación de tu pedido...');

                    setTimeout(() => {
                        window.location.href = '/confirmacion/';
                    }, 1000);

                } catch (error) {
                    console.error('❌ Error preparando pedido:', error);
                    this.showError(`❌ Error al preparar el pedido: ${error.message}`);
                } finally {
                    setTimeout(() => {
                        submitBtn.textContent = originalText;
                        submitBtn.disabled = false;
                        this.updateDisplay();
                    }, 2000);
                }
            }

            getCSRFToken() {
                const name = 'csrftoken';
                const cookies = document.cookie.split(';');
                for (let cookie of cookies) {
                    const trimmed = cookie.trim();
                    if (trimmed.startsWith(name + '=')) {
                        return decodeURIComponent(trimmed.substring(name.length + 1));
                    }
                }
                
                const csrfMeta = document.querySelector('meta[name="csrf-token"]');
                if (csrfMeta) {
                    return csrfMeta.getAttribute('content');
                }
                
                const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
                if (csrfInput) {
                    return csrfInput.value;
                }
                
                if (window.csrfToken) {
                    return window.csrfToken;
                }
                
                console.warn('⚠️ No se encontró CSRF token');
                return '';
            }

            showSuccess(message) {
                const container = document.querySelector('.container');
                const alert = document.createElement('div');
                alert.className = 'success';
                alert.innerHTML = message;
                container.insertBefore(alert, container.firstChild);
                
                window.scrollTo({ top: 0, behavior: 'smooth' });
                
                setTimeout(() => {
                    alert.remove();
                }, 7000);
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

            // ✅ NUEVO: Abrir modal de producto
            openProductModal(productId) {
                console.log('🔍 Abriendo modal para producto ID:', productId);
                const product = this.findProductById(productId);
                if (!product) {
                    console.error('❌ Producto no encontrado:', productId);
                    return;
                }
                console.log('✅ Producto encontrado:', product);

                this.modalProduct = product;
                this.modalQuantity = this.cart[productId] || 1;

                // Actualizar contenido del modal
                document.getElementById('modalProductName').textContent = product.nombre;
                document.getElementById('modalProductDescription').textContent = product.descripcion || 'Delicioso producto preparado con ingredientes frescos';
                document.getElementById('modalProductPrice').textContent = `Bs/ ${parseFloat(product.precio).toFixed(2)}`;

                const imageUrl = this.getProductImage(product);
                document.getElementById('modalProductImage').src = imageUrl;
                document.getElementById('modalProductImage').alt = product.nombre;

                document.getElementById('modalQuantity').textContent = this.modalQuantity;
                this.updateModalSubtotal();

                // Mostrar modal
                const modal = document.getElementById('productModal');
                modal.classList.add('active');
                document.body.style.overflow = 'hidden'; // Prevenir scroll
            }

            // ✅ NUEVO: Cerrar modal
            closeProductModal() {
                const modal = document.getElementById('productModal');
                modal.classList.remove('active');
                document.body.style.overflow = ''; // Restaurar scroll
                this.modalProduct = null;
                this.modalQuantity = 1;
            }

            // ✅ NUEVO: Incrementar cantidad en modal
            increaseModalQuantity() {
                this.modalQuantity++;
                document.getElementById('modalQuantity').textContent = this.modalQuantity;
                this.updateModalSubtotal();
            }

            // ✅ NUEVO: Decrementar cantidad en modal
            decreaseModalQuantity() {
                if (this.modalQuantity > 1) {
                    this.modalQuantity--;
                    document.getElementById('modalQuantity').textContent = this.modalQuantity;
                    this.updateModalSubtotal();
                }
            }

            // ✅ NUEVO: Actualizar subtotal del modal
            updateModalSubtotal() {
                if (this.modalProduct) {
                    const subtotal = parseFloat(this.modalProduct.precio) * this.modalQuantity;
                    document.getElementById('modalSubtotal').textContent = `Bs/ ${subtotal.toFixed(2)}`;
                }
            }

            // ✅ NUEVO: Agregar producto desde el modal
            addFromModal() {
                if (!this.modalProduct) return;

                // Agregar o actualizar cantidad en el carrito
                this.cart[this.modalProduct.id] = this.modalQuantity;

                // Actualizar display principal
                this.updateDisplay();

                // Actualizar el botón de cantidad en la tarjeta del producto
                this.updateQuantityButton(this.modalProduct.id);

                // Cerrar modal
                this.closeProductModal();

                // Mostrar mensaje de éxito
                this.showSuccess(`✓ ${this.modalProduct.nombre} agregado al pedido`);
            }

            // ✅ NUEVO: Búsqueda global de productos
            setupGlobalSearch() {
                const searchInput = document.getElementById('globalSearch');
                const clearBtn = document.getElementById('clearSearch');
                const resultsContainer = document.getElementById('searchResults');

                if (!searchInput) return;

                let searchTimeout;

                searchInput.addEventListener('input', (e) => {
                    const query = e.target.value.trim().toLowerCase();

                    // Mostrar/ocultar botón limpiar
                    clearBtn.style.display = query ? 'flex' : 'none';

                    // Limpiar timeout anterior
                    clearTimeout(searchTimeout);

                    if (!query) {
                        resultsContainer.style.display = 'none';
                        return;
                    }

                    // Buscar después de 300ms (debounce)
                    searchTimeout = setTimeout(() => {
                        this.performSearch(query, resultsContainer);
                    }, 300);
                });

                // Botón limpiar búsqueda
                clearBtn.addEventListener('click', () => {
                    searchInput.value = '';
                    clearBtn.style.display = 'none';
                    resultsContainer.style.display = 'none';
                    searchInput.focus();
                });

                // Cerrar resultados al hacer clic fuera
                document.addEventListener('click', (e) => {
                    if (!e.target.closest('.search-container')) {
                        resultsContainer.style.display = 'none';
                    }
                });
            }

            // ✅ NUEVO: Realizar búsqueda con coincidencias parciales
            performSearch(query, resultsContainer) {
                const results = [];

                // Buscar en todos los productos de todas las categorías
                Object.keys(this.products).forEach(category => {
                    this.products[category].forEach(product => {
                        if (!product.disponible) return; // Ignorar no disponibles

                        const nombre = product.nombre.toLowerCase();
                        const descripcion = (product.descripcion || '').toLowerCase();

                        // Búsqueda por coincidencia parcial
                        if (nombre.includes(query) || descripcion.includes(query)) {
                            results.push({
                                ...product,
                                category,
                                matchInName: nombre.includes(query),
                                matchInDescription: descripcion.includes(query)
                            });
                        }
                    });
                });

                this.displaySearchResults(results, query, resultsContainer);
            }

            // ✅ NUEVO: Mostrar resultados de búsqueda
            displaySearchResults(results, query, container) {
                if (results.length === 0) {
                    container.innerHTML = `
                        <div class="search-no-results">
                            <div class="search-no-results-icon">🔍</div>
                            <div class="search-no-results-text">No se encontraron productos</div>
                            <div class="search-no-results-hint">Intenta con: "${query.charAt(0).toUpperCase() + query.slice(1)}", o busca por categoría</div>
                        </div>
                    `;
                    container.style.display = 'block';
                    return;
                }

                const html = results.map(product => {
                    // Resaltar coincidencias
                    const highlightedName = this.highlightMatch(product.nombre, query);
                    const highlightedDesc = product.descripcion ?
                        this.highlightMatch(product.descripcion, query) :
                        `Categoría: ${product.category}`;

                    return `
                        <div class="search-result-item" onclick="orderSystem.selectSearchResult(${product.id})">
                            <img src="${product.imagen || '/static/images/no-image.png'}"
                                 alt="${product.nombre}"
                                 class="search-result-image"
                                 onerror="this.src='/static/images/no-image.png'">
                            <div class="search-result-info">
                                <div class="search-result-name">${highlightedName}</div>
                                <div class="search-result-description">${highlightedDesc}</div>
                            </div>
                            <div class="search-result-price">Bs/ ${parseFloat(product.precio).toFixed(2)}</div>
                        </div>
                    `;
                }).join('');

                container.innerHTML = html;
                container.style.display = 'block';
            }

            // ✅ NUEVO: Resaltar coincidencias en texto
            highlightMatch(text, query) {
                const regex = new RegExp(`(${query})`, 'gi');
                return text.replace(regex, '<mark>$1</mark>');
            }

            // ✅ NUEVO: Seleccionar producto desde resultados de búsqueda
            selectSearchResult(productId) {
                // Buscar el producto en todas las categorías
                let foundProduct = null;
                let foundCategory = null;

                Object.keys(this.products).forEach(category => {
                    const product = this.products[category].find(p => p.id === productId);
                    if (product) {
                        foundProduct = product;
                        foundCategory = category;
                    }
                });

                if (foundProduct) {
                    // Cerrar búsqueda
                    document.getElementById('globalSearch').value = '';
                    document.getElementById('clearSearch').style.display = 'none';
                    document.getElementById('searchResults').style.display = 'none';

                    // Cambiar a la pestaña de la categoría del producto
                    this.switchTab(foundCategory);

                    // Abrir modal del producto
                    setTimeout(() => {
                        this.openProductModal(foundProduct);
                    }, 300);
                }
            }

            resetForm() {
                this.cart = {};
                this.total = 0;
                document.getElementById('tableNumber').value = '';
                this.renderTabs();
                this.updateDisplay();
            }
        }

        // Inicializar el sistema cuando se carga la página
        let orderSystem;
        document.addEventListener('DOMContentLoaded', () => {
            console.log('🚀 Iniciando sistema de pedidos...');
            orderSystem = new RestaurantOrderSystem();
            console.log('✅ Sistema de pedidos iniciado:', orderSystem);

            // ✅ Inicializar búsqueda global
            orderSystem.setupGlobalSearch();
            console.log('🔍 Búsqueda global activada');
        });