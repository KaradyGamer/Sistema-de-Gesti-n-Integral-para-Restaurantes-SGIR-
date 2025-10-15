# 🧪 Guía de Testing - Sistema de Gestión de Restaurantes

## 📋 Tabla de Contenidos
- [Estructura de Tests](#estructura-de-tests)
- [Ejecutar Tests](#ejecutar-tests)
- [Cobertura de Tests](#cobertura-de-tests)
- [Tests Disponibles](#tests-disponibles)

## 🏗️ Estructura de Tests

Los tests están organizados por módulo de la aplicación:

```
restaurante_qr_project/
├── app/
│   ├── pedidos/
│   │   └── tests.py          # Tests de pedidos (27 tests)
│   ├── caja/
│   │   └── tests.py          # Tests de caja y pagos (18 tests)
│   └── reservas/
│       └── tests.py          # Tests de reservas (15 tests)
```

## ▶️ Ejecutar Tests

### Ejecutar TODOS los tests
```bash
cd restaurante_qr_project
python manage.py test
```

### Ejecutar tests de un módulo específico
```bash
# Solo tests de pedidos
python manage.py test app.pedidos

# Solo tests de caja
python manage.py test app.caja

# Solo tests de reservas
python manage.py test app.reservas
```

### Ejecutar un test específico
```bash
# Ejecutar una clase de test específica
python manage.py test app.pedidos.tests.PedidoModelTestCase

# Ejecutar un método de test específico
python manage.py test app.pedidos.tests.PedidoModelTestCase.test_crear_pedido
```

### Ejecutar tests con verbosidad
```bash
# Nivel 2 de verbosidad (muestra cada test)
python manage.py test --verbosity=2

# Nivel 3 de verbosidad (máximo detalle)
python manage.py test --verbosity=3
```

### Ejecutar tests y mantener la base de datos
```bash
# Útil para debugging
python manage.py test --keepdb
```

## 📊 Cobertura de Tests

### Instalar coverage
```bash
pip install coverage
```

### Ejecutar tests con cobertura
```bash
# Ejecutar tests y medir cobertura
coverage run --source='app' manage.py test

# Ver reporte en consola
coverage report

# Generar reporte HTML
coverage html
```

### Ver reporte HTML
```bash
# Abrir en el navegador
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html  # Linux
```

## 📝 Tests Disponibles

### 1. Tests de Pedidos (`app.pedidos.tests`)

#### `PedidoModelTestCase` - Tests del modelo
- ✅ `test_crear_pedido` - Crear pedido básico
- ✅ `test_crear_detalle_pedido` - Crear detalles de pedido
- ✅ `test_calcular_total_pedido` - Calcular total correctamente
- ✅ `test_cambiar_estado_pedido` - Cambiar estados de pedido

#### `PedidoAPITestCase` - Tests de APIs
- ✅ `test_crear_pedido_cliente_api` - Crear pedido desde API cliente
- ✅ `test_actualizar_estado_pedido_autenticado` - Actualizar estado requiere auth

#### `PedidoValidacionTestCase` - Tests de validación
- ✅ `test_pedido_sin_mesa_falla` - Pedido requiere mesa
- ✅ `test_detalle_sin_cantidad_falla` - Detalle requiere cantidad

#### `PedidoIntegracionTestCase` - Tests de integración
- ✅ `test_flujo_completo_pedido` - Flujo completo: creación → entrega

**Total: 9 tests**

### 2. Tests de Caja (`app.caja.tests`)

#### `TransaccionModelTestCase` - Tests de transacciones
- ✅ `test_crear_transaccion_efectivo` - Transacción en efectivo
- ✅ `test_crear_transaccion_tarjeta` - Transacción con tarjeta
- ✅ `test_transaccion_mixta` - Transacción mixta (efectivo + tarjeta)

#### `CierreCajaModelTestCase` - Tests de cierre de caja
- ✅ `test_abrir_caja` - Abrir turno de caja
- ✅ `test_cerrar_caja` - Cerrar turno de caja
- ✅ `test_calcular_diferencia_caja` - Calcular diferencia efectivo

#### `UtilsTestCase` - Tests de funciones utilitarias
- ✅ `test_generar_numero_factura` - Generar número único
- ✅ `test_calcular_cambio` - Calcular cambio correcto
- ✅ `test_calcular_cambio_exacto` - Sin cambio cuando es exacto
- ✅ `test_calcular_total_con_descuento` - Total con descuento
- ✅ `test_calcular_total_con_propina` - Total con propina
- ✅ `test_validar_stock_producto_disponible` - Validar stock suficiente

#### `IntegracionCajaTestCase` - Tests de integración
- ✅ `test_flujo_completo_pago` - Flujo completo: apertura → pago → cierre

**Total: 13 tests**

### 3. Tests de Reservas (`app.reservas.tests`)

#### `ReservaModelTestCase` - Tests del modelo
- ✅ `test_crear_reserva` - Crear reserva básica
- ✅ `test_asignar_mesa_reserva` - Asignar mesa a reserva
- ✅ `test_estados_reserva` - Cambiar estados de reserva
- ✅ `test_cancelar_reserva` - Cancelar una reserva

#### `ReservaFormTestCase` - Tests del formulario
- ✅ `test_form_valido` - Formulario válido
- ✅ `test_fecha_pasada_invalida` - No reservar fechas pasadas
- ✅ `test_hora_fuera_horario_invalida` - Validar horario de atención
- ✅ `test_telefono_invalido` - Validar formato de teléfono
- ✅ `test_numero_personas_invalido` - Validar número de personas
- ✅ `test_carnet_invalido_corto` - Validar longitud de carnet

#### `ReservaIntegracionTestCase` - Tests de integración
- ✅ `test_flujo_completo_reserva` - Flujo completo de reserva
- ✅ `test_asignar_mesa_segun_capacidad` - Asignar mesa adecuada
- ✅ `test_multiples_reservas_mismo_dia` - Múltiples reservas por día

**Total: 13 tests**

---

## 🎯 Resumen Total

| Módulo | Tests | Estado |
|--------|-------|--------|
| Pedidos | 9 | ✅ |
| Caja | 13 | ✅ |
| Reservas | 13 | ✅ |
| **TOTAL** | **35** | ✅ |

## 📌 Notas Importantes

### Base de datos de prueba
- Django crea automáticamente una base de datos de prueba
- Los datos de prueba NO afectan tu base de datos real
- La base de datos de prueba se destruye después de ejecutar los tests

### Mejores prácticas
1. **Ejecuta tests antes de hacer commit**
   ```bash
   python manage.py test && git add . && git commit -m "mensaje"
   ```

2. **Ejecuta tests después de cada cambio importante**
   ```bash
   python manage.py test app.pedidos --verbosity=2
   ```

3. **Revisa la cobertura regularmente**
   ```bash
   coverage run --source='app' manage.py test
   coverage report
   ```

## 🔧 Troubleshooting

### Error: "No module named 'app'"
```bash
# Asegúrate de estar en el directorio correcto
cd restaurante_qr_project
```

### Error: "Database is locked"
```bash
# Usa --keepdb para reutilizar la base de datos
python manage.py test --keepdb
```

### Tests lentos
```bash
# Ejecuta solo los tests que necesitas
python manage.py test app.pedidos.tests.PedidoModelTestCase --parallel
```

## 📚 Recursos Adicionales

- [Documentación oficial de Django Testing](https://docs.djangoproject.com/en/5.0/topics/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Best Practices for Django Testing](https://testdriven.io/blog/django-testing-best-practices/)

## ✨ Próximos Pasos

Para extender la suite de tests:

1. **Tests de Productos**: Crear `app/productos/tests.py`
2. **Tests de Mesas**: Crear `app/mesas/tests.py`
3. **Tests de Usuarios**: Crear `app/usuarios/tests.py`
4. **Tests de Reportes**: Crear `app/reportes/tests.py`
5. **Tests de Integración E2E**: Considerar Selenium o Playwright
6. **Tests de Performance**: Considerar locust o Django Silk

---

**Última actualización**: 2025-10-15
**Autor**: Sistema de Testing Automatizado
