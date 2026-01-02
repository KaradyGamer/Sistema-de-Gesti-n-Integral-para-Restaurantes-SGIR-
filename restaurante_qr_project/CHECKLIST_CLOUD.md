# ✅ CHECKLIST CLOUD – BACKEND SGIR

**Proyecto:** Sistema de Gestión Integral para Restaurantes (SGIR)
**Alcance:** Backend · Seguridad · Docker · Preparación Cloud
**Estado base:** Código limpio, auditado y hardened

---

## 📋 Cómo Usar Esta Checklist

1. **Pre-Despliegue:** Completar TODAS las secciones marcadas como 🔴 CRÍTICO
2. **Recomendado:** Completar las secciones marcadas como 🟡 RECOMENDADO
3. **Opcional:** Revisar y completar según necesidad las marcadas como 🟢 OPCIONAL

**Estados:**
- ✅ Completado
- ⚠️ Parcial
- ❌ Pendiente

---

## 1️⃣ GIT & CONTROL DE VERSIONES 🔴 CRÍTICO

### Exclusiones Obligatorias (.gitignore)

- [ ] ✅ `.env` excluido
- [ ] ✅ `.env.*` excluido (excepto `.env.example`)
- [ ] ✅ `media/` excluido
- [ ] ✅ `staticfiles/` excluido
- [ ] ✅ `logs/` excluido
- [ ] ✅ `audit_out/` excluido
- [ ] ✅ `env/`, `.venv/` excluido
- [ ] ✅ `__pycache__/` excluido
- [ ] ✅ `*.pyc`, `*.pyo` excluido
- [ ] ✅ `.DS_Store`, `Thumbs.db` excluido
- [ ] ✅ `*.sqlite3` excluido
- [ ] ✅ `*.bak`, `*.dump`, `*.sql` excluido

### Verificación de Historial

```bash
# Verificar que .env nunca fue commiteado
git log --all --full-history -- .env
# Output esperado: vacío

# Verificar .gitignore funciona
git check-ignore .env
# Output esperado: .env
```

- [ ] ✅ `.env` nunca fue commiteado
- [ ] ✅ Ningún secreto en historial de Git
- [ ] ✅ `.env.example` actualizado y documentado

### Repositorio Limpio

- [ ] ✅ No existe `.git/` en ZIPs compartidos
- [ ] ✅ No se versionan archivos binarios ni media
- [ ] ✅ README único y actualizado
- [ ] ✅ No hay archivos temporales trackeados

---

## 2️⃣ SEGURIDAD BACKEND 🔴 CRÍTICO

### Variables de Entorno

- [ ] ✅ Ningún secreto hardcodeado en código
- [ ] ✅ `SECRET_KEY` solo por entorno
- [ ] ✅ Credenciales rotadas si `.env` local fue compartido
- [ ] ✅ `DEBUG=False` en producción (forzado)
- [ ] ✅ `.env.example` existe y está documentado

**Verificación:**
```bash
# Buscar secretos hardcodeados
grep -r "SECRET_KEY\s*=\s*['\"]" app/ backend/
# Output esperado: vacío (excepto settings.py con get())
```

### Django Hardening

- [ ] ✅ `SECURE_SSL_REDIRECT = True`
- [ ] ✅ `SESSION_COOKIE_SECURE = True`
- [ ] ✅ `CSRF_COOKIE_SECURE = True`
- [ ] ✅ `SECURE_HSTS_SECONDS >= 31536000`
- [ ] ✅ `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- [ ] ✅ `SECURE_HSTS_PRELOAD = True`
- [ ] ✅ `SECURE_CONTENT_TYPE_NOSNIFF = True`
- [ ] ✅ `X_FRAME_OPTIONS = 'DENY'`

**Verificación:**
```bash
# Ejecutar check de Django
python manage.py check --deploy
```

---

## 3️⃣ AUTENTICACIÓN Y AUTORIZACIÓN 🔴 CRÍTICO

### Endpoints Protegidos

- [ ] ✅ Endpoints críticos requieren `IsAuthenticated`
- [ ] ✅ Vistas críticas tienen `@login_required`
- [ ] ✅ Endpoints públicos están justificados y documentados
- [ ] ✅ No hay bypass de permisos

**Endpoints Públicos Permitidos:**
- `/` - Formulario cliente ✅
- `/health/` - Healthcheck cloud ✅
- `/api/mesas/` - Consulta mesas ✅

- [ ] ✅ TODOS los demás endpoints están protegidos

### JWT y Sesiones

- [ ] ✅ JWT configurado correctamente
- [ ] ✅ Tokens expiran (60 min access, 14 días refresh)
- [ ] ✅ Refresh tokens rotan correctamente
- [ ] ✅ Sesiones caducan (1 hora)

**Verificación:**
```bash
# Probar endpoint sin auth (debe fallar)
curl -I http://localhost:8000/api/usuarios/
# Esperado: 401 Unauthorized o 403 Forbidden
```

---

## 4️⃣ MANEJO DE ERRORES Y LOGGING 🔴 CRÍTICO

### Errores

- [ ] ✅ **0 bare except (E722)**
- [ ] ✅ Excepciones capturan `Exception as e`
- [ ] ✅ No hay errores silenciosos
- [ ] ✅ Mensajes de error informativos (sin exponer internals)

**Verificación:**
```bash
ruff check . --select E722
# Esperado: All checks passed!
```

### Logging

- [ ] ✅ Logging activo en puntos críticos
- [ ] ✅ Uso de `logger.warning()` / `logger.error()`
- [ ] ✅ Contexto incluido (IDs, acción, módulo)
- [ ] ✅ Logs salen por stdout (cloud-ready)
- [ ] ✅ No se loggean secretos ni passwords

**Verificación:**
```bash
# Buscar posibles logs de secretos
grep -r "logger.*password\|logger.*secret" app/
# Revisar manualmente cada caso
```

---

## 5️⃣ CALIDAD DE CÓDIGO 🟡 RECOMENDADO

### Linting

- [ ] ✅ `ruff check .` sin errores críticos
- [ ] ✅ F841 eliminados (variables no usadas)
- [ ] ✅ E722 eliminados (bare except)
- [ ] ✅ Imports limpios (F401)
- [ ] ⚠️ E501 aceptado como informativo (392 líneas largas)

**Verificación:**
```bash
ruff check . --select E722,F841,F401
# Esperado: All checks passed!
```

### Código Limpio

- [ ] ✅ Apps vacías eliminadas
- [ ] ✅ Clases no usadas eliminadas
- [ ] ✅ Scripts de debug aislados en `scripts/dev/`
- [ ] ✅ Código legible y bien estructurado

---

## 6️⃣ APIs Y RUTAS 🔴 CRÍTICO

- [ ] ✅ Convención `/api/*` unificada
- [ ] ✅ No existen rutas duplicadas
- [ ] ✅ `show_urls` verificado
- [ ] ✅ Mapa de URLs auditado ([audit_out/urls.txt](audit_out/urls.txt))
- [ ] ✅ Frontend apunta solo a rutas válidas

**Verificación:**
```bash
python manage.py show_urls > audit_out/urls_current.txt
diff audit_out/urls.txt audit_out/urls_current.txt
# Esperado: sin diferencias significativas
```

---

## 7️⃣ MODELOS Y BASE DE DATOS 🔴 CRÍTICO

- [ ] ✅ ORM usado correctamente
- [ ] ✅ No hay SQL raw inseguro
- [ ] ✅ Migraciones aplicadas
- [ ] ✅ `migrate --plan` sin pendientes
- [ ] ✅ Relaciones consistentes
- [ ] ✅ Índices en campos frecuentemente consultados

**Verificación:**
```bash
python manage.py showmigrations
python manage.py migrate --plan
# Esperado: todas aplicadas
```

---

## 8️⃣ DOCKER & CONTAINERS 🔴 CRÍTICO

### Docker Compose

- [ ] ✅ Contenedores levantan sin errores
- [ ] ✅ Healthcheck responde 200 OK
- [ ] ✅ Variables por entorno (.env)
- [ ] ✅ **Sin passwords por defecto en producción**
- [ ] ✅ Volúmenes para `media/` externos al repo
- [ ] ✅ Volúmenes para `logs/` persistentes

**Verificación:**
```bash
docker compose ps
# Esperado: todos "Up" y "healthy"

docker compose exec web python manage.py check
# Esperado: System check identified no issues

curl http://localhost:8000/health/
# Esperado: {"status":"healthy",...}
```

### Producción

- [ ] ✅ `docker-compose.prod.yml` separado
- [ ] ✅ Gunicorn como servidor WSGI
- [ ] ✅ Whitenoise configurado para estáticos
- [ ] ✅ Preparado para reverse proxy (Nginx/Traefik)
- [ ] ✅ Logs centralizados

---

## 9️⃣ PREPARACIÓN CLOUD 🔴 CRÍTICO

- [ ] ✅ Backend stateless
- [ ] ✅ Configuración 100% por env
- [ ] ✅ Logs a stdout/stderr
- [ ] ✅ Compatible con CI/CD
- [ ] ✅ Compatible con Docker registry
- [ ] ✅ Listo para Nginx / Traefik / LB
- [ ] ✅ Health endpoint expuesto
- [ ] ✅ Métricas básicas disponibles

**Servicios Cloud Compatibles:**
- ✅ AWS (ECS, Fargate, EC2)
- ✅ Google Cloud (Cloud Run, GKE)
- ✅ Azure (Container Instances, AKS)
- ✅ DigitalOcean (App Platform, Droplets)
- ✅ Heroku, Render, Railway

---

## 🔟 DOCUMENTACIÓN 🟡 RECOMENDADO

- [ ] ✅ `README.md` actualizado
- [ ] ✅ `SECURITY.md` creado
- [ ] ✅ `DEPLOYMENT.md` creado
- [ ] ✅ `CHECKLIST_CLOUD.md` creado (este archivo)
- [ ] ✅ `.env.example` documentado
- [ ] ⚠️ Diagrama de arquitectura (opcional)
- [ ] ⚠️ API documentation (Swagger/OpenAPI) (opcional)

---

## 1️⃣1️⃣ BACKUPS Y RECUPERACIÓN 🔴 CRÍTICO

### Estrategia de Backups

- [ ] ⚠️ Backups automáticos de BD configurados
- [ ] ⚠️ Backups de `media/` configurados
- [ ] ⚠️ Retención definida (30 días recomendado)
- [ ] ⚠️ Proceso de restauración probado

**Script de Backup Ejemplo:**
```bash
# Backup de PostgreSQL
docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup de media
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz media/
```

---

## 1️⃣2️⃣ MONITOREO Y ALERTAS 🟡 RECOMENDADO

### Servicios de Monitoreo

- [ ] ⚠️ Sentry configurado (errores y excepciones)
- [ ] ⚠️ Uptime monitoring activo (UptimeRobot, Pingdom)
- [ ] ⚠️ APM configurado (Datadog, New Relic)
- [ ] ⚠️ Logs centralizados (ELK, Splunk, CloudWatch)

### Alertas Configuradas

- [ ] ⚠️ Alerta cuando healthcheck falla
- [ ] ⚠️ Alerta cuando errores 5xx > umbral
- [ ] ⚠️ Alerta cuando uso de CPU > 80%
- [ ] ⚠️ Alerta cuando uso de memoria > 80%
- [ ] ⚠️ Alerta cuando disco > 90%

---

## 1️⃣3️⃣ SSL/TLS Y CERTIFICADOS 🔴 CRÍTICO

- [ ] ✅ Certificado SSL válido instalado
- [ ] ✅ HTTPS forzado (redirect 80→443)
- [ ] ✅ Certificado auto-renovable (Let's Encrypt)
- [ ] ✅ TLS 1.2+ únicamente
- [ ] ✅ Ciphers seguros configurados

**Verificación:**
```bash
# Verificar certificado
openssl s_client -connect tu-dominio.com:443 -servername tu-dominio.com

# Test SSL
https://www.ssllabs.com/ssltest/analyze.html?d=tu-dominio.com
# Esperado: A o A+
```

---

## 1️⃣4️⃣ PERFORMANCE Y OPTIMIZACIÓN 🟡 RECOMENDADO

### Django

- [ ] ⚠️ Cache configurado (Redis/Memcached)
- [ ] ⚠️ Query optimization con `select_related` / `prefetch_related`
- [ ] ⚠️ Índices de BD optimizados
- [ ] ⚠️ Archivos estáticos comprimidos (gzip)
- [ ] ⚠️ CDN para estáticos (opcional)

### Servidor

- [ ] ⚠️ Gunicorn workers configurados (2-4 × CPU cores)
- [ ] ⚠️ Connection pooling para BD
- [ ] ⚠️ Nginx con cache de proxy
- [ ] ⚠️ HTTP/2 habilitado

**Verificación:**
```bash
# Test de carga básico
ab -n 1000 -c 10 https://tu-dominio.com/health/
```

---

## 1️⃣5️⃣ COMPLIANCE Y REGULACIONES 🟢 OPCIONAL

### GDPR / LOPD (Si aplica)

- [ ] ⚠️ Política de privacidad
- [ ] ⚠️ Cookie consent
- [ ] ⚠️ Derecho al olvido implementado
- [ ] ⚠️ Exportación de datos de usuario

### Auditoría

- [ ] ⚠️ Logs de acceso a datos sensibles
- [ ] ⚠️ Trail de cambios en BD
- [ ] ⚠️ Registro de permisos y accesos

---

## ✅ VEREDICTO FINAL

### Puntuación por Sección

| Sección | Completado | Estado |
|---------|-----------|--------|
| Git & Control de Versiones | __/13 | ⚠️ |
| Seguridad Backend | __/10 | ⚠️ |
| Autenticación | __/9 | ⚠️ |
| Errores y Logging | __/9 | ⚠️ |
| Calidad de Código | __/9 | ⚠️ |
| APIs y Rutas | __/5 | ⚠️ |
| Base de Datos | __/6 | ⚠️ |
| Docker | __/11 | ⚠️ |
| Cloud Readiness | __/9 | ⚠️ |
| Documentación | __/7 | ⚠️ |

### Estado General

- 🔴 **BLOQUEANTE**: < 80% de ítems críticos completados
- 🟡 **PRECAUCIÓN**: 80-95% de ítems críticos completados
- 🟢 **LISTO**: > 95% de ítems críticos completados

**Cálculo:**
```
Total Críticos Completados / Total Críticos = ____%
```

### Aprobación para Despliegue

- [ ] ✅ Todos los ítems 🔴 CRÍTICO completados
- [ ] ✅ Al menos 80% de ítems 🟡 RECOMENDADO completados
- [ ] ✅ SECURITY.md revisado
- [ ] ✅ DEPLOYMENT.md probado
- [ ] ✅ Equipo informado y capacitado

**Firma de Aprobación:**
- **Desarrollador:** ________________ Fecha: ________
- **DevOps:** ________________ Fecha: ________
- **Seguridad:** ________________ Fecha: ________

---

## 🚀 Próximos Pasos

Una vez completada esta checklist:

1. **Revisar** todos los ítems marcados
2. **Documentar** cualquier excepción o decisión
3. **Ejecutar** deployment en entorno de staging
4. **Validar** con pruebas de humo
5. **Programar** deployment a producción
6. **Monitorear** 48h post-despliegue

---

**Mantenido por:** Equipo SGIR
**Última revisión:** 2025-01-02