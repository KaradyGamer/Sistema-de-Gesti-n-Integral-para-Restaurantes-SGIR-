# 🔐 SECRET_KEY Rotation - PATCH-003

**Status**: ⚠️ ACCIÓN REQUERIDA ANTES DE PRODUCCIÓN

---

## 📋 Contexto

La `SECRET_KEY` actual fue generada durante desarrollo y está presente en el archivo `.env` local (que NO está en Git ✅).

Para **producción**, es **OBLIGATORIO** generar una nueva `SECRET_KEY` única y segura.

---

## ⚙️ Instrucciones de Rotación

### 1. Generar Nueva SECRET_KEY

Ejecutar en terminal (local o servidor):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Output esperado** (ejemplo):
```
django-insecure-8a9b7c6d5e4f3g2h1i0j9k8l7m6n5o4p3q2r1s0
```

---

### 2. Actualizar Archivos

#### A) Producción (Servidor)

Actualizar el archivo `.env` en el servidor:

```bash
# Editar .env en servidor
nano /ruta/al/proyecto/.env

# Cambiar línea:
SECRET_KEY=<NUEVA_KEY_GENERADA>
```

**NO COMMITEAR `.env`** (ya está en `.gitignore` ✅)

#### B) Desarrollo Local (Opcional)

Si trabajas en desarrollo local, actualiza tu `.env` local:

```bash
# Editar .env local
SECRET_KEY=<NUEVA_KEY_GENERADA_LOCAL>
```

**Notas**:
- Dev y prod pueden usar diferentes SECRET_KEYs
- Lo importante es que **producción tenga una key única y segura**

#### C) Template (.env.example)

Actualizar el placeholder en `.env.example`:

```bash
# Editar .env.example
SECRET_KEY=django-insecure-CAMBIAR_ESTO_EN_PRODUCCION
```

**SÍ COMMITEAR `.env.example`** (es template, no contiene secreto real)

---

### 3. Reiniciar Servicios

Después de cambiar la SECRET_KEY, reiniciar los servicios:

#### Docker Compose:
```bash
docker-compose restart web
# o
docker-compose down && docker-compose up -d
```

#### Docker Compose Prod:
```bash
docker-compose -f docker-compose.prod.yml restart web
```

#### Gunicorn (sin Docker):
```bash
systemctl restart gunicorn
# o
supervisorctl restart sgir
```

---

## ⚠️ IMPORTANTE

### ¿Qué pasa al cambiar SECRET_KEY?

**Impacto inmediato**:
- ✅ Sesiones existentes se invalidan (usuarios deben re-loguearse)
- ✅ Cookies firmadas se invalidan
- ✅ Tokens JWT existentes se invalidan (se regeneran al login)

**NO afecta**:
- ✅ Base de datos
- ✅ Migraciones
- ✅ Datos de pedidos/caja/reportes
- ✅ Archivos media

**Recomendación**: Cambiar SECRET_KEY durante **ventana de mantenimiento** o fuera de horario pico.

---

## ✅ Verificación Post-Rotación

Después de rotar la SECRET_KEY, verificar:

```bash
# 1. Django check
python manage.py check
# Esperado: System check identified no issues (0 silenced).

# 2. Verificar que settings lee la nueva key (sin imprimirla)
python manage.py shell -c "from django.conf import settings; print('SECRET_KEY loaded:', len(settings.SECRET_KEY), 'chars')"
# Esperado: SECRET_KEY loaded: 50 chars (o similar)

# 3. Test de login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# Esperado: JSON con token JWT
```

---

## 📚 Referencias

- [Django SECRET_KEY Docs](https://docs.djangoproject.com/en/5.1/ref/settings/#secret-key)
- [Security Best Practices](https://docs.djangoproject.com/en/5.1/topics/security/)

---

**Checklist de Rotación**:

- [ ] Generar nueva SECRET_KEY
- [ ] Actualizar `.env` en servidor producción
- [ ] Actualizar `.env.example` con placeholder
- [ ] Commitear `.env.example` (NO `.env`)
- [ ] Reiniciar servicios
- [ ] Verificar Django check (0 issues)
- [ ] Verificar login funciona
- [ ] Notificar usuarios (sesiones expiradas)

---

**Estado**: ⏳ Pendiente de ejecutar antes de despliegue a producción.