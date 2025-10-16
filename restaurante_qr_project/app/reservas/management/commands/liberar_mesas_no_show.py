"""
Comando de Django para liberar mesas de reservas vencidas (no-show).

Uso:
    python manage.py liberar_mesas_no_show

Este comando debe ejecutarse periódicamente (cada 5-15 minutos) usando:
- Cron (Linux/Mac)
- Task Scheduler (Windows)
- Celery Beat (producción)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from app.reservas.models import Reserva
import logging

logger = logging.getLogger('app.reservas')


class Command(BaseCommand):
    help = 'Libera mesas de reservas que no llegaron después de 15 minutos de tolerancia'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutos',
            type=int,
            default=15,
            help='Minutos de tolerancia antes de marcar como no-show (default: 15)'
        )

    def handle(self, *args, **options):
        minutos_tolerancia = options['minutos']

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🔍 Buscando reservas vencidas con tolerancia de {minutos_tolerancia} minutos...'
            )
        )

        # Buscar reservas pendientes o confirmadas que ya pasaron la tolerancia
        reservas_pendientes = Reserva.objects.filter(
            estado__in=['pendiente', 'confirmada'],
            fecha_reserva__lte=timezone.now().date()
        )

        total_liberadas = 0
        total_analizadas = 0

        for reserva in reservas_pendientes:
            total_analizadas += 1

            # Verificar si está vencida con tolerancia
            if reserva.esta_vencida_con_tolerancia(minutos_tolerancia):
                # Intentar liberar
                if reserva.liberar_por_no_show():
                    total_liberadas += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ❌ NO-SHOW: Reserva #{reserva.id} - {reserva.nombre_completo} '
                            f'(Mesa {reserva.mesa.numero if reserva.mesa else "N/A"}) - '
                            f'Hora: {reserva.hora_reserva.strftime("%H:%M")}'
                        )
                    )
                    logger.warning(
                        f'Reserva #{reserva.id} marcada como no-show y mesa liberada - '
                        f'{reserva.nombre_completo}'
                    )

        if total_liberadas == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ No hay reservas vencidas. Analizadas: {total_analizadas}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Proceso completado:'
                    f'\n   - Reservas analizadas: {total_analizadas}'
                    f'\n   - Mesas liberadas: {total_liberadas}'
                )
            )

        logger.info(
            f'Comando liberar_mesas_no_show ejecutado: '
            f'{total_analizadas} analizadas, {total_liberadas} liberadas'
        )
