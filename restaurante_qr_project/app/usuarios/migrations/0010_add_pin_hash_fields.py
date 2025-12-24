# Generated manually for SGIR v40.5.1
from django.db import migrations, models
from django.contrib.auth.hashers import make_password


def hashear_pins_existentes(apps, schema_editor):
    """
    Hashea los PINs existentes en texto plano hacia campos hash.
    """
    Usuario = apps.get_model('usuarios', 'Usuario')

    usuarios_actualizados = 0

    for usuario in Usuario.objects.all():
        changed = False

        # Hashear pin_caja si existe
        if usuario.pin and not usuario.pin_caja_hash:
            try:
                usuario.pin_caja_hash = make_password(str(usuario.pin))
                changed = True
                print(f"  [HASH] PIN caja hasheado para: {usuario.username}")
            except Exception as e:
                print(f"  [ERROR] No se pudo hashear PIN caja para {usuario.username}: {e}")

        # Hashear pin_secundario si existe
        if usuario.pin_secundario and not usuario.pin_secundario_hash:
            try:
                usuario.pin_secundario_hash = make_password(str(usuario.pin_secundario))
                changed = True
                print(f"  [HASH] PIN secundario hasheado para: {usuario.username}")
            except Exception as e:
                print(f"  [ERROR] No se pudo hashear PIN secundario para {usuario.username}: {e}")

        if changed:
            usuario.save(update_fields=['pin_caja_hash', 'pin_secundario_hash'])
            usuarios_actualizados += 1

    print(f"\n[OK] {usuarios_actualizados} usuarios actualizados con PINs hasheados")


def reverse_hashear_pins(apps, schema_editor):
    """
    Reversa: limpia los hashes (no se pueden recuperar los PINs originales)
    """
    Usuario = apps.get_model('usuarios', 'Usuario')
    Usuario.objects.all().update(pin_caja_hash=None, pin_secundario_hash=None)
    print("[REVERSA] PINs hash limpiados")


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0009_usuario_pin_secundario'),
    ]

    operations = [
        # Agregar campos hash
        migrations.AddField(
            model_name='usuario',
            name='pin_caja_hash',
            field=models.CharField(
                blank=True,
                help_text='Hash del PIN de caja (PBKDF2) - NUNCA guardar texto plano',
                max_length=128,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='usuario',
            name='pin_secundario_hash',
            field=models.CharField(
                blank=True,
                help_text='Hash del PIN secundario para operaciones sensibles (anular producción, cerrar con deuda)',
                max_length=128,
                null=True
            ),
        ),

        # Hashear PINs existentes
        migrations.RunPython(hashear_pins_existentes, reverse_hashear_pins),

        # Marcar campos antiguos como deprecados (modificar help_text)
        migrations.AlterField(
            model_name='usuario',
            name='pin',
            field=models.CharField(
                blank=True,
                help_text='DEPRECADO: PIN numérico de 4-6 dígitos - usar pin_caja_hash',
                max_length=6,
                null=True,
                unique=True,
                validators=[
                    models.validators.MinLengthValidator(4),
                    models.validators.RegexValidator('^\\d+$', 'El PIN debe contener solo números.')
                ]
            ),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='pin_secundario',
            field=models.CharField(
                blank=True,
                help_text='DEPRECADO: usar pin_secundario_hash',
                max_length=6,
                null=True,
                validators=[
                    models.validators.MinLengthValidator(4),
                    models.validators.RegexValidator('^\\d+$', 'El PIN secundario debe contener solo números.')
                ]
            ),
        ),
    ]