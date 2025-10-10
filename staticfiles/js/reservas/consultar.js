function cancelarReserva(reservaId) {
            if (confirm('¿Estás seguro de que deseas cancelar esta reserva? Esta acción no se puede deshacer.')) {
                fetch(`/reservas/api/cancelar/${reservaId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Reserva cancelada exitosamente.');
                        location.reload();
                    } else {
                        alert('Error al cancelar la reserva: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error al procesar la cancelación.');
                });
            }
        }