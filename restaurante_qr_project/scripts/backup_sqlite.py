#!/usr/bin/env python
"""
Script de Backup Automático de Base de Datos SQLite
SGIR v38.8 - Solo para entorno de desarrollo

Uso:
    python scripts/backup_sqlite.py

Funcionalidad:
    - Crea backup con timestamp de db.sqlite3
    - Guarda en carpeta backups/
    - Mantiene solo los últimos 7 backups
    - Solo funciona en modo DEBUG=True

Para automatizar (Windows Task Scheduler o Linux cron):
    # Diariamente a las 2 AM
    0 2 * * * cd /ruta/proyecto && python scripts/backup_sqlite.py
"""

import os
import sys
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    import django
    django.setup()
    from django.conf import settings
except ImportError as e:
    print(f"Error: No se pudo importar Django - {e}")
    sys.exit(1)

# Configurar logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def validar_entorno():
    """Valida que el script solo se ejecute en desarrollo"""
    if not settings.DEBUG:
        logger.error("❌ ERROR: Este script solo debe ejecutarse en modo DEBUG=True")
        logger.error("   No se permiten backups automáticos en producción.")
        logger.error("   Para producción, usa herramientas profesionales como:")
        logger.error("   - pg_dump para PostgreSQL")
        logger.error("   - Cloud backups automáticos")
        return False
    return True


def crear_directorio_backups():
    """Crea el directorio de backups si no existe"""
    backup_dir = BASE_DIR / 'backups'
    backup_dir.mkdir(exist_ok=True)
    logger.info(f"📁 Directorio de backups: {backup_dir}")
    return backup_dir


def obtener_ruta_db():
    """Obtiene la ruta de la base de datos SQLite"""
    db_path = BASE_DIR / 'db.sqlite3'

    if not db_path.exists():
        logger.error(f"❌ ERROR: No se encontró db.sqlite3 en {db_path}")
        return None

    # Verificar tamaño
    size_mb = db_path.stat().st_size / (1024 * 1024)
    logger.info(f"📊 Tamaño de la base de datos: {size_mb:.2f} MB")

    return db_path


def crear_backup(db_path, backup_dir):
    """Crea un backup con timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"db_backup_{timestamp}.sqlite3"
    backup_path = backup_dir / backup_filename

    try:
        logger.info(f"🔄 Creando backup: {backup_filename}")
        shutil.copy2(db_path, backup_path)

        # Verificar que el backup se creó correctamente
        if backup_path.exists():
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            logger.info(f"✅ Backup creado exitosamente ({size_mb:.2f} MB)")
            return backup_path
        else:
            logger.error("❌ ERROR: El backup no se creó correctamente")
            return None

    except Exception as e:
        logger.error(f"❌ ERROR al crear backup: {str(e)}")
        return None


def limpiar_backups_antiguos(backup_dir, max_backups=7):
    """Mantiene solo los últimos N backups"""
    backups = sorted(
        backup_dir.glob('db_backup_*.sqlite3'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if len(backups) <= max_backups:
        logger.info(f"📦 Total de backups: {len(backups)}/{max_backups}")
        return

    # Eliminar backups antiguos
    backups_a_eliminar = backups[max_backups:]
    logger.info(f"🧹 Limpiando {len(backups_a_eliminar)} backup(s) antiguo(s)")

    for backup in backups_a_eliminar:
        try:
            backup.unlink()
            logger.info(f"   ✓ Eliminado: {backup.name}")
        except Exception as e:
            logger.error(f"   ✗ Error al eliminar {backup.name}: {str(e)}")

    logger.info(f"✅ Backups mantenidos: {max_backups}")


def listar_backups(backup_dir):
    """Lista todos los backups disponibles"""
    backups = sorted(
        backup_dir.glob('db_backup_*.sqlite3'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not backups:
        logger.info("📦 No hay backups disponibles")
        return

    logger.info("\n📦 BACKUPS DISPONIBLES:")
    logger.info("=" * 60)

    for i, backup in enumerate(backups, 1):
        size_mb = backup.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        logger.info(f"{i}. {backup.name}")
        logger.info(f"   Tamaño: {size_mb:.2f} MB | Fecha: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

    logger.info("=" * 60)


def main():
    """Función principal"""
    logger.info("\n" + "=" * 60)
    logger.info("🔄 SGIR - Backup Automático de SQLite")
    logger.info("=" * 60)

    # 1. Validar entorno
    if not validar_entorno():
        sys.exit(1)

    # 2. Crear directorio de backups
    backup_dir = crear_directorio_backups()

    # 3. Obtener ruta de la base de datos
    db_path = obtener_ruta_db()
    if not db_path:
        sys.exit(1)

    # 4. Crear backup
    backup_path = crear_backup(db_path, backup_dir)
    if not backup_path:
        sys.exit(1)

    # 5. Limpiar backups antiguos
    limpiar_backups_antiguos(backup_dir, max_backups=7)

    # 6. Listar backups disponibles
    listar_backups(backup_dir)

    logger.info("\n✅ Backup completado exitosamente")
    logger.info("=" * 60 + "\n")


if __name__ == '__main__':
    main()
