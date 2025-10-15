let currentPin = '';

// Función switchMode ya no es necesaria en el nuevo diseño
// Ambos paneles están siempre visibles

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

function showEmployeeInfo(e) {
    e.preventDefault();
    showError('Los empleados (meseros y cocineros) deben escanear su código QR para acceder al sistema. Solicita tu código QR al cajero.');
}

// Soporte para teclado físico en modo PIN
// Solo funciona si el foco NO está en los inputs de admin
document.addEventListener('keydown', (e) => {
    const activeElement = document.activeElement;
    const isInputFocused = activeElement.tagName === 'INPUT';

    // Si el usuario no está escribiendo en los campos de admin, permitir entrada de PIN
    if (!isInputFocused) {
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