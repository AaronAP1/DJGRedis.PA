"""
URLs para la API GraphQL.
"""

from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from graphql_jwt.decorators import jwt_cookie

from .schema import schema


# Vista GraphQL con autenticación JWT
class CustomGraphQLView(GraphQLView):
    """Vista personalizada de GraphQL con configuraciones adicionales."""
    
    def dispatch(self, request, *args, **kwargs):
        """Procesa la petición con soporte para JWT."""
        return super().dispatch(request, *args, **kwargs)


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
]
