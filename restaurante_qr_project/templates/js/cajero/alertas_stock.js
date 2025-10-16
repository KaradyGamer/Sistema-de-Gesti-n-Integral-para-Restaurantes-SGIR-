function filtrarAlertas() {
            const filtro = document.getElementById('filtro-tipo').value;
            const alertas = document.querySelectorAll('.alert');

            alertas.forEach(alerta => {
                const tipo = alerta.dataset.tipo;

                if (filtro === 'todas') {
                    alerta.style.display = 'flex';
                } else if (filtro === tipo) {
                    alerta.style.display = 'flex';
                } else {
                    alerta.style.display = 'none';
                }
            });
        }

        // Auto-refresh cada 60 segundos
        setTimeout(() => {
            location.reload();
        }, 60000);