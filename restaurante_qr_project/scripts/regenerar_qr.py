"""
Script para regenerar códigos QR de mesas con la IP actual
Uso: python scripts/regenerar_qr.py
"""

import os
import sys
import django
import qrcode
from pathlib import Path

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from app.mesas.models import Mesa
from django.conf import settings


def regenerar_qr_mesas(ip_servidor):
    """
    Regenera todos los códigos QR de las mesas con la nueva IP

    Args:
        ip_servidor (str): IP actual del servidor (ej: '10.165.187.107:8000')
    """
    from io import BytesIO
    from django.core.files import File

    mesas = Mesa.objects.filter(activo=True)
    total_mesas = mesas.count()

    if total_mesas == 0:
        print("ERROR: No hay mesas activas en la base de datos")
        return

    print(f"Regenerando QR para {total_mesas} mesas con IP: {ip_servidor}")
    print("-" * 60)

    actualizadas = 0
    errores = 0

    for mesa in mesas:
        try:
            # Generar URL completa con la nueva IP (formulario con parámetro mesa)
            url_qr = f"http://{ip_servidor}/?mesa={mesa.numero}"

            # Crear código QR
            qr = qrcode.make(url_qr)

            # Guardar en buffer
            buffer = BytesIO()
            qr.save(buffer, format='PNG')
            buffer.seek(0)

            # Nombre del archivo
            file_name = f"mesa-{mesa.numero}-qr.png"

            # Guardar en el modelo (esto guardará automáticamente en media/qrcodes/)
            mesa.qr_image.save(file_name, File(buffer), save=True)

            actualizadas += 1
            print(f"OK Mesa {mesa.numero}: {url_qr}")

        except Exception as e:
            errores += 1
            print(f"ERROR en Mesa {mesa.numero}: {str(e)}")

    print("-" * 60)
    print(f"Actualizadas: {actualizadas}/{total_mesas}")
    if errores > 0:
        print(f"Errores: {errores}")
    print(f"\nLos QR ahora apuntan a: http://{ip_servidor}")


if __name__ == "__main__":
    print("=" * 60)
    print("REGENERADOR DE CODIGOS QR - SGIR")
    print("=" * 60)
    print()

    # Leer IP de argumento o usar valor por defecto
    if len(sys.argv) > 1:
        ip = sys.argv[1].strip()
    else:
        print("Uso: python scripts/regenerar_qr.py <IP:PUERTO>")
        print("Ejemplo: python scripts/regenerar_qr.py 10.165.187.107:8000")
        sys.exit(1)

    # Validar formato básico
    if ':' not in ip:
        print("Advertencia: No detecte puerto, agregando :8000")
        ip = f"{ip}:8000"

    print(f"Regenerando QRs con IP: {ip}")
    print()
    regenerar_qr_mesas(ip)
    print()
    print("Proceso completado!")
    print(f"Los QR ahora apuntan a: http://{ip}")
