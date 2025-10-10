# 🚀 Actualización Completa del Sistema de Login

## ✅ Archivos Ya Actualizados

### 1. HTML - [templates/login.html](templates/login.html)
✅ **Completado** - Nuevo diseño con botones de selección

### 2. CSS - Necesita actualización
📄 Archivo: `staticfiles/css/login.css`

Agrega estos estilos AL FINAL del archivo (después de la línea 402):

```css
/* ========== VARIABLES CSS (VELOCIDAD AJUSTABLE) ========== */
:root {
    --animation-speed-fast: 0.3s;
    --animation-speed-normal: 0.6s;
    --animation-speed-slow: 0.8s;
    --zoom-duration: 0.8s;
    --cubic-smooth: cubic-bezier(0.25, 0.8, 0.25, 1);
}

/* ========== PANTALLA DE SELECCIÓN ========== */
.selection-screen {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 100vh;
    position: absolute;
    top: 0;
    left: 0;
    z-index: 100;
    transition: opacity var(--animation-speed-normal) var(--cubic-smooth);
}

.selection-screen.hidden {
    opacity: 0;
    pointer-events: none;
}

.button-container {
    display: flex;
    justify-content: center;
    gap: 40px;
    flex-wrap: wrap;
}

/* ========== BOTONES BRUTALIST ========== */
.brutalist-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 180px;
    height: 180px;
    color: #fff;
    font-weight: bold;
    text-decoration: none;
    position: relative;
    cursor: pointer;
    overflow: hidden;
    border: none;
    transition: all var(--animation-speed-normal) var(--cubic-smooth);
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.button-cajero {
    border: 3px solid rgba(66, 196, 152, 0.6);
}

.button-cajero:hover {
    background: rgba(6, 53, 37, 0.4);
    border-color: #42c498;
    transform: translate(-8px, -8px) rotate(2deg);
    box-shadow: 12px 12px 0 rgba(0, 0, 0, 0.4), 18px 18px 25px rgba(66, 196, 152, 0.3);
}

.button-admin {
    border: 3px solid rgba(99, 102, 241, 0.6);
}

.button-admin:hover {
    background: rgba(30, 58, 138, 0.4);
    border-color: #6366f1;
    transform: translate(-8px, -8px) rotate(-2deg);
    box-shadow: 12px 12px 0 rgba(0, 0, 0, 0.4), 18px 18px 25px rgba(99, 102, 241, 0.3);
}

.brutalist-button::before,
.brutalist-button::after {
    content: "";
    position: absolute;
    top: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: 0.6s;
    pointer-events: none;
}

.brutalist-button::before {
    left: -100%;
}

.brutalist-button::after {
    left: 100%;
}

.brutalist-button:hover::before {
    animation: swipeRight 1.5s infinite;
}

.brutalist-button:hover::after {
    animation: swipeLeft 1.5s infinite;
}

@keyframes swipeRight {
    100% {
        transform: translateX(200%) skew(-45deg);
    }
}

@keyframes swipeLeft {
    100% {
        transform: translateX(-200%) skew(-45deg);
    }
}

.button-icon {
    font-size: 64px;
    margin-bottom: 15px;
    transition: all var(--animation-speed-normal) var(--cubic-smooth);
    z-index: 3;
}

.brutalist-button:hover .button-icon {
    transform: translateY(-10px) scale(1.1);
    animation: iconPulse 2s ease-in-out infinite;
}

@keyframes iconPulse {
    0%, 100% {
        transform: translateY(-10px) scale(1.1);
    }
    50% {
        transform: translateY(-10px) scale(1.15);
    }
}

.button-text {
    display: flex;
    flex-direction: column;
    align-items: center;
    line-height: 1.3;
    text-align: center;
    z-index: 3;
}

.small-text {
    font-size: 14px;
    font-weight: 500;
    opacity: 0.9;
}

.main-text {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 1px;
}

.brutalist-button.zoom-in {
    animation: zoomToFullScreen var(--zoom-duration) var(--cubic-smooth) forwards;
    z-index: 1000;
}

@keyframes zoomToFullScreen {
    0% {
        transform: scale(1) translate(0, 0);
    }
    50% {
        transform: scale(1.2) rotate(0deg);
    }
    100% {
        transform: scale(20) translate(0, 0);
        opacity: 0;
    }
}

/* ========== BOTÓN DE VOLVER ========== */
.back-button {
    position: absolute;
    top: 20px;
    left: 20px;
    padding: 12px 24px;
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 12px;
    color: white;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--animation-speed-fast) var(--cubic-smooth);
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 8px;
}

.back-button:hover {
    background: rgba(255, 255, 255, 0.25);
    border-color: rgba(255, 255, 255, 0.5);
    transform: translateX(-5px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.back-button i {
    font-size: 20px;
}

/* ========== OCULTAR PANELES POR DEFECTO ========== */
.welcome-panel,
.wrapper {
    display: none;
    opacity: 0;
    transform: scale(0.8);
    position: relative;
    transition: all var(--animation-speed-slow) var(--cubic-smooth);
}

.welcome-panel.show,
.wrapper.show {
    display: block;
    animation: fadeInScale var(--animation-speed-slow) var(--cubic-smooth) forwards;
}

@keyframes fadeInScale {
    0% {
        opacity: 0;
        transform: scale(0.8);
    }
    100% {
        opacity: 1;
        transform: scale(1);
    }
}

@keyframes fadeOutScale {
    0% {
        opacity: 1;
        transform: scale(1);
    }
    100% {
        opacity: 0;
        transform: scale(0.8);
    }
}

.welcome-panel.hide,
.wrapper.hide {
    animation: fadeOutScale var(--animation-speed-slow) var(--cubic-smooth) forwards;
}

/* Ajustar títulos */
.welcome-content h1,
.wrapper h1 {
    margin-top: 30px;
}
```

### 3. JavaScript - Reemplaza TODO el contenido
📄 Archivo: `staticfiles/js/login.js`

REEMPLAZA todo el contenido del archivo con:

```javascript
let currentPin = '';

// ========== FUNCIONES DE NAVEGACIÓN ==========
function showCajeroPanel() {
    const button = event.target.closest('.button-cajero');
    const selectionScreen = document.getElementById('selectionScreen');
    const cajeroPanel = document.getElementById('cajeroPanel');

    // Animación de zoom del botón
    button.classList.add('zoom-in');

    // Después de la animación, ocultar selección y mostrar panel
    setTimeout(() => {
        selectionScreen.classList.add('hidden');
        cajeroPanel.classList.add('show');
        clearPin(); // Limpiar PIN al entrar
    }, 800); // Duración del zoom
}

function showAdminPanel() {
    const button = event.target.closest('.button-admin');
    const selectionScreen = document.getElementById('selectionScreen');
    const adminPanel = document.getElementById('adminPanel');

    // Animación de zoom del botón
    button.classList.add('zoom-in');

    // Después de la animación, ocultar selección y mostrar panel
    setTimeout(() => {
        selectionScreen.classList.add('hidden');
        adminPanel.classList.add('show');
    }, 800);
}

function backToSelection() {
    const selectionScreen = document.getElementById('selectionScreen');
    const cajeroPanel = document.getElementById('cajeroPanel');
    const adminPanel = document.getElementById('adminPanel');

    // Ocultar paneles con animación
    cajeroPanel.classList.remove('show');
    cajeroPanel.classList.add('hide');
    adminPanel.classList.remove('show');
    adminPanel.classList.add('hide');

    // Después de la animación, mostrar selección y resetear
    setTimeout(() => {
        // Quitar clases de animación
        cajeroPanel.classList.remove('hide');
        adminPanel.classList.remove('hide');

        // Resetear zoom de botones
        document.querySelectorAll('.brutalist-button').forEach(btn => {
            btn.classList.remove('zoom-in');
        });

        // Mostrar pantalla de selección
        selectionScreen.classList.remove('hidden');

        // Limpiar campos
        clearPin();
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        hideMessages();
    }, 800);
}

// ========== FUNCIONES DE PIN ==========
function addDigit(digit) {
    if (currentPin.length < 6) {
        currentPin += digit;
        updatePinDisplay();
    }
}

function clearPin() {
    currentPin = '';
    updatePinDisplay();
}

function updatePinDisplay() {
    const display = document.getElementById('pin-display');
    if (currentPin.length === 0) {
        display.textContent = '••••';
    } else {
        display.textContent = '●'.repeat(currentPin.length);
    }
}

async function loginWithPin() {
    if (currentPin.length < 4) {
        showError('El PIN debe tener al menos 4 dígitos');
        return;
    }

    const loading = document.getElementById('loading');
    loading.classList.add('show');
    hideMessages();

    try {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

        const response = await fetch('/usuarios/login-pin/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ pin: currentPin })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showSuccess('✓ Acceso concedido');
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 500);
        } else {
            showError(data.error || 'PIN incorrecto');
            clearPin();
        }
    } catch (error) {
        showError('Error de conexión. Inténtalo de nuevo.');
        clearPin();
    } finally {
        loading.classList.remove('show');
    }
}

// ========== FUNCIONES DE LOGIN ADMIN ==========
async function loginWithPassword(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!username || !password) {
        showError('Por favor completa todos los campos');
        return;
    }

    const loading = document.getElementById('loading');
    const loginBtn = document.getElementById('loginBtn');

    loading.classList.add('show');
    loginBtn.disabled = true;
    hideMessages();

    try {
        const formData = new FormData(e.target);

        const response = await fetch('/usuarios/login-admin/', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showSuccess('✓ Acceso concedido');
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 500);
        } else {
            showError(data.error || 'Credenciales incorrectas');
        }
    } catch (error) {
        showError('Error de conexión. Inténtalo de nuevo.');
    } finally {
        loading.classList.remove('show');
        loginBtn.disabled = false;
    }
}

// ========== FUNCIONES DE MENSAJES ==========
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
    document.getElementById('successMessage').classList.remove('show');
}

function showSuccess(message) {
    const successMessage = document.getElementById('successMessage');
    successMessage.textContent = message;
    successMessage.classList.add('show');
    document.getElementById('errorMessage').classList.remove('show');
}

function hideMessages() {
    document.getElementById('errorMessage').classList.remove('show');
    document.getElementById('successMessage').classList.remove('show');
}

// ========== SOPORTE PARA TECLADO FÍSICO ==========
document.addEventListener('keydown', (e) => {
    const activeElement = document.activeElement;
    const isInputFocused = activeElement.tagName === 'INPUT';
    const cajeroPanel = document.getElementById('cajeroPanel');
    const isCajeroVisible = cajeroPanel.classList.contains('show');

    // Solo funciona si el panel de cajero está visible y no hay input enfocado
    if (isCajeroVisible && !isInputFocused) {
        if (e.key >= '0' && e.key <= '9') {
            addDigit(e.key);
        } else if (e.key === 'Backspace') {
            currentPin = currentPin.slice(0, -1);
            updatePinDisplay();
        } else if (e.key === 'Enter' && currentPin.length >= 4) {
            loginWithPin();
        } else if (e.key === 'Escape') {
            clearPin();
        }
    }
});

// Soporte para tecla ESC en cualquier panel (volver)
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const selectionScreen = document.getElementById('selectionScreen');
        if (selectionScreen.classList.contains('hidden')) {
            backToSelection();
        }
    }
});
```

## 🚀 Instrucciones de Aplicación

1. ✅ El HTML ya está actualizado
2. ⚠️ Abre `staticfiles/css/login.css` y agrega el CSS al final
3. ⚠️ Abre `staticfiles/js/login.js` y reemplaza todo el contenido
4. 🔄 Reinicia el servidor Django
5. 🌐 Recarga la página con Ctrl+Shift+R

## 🎯 Resultado Esperado

**Pantalla Inicial:**
- 2 botones grandes con efecto glassmorphism
- Botón verde (CAJERO) con icono de calculadora
- Botón azul (ADMIN) con icono de usuario
- Efectos hover brutalist (sombras, rotación)
- Animaciones de brillo continuas

**Al hacer click:**
- Animación de zoom gigante del botón
- Aparece el panel correspondiente con fade in
- Botón "Volver" en cada panel

**Velocidades configurables:**
- Fast: 0.3s
- Normal: 0.6s
- Slow: 0.8s
- Zoom: 0.8s

## ✨ Características Implementadas

✅ Pantalla de selección con botones brutalist
✅ Efecto glassmorphism (transparencia + blur)
✅ Animación de zoom al hacer click
✅ Botón volver con animación inversa
✅ Velocidades de animación ajustables (variables CSS)
✅ Responsive design
✅ Soporte para teclado físico
✅ Tecla ESC para volver

¡LISTO PARA PROBAR! 🎉
