function verDetalleMesa(mesaId) {
            // Esta función se puede expandir para mostrar más detalles
            console.log('Ver detalle de mesa:', mesaId);
        }

        // Auto-refresh cada 10 segundos
        setTimeout(() => {
            location.reload();
        }, 10000);

        // Mostrar última actualización
        const now = new Date();
        console.log('Última actualización:', now.toLocaleTimeString());