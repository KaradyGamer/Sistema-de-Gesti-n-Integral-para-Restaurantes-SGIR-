async function generarQR(empleadoId, nombre, rol) {
            try {
                const response = await fetch(`/caja/personal/generar-qr/${empleadoId}/`);
                const data = await response.json();

                if (data.success) {
                    document.getElementById('empleado-nombre').textContent = `${nombre} - ${rol}`;
                    document.getElementById('qr-image').src = data.qr_image;
                    document.getElementById('qrModal').classList.add('show');
                } else {
                    alert('Error: ' + (data.error || 'No se pudo generar el QR'));
                }
            } catch (error) {
                alert('Error de conexión: ' + error.message);
            }
        }

        function cerrarModal() {
            document.getElementById('qrModal').classList.remove('show');
        }

        // Cerrar modal al hacer clic fuera
        document.getElementById('qrModal').addEventListener('click', function(e) {
            if (e.target === this) {
                cerrarModal();
            }
        });