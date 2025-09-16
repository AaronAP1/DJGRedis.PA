from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.request import Request
from django.conf import settings


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request):
        # No usar blacklist; solo limpiar cookies
        resp = Response({'success': True, 'message': 'Logout exitoso'}, status=status.HTTP_200_OK)

        # Intentar borrar las cookies usadas por GraphQL
        cookie_name = getattr(settings, 'GRAPHQL_JWT', {}).get('JWT_COOKIE_NAME', 'JWT')
        refresh_cookie_name = getattr(settings, 'GRAPHQL_JWT', {}).get('JWT_REFRESH_TOKEN_COOKIE_NAME', 'JWT_REFRESH_TOKEN')
        cookie_path = getattr(settings, 'GRAPHQL_JWT', {}).get('JWT_COOKIE_PATH', '/api/graphql/')
        resp.delete_cookie(cookie_name, path=cookie_path)
        resp.delete_cookie(refresh_cookie_name, path=cookie_path)
        return resp
