let ventasChart, productosChart;

document.addEventListener('DOMContentLoaded', function() {
    cargarDatos();
});

async function cargarDatos() {
    try {
        // Cargar datos de ventas semanales
        const responseVentas = await fetch('/reportes/api/ventas-semanales/');
        const datosVentas = await responseVentas.json();
        
        // Cargar datos de productos top
        const responseProductos = await fetch('/reportes/api/productos-top/');
        const datosProductos = await responseProductos.json();
        
        // Actualizar métricas
        actualizarMetricas(datosVentas);
        
        // Crear gráficos
        crearGraficoVentas(datosVentas);
        crearGraficoProductos(datosProductos);
        
        // Actualizar tabla
        actualizarTablaProductos(datosProductos);
        
        // Generar análisis inteligente
        generarAnalisisInteligente(datosVentas, datosProductos);
        
    } catch (error) {
        console.error('Error cargando datos:', error);
        mostrarError('Error cargando los datos del dashboard');
    }
}

function actualizarMetricas(datos) {
    document.getElementById('totalVentas').textContent = `Bs/ ${datos.total_semana.toFixed(2)}`;
    document.getElementById('totalPedidos').textContent = datos.total_pedidos;
    
    const promedio = datos.total_pedidos > 0 ? datos.total_semana / datos.total_pedidos : 0;
    document.getElementById('promedioPedido').textContent = `Bs/ ${promedio.toFixed(2)}`;
}

function crearGraficoVentas(datos) {
    const ctx = document.getElementById('ventasChart').getContext('2d');
    
    if (ventasChart) {
        ventasChart.destroy();
    }
    
    ventasChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: datos.ventas_por_dia.map(d => `${d.dia}\n${d.fecha}`),
            datasets: [{
                label: 'Ventas (Bs/)',
                data: datos.ventas_por_dia.map(d => d.ventas),
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }, {
                label: 'Pedidos',
                data: datos.ventas_por_dia.map(d => d.pedidos),
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 2,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            interaction: {
                intersect: false,
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Ventas (Bs/)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Número de Pedidos'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.datasetIndex === 0) {
                                return `Ventas: Bs/ ${context.parsed.y.toFixed(2)}`;
                            } else {
                                return `Pedidos: ${context.parsed.y}`;
                            }
                        }
                    }
                }
            }
        }
    });
}

function crearGraficoProductos(datos) {
    const ctx = document.getElementById('productosChart').getContext('2d');
    
    if (productosChart) {
        productosChart.destroy();
    }
    
    const top5 = datos.productos_top.slice(0, 5);
    
    productosChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: top5.map(p => p.nombre),
            datasets: [{
                data: top5.map(p => p.cantidad),
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const producto = top5[context.dataIndex];
                            return `${producto.nombre}: ${producto.cantidad} unidades (Bs/ ${producto.ingresos.toFixed(2)})`;
                        }
                    }
                }
            }
        }
    });
}

function actualizarTablaProductos(datos) {
    const tbody = document.getElementById('productosTableBody');
    const totalIngresos = datos.productos_top.reduce((sum, p) => sum + p.ingresos, 0);
    
    if (datos.productos_top.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="padding: 20px; text-align: center; color: #666;">No hay datos disponibles</td></tr>';
        return;
    }
    
    tbody.innerHTML = datos.productos_top.map(producto => {
        const porcentaje = totalIngresos > 0 ? (producto.ingresos / totalIngresos * 100).toFixed(1) : 0;
        return `
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 12px; border: 1px solid #ddd;">${producto.nombre}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">${producto.cantidad}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">Bs/ ${producto.ingresos.toFixed(2)}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">${porcentaje}%</td>
            </tr>
        `;
    }).join('');
}

function generarAnalisisInteligente(datosVentas, datosProductos) {
    const analisis = [];
    
    // Análisis de ventas totales
    const totalVentas = datosVentas.total_semana;
    if (totalVentas > 1000) {
        analisis.push("📈 <strong>Excelente desempeño:</strong> Las ventas de esta semana superan los Bs/ 1,000, indicando un rendimiento muy sólido.");
    } else if (totalVentas > 500) {
        analisis.push("📊 <strong>Desempeño promedio:</strong> Las ventas se mantienen en un rango saludable.");
    } else {
        analisis.push("📉 <strong>Oportunidad de mejora:</strong> Las ventas están por debajo del promedio. Considerar promociones o estrategias de marketing.");
    }
    
    // Análisis del día con más ventas
    const mejorDia = datosVentas.ventas_por_dia.reduce((max, dia) => 
        dia.ventas > max.ventas ? dia : max
    );
    
    analisis.push(`🔥 <strong>Día estrella:</strong> ${mejorDia.dia} fue el mejor día con Bs/ ${mejorDia.ventas.toFixed(2)} en ventas. Replicar las estrategias de este día.`);
    
    // Análisis de productos
    if (datosProductos.productos_top.length > 0) {
        const productoEstrella = datosProductos.productos_top[0];
        analisis.push(`⭐ <strong>Producto estrella:</strong> "${productoEstrella.nombre}" lidera las ventas con ${productoEstrella.cantidad} unidades vendidas. Asegurar stock suficiente.`);
    }
    
    // Análisis de promedio por pedido
    const promedio = datosVentas.total_pedidos > 0 ? totalVentas / datosVentas.total_pedidos : 0;
    if (promedio > 25) {
        analisis.push("💰 <strong>Excelente ticket promedio:</strong> Los clientes están gastando bien por pedido. Mantener la calidad del servicio.");
    } else if (promedio > 15) {
        analisis.push("💵 <strong>Ticket promedio saludable:</strong> Hay potencial para aumentar el valor promedio con técnicas de upselling.");
    } else {
        analisis.push("💸 <strong>Oportunidad de upselling:</strong> El ticket promedio es bajo. Considerar combos o sugerencias de productos adicionales.");
    }
    
    // Análisis de diversidad de productos
    const productosVendidos = datosProductos.productos_top.length;
    if (productosVendidos > 10) {
        analisis.push("🎯 <strong>Buena diversidad:</strong> Se están vendiendo múltiples productos, lo que indica un menú balanceado.");
    } else if (productosVendidos < 5) {
        analisis.push("📋 <strong>Concentración alta:</strong> Las ventas se concentran en pocos productos. Evaluar promocionar otros ítems del menú.");
    }
    
    document.getElementById('analisisInteligente').innerHTML = analisis.join('<br><br>');
}

async function actualizarDatos() {
    const button = event.target;
    const textoOriginal = button.textContent;
    
    button.textContent = '🔄 Actualizando...';
    button.disabled = true;
    
    try {
        await cargarDatos();
        button.textContent = '✅ Actualizado';
        setTimeout(() => {
            button.textContent = textoOriginal;
        }, 2000);
    } catch (error) {
        button.textContent = '❌ Error';
        setTimeout(() => {
            button.textContent = textoOriginal;
        }, 2000);
    } finally {
        button.disabled = false;
    }
}

function mostrarError(mensaje) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = 'background: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; margin: 20px 0; border: 1px solid #f5c6cb;';
    errorDiv.textContent = mensaje;
    
    const container = document.querySelector('.module');
    container.insertBefore(errorDiv, container.firstChild);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Responsividad para móviles
if (window.innerWidth < 768) {
    document.querySelector('.charts-container').style.gridTemplateColumns = '1fr';
}