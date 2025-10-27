# 📋 Guía Completa de Testing - Sistema Restaurante QR

## 📚 Índice

1. [Introducción a las Pruebas de Software](#introducción)
2. [Tipos de Pruebas de Caja](#tipos-de-pruebas)
3. [Pruebas de Caja Negra](#pruebas-caja-negra)
4. [Pruebas de Caja Blanca](#pruebas-caja-blanca)
5. [Pruebas de Caja Gris](#pruebas-caja-gris)
6. [Pruebas de Carga con Locust](#pruebas-con-locust)
7. [Plan de Pruebas para el Sistema](#plan-de-pruebas)

---

## 🎯 Introducción

Las pruebas de software son esenciales para garantizar la calidad, confiabilidad y rendimiento de una aplicación. Existen tres enfoques principales de testing basados en el conocimiento del sistema:

---

## 📦 Tipos de Pruebas de Caja

### 🖤 Caja Negra (Black Box Testing)
**Definición**: Se prueba el sistema sin conocer su estructura interna. Solo se evalúa la funcionalidad desde la perspectiva del usuario.

**Características**:
- ✅ No requiere conocimiento del código
- ✅ Enfoque en entradas y salidas
- ✅ Ideal para pruebas funcionales y de aceptación
- ✅ Simula el comportamiento del usuario final

**Cuándo usar**:
- Pruebas de interfaz de usuario
- Validación de requisitos funcionales
- Pruebas de integración de extremo a extremo
- Pruebas de aceptación del cliente

---

### 🤍 Caja Blanca (White Box Testing)
**Definición**: Se prueba el sistema con pleno conocimiento de su estructura interna, código fuente y lógica de programación.

**Características**:
- ✅ Requiere acceso al código fuente
- ✅ Enfoque en la lógica interna
- ✅ Ideal para pruebas unitarias
- ✅ Verifica rutas de ejecución y estructuras de datos

**Cuándo usar**:
- Pruebas unitarias de funciones
- Análisis de cobertura de código
- Detección de código muerto
- Optimización de algoritmos

---

### 🩶 Caja Gris (Grey Box Testing)
**Definición**: Combina elementos de caja negra y blanca. Se tiene conocimiento parcial del sistema (arquitectura, base de datos, APIs).

**Características**:
- ✅ Conocimiento parcial de la estructura
- ✅ Acceso a documentación técnica
- ✅ Ideal para pruebas de integración
- ✅ Balance entre funcionalidad y estructura

**Cuándo usar**:
- Pruebas de APIs
- Pruebas de base de datos
- Pruebas de integración
- Pruebas de seguridad

---

## 🖤 Pruebas de Caja Negra para el Sistema

### 1. **Pruebas Funcionales de Usuario**

#### 🍽️ Módulo de Pedidos (Cliente)
```
Escenario: Cliente hace un pedido desde QR

Pasos:
1. Escanear código QR de mesa
2. Seleccionar productos del menú
3. Agregar cantidades
4. Confirmar pedido

Resultados esperados:
✅ Pedido aparece en panel de cocina
✅ Pedido aparece en panel de mesero
✅ Estado inicial: "Pendiente"
✅ Productos correctos con cantidades exactas
```

#### 💰 Módulo de Caja
```
Escenario: Cajero procesa pago completo

Pasos:
1. Login como cajero
2. Ir a "Mapa de Mesas"
3. Seleccionar mesa ocupada
4. Clic en "Procesar Pago"
5. Ingresar método de pago y monto
6. Confirmar pago

Resultados esperados:
✅ Pago registrado correctamente
✅ Mesa liberada (estado "Disponible")
✅ Factura generada con número único
✅ Stock descontado automáticamente
```

#### 🔄 Pago Parcial
```
Escenario: Cliente paga solo parte de la cuenta

Pasos:
1. Seleccionar "Pago Separado"
2. Usar botones +/- para seleccionar 3 de 10 productos
3. Confirmar pago parcial
4. Verificar monto pendiente

Resultados esperados:
✅ Monto parcial registrado
✅ Mesa sigue ocupada
✅ Muestra monto pendiente correcto
✅ Permite segundo pago del resto
```

### 2. **Pruebas de Validación**

```
Test: Validación de campos obligatorios
- Intentar crear pedido sin productos → Error
- Intentar pagar con monto insuficiente → Error
- Intentar generar QR sin ser cajero → Error
```

### 3. **Pruebas de Navegación**

```
Test: Flujo completo del pedido
Mesa QR → Cliente pide → Cocina prepara → Mesero entrega → Cajero cobra → Mesa libre
```

---

## 🤍 Pruebas de Caja Blanca para el Sistema

### 1. **Pruebas Unitarias de Funciones**

#### Función: `calcular_total_con_descuento_propina`
```python
def test_calcular_total_con_descuento():
    # Arrange
    pedido = Pedido(total=100, descuento=10, propina=5)

    # Act
    resultado = calcular_total_con_descuento_propina(pedido)

    # Assert
    assert resultado == 95  # 100 - 10 + 5
```

#### Función: `validar_stock_pedido`
```python
def test_validar_stock_insuficiente():
    # Arrange
    producto = Producto(nombre="Pizza", stock=5)
    pedido_detalle = DetallePedido(producto=producto, cantidad=10)

    # Act
    es_valido, productos_sin_stock = validar_stock_pedido(pedido)

    # Assert
    assert es_valido == False
    assert "Pizza" in productos_sin_stock
```

### 2. **Cobertura de Código**

```bash
# Instalar pytest-cov
pip install pytest-cov

# Ejecutar con cobertura
pytest --cov=app --cov-report=html

# Ver reporte en: htmlcov/index.html
```

### 3. **Análisis de Rutas de Ejecución**

```python
# Test: Flujo de pago con diferentes métodos
def test_pago_efectivo_con_cambio():
    # Verificar ruta: efectivo → calcular_cambio → crear_transaccion

def test_pago_tarjeta_sin_cambio():
    # Verificar ruta: tarjeta → crear_transaccion (sin calcular_cambio)
```

---

## 🩶 Pruebas de Caja Gris para el Sistema

### 1. **Pruebas de API**

#### Endpoint: `/api/caja/pago/simple/`
```python
import requests

def test_api_pago_simple():
    url = "http://localhost:8000/api/caja/pago/simple/"
    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": "token_csrf"
    }
    data = {
        "pedido_id": 1,
        "metodo_pago": "efectivo",
        "monto_recibido": 50.00
    }

    response = requests.post(url, json=data, headers=headers)

    assert response.status_code == 200
    assert response.json()["success"] == True
    assert "numero_factura" in response.json()
```

### 2. **Pruebas de Base de Datos**

```python
def test_integridad_referencial():
    # Verificar que al eliminar un producto, sus detalles se manejen correctamente

def test_transacciones_atomicas():
    # Verificar rollback en caso de error durante pago
```

### 3. **Pruebas de Integración**

```python
def test_flujo_completo_pedido():
    # 1. Crear pedido
    # 2. Verificar en base de datos
    # 3. Actualizar estado
    # 4. Procesar pago
    # 5. Verificar mesa liberada
```

---

## 🚀 Pruebas de Carga con Locust

### ¿Qué es Locust?
Locust es una herramienta de pruebas de carga de código abierto que permite simular miles de usuarios concurrentes para evaluar el rendimiento del sistema.

### Instalación
```bash
pip install locust
```

### Casos de Uso para el Sistema

#### 1. **Prueba de Carga en Caja**
**Objetivo**: Simular múltiples cajeros procesando pagos simultáneamente

**Escenarios**:
- 10 cajeros procesando pagos cada 5 segundos
- 50 cajeros durante hora pico
- 100 usuarios consultando mapa de mesas

#### 2. **Prueba de Estrés en Cocina**
**Objetivo**: Verificar que el panel de cocina maneja alta concurrencia

**Escenarios**:
- 20 cocineros actualizando estados
- 100 pedidos entrando simultáneamente
- Kanban con 500+ tarjetas activas

#### 3. **Prueba de Pico en Pedidos**
**Objetivo**: Simular hora pico del restaurante

**Escenarios**:
- 50 clientes pidiendo al mismo tiempo
- 200 productos agregados en 1 minuto
- 30 mesas activas simultáneamente

---

## 📊 Plan de Pruebas Recomendado

### Semana 1: Caja Negra
```
Día 1-2: Pruebas funcionales de módulos
Día 3-4: Pruebas de validación
Día 5: Pruebas de navegación completa
```

### Semana 2: Caja Blanca
```
Día 1-2: Pruebas unitarias de funciones críticas
Día 3: Análisis de cobertura de código
Día 4-5: Pruebas de rutas y lógica interna
```

### Semana 3: Caja Gris
```
Día 1-2: Pruebas de APIs
Día 3: Pruebas de base de datos
Día 4-5: Pruebas de integración
```

### Semana 4: Pruebas de Carga
```
Día 1-2: Configuración de Locust
Día 3-4: Ejecución de pruebas de carga
Día 5: Análisis de resultados y optimización
```

---

## 🎯 Métricas Clave a Medir

### Performance
- ⏱️ Tiempo de respuesta promedio: < 200ms
- 🚀 Throughput: > 100 requests/segundo
- 💾 Uso de memoria: < 80%
- 🔄 Tiempo de carga de página: < 2 segundos

### Confiabilidad
- ✅ Tasa de éxito: > 99.9%
- 🔒 Cero pérdida de datos en transacciones
- 🛡️ Manejo correcto de errores: 100%

### Escalabilidad
- 👥 Usuarios concurrentes: > 100
- 📈 Pedidos simultáneos: > 50
- 🗄️ Consultas DB simultáneas: > 200

---

## 🛠️ Herramientas Recomendadas

### Testing Funcional
- ✅ **Selenium**: Automatización de navegador
- ✅ **Postman**: Pruebas de API
- ✅ **JUnit/PyTest**: Pruebas unitarias

### Testing de Carga
- ✅ **Locust**: Pruebas de carga
- ✅ **Apache JMeter**: Alternativa a Locust
- ✅ **k6**: Pruebas de rendimiento

### Monitoreo
- ✅ **Django Debug Toolbar**: Análisis de consultas
- ✅ **New Relic**: Monitoreo en producción
- ✅ **Sentry**: Tracking de errores

---

## 📌 Próximos Pasos

1. ✅ Revisar esta guía completa
2. ✅ Ejecutar script de Locust (ver `locustfile.py`)
3. ✅ Analizar resultados y optimizar
4. ✅ Documentar hallazgos
5. ✅ Implementar mejoras

---

**Última actualización**: Octubre 2025
**Versión del Sistema**: v36.0
