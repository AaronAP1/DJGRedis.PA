"""
Comando de gestión para tokens JWT.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

User = get_user_model()


class Command(BaseCommand):
    help = 'Gestiona tokens JWT del sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['cleanup', 'list', 'stats', 'blacklist_user', 'blacklist_all'],
            help='Acción a realizar'
        )
        
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email del usuario (para blacklist_user)'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Días para estadísticas (default: 7)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar acción sin confirmación'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'cleanup':
            self.cleanup_tokens(options['force'])
        elif action == 'list':
            self.list_tokens()
        elif action == 'stats':
            self.show_stats(options['days'])
        elif action == 'blacklist_user':
            self.blacklist_user_tokens(options['user_email'], options['force'])
        elif action == 'blacklist_all':
            self.blacklist_all_tokens(options['force'])
    
    def cleanup_tokens(self, force=False):
        """Limpia tokens expirados."""
        expired_tokens = OutstandingToken.objects.filter(
            expires_at__lt=timezone.now()
        )
        expired_count = expired_tokens.count()
        
        if expired_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No hay tokens expirados para limpiar.')
            )
            return
        
        if not force:
            confirm = input(f'¿Eliminar {expired_count} tokens expirados? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Operación cancelada.')
                return
        
        # Eliminar tokens expirados
        deleted_count = expired_tokens.delete()[0]
        self.stdout.write(
            self.style.SUCCESS(f'Se eliminaron {deleted_count} tokens expirados.')
        )
    
    def list_tokens(self):
        """Lista tokens activos."""
        tokens = OutstandingToken.objects.select_related('user').filter(
            expires_at__gt=timezone.now()
        ).order_by('-created_at')
        
        # Filtrar tokens no blacklisted
        active_tokens = []
        for token in tokens:
            if not hasattr(token, 'blacklistedtoken'):
                active_tokens.append(token)
        
        if not active_tokens:
            self.stdout.write('No hay tokens activos.')
            return
        
        self.stdout.write(f'\n{"Token ID":<12} {"Usuario":<25} {"Creado":<20} {"Expira":<20} {"Estado":<10}')
        self.stdout.write('-' * 95)
        
        for token in active_tokens[:20]:  # Mostrar solo los primeros 20
            token_short = token.jti[:8] + '...'
            user_email = token.user.email[:22] + '...' if len(token.user.email) > 25 else token.user.email
            created_at = token.created_at.strftime('%Y-%m-%d %H:%M:%S')
            expires_at = token.expires_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # Verificar si está blacklisted
            is_blacklisted = hasattr(token, 'blacklistedtoken')
            status = 'BLACKLIST' if is_blacklisted else 'ACTIVO'
            
            self.stdout.write(
                f'{token_short:<12} {user_email:<25} {created_at:<20} {expires_at:<20} {status:<10}'
            )
        
        if len(active_tokens) > 20:
            self.stdout.write(f'\n... y {len(active_tokens) - 20} tokens más')
    
    def show_stats(self, days):
        """Muestra estadísticas de tokens."""
        now = timezone.now()
        since = now - timezone.timedelta(days=days)
        
        # Estadísticas generales
        total_tokens = OutstandingToken.objects.count()
        active_tokens = OutstandingToken.objects.filter(
            expires_at__gt=now
        ).count()
        blacklisted_tokens = BlacklistedToken.objects.count()
        expired_tokens = OutstandingToken.objects.filter(
            expires_at__lt=now
        ).count()
        recent_tokens = OutstandingToken.objects.filter(
            created_at__gte=since
        ).count()
        
        # Usuarios más activos
        active_users = OutstandingToken.objects.filter(
            created_at__gte=since
        ).values('user__email').annotate(
            token_count=models.Count('id')
        ).order_by('-token_count')[:10]
        
        self.stdout.write(self.style.SUCCESS(f'\n=== Estadísticas de Tokens JWT (últimos {days} días) ==='))
        
        self.stdout.write(f'\n📊 Resumen General:')
        self.stdout.write(f'  • Total tokens: {total_tokens}')
        self.stdout.write(f'  • Tokens activos: {active_tokens}')
        self.stdout.write(f'  • Tokens blacklisted: {blacklisted_tokens}')
        self.stdout.write(f'  • Tokens expirados: {expired_tokens}')
        self.stdout.write(f'  • Tokens creados (período): {recent_tokens}')
        
        if active_users:
            self.stdout.write(f'\n👥 Usuarios Más Activos:')
            for user in active_users:
                email = user['user__email'] or 'N/A'
                count = user['token_count']
                self.stdout.write(f'  • {email}: {count} tokens')
    
    def blacklist_user_tokens(self, user_email, force=False):
        """Agrega todos los tokens de un usuario a blacklist."""
        if not user_email:
            self.stdout.write(
                self.style.ERROR('Debe especificar --user-email')
            )
            return
        
        try:
            user = User.objects.get(email=user_email)
            tokens = OutstandingToken.objects.filter(user=user)
            
            # Contar tokens activos (no blacklisted)
            active_count = 0
            for token in tokens:
                if not hasattr(token, 'blacklistedtoken'):
                    active_count += 1
            
            if active_count == 0:
                self.stdout.write(f'No hay tokens activos para {user_email}')
                return
            
            if not force:
                confirm = input(f'¿Agregar {active_count} tokens de {user_email} a blacklist? (y/N): ')
                if confirm.lower() != 'y':
                    self.stdout.write('Operación cancelada.')
                    return
            
            # Agregar a blacklist
            blacklisted_count = 0
            for token in tokens:
                if not hasattr(token, 'blacklistedtoken'):
                    BlacklistedToken.objects.get_or_create(token=token)
                    blacklisted_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Se agregaron {blacklisted_count} tokens a blacklist para {user_email}')
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Usuario no encontrado: {user_email}')
            )
    
    def blacklist_all_tokens(self, force=False):
        """Agrega todos los tokens activos a blacklist."""
        tokens = OutstandingToken.objects.all()
        
        # Contar tokens activos (no blacklisted)
        active_count = 0
        for token in tokens:
            if not hasattr(token, 'blacklistedtoken'):
                active_count += 1
        
        if active_count == 0:
            self.stdout.write('No hay tokens activos para agregar a blacklist.')
            return
        
        if not force:
            confirm = input(f'¿Agregar TODOS los {active_count} tokens activos a blacklist? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Operación cancelada.')
                return
        
        # Agregar todos a blacklist
        blacklisted_count = 0
        for token in tokens:
            if not hasattr(token, 'blacklistedtoken'):
                BlacklistedToken.objects.get_or_create(token=token)
                blacklisted_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Se agregaron {blacklisted_count} tokens a blacklist.')
        )
