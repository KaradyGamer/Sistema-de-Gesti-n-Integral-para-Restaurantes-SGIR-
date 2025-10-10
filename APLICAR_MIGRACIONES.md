# 🔧 Solución: Aplicar Migraciones Pendientes

## ⚠️ Problema Detectado
```
You have 2 unapplied migration(s). Your project may not work properly until you apply the migrations for app(s): sites.
```

## ✅ Solución Simple

Ejecuta este comando en tu terminal PowerShell (con el entorno virtual activado):

```powershell
cd restaurante_qr_project
python manage.py migrate
```

## 📋 Explicación

El proyecto tiene la app `django.contrib.sites` instalada (línea 33 de `settings.py`), que se usa para:
- Generar URLs absolutas en los códigos QR
- Gestionar múltiples sitios desde una misma base de datos

Las migraciones pendientes son de esta app y solo necesitan aplicarse una vez.

## 🎯 Después de Ejecutar

Deberías ver algo como:
```
Running migrations:
  Applying sites.0001_initial... OK
  Applying sites.0002_alter_domain_unique... OK
```

Luego el servidor funcionará sin advertencias.

## 🚀 Reiniciar el Servidor

Después de aplicar las migraciones:
```powershell
python manage.py runserver
```

O si quieres acceso desde tu red local (para escanear QR desde celular):
```powershell
python manage.py runserver 0.0.0.0:8000
```
