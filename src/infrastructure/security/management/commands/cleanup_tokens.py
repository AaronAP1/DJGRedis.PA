from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

class Command(BaseCommand):
    help = "Limpia tokens JWT expirados del sistema JWT PURO."

    def handle(self, *args, **options):
        total_deleted = 0

        # 1. SimpleJWT blacklist cleanup (sistema JWT PURO)
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

            now = timezone.now()
            expired = OutstandingToken.objects.filter(expires_at__lte=now)
            count_out = expired.count()
            # Delete blacklisted rows referencing expired tokens first
            bl_deleted = BlacklistedToken.objects.filter(token__in=expired).delete()[0]
            out_deleted = expired.delete()[0]
            total_deleted += bl_deleted + out_deleted
            self.stdout.write(self.style.SUCCESS(
                f"✅ JWT PURO: eliminados {bl_deleted} blacklisted + {out_deleted} outstanding tokens expirados"
            ))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  SimpleJWT cleanup omitido: {e}"))

        # 2. JWT Sessions cleanup - Ya no hay sesiones opacas
        self.stdout.write(
            self.style.SUCCESS('Sistema JWT PURO - No hay sesiones opacas que limpiar')
        )
        self.stdout.write(self.style.SUCCESS(f"\n✨ Limpieza completada. Total eliminado: {total_deleted} registros"))
