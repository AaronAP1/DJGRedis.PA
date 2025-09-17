"""
reCAPTCHA verification utility.
"""
from django.conf import settings
import requests

VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def verify_recaptcha(token: str, remote_ip: str = None) -> bool:
    """Verify a reCAPTCHA token with Google.

    Returns True if verification succeeds or if RECAPTCHA is disabled in settings.
    """
    if not getattr(settings, 'RECAPTCHA_ENABLED', False):
        return True

    # Bypass en desarrollo endurecido:
    # Solo permitir si DEBUG=True y el token de bypass es personalizado (no vacío, no 'dev-bypass', no '__DISABLED__').
    try:
        bypass_token = getattr(settings, 'RECAPTCHA_DEV_BYPASS_TOKEN', 'dev-bypass')
        debug_mode = getattr(settings, 'DEBUG', False)
        custom_bypass = bool(bypass_token) and bypass_token not in ('dev-bypass', '__DISABLED__')
        if debug_mode and custom_bypass and token == bypass_token:
            return True
    except Exception:
        pass

    secret = getattr(settings, 'RECAPTCHA_SECRET', '')
    if not secret or not token:
        return False

    data = {
        'secret': secret,
        'response': token,
    }
    if remote_ip:
        data['remoteip'] = remote_ip

    try:
        resp = requests.post(VERIFY_URL, data=data, timeout=5)
        resp.raise_for_status()
        payload = resp.json()
        return bool(payload.get('success'))
    except Exception:
        return False
