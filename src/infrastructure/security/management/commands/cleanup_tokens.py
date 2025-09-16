from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

class Command(BaseCommand):
    help = "Cleanup expired/revoked JWT tokens (SimpleJWT and GraphQL JWT)."

    def handle(self, *args, **options):
        total_deleted = 0

        # SimpleJWT blacklist cleanup
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
                f"SimpleJWT: deleted {bl_deleted} blacklisted and {out_deleted} outstanding expired tokens"
            ))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"SimpleJWT cleanup skipped: {e}"))

        # graphql_jwt refresh tokens cleanup
        try:
            from graphql_jwt.refresh_token.models import RefreshToken

            now = timezone.now()

            # 1) Delete unrevoked but expired tokens (created <= now - REFRESH_EXPIRATION_DELTA)
            gql_jwt = getattr(settings, 'GRAPHQL_JWT', {})
            refresh_delta = gql_jwt.get('JWT_REFRESH_EXPIRATION_DELTA') or timedelta(days=7)
            cutoff_expired = now - refresh_delta
            qs_expired = RefreshToken.objects.filter(revoked__isnull=True, created__lte=cutoff_expired)
            deleted_expired = qs_expired.delete()[0]
            total_deleted += deleted_expired
            self.stdout.write(self.style.SUCCESS(
                f"GraphQL JWT: deleted {deleted_expired} expired (unrevoked) refresh tokens"
            ))

            # 2) Delete revoked tokens older than 30 days (audit retention)
            cutoff_revoked = now - timezone.timedelta(days=30)
            qs_revoked = RefreshToken.objects.filter(revoked__isnull=False, created__lte=cutoff_revoked)
            deleted_revoked = qs_revoked.delete()[0]
            total_deleted += deleted_revoked
            self.stdout.write(self.style.SUCCESS(
                f"GraphQL JWT: deleted {deleted_revoked} revoked refresh tokens older than 30 days"
            ))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"GraphQL JWT cleanup skipped: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Done. Total deleted: {total_deleted}"))
