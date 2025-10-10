"""
Comando Django para configurar PINes y áreas a usuarios existentes
Ejecutar con: python manage.py configurar_usuarios
"""
from django.core.management.base import BaseCommand
from app.usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Configura PINes y áreas para todos los usuarios del sistema'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando configuracion de usuarios...\n")

        # Configurar SOLO cajeros con PIN
        cajeros = Usuario.objects.filter(rol='cajero')
        pin_cajero = 1000
        for cajero in cajeros:
            cajero.pin = str(pin_cajero)
            cajero.activo = True
            cajero.areas_permitidas = ['caja']
            cajero.save()
            self.stdout.write(f"[OK] Cajero '{cajero.username}': PIN = {pin_cajero}")
            pin_cajero += 1

        # Configurar meseros - SIN PIN, solo QR
        meseros = Usuario.objects.filter(rol='mesero')
        for mesero in meseros:
            mesero.pin = None  # SIN PIN
            mesero.activo = True
            mesero.areas_permitidas = ['mesero']
            mesero.save()
            self.stdout.write(f"[OK] Mesero '{mesero.username}': Acceso SOLO por QR")

        # Configurar cocineros - SIN PIN, solo QR
        cocineros = Usuario.objects.filter(rol='cocinero')
        for cocinero in cocineros:
            cocinero.pin = None  # SIN PIN
            cocinero.activo = True
            cocinero.areas_permitidas = ['cocina']
            cocinero.save()
            self.stdout.write(f"[OK] Cocinero '{cocinero.username}': Acceso SOLO por QR")

        # Activar admins y gerentes - Login tradicional
        admins = Usuario.objects.filter(rol__in=['admin', 'gerente'])
        for admin in admins:
            admin.pin = None  # SIN PIN - usan login tradicional
            admin.activo = True
            admin.areas_permitidas = ['mesero', 'cocina', 'caja', 'reportes']
            admin.save()
            self.stdout.write(f"[OK] Admin/Gerente '{admin.username}': Login tradicional + Acceso total")

        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("CONFIGURACION COMPLETADA"))
        self.stdout.write("="*50)
        self.stdout.write("\nRESUMEN:")
        self.stdout.write(f"  Cajeros (con PIN):    {Usuario.objects.filter(rol='cajero', pin__isnull=False).count()} usuarios")
        self.stdout.write(f"  Meseros (solo QR):    {Usuario.objects.filter(rol='mesero').count()} usuarios")
        self.stdout.write(f"  Cocineros (solo QR):  {Usuario.objects.filter(rol='cocinero').count()} usuarios")
        self.stdout.write(f"  Admins (tradicional): {Usuario.objects.filter(rol__in=['admin', 'gerente']).count()} usuarios")

        self.stdout.write("\nMETODOS DE ACCESO:")
        self.stdout.write("  Admin/Gerente -> Login tradicional (usuario/contrasena)")
        self.stdout.write("  Cajero        -> Login con PIN (1000, 1001...)")
        self.stdout.write("  Mesero        -> Solo QR (generado por cajero)")
        self.stdout.write("  Cocinero      -> Solo QR (generado por cajero)")

        self.stdout.write("\nPROXIMOS PASOS:")
        self.stdout.write("  1. Inicia sesion como cajero con PIN (ej: 1000)")
        self.stdout.write("  2. Ve a 'Gestion de Personal'")
        self.stdout.write("  3. Genera QR para meseros y cocineros")
        self.stdout.write("  4. Empleados escanean QR -> Acceso automatico")
