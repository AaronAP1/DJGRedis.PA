"""
URLs para REST API - Sistema de Gestión de Prácticas Profesionales.

Este módulo configura todas las rutas REST usando Django REST Framework router.
Incluye endpoints para todos los ViewSets implementados en Fase 3.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from src.adapters.primary.rest_api.viewsets import (
    UserViewSet,
    StudentViewSet,
    CompanyViewSet,
    SupervisorViewSet,
    PracticeViewSet,
    DocumentViewSet,
    NotificationViewSet,
    SchoolViewSet,
    BranchViewSet,
    PracticeEvaluationViewSet,
    PracticeStatusHistoryViewSet
)

# Avatar ViewSet
from src.adapters.primary.rest_api.avatars.viewset import AvatarViewSet

# Security ViewSets (RBAC) - Tablas permissions, roles, role_permissions, user_permissions existen en BD
from src.adapters.primary.rest_api.roles.viewset import RoleViewSet
from src.adapters.primary.rest_api.permissions.viewset import PermissionViewSet
from src.adapters.primary.rest_api.user_permissions.viewset import UserPermissionViewSet

# Dashboard y Reports ViewSets (Fase 7)
from src.adapters.primary.rest_api.views.dashboards import DashboardViewSet
from src.adapters.primary.rest_api.views.reports import ReportsViewSet

# Presentation Letter ViewSet (Nuevo - Carta de Presentación)
from src.adapters.primary.rest_api.presentation_letter_viewset import PresentationLetterRequestViewSet

# NOTA: Los endpoints de School y Company ya están registrados arriba
# No necesitamos importar school_company_viewsets porque usamos los existentes


# ============================================================================
# ROUTER CONFIGURATION
# ============================================================================

# Router principal con trailing slash opcional
router = DefaultRouter(trailing_slash=True)

# Registrar ViewSets principales (Fase 3)
router.register(r'users', UserViewSet, basename='user')
router.register(r'avatars', AvatarViewSet, basename='avatar')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'user-permissions', UserPermissionViewSet, basename='user-permission')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'supervisors', SupervisorViewSet, basename='supervisor')
router.register(r'practices', PracticeViewSet, basename='practice')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'notifications', NotificationViewSet, basename='notification')

# Registrar ViewSets académicos (Nuevos modelos)
router.register(r'schools', SchoolViewSet, basename='school')
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'evaluations', PracticeEvaluationViewSet, basename='evaluation')
router.register(r'practice-status-history', PracticeStatusHistoryViewSet, basename='practice-status-history')

# Registrar ViewSets de Dashboard y Reportes (Fase 7)
router.register(r'dashboards', DashboardViewSet, basename='dashboard')
router.register(r'reports', ReportsViewSet, basename='report')

# Registrar ViewSet de Solicitud de Carta de Presentación
router.register(r'cartas-presentacion', PresentationLetterRequestViewSet, basename='carta-presentacion')


# ============================================================================
# API ROOT VIEW
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    API Root - Sistema de Gestión de Prácticas Profesionales UPEU.
    
    Retorna información sobre los endpoints disponibles.
    """
    return Response({
        'version': '2.0',
        'description': 'Sistema de Gestión de Prácticas Profesionales',
        'institution': 'Universidad Peruana Unión',
        'endpoints': {
            'users': request.build_absolute_uri('users/'),
            'avatars': request.build_absolute_uri('avatars/'),
            'roles': request.build_absolute_uri('roles/'),
            'permissions': request.build_absolute_uri('permissions/'),
            'user_permissions': request.build_absolute_uri('user-permissions/'),
            'students': request.build_absolute_uri('students/'),
            'companies': request.build_absolute_uri('companies/'),
            'supervisors': request.build_absolute_uri('supervisors/'),
            'practices': request.build_absolute_uri('practices/'),
            'documents': request.build_absolute_uri('documents/'),
            'notifications': request.build_absolute_uri('notifications/'),
            'schools': request.build_absolute_uri('schools/'),
            'branches': request.build_absolute_uri('branches/'),
            'evaluations': request.build_absolute_uri('evaluations/'),
            'practice_status_history': request.build_absolute_uri('practice-status-history/'),
            'dashboards': request.build_absolute_uri('dashboards/'),
            'reports': request.build_absolute_uri('reports/'),
            'cartas_presentacion': request.build_absolute_uri('cartas-presentacion/'),
        },
        'documentation': {
            'swagger': '/api/docs/',
            'redoc': '/api/redoc/',
            'schema': '/api/schema/',
            'postman': '/docs/Postman_Collection_DJGRedisPA.json'
        },
        'authentication': {
            'methods': ['JWT', 'Session'],
            'login': '/api/v1/auth/login/',
            'refresh': '/api/v1/auth/refresh/',
            'logout': '/api/v1/auth/logout/'
        },
        'graphql': {
            'endpoint': '/graphql/',
            'playground': '/graphql/' if hasattr(request, 'user') and not request.user.is_authenticated else None
        }
    })


# ============================================================================
# URL PATTERNS
# ============================================================================

urlpatterns = [
    # API Root
    path('', api_root, name='api-v2-root'),
    
    # Router URLs (incluye todos los ViewSets)
    path('', include(router.urls)),
]


# ============================================================================
# ENDPOINTS GENERADOS POR EL ROUTER
# ============================================================================

"""
El router genera automáticamente los siguientes endpoints:

USERS:
  GET    /api/v2/users/                    - Lista de usuarios (paginada)
  POST   /api/v2/users/                    - Crear usuario
  GET    /api/v2/users/{id}/               - Detalle de usuario
  PUT    /api/v2/users/{id}/               - Actualizar usuario (completo)
  PATCH  /api/v2/users/{id}/               - Actualizar usuario (parcial)
  DELETE /api/v2/users/{id}/               - Eliminar usuario
  GET    /api/v2/users/me/                 - Usuario actual
  POST   /api/v2/users/{id}/change_password/ - Cambiar contraseña
  POST   /api/v2/users/{id}/activate/      - Activar usuario
  POST   /api/v2/users/{id}/deactivate/    - Desactivar usuario
  GET    /api/v2/users/by_role/            - Usuarios por rol

STUDENTS:
  GET    /api/v2/students/                 - Lista de estudiantes
  POST   /api/v2/students/                 - Crear estudiante
  GET    /api/v2/students/{id}/            - Detalle de estudiante
  PUT    /api/v2/students/{id}/            - Actualizar estudiante
  PATCH  /api/v2/students/{id}/            - Actualizar estudiante (parcial)
  DELETE /api/v2/students/{id}/            - Eliminar estudiante
  GET    /api/v2/students/me/              - Perfil del estudiante actual
  GET    /api/v2/students/eligible/        - Estudiantes elegibles
  GET    /api/v2/students/without_practice/ - Sin práctica
  GET    /api/v2/students/by_semester/     - Por semestre
  GET    /api/v2/students/by_career/       - Por carrera
  GET    /api/v2/students/{id}/practices/  - Prácticas del estudiante

COMPANIES:
  GET    /api/v2/companies/                - Lista de empresas
  POST   /api/v2/companies/                - Crear empresa
  GET    /api/v2/companies/{id}/           - Detalle de empresa
  PUT    /api/v2/companies/{id}/           - Actualizar empresa
  PATCH  /api/v2/companies/{id}/           - Actualizar empresa (parcial)
  DELETE /api/v2/companies/{id}/           - Eliminar empresa
  POST   /api/v2/companies/{id}/validate/  - Validar empresa
  POST   /api/v2/companies/{id}/suspend/   - Suspender empresa
  POST   /api/v2/companies/{id}/blacklist/ - Poner en lista negra
  GET    /api/v2/companies/active/         - Empresas activas
  GET    /api/v2/companies/pending/        - Pendientes de validación
  GET    /api/v2/companies/by_sector/      - Por sector económico
  GET    /api/v2/companies/{id}/practices/ - Prácticas de la empresa
  GET    /api/v2/companies/{id}/supervisors/ - Supervisores de la empresa

SUPERVISORS:
  GET    /api/v2/supervisors/              - Lista de supervisores
  POST   /api/v2/supervisors/              - Crear supervisor
  GET    /api/v2/supervisors/{id}/         - Detalle de supervisor
  PUT    /api/v2/supervisors/{id}/         - Actualizar supervisor
  PATCH  /api/v2/supervisors/{id}/         - Actualizar supervisor (parcial)
  DELETE /api/v2/supervisors/{id}/         - Eliminar supervisor
  GET    /api/v2/supervisors/me/           - Perfil del supervisor actual
  GET    /api/v2/supervisors/by_company/   - Por empresa
  GET    /api/v2/supervisors/available/    - Supervisores disponibles
  GET    /api/v2/supervisors/{id}/practices/ - Prácticas supervisadas

PRACTICES:
  GET    /api/v2/practices/                - Lista de prácticas
  POST   /api/v2/practices/                - Crear práctica
  GET    /api/v2/practices/{id}/           - Detalle de práctica
  PUT    /api/v2/practices/{id}/           - Actualizar práctica
  PATCH  /api/v2/practices/{id}/           - Actualizar práctica (parcial)
  DELETE /api/v2/practices/{id}/           - Eliminar práctica
  GET    /api/v2/practices/my_practices/   - Mis prácticas
  POST   /api/v2/practices/{id}/submit/    - Enviar a revisión
  POST   /api/v2/practices/{id}/approve/   - Aprobar práctica
  POST   /api/v2/practices/{id}/reject/    - Rechazar práctica
  POST   /api/v2/practices/{id}/start/     - Iniciar práctica
  POST   /api/v2/practices/{id}/complete/  - Completar práctica
  POST   /api/v2/practices/{id}/cancel/    - Cancelar práctica
  GET    /api/v2/practices/by_status/      - Por estado
  GET    /api/v2/practices/pending_approval/ - Pendientes de aprobación
  GET    /api/v2/practices/active/         - Prácticas activas
  GET    /api/v2/practices/{id}/documents/ - Documentos de la práctica
  POST   /api/v2/practices/{id}/add_hours/ - Agregar horas
  GET    /api/v2/practices/{id}/progress/  - Progreso de la práctica

DOCUMENTS:
  GET    /api/v2/documents/                - Lista de documentos
  POST   /api/v2/documents/                - Subir documento
  GET    /api/v2/documents/{id}/           - Detalle de documento
  PUT    /api/v2/documents/{id}/           - Actualizar documento
  PATCH  /api/v2/documents/{id}/           - Actualizar documento (parcial)
  DELETE /api/v2/documents/{id}/           - Eliminar documento
  POST   /api/v2/documents/{id}/approve/   - Aprobar documento
  POST   /api/v2/documents/{id}/reject/    - Rechazar documento
  GET    /api/v2/documents/{id}/download/  - Descargar documento
  GET    /api/v2/documents/pending/        - Pendientes de aprobación
  GET    /api/v2/documents/by_practice/    - Por práctica
  GET    /api/v2/documents/by_type/        - Por tipo

NOTIFICATIONS:
  GET    /api/v2/notifications/            - Lista de notificaciones
  POST   /api/v2/notifications/            - Crear notificación (admin)
  GET    /api/v2/notifications/{id}/       - Detalle de notificación
  DELETE /api/v2/notifications/{id}/       - Eliminar notificación
  POST   /api/v2/notifications/{id}/mark_read/ - Marcar como leída
  POST   /api/v2/notifications/mark_all_read/ - Marcar todas como leídas
  GET    /api/v2/notifications/unread/     - No leídas
  GET    /api/v2/notifications/by_type/    - Por tipo
  DELETE /api/v2/notifications/clear_all/  - Limpiar todas

Total: 65+ endpoints REST
"""
