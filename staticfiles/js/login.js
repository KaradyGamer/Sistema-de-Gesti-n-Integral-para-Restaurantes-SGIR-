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
