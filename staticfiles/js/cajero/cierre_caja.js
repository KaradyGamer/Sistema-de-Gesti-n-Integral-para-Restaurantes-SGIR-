const efectivoEsperado = parseFloat('{{ cierre.efectivo_esperado|default:0 }}');

        document.getElementById('efectivo_real')?.addEventListener('input', function() {
            const efectivoReal = parseFloat(this.value) || 0;
            const diferencia = efectivoReal - efectivoEsperado;

            const container = document.getElementById('diferencia-container');
            const box = document.getElementById('diferencia-box');
            const texto = document.getElementById('diferencia-texto');

            container.style.display = 'block';

            // Remover clases anteriores
            box.classList.remove('positive', 'negative', 'neutral');

            if (diferencia > 0) {
                box.classList.add('positive');
                texto.innerHTML = `✓ Sobrante: Bs/ ${diferencia.toFixed(2)}`;
            } else if (diferencia < 0) {
                box.classList.add('negative');
                texto.innerHTML = `⚠️ Faltante: Bs/ ${Math.abs(diferencia).toFixed(2)}`;
            } else {
                box.classList.add('neutral');
                texto.innerHTML = `✓ Sin diferencia - Cuadre perfecto`;
            }
        });

        document.getElementById('cierre-form')?.addEventListener('submit', function(e) {
            e.preventDefault();

            const efectivoReal = parseFloat(document.getElementById('efectivo_real').value) || 0;
            const diferencia = efectivoReal - efectivoEsperado;

            let mensaje = `¿Confirmar cierre de caja?\n\n`;
            mensaje += `Efectivo Esperado: Bs/ ${efectivoEsperado.toFixed(2)}\n`;
            mensaje += `Efectivo Real: Bs/ ${efectivoReal.toFixed(2)}\n`;

            if (diferencia !== 0) {
                mensaje += `\n⚠️ Diferencia: Bs/ ${diferencia.toFixed(2)}\n`;
            } else {
                mensaje += `\n✓ Cuadre perfecto\n`;
            }

            if (confirm(mensaje)) {
                this.submit();
            }
        });

        // Calcular diferencia inicial si ya hay un valor
        if (document.getElementById('efectivo_real')?.value) {
            document.getElementById('efectivo_real').dispatchEvent(new Event('input'));
        }