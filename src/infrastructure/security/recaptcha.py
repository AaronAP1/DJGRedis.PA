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

    # Bypass en desarrollo: si DEBUG=True y token coincide con RECAPTCHA_DEV_BYPASS_TOKEN
    try:
        bypass_token = getattr(settings, 'RECAPTCHA_DEV_BYPASS_TOKEN', 'dev-bypass')
        if getattr(settings, 'DEBUG', False) and token == bypass_token:
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
