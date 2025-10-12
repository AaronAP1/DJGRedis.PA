"""
Comando para debuggear tokens JWT activos.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

User = get_user_model()


class Command(BaseCommand):
    help = "Muestra información de debug sobre tokens JWT activos"

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email del usuario para filtrar tokens',
        )
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Limpiar todos los tokens activos (blacklist)',
        )

    def handle(self, *args, **options):
        user_email = options.get('user_email')
        clear_all = options.get('clear_all')
        
        self.stdout.write('🔍 Debug de Tokens JWT Activos\n')
        
        if clear_all:
            self._clear_all_tokens()
            return
        
        if user_email:
            self._show_user_tokens(user_email)
        else:
            self._show_all_tokens()
    
    def _clear_all_tokens(self):
        """Limpia todos los tokens activos agregándolos a blacklist."""
        outstanding_tokens = OutstandingToken.objects.all()
        count = 0
        
        for token in outstanding_tokens:
            if not hasattr(token, 'blacklistedtoken'):
                BlacklistedToken.objects.get_or_create(token=token)
                count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Se agregaron {count} tokens a la blacklist')
        )
    
    def _show_user_tokens(self, user_email):
        """Muestra tokens de un usuario específico."""
        try:
            user = User.objects.get(email=user_email)
            tokens = OutstandingToken.objects.filter(user=user)
            
            self.stdout.write(f'👤 Tokens para usuario: {user_email}\n')
            
            if not tokens.exists():
                self.stdout.write('❌ No hay tokens para este usuario')
                return
            
            for token in tokens:
                is_blacklisted = hasattr(token, 'blacklistedtoken')
                status = '🚫 BLACKLISTED' if is_blacklisted else '✅ ACTIVO'
                
                self.stdout.write(f'Token ID: {token.jti}')
                self.stdout.write(f'  Estado: {status}')
                self.stdout.write(f'  Creado: {token.created_at}')
                self.stdout.write(f'  Expira: {token.expires_at}')
                self.stdout.write('')
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Usuario no encontrado: {user_email}')
            )
    
    def _show_all_tokens(self):
        """Muestra estadísticas generales de tokens."""
        total_tokens = OutstandingToken.objects.count()
        blacklisted_tokens = BlacklistedToken.objects.count()
        active_tokens = total_tokens - blacklisted_tokens
        expired_tokens = OutstandingToken.objects.filter(
            expires_at__lt=timezone.now()
        ).count()
        
        self.stdout.write('📊 Estadísticas de Tokens JWT:')
        self.stdout.write(f'  • Total tokens: {total_tokens}')
        self.stdout.write(f'  • Tokens activos: {active_tokens}')
        self.stdout.write(f'  • Tokens blacklisted: {blacklisted_tokens}')
        self.stdout.write(f'  • Tokens expirados: {expired_tokens}')
        self.stdout.write('')
        
        # Mostrar últimos tokens activos
        recent_tokens = OutstandingToken.objects.select_related('user').order_by('-created_at')[:10]
        
        if recent_tokens:
            self.stdout.write('🕐 Últimos 10 tokens:')
            for token in recent_tokens:
                is_blacklisted = hasattr(token, 'blacklistedtoken')
                status = '🚫' if is_blacklisted else '✅'
                user_email = token.user.email if token.user else 'N/A'
                
                self.stdout.write(f'  {status} {user_email} - {token.created_at.strftime("%Y-%m-%d %H:%M:%S")}')