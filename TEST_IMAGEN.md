# 🔍 Test de Imagen de Fondo

## ✅ Verificación Completada

### 📁 Ubicación de la Imagen
- **Ruta física**: `restaurante_qr_project/media/Fondos/interior-del-restaurante.jpg`
- **Tamaño**: 8.6 MB
- **URL esperada**: `http://127.0.0.1:8000/media/Fondos/interior-del-restaurante.jpg`

### 🔧 Cambios Realizados

1. **CSS Actualizado** ([staticfiles/css/login.css](staticfiles/css/login.css:14-18)):
   - Agregado gradiente de respaldo
   - URL de imagen corregida a `/media/Fondos/interior-del-restaurante.jpg`

2. **URLs Actualizadas** ([restaurante_qr_project/backend/urls.py](restaurante_qr_project/backend/urls.py:79-80)):
   - Agregado servicio de archivos estáticos y media en DEBUG mode

### 🚀 Próximos Pasos

1. **Reinicia el servidor de desarrollo**:
   ```powershell
   # Detener servidor (CTRL+C)
   python manage.py runserver
   ```

2. **Prueba la URL de la imagen directamente**:
   - Abre en tu navegador: `http://127.0.0.1:8000/media/Fondos/interior-del-restaurante.jpg`
   - Si ves la imagen del restaurante, la configuración está correcta

3. **Recarga el login con caché limpia**:
   - Presiona `Ctrl + Shift + R` (Windows/Linux)
   - O `Cmd + Shift + R` (Mac)

### 🐛 Si Aún No Funciona

Ejecuta este comando para verificar el DEBUG está en True:
```powershell
python -c "from backend import settings; print(f'DEBUG={settings.DEBUG}')"
```

Debe mostrar: `DEBUG=True`

Si está en False, edita el archivo `.env` y asegúrate que tenga:
```
DEBUG=True
```
