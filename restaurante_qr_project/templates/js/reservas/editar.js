// Configurar fecha mínima como hoy
        document.getElementById('id_fecha_reserva').setAttribute('min', new Date().toISOString().split('T')[0]);