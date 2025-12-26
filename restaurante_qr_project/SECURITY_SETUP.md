# 🔐 Configuración de Seguridad - SGIR

## ⚠️ IMPORTANTE: Configuración del archivo .env

El archivo `.env` contiene información sensible y **NUNCA** debe subirse al repositorio.

---

## 🚀 Configuración Inicial

### 1. Copiar el archivo ejemplo

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Linux/Mac (Bash):**
```bash
cp .env.example .env
```

### 2. Generar SECRET_KEY seguro

**Usando Django:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Usando OpenSSL:**
```bash
openssl rand -base64 50
```

### 3. Generar claves seguras para n8n

**N8N_ENCRYPTION_KEY (32+ caracteres):**
```bash
openssl rand -base64 32
```

**N8N_API_KEY (32+ caracteres):**
```bash
openssl rand -hex 32
```

### 4. Configurar variables en .env

Edita el archivo `.env` y actualiza:

#### Django Core
- `SECRET_KEY`: Usar la key generada en paso 2
- `DEBUG`: **False** en producción, **True** solo en desarrollo local
- `ALLOWED_HOSTS`: Agregar tu dominio (ej: `tudominio.com,www.tudominio.com,localhost,127.0.0.1`)

#### Base de Datos
- `POSTGRES_PASSWORD`: Password seguro (mínimo 16 caracteres, letras+números+símbolos)
- `POSTGRES_DB`: Nombre de tu base de datos (por defecto `sgir`)
- `POSTGRES_USER`: Usuario de PostgreSQL (por defecto `sgir_user`)

#### n8n Automation
- `N8N_API_KEY`: Clave generada en paso 3
- `N8N_DB_PASSWORD`: Password seguro para base de datos de n8n
- `N8N_BASIC_AUTH_PASSWORD`: Password para login en interfaz n8n
- `N8N_ENCRYPTION_KEY`: Clave de 32+ caracteres generada en paso 3
- `N8N_HOST`: Tu dominio o IP (localhost para desarrollo)

#### QR System
- `QR_HOST`: IP o dominio del servidor (ej: `192.168.1.100:8000` o `tudominio.com`)

---

## 🔥 Variables Críticas de Seguridad

| Variable | Importancia | Acción si se expone |
|----------|-------------|---------------------|
| `SECRET_KEY` | 🔴 CRÍTICA | Rotar inmediatamente + invalidar sesiones |
| `POSTGRES_PASSWORD` | 🔴 CRÍTICA | Cambiar en servidor + actualizar .env |
| `N8N_API_KEY` | 🔴 CRÍTICA | Regenerar + actualizar workflows |
| `N8N_ENCRYPTION_KEY` | 🔴 CRÍTICA | Re-encriptar credenciales en n8n |
| `N8N_DB_PASSWORD` | 🟡 ALTA | Cambiar password de PostgreSQL n8n |
| `N8N_BASIC_AUTH_PASSWORD` | 🟡 ALTA | Cambiar password de login n8n |
| `DEBUG` | 🟡 ALTA | **SIEMPRE False** en producción |

---

## 🚨 En caso de exposición accidental

### Si .env fue subido a GitHub:

1. **Rotar TODAS las credenciales inmediatamente:**
   ```bash
   # Generar nuevo SECRET_KEY
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

   # Generar nuevo N8N_API_KEY
   openssl rand -hex 32

   # Generar nuevo N8N_ENCRYPTION_KEY
   openssl rand -base64 32
   ```

2. **Cambiar passwords de bases de datos:**
   ```bash
   # Conectar a PostgreSQL y cambiar password
   docker compose exec db psql -U sgir_user -d sgir
   ALTER USER sgir_user WITH PASSWORD 'nuevo_password_seguro';

   # Cambiar password de n8n_db
   docker compose exec n8n_db psql -U n8n -d n8n
   ALTER USER n8n WITH PASSWORD 'nuevo_password_n8n';
   ```

3. **Actualizar .env con nuevas credenciales**

4. **Reiniciar servicios:**
   ```bash
   docker compose down
   docker compose up -d
   ```

5. **Revisar logs de acceso no autorizados:**
   ```bash
   docker compose logs --tail=200 web
   docker compose logs --tail=200 n8n
   ```

6. **Considerar que el repositorio está comprometido** - Las credenciales quedaron en el historial de Git

---

## ✅ Verificación de Seguridad

### Verificar que .env NO esté en Git

**Windows (PowerShell):**
```powershell
git ls-files | Select-String ".env"
# No debe devolver nada
```

**Linux/Mac (Bash):**
```bash
git ls-files | grep .env$
# No debe devolver nada
```

### Si .env aparece en Git, removerlo:

**Windows (PowerShell):**
```powershell
cd restaurante_qr_project
git rm --cached .env
git commit -m "security: Remove .env from tracking"
git push
```

**Linux/Mac (Bash):**
```bash
cd restaurante_qr_project
git rm --cached .env
git commit -m "security: Remove .env from tracking"
git push
```

### Verificar que .gitignore incluye .env:

```bash
# En restaurante_qr_project/.gitignore debe aparecer:
.env
.env.local
.env.*
```

---

## 🔒 Checklist de Seguridad Pre-Producción

- [ ] `DEBUG=False` en .env
- [ ] SECRET_KEY único y seguro (50+ caracteres)
- [ ] POSTGRES_PASSWORD fuerte (16+ caracteres)
- [ ] N8N_API_KEY único (32+ caracteres)
- [ ] N8N_ENCRYPTION_KEY único (32+ caracteres)
- [ ] ALLOWED_HOSTS configurado con dominio real
- [ ] .env NO está en Git (verificado)
- [ ] .env.example actualizado sin secretos reales
- [ ] CSRF_TRUSTED_ORIGINS incluye dominio de producción
- [ ] QR_HOST apunta a dominio/IP correcto
- [ ] Logs de acceso configurados
- [ ] Backups de base de datos programados

---

## 📚 Referencias

- [Django Security Best Practices](https://docs.djangoproject.com/en/5.0/topics/security/)
- [n8n Security Guide](https://docs.n8n.io/hosting/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
