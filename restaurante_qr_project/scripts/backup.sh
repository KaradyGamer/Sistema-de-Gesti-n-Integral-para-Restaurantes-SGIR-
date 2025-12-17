#!/bin/bash
# ====================================
# SGIR - Script de Backup Automático
# ====================================

# Configuración
BACKUP_DIR="/opt/backups"
PROJECT_DIR="/opt/sgir/restaurante_qr_project"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="${POSTGRES_DB:-sgir_prod}"
DB_USER="${POSTGRES_USER:-sgir_prod_user}"
RETENTION_DAYS=7

# Crear directorio de backups si no existe
mkdir -p $BACKUP_DIR

# Ir al directorio del proyecto
cd $PROJECT_DIR

echo "========================================="
echo "SGIR Backup - $(date)"
echo "========================================="

# 1. Backup de PostgreSQL
echo "=æ Creando backup de PostgreSQL..."
docker compose exec -T db pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

if [ $? -eq 0 ]; then
    echo " Backup de BD completado: db_$DATE.sql.gz"
else
    echo "L Error en backup de BD"
    exit 1
fi

# 2. Backup de archivos media
echo "=æ Creando backup de archivos media..."
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C $PROJECT_DIR media/

if [ $? -eq 0 ]; then
    echo " Backup de media completado: media_$DATE.tar.gz"
else
    echo "L Error en backup de media"
fi

# 3. Backup de .env (sin credenciales sensibles)
echo "=æ Creando backup de configuración..."
grep -v "SECRET_KEY\|PASSWORD" $PROJECT_DIR/.env > $BACKUP_DIR/env_$DATE.txt 2>/dev/null

# 4. Limpieza de backups antiguos
echo "=Ñ  Eliminando backups antiguos (>$RETENTION_DAYS días)..."
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "env_*.txt" -mtime +$RETENTION_DAYS -delete

# 5. Resumen
echo "========================================="
echo "=Ê Resumen de Backups:"
echo "========================================="
ls -lh $BACKUP_DIR | grep "$(date +%Y%m%d)"

# 6. Espacio en disco
echo ""
echo "=¾ Espacio en disco:"
df -h $BACKUP_DIR | tail -1

echo ""
echo " Backup completado exitosamente"
echo "========================================="
