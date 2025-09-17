"""
Simple rate limit middleware using Django cache.
Limits requests per IP per time window. Tightens limits for login/auth operations.
"""
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
import time
import json


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Defaults
        self.default_requests = int(getattr(settings, 'RATE_LIMIT_REQUESTS_PER_MINUTE', 120))
        self.default_window = 60
        self.login_requests = int(getattr(settings, 'RATE_LIMIT_LOGIN_PER_5MIN', 20))
        self.login_window = 300

    def __call__(self, request):
        client_ip = self._get_client_ip(request)
        path = request.path
        method = request.method

        # Determine bucket and limits
        if path.startswith('/api/graphql/') and method == 'POST':
            # Try to detect login (tokenAuth) in GraphQL body
            try:
                body = request.body.decode('utf-8') if request.body else ''
                op_name = None
                if body:
                    data = json.loads(body)
                    op_name = data.get('operationName') or ''
                    query = data.get('query') or ''
                if op_name == 'TokenAuth' or 'tokenAuth' in (query or '').replace('\n', ' '):
                    limit = self.login_requests
                    window = self.login_window
                    bucket = 'login'
                else:
                    limit = self.default_requests
                    window = self.default_window
                    bucket = 'graphql'
            except Exception:
                limit = self.default_requests
                window = self.default_window
                bucket = 'graphql'
        else:
            limit = self.default_requests
            window = self.default_window
            bucket = 'default'

        key = f"rl:{bucket}:{client_ip}:{int(time.time() // window)}"
        count = cache.get(key)
        if count is not None and count >= limit:
            return JsonResponse({
                'detail': 'Too many requests. Please try again later.'
            }, status=429)
        # increment with TTL window
        # Try to create the key with TTL if it doesn't exist
        added = cache.add(key, 1, timeout=window)
        if not added:
            try:
                cache.incr(key)
            except Exception:
                # Fallback to set with TTL
                current = cache.get(key) or 0
                cache.set(key, current + 1, timeout=window)

        response = self.get_response(request)
        return response

    def _get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
