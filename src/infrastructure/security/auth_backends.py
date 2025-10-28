"""
Backend de autenticación personalizado que permite login con email (correo).
ADAPTADO para modelo User con campo 'correo' en lugar de 'username'.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Backend de autenticación que permite login con email (correo).
    Adaptado a la estructura de BD existente con campo 'correo'.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica usuario por email.
        
        Args:
            username: En Django admin se llama 'username', pero buscamos por correo
            password: Contraseña del usuario
        
        Returns:
            User object si autenticación exitosa, None en caso contrario
        """
        if username is None or password is None:
            return None
        
        try:
            # Buscar usuario por correo (case-insensitive)
            # El formulario de Django admin envía 'username', pero nosotros buscamos por 'correo'
            user = User.objects.get(correo__iexact=username)
            
            # Verificar contraseña
            if user.check_password(password):
                return user
            
        except User.DoesNotExist:
            # Ejecutar hash de password para evitar timing attacks
            User().set_password(password)
            return None
        
        return None
    
    def get_user(self, user_id):
        """Obtiene usuario por ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


# Alias para mantener compatibilidad
UsernameOnlyBackend = EmailBackend
