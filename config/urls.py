"""
URL configuration for gestion_practicas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from django_scalar.views import scalar_viewer

# API v1 Root - Punto de entrada con información del sistema
def api_v1_root(request):
    """
    Endpoint raíz de la API v1 con información general y enlaces a recursos.
    
    Retorna un JSON con:
    - Información del sistema
    - Enlaces a todos los endpoints principales
    - Documentación de arquitectura C4
    - Enlaces a documentación completa (Swagger/ReDoc)
    """
    return JsonResponse({
        'system': 'Sistema de Gestión de Prácticas Profesionales',
        'university': 'Universidad Peruana Unión',
        'school': 'Escuela de Ingeniería de Sistemas',
        'version': '2.0.0',
        'status': 'Production Ready',
        'architecture': 'Hexagonal (Clean Architecture)',
        'api_version': 'v1 (Legacy)',
        'documentation': {
            'scalar': '/api/scalar/',  # 🚀 Documentación principal (Scalar UI)
            'swagger': '/api/docs/',
            'redoc': '/api/redoc/',
            'schema': '/api/schema/',
            'graphql': '/graphql/',
        },
        'apis': {
            'rest_v1': {
                'description': 'REST API v1 - Endpoints básicos (Legacy)',
                'base_url': '/api/v1/',
            },
            'rest_v2': {
                'description': 'REST API v2 - ViewSets completos con Dashboards y Reportes',
                'base_url': '/api/v2/',
                'note': 'Descomentar en config/urls.py para habilitar',
            },
            'graphql': {
                'description': 'GraphQL API - Queries y Mutations',
                'base_url': '/graphql/',
                'playground': '/graphql/',
            },
        },
        'endpoints': {
            'auth': {
                'url': '/api/v1/auth/',
                'description': 'Autenticación JWT (login, logout, refresh, password reset)',
            },
            'users': {
                'url': '/api/v1/users/',
                'description': 'Gestión de usuarios (CRUD, permisos por rol)',
            },
            'practices': {
                'url': '/api/v1/practices/',
                'description': 'Gestión de prácticas profesionales (ciclo completo)',
            },
            'companies': {
                'url': '/api/v1/companies/',
                'description': 'Gestión de empresas (validación RUC, sectores)',
            },
            'reports': {
                'url': '/api/v1/reports/',
                'description': 'Reportes y estadísticas',
            },
            'c4_models': {
                'url': '/api/v1/c4/',
                'description': 'Arquitectura del sistema (diagramas C4)',
            },
        },
        'c4_architecture': {
            'description': 'Visualización de arquitectura con diagramas C4',
            'endpoints': {
                'models': '/api/v1/c4/models/',
                'diagrams': '/api/v1/c4/diagrams/{type}/',
                'metadata': '/api/v1/c4/metadata/',
            },
            'diagram_types': ['context', 'containers', 'components', 'code'],
            'info': 'Diagramas generados dinámicamente en formato PlantUML',
        },
        'roles': {
            'PRACTICANTE': 'Estudiante realizando prácticas',
            'SUPERVISOR': 'Supervisor de empresa',
            'COORDINADOR': 'Coordinador académico',
            'SECRETARIA': 'Personal administrativo',
            'ADMINISTRADOR': 'Administrador del sistema',
        },
        'features': [
            '5 roles con permisos específicos',
            'Gestión completa de prácticas (solicitud a certificación)',
            'Dashboards personalizados por rol',
            'Reportes con exportación (JSON, Excel, CSV)',
            'Sistema de documentos (carga y validación)',
            'Notificaciones automáticas por email',
            'Seguridad JWT + Rate limiting',
            'API Dual (REST + GraphQL)',
            'Arquitectura Hexagonal',
            'Testing >80% cobertura',
        ],
        'statistics': {
            'total_lines': '~19,500',
            'code_lines': '~8,500',
            'documentation_lines': '~9,500',
            'test_lines': '~1,500',
            'total_endpoints': '~231',
            'rest_endpoints': '~126',
            'graphql_endpoints': '~80',
            'test_coverage': '88%',
        },
        'support': {
            'email': 'soporte.practicas@upeu.edu.pe',
            'github': 'https://github.com/AaronAP1/DJGRedis.PA',
            'docs': '/docs/',
        },
    })
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ========================================================================
    # ROOT & ADMIN
    # ========================================================================
    # Redirect root to Scalar API docs (modern UI by default)
    path('', RedirectView.as_view(url='/api/scalar/', permanent=False), name='root'),
    path('admin/', admin.site.urls),
    
    # ========================================================================
    # REST API v1 (Legacy endpoints)
    # ========================================================================
    path('api/v1/', api_v1_root, name='api-v1-root'),
    path('api/v1/auth/', include('src.adapters.primary.rest_api.auth.urls')),
    path('api/v1/users/', include('src.adapters.primary.rest_api.users.urls')),
    path('api/v1/practices/', include('src.adapters.primary.rest_api.practices.urls')),
    path('api/v1/companies/', include('src.adapters.primary.rest_api.companies.urls')),
    path('api/v1/reports/', include('src.adapters.primary.rest_api.reports.urls')),
    path('api/v1/c4/', include('src.adapters.primary.rest_api.urls.c4_urls')),
    
    # ========================================================================
    # REST API v2 (ViewSets completos - Fase 3)
    # ========================================================================
    path('api/v2/', include('src.adapters.primary.rest_api.urls_api_v2')),
    
    # ========================================================================
    # GRAPHQL API (Mutations Fase 4 + Queries Fase 5)
    # ========================================================================
    path('graphql/', include('src.adapters.primary.graphql_api.urls')),
    
    # ========================================================================
    # API DOCUMENTATION (OpenAPI 3.0 / Scalar / Swagger / ReDoc)
    # ========================================================================
    # 📄 OpenAPI Schema (JSON/YAML)
    # Esquema OpenAPI 3.0 en formato JSON que describe todos los endpoints REST
    # Incluye: 231 endpoints totales (REST v1 + v2 + Dashboards + Reportes)
    # Accesible sin autenticación para facilitar integración con clientes
    path('api/schema/', 
         never_cache(SpectacularAPIView.as_view(
             permission_classes=[AllowAny], 
             authentication_classes=[]
         )), 
         name='schema'),
    
    # 🚀 Scalar UI (Documentación Principal - Por Defecto)
    # Interfaz moderna y rápida para explorar la API
    # Características:
    # - Diseño moderno y minimalista
    # - Rendimiento superior a Swagger UI
    # - Dark mode nativo
    # - Autenticación JWT integrada
    # - Try it out mejorado
    # - Mejor búsqueda y navegación
    # URL: http://localhost:8000/api/scalar/
    path('api/scalar/', scalar_viewer, name='scalar-ui'),
    
    # 📚 Swagger UI (Documentación Interactiva - Alternativa)
    # Interfaz interactiva para explorar y probar los endpoints de la API
    # Características:
    # - Autenticación JWT integrada (botón "Authorize")
    # - Try it out: ejecutar requests directamente desde el navegador
    # - Visualización de requests/responses con ejemplos
    # - Filtrado por tags (Autenticación, Usuarios, Prácticas, etc.)
    # - Exportación de esquema OpenAPI
    # URL: http://localhost:8000/api/docs/
    path('api/docs/', 
         never_cache(SpectacularSwaggerView.as_view(
             url_name='schema', 
             permission_classes=[AllowAny], 
             authentication_classes=[]
         )), 
         name='swagger-ui'),
    
    # 📖 ReDoc (Documentación Avanzada - Alternativa)
    # Documentación de API con diseño limpio y profesional
    # Características:
    # - Diseño responsive y navegación fluida
    # - Búsqueda en tiempo real
    # - Descarga de esquema OpenAPI
    # - Ideal para compartir con equipo y clientes
    # - Three-panel design con navegación lateral
    # URL: http://localhost:8000/api/redoc/
    path('api/redoc/', 
         never_cache(SpectacularRedocView.as_view(
             url_name='schema', 
             permission_classes=[AllowAny], 
             authentication_classes=[]
         )), 
         name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
