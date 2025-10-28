from django.urls import path
from django.http import JsonResponse
from django.conf import settings
import jwt
from datetime import datetime, timedelta
import logging


def placeholder(request):
    logger = logging.getLogger(__name__)

    try:
        secret = getattr(settings, "SECRET_KEY", None)
        if not secret:
            logger.error("JWT secret not configured")
            return JsonResponse({"status": "error", "message": "server misconfiguration"}, status=500)

        exp_minutes = getattr(settings, "ACCESS_TOKEN_EXP_MINUTES", 60)
        algorithm = getattr(settings, "JWT_ALGORITHM", "HS256")
        now = datetime.utcnow()
        payload = {
            "iss": getattr(settings, "JWT_ISSUER", "djgredis.pa"),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=exp_minutes)).timestamp()),
            "sub": "anonymous",
            "scope": "access",
        }

        token = jwt.encode(payload, secret, algorithm=algorithm)
        # PyJWT may return bytes on older versions
        if isinstance(token, bytes):
            token = token.decode()

        logger.info("ACCESS_TOKEN_ISSUED", extra={"module": "auth"})
        return JsonResponse({"status": "ok", "module": "auth", "token": token})
    except Exception as e:
        logger.exception("Failed to generate access token")
        return JsonResponse({"status": "error", "message": "failed to generate token"}, status=500)


urlpatterns = [
    path('', placeholder, name='auth-root'),
]
