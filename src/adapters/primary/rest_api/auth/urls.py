"""
URLs de Autenticación REST API.

Endpoints disponibles:
- POST /api/v1/auth/login/      → Obtener access + refresh tokens
- POST /api/v1/auth/refresh/    → Refrescar access token
- POST /api/v1/auth/logout/     → Cerrar sesión (blacklist token)
- GET  /api/v1/auth/me/         → Obtener datos del usuario autenticado
"""

from django.urls import path
from .views import LoginView, RefreshTokenView, LogoutView, MeView

app_name = 'auth'

urlpatterns = [
    # Login - Obtener tokens JWT
    path('login/', LoginView.as_view(), name='login'),
    
    # Refresh - Renovar access token
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    
    # Logout - Cerrar sesión
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Me - Datos del usuario autenticado
    path('me/', MeView.as_view(), name='me'),
]
