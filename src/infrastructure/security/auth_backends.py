"""
Backend de autenticación personalizado que permite login con email o username.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class UsernameOnlyBackend(ModelBackend):
    """
    Backend de autenticación que SOLO permite login con username.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        try:
            # Buscar usuario SOLO por username
            user = User.objects.get(username__iexact=username)
            
            # Verificar contraseña
            if user.check_password(password):
                return user
            
        except User.DoesNotExist:
            # Ejecutar hash de password para evitar timing attacks
            User().set_password(password)
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
