"""
Script para regenerar códigos QR de empleados (meseros/cocineros) con la IP actual
Uso: python scripts/regenerar_qr_empleados.py <IP:PUERTO>
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

from app.usuarios.models import Usuario
from django.conf import settings


def regenerar_qr_empleados(ip_servidor):
    """
    Regenera todos los códigos QR de empleados con la nueva IP

    Args:
        ip_servidor (str): IP actual del servidor (ej: '10.165.187.107:8000')
    """
    # Obtener meseros y cocineros activos
    empleados = Usuario.objects.filter(
        rol__in=['mesero', 'cocinero'],
        activo=True
    )

    total_empleados = empleados.count()

    if total_empleados == 0:
        print("ERROR: No hay empleados (meseros/cocineros) activos")
        return

    print(f"Regenerando QR para {total_empleados} empleados con IP: {ip_servidor}")
    print("-" * 60)

    actualizados = 0
    errores = 0

    # Crear directorio para QR de empleados
    qr_dir = Path(settings.MEDIA_ROOT) / 'qr_empleados'
    qr_dir.mkdir(parents=True, exist_ok=True)

    for empleado in empleados:
        try:
            # Obtener o generar token QR
            token = empleado.get_qr_token()

            # Generar URL completa con la nueva IP
            url_qr = f"http://{ip_servidor}/usuarios/auth-qr/{token}/"

            # Crear código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url_qr)
            qr.make(fit=True)

            # Crear imagen
            img = qr.make_image(fill_color="black", back_color="white")

            # Guardar archivo
            nombre_archivo = f"{empleado.rol}-{empleado.username}-qr.png"
            ruta_archivo = qr_dir / nombre_archivo
            img.save(ruta_archivo)

            actualizados += 1
            print(f"OK {empleado.get_rol_display()} {empleado.username}: {url_qr}")

        except Exception as e:
            errores += 1
            print(f"ERROR {empleado.username}: {str(e)}")

    print("-" * 60)
    print(f"Actualizados: {actualizados}/{total_empleados}")
    if errores > 0:
        print(f"Errores: {errores}")
    print(f"\nLos QR de empleados estan en: {qr_dir}")
    print(f"Ahora apuntan a: http://{ip_servidor}/usuarios/auth-qr/TOKEN/")


if __name__ == "__main__":
    print("=" * 60)
    print("REGENERADOR DE QR EMPLEADOS - SGIR")
    print("=" * 60)
    print()

    # Leer IP de argumento
    if len(sys.argv) > 1:
        ip = sys.argv[1].strip()
    else:
        print("Uso: python scripts/regenerar_qr_empleados.py <IP:PUERTO>")
        print("Ejemplo: python scripts/regenerar_qr_empleados.py 10.165.187.107:8000")
        sys.exit(1)

    # Validar formato básico
    if ':' not in ip:
        print("Advertencia: No detecte puerto, agregando :8000")
        ip = f"{ip}:8000"

    print(f"Regenerando QRs de empleados con IP: {ip}")
    print()
    regenerar_qr_empleados(ip)
    print()
    print("Proceso completado!")
