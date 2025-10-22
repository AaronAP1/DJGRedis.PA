"""
Verificación de Cloudflare Turnstile.
"""
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile_token(token: str, remote_ip: str = None) -> bool:
    """
    Verifica un token de Cloudflare Turnstile.
    
    Args:
        token: Token de Turnstile del frontend
        remote_ip: IP del cliente (opcional)
    
    Returns:
        bool: True si la verificación es exitosa
    """
    # Si Turnstile está deshabilitado, permitir
    if not getattr(settings, 'CLOUDFLARE_TURNSTILE_ENABLED', False):
        return True
    
    # Sin bypass - siempre usar Cloudflare real
    # if settings.DEBUG and token == 'dev-bypass-turnstile':
    #     logger.info("Turnstile bypass usado en desarrollo")
    #     return True
    
    secret_key = getattr(settings, 'CLOUDFLARE_TURNSTILE_SECRET_KEY', '')
    
    if not secret_key or not token:
        logger.warning("Turnstile: Falta secret_key o token")
        return False
    
    # Preparar datos para verificación
    data = {
        'secret': secret_key,
        'response': token,
    }
    
    if remote_ip:
        data['remoteip'] = remote_ip
    
    try:
        # Hacer request a Cloudflare
        response = requests.post(
            TURNSTILE_VERIFY_URL,
            data=data,
            timeout=10
        )
        
        response.raise_for_status()
        
        result = response.json()
        success = result.get('success', False)
        
        if not success:
            error_codes = result.get('error-codes', [])
            logger.warning(f"Turnstile verification failed: {error_codes}")
        else:
            logger.info("Turnstile verification successful")
        
        return success
        
    except requests.RequestException as e:
        logger.error(f"Error verificando Turnstile: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado verificando Turnstile: {e}", exc_info=True)
        return False


def get_turnstile_site_key() -> str:
    """Obtiene la site key de Turnstile para el frontend."""


def is_turnstile_enabled() -> bool:
    """Verifica si Turnstile está habilitado."""
    return getattr(settings, 'CLOUDFLARE_TURNSTILE_ENABLED', False)
