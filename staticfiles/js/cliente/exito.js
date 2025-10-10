// Limpiar el localStorage al llegar a la página de éxito
        localStorage.removeItem('pendingOrder');
        
        // Simular progreso del pedido (opcional)
        setTimeout(() => {
            const activeStep = document.querySelector('.step.active');
            const nextStep = activeStep.nextElementSibling;
            
            if (nextStep && nextStep.classList.contains('step')) {
                activeStep.classList.remove('active');
                activeStep.classList.add('completed');
                nextStep.classList.add('active');
            }
        }, 5000); // Simula que pasa al siguiente paso después de 5 segundos