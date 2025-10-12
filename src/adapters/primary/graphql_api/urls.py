"""
URLs para la API GraphQL del sistema de gestión de prácticas profesionales.
Sistema JWT PURO.
"""

from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from graphene_django.views import GraphQLView
from django.conf import settings
import json

from .schema import schema
from .quickstart_views import GraphiQLQuickstartView

# Dummy decorator si no existe jwt_cookie
def jwt_cookie(view_func):
    """Decorator dummy para compatibilidad."""
    return view_func


# Vista GraphQL con autenticación JWT
class CustomGraphQLView(GraphQLView):
    """Vista personalizada de GraphQL con configuraciones adicionales."""
    def dispatch(self, request, *args, **kwargs):
        """Procesa la petición con soporte para JWT."""
        response = super().dispatch(request, *args, **kwargs)

        # Intentar establecer cookies HttpOnly cuando TokenAuth/refreshToken tienen éxito
        try:
            # Config names
            jwt_settings = getattr(settings, 'GRAPHQL_JWT', {})
            cookie_name = jwt_settings.get('JWT_COOKIE_NAME', 'JWT')
            refresh_cookie_name = jwt_settings.get('JWT_REFRESH_TOKEN_COOKIE_NAME', 'JWT_REFRESH_TOKEN')
            secure = jwt_settings.get('JWT_COOKIE_SECURE', not settings.DEBUG)
            samesite = jwt_settings.get('JWT_COOKIE_SAMESITE', 'Strict')
            path = jwt_settings.get('JWT_COOKIE_PATH', '/api/graphql/')
            # DRF cookie names (SimpleJWT)
            drf_cookie_name = getattr(settings, 'DRF_JWT_COOKIE_NAME', 'DRF_JWT')
            drf_refresh_cookie_name = getattr(settings, 'DRF_JWT_REFRESH_COOKIE_NAME', 'DRF_JWT_REFRESH')

            # Helper to set cookie
            def _set_cookie(name, value, max_age=None):
                if value:
                    response.set_cookie(
                        name,
                        value,
                        httponly=True,
                        secure=secure,
                        samesite=samesite,
                        path=path,
                        max_age=max_age,
                    )

            # Calculate cookie TTLs from settings
            access_ttl = int((jwt_settings.get('JWT_EXPIRATION_DELTA') or 0).total_seconds()) if jwt_settings.get('JWT_EXPIRATION_DELTA') else 60 * 15
            refresh_ttl = int((jwt_settings.get('JWT_REFRESH_EXPIRATION_DELTA') or 0).total_seconds()) if jwt_settings.get('JWT_REFRESH_EXPIRATION_DELTA') else 60 * 60 * 24 * 5

            # 1) Preferir tokens que la mutation dejó en el request (no requiere seleccionar campos)
            req_tokens = getattr(request, '_jwt_tokens', None)
            if isinstance(req_tokens, dict):
                # GraphQL cookies (graphql_jwt tokens)
                _set_cookie(cookie_name, req_tokens.get('graphql_access') or req_tokens.get('access'), max_age=access_ttl)
                _set_cookie(refresh_cookie_name, req_tokens.get('graphql_refresh') or req_tokens.get('refresh'), max_age=refresh_ttl)
                # DRF cookies (SimpleJWT tokens) para REST
                _set_cookie(drf_cookie_name, req_tokens.get('drf_access') or req_tokens.get('graphql_access') or req_tokens.get('access'), max_age=access_ttl)
                _set_cookie(drf_refresh_cookie_name, req_tokens.get('drf_refresh') or req_tokens.get('graphql_refresh') or req_tokens.get('refresh'), max_age=refresh_ttl)

            # 2) Fallback: parsear el body si el cliente solicitó los campos de token
            if request.method == 'POST' and request.body:
                body = json.loads(request.body.decode('utf-8'))
                query = (body.get('query') or '').replace('\n', ' ')
                op_name = body.get('operationName') or ''

                content = response.content.decode('utf-8') if hasattr(response, 'content') else None
                data = json.loads(content) if content else None
                payload = (data or {}).get('data') or {}

                # TokenAuth custom mutation
                if op_name == 'TokenAuth' or 'tokenAuth' in query:
                    t = ((payload.get('TokenAuth') or payload.get('tokenAuth')) or {})
                    access = t.get('token')
                    refresh = t.get('refreshToken') or t.get('refresh_token')
                    _set_cookie(cookie_name, access, max_age=access_ttl)
                    _set_cookie(refresh_cookie_name, refresh, max_age=refresh_ttl)

                # refreshToken mutation (rotating)
                if op_name == 'Refresh' or 'refreshToken' in query:
                    t = ((payload.get('Refresh') or payload.get('refreshToken')) or {})
                    access = t.get('token')
                    refresh = t.get('refreshToken') or t.get('refresh_token')
                    _set_cookie(cookie_name, access, max_age=access_ttl)
                    if refresh:
                        _set_cookie(refresh_cookie_name, refresh, max_age=refresh_ttl)

                # stableRefresh mutation (non-rotating refresh)
                if op_name == 'StableRefresh' or 'stableRefresh' in query:
                    t = ((payload.get('StableRefresh') or payload.get('stableRefresh')) or {})
                    access = t.get('token')
                    refresh = t.get('refreshToken') or t.get('refresh_token')
                    _set_cookie(cookie_name, access, max_age=access_ttl)
                    if refresh:
                        _set_cookie(refresh_cookie_name, refresh, max_age=refresh_ttl)

                # Logout: limpiar cookies si el request lo indica
                if getattr(request, '_clear_jwt_cookies', False) or op_name == 'Logout' or 'logout' in query:
                    response.delete_cookie(cookie_name, path=path, samesite=samesite)
                    response.delete_cookie(refresh_cookie_name, path=path, samesite=samesite)
                    # Borrar también cookies DRF
                    response.delete_cookie(drf_cookie_name, path=path, samesite=samesite)
                    response.delete_cookie(drf_refresh_cookie_name, path=path, samesite=samesite)
            # Si es una carga de GraphiQL (GET html) y viene prefill=1, solo prellenar editor.
            if request.method == 'GET' and hasattr(response, 'content') and 'text/html' in response.get('Content-Type', ''):
                prefill = str(request.GET.get('prefill', '')).lower() in ('1','true','yes','y')
                if prefill:
                    try:
                        html = response.content.decode('utf-8')
                        import json as _json
                        jq = _json.dumps(request.GET.get('query'))
                        jv = _json.dumps(request.GET.get('variables'))
                        jo = _json.dumps(request.GET.get('operationName'))
                        inject_pf = ("<script>(function(){try{"
                                     "var Q=%s,V=%s,OP=%s;"
                                     "if(Q){localStorage.setItem('graphiql:query',Q);}"
                                     "if(V){localStorage.setItem('graphiql:variables',V);}"
                                     "if(OP){localStorage.setItem('graphiql:operationName',OP);}"
                                     "}catch(e){}})();</script>") % (jq, jv, jo)
                        if '</head>' in html:
                            html = html.replace('</head>', inject_pf + '</head>')
                        else:
                            html = inject_pf + html
                        response.content = html.encode('utf-8')
                    except Exception:
                        pass
        except Exception:
            # No bloquear la respuesta si falla el seteo de cookies
            pass

        return response


urlpatterns = [
    # Endpoint principal de GraphQL
    path(
        'graphql/',
        csrf_exempt(
            jwt_cookie(
                CustomGraphQLView.as_view(
                    schema=schema,
                    graphiql=True  # Habilitar interfaz GraphiQL en desarrollo
                )
            )
        ),
        name='graphql'
    ),
    
    # Endpoint solo para producción sin GraphiQL
    path(
        'graphql/api/',
        csrf_exempt(
            jwt_cookie(
                CustomGraphQLView.as_view(
                    schema=schema,
                    graphiql=False
                )
            )
        ),
        name='graphql_api'
    ),

    # Página de inicio rápido con enlaces que precargan consultas en GraphiQL
    path(
        'graphql/quickstart/',
        GraphiQLQuickstartView.as_view(),
        name='graphql_quickstart'
    ),
    
    # Cloudflare Turnstile será implementado próximamente

]
