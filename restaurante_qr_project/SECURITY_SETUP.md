# Configuración de Seguridad - SGIR

## ⚠️ IMPORTANTE: Configuración del archivo .env

El archivo `.env` contiene información sensible y **NUNCA** debe subirse al repositorio.

### Pasos para configurar:

1. **Copiar el archivo ejemplo:**
   ```bash
   cp .env.example .env
   ```

2. **Generar SECRET_KEY seguro:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. **Editar .env y configurar:**
   - `SECRET_KEY`: Usar la key generada en paso 2
   - `DEBUG`: `False` en producción, `True` solo en desarrollo
   - `POSTGRES_PASSWORD`: Generar password seguro (mínimo 16 caracteres)
   - `ALLOWED_HOSTS`: Agregar dominio de producción
   - `QR_HOST`: IP o dominio del servidor

### Variables críticas:

- **SECRET_KEY**: Clave secreta de Django (rotar si se expone)
- **POSTGRES_PASSWORD**: Password de base de datos
- **DEBUG**: SIEMPRE False en producción

### En caso de exposición accidental:

1. Generar nuevo SECRET_KEY
2. Cambiar password de PostgreSQL
3. Revisar logs de acceso no autorizados
4. Actualizar .env en servidor de producción

### Verificar que .env NO esté en Git:

```bash
git ls-files | grep .env$
# No debe devolver nada
```

Si aparece, ejecutar:
```bash
git rm --cached .env
git commit -m "security: Remove .env from tracking"
```
