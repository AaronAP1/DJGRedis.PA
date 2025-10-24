"""
URLs para GraphQL API - Sistema de Gestión de Prácticas Profesionales.

Este módulo configura el endpoint GraphQL con soporte para:
- Mutations completas (Fase 4)
- Queries avanzadas (Fase 5)
- Autenticación JWT
- GraphiQL interface (desarrollo)
- CORS y seguridad
"""

from django.urls import path
from django.views.generic import TemplateView, RedirectView
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from graphene_django.views import GraphQLView
from graphql_jwt.decorators import jwt_cookie

# Importar schema completo (queries_complete + mutations_complete)
from .schema import schema


# ============================================================================
# CUSTOM GRAPHQL VIEW
# ============================================================================

class CustomGraphQLView(GraphQLView):
    """
    Vista personalizada de GraphQL con:
    - Soporte JWT con cookies HttpOnly
    - Manejo de errores mejorado
    - Logging de queries
    - CORS headers
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Procesa la petición con soporte para JWT y cookies."""
        response = super().dispatch(request, *args, **kwargs)
        
        # Configurar CORS headers si es necesario
        if settings.DEBUG:
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        # Gestión de cookies JWT
        try:
            import json
            
            jwt_settings = getattr(settings, 'GRAPHQL_JWT', {})
            cookie_name = jwt_settings.get('JWT_COOKIE_NAME', 'JWT')
            refresh_cookie_name = jwt_settings.get('JWT_REFRESH_TOKEN_COOKIE_NAME', 'JWT_REFRESH_TOKEN')
            secure = jwt_settings.get('JWT_COOKIE_SECURE', not settings.DEBUG)
            samesite = jwt_settings.get('JWT_COOKIE_SAMESITE', 'Lax')
            path = '/'
            
            def _set_cookie(name, value, max_age=None):
                """Helper para establecer cookies HttpOnly."""
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
            
            # TTLs de cookies
            access_ttl = 60 * 15  # 15 minutos
            refresh_ttl = 60 * 60 * 24 * 7  # 7 días
            
            # 1) Tokens desde request._jwt_tokens (establecidos por mutations)
            req_tokens = getattr(request, '_jwt_tokens', None)
            if isinstance(req_tokens, dict):
                _set_cookie(cookie_name, req_tokens.get('access'), max_age=access_ttl)
                _set_cookie(refresh_cookie_name, req_tokens.get('refresh'), max_age=refresh_ttl)
            
            # 2) Parsear respuesta para TokenAuth/RefreshToken
            if request.method == 'POST' and hasattr(response, 'content'):
                try:
                    body = json.loads(request.body.decode('utf-8'))
                    query = (body.get('query') or '').replace('\n', ' ')
                    op_name = body.get('operationName') or ''
                    
                    content = response.content.decode('utf-8')
                    data = json.loads(content)
                    payload = (data or {}).get('data') or {}
                    
                    # TokenAuth mutation
                    if 'tokenAuth' in query.lower() or op_name == 'TokenAuth':
                        token_data = payload.get('tokenAuth') or {}
                        access = token_data.get('token')
                        refresh = token_data.get('refreshToken')
                        _set_cookie(cookie_name, access, max_age=access_ttl)
                        _set_cookie(refresh_cookie_name, refresh, max_age=refresh_ttl)
                    
                    # RefreshToken mutation
                    if 'refreshtoken' in query.lower() or op_name == 'RefreshToken':
                        token_data = payload.get('refreshToken') or {}
                        access = token_data.get('token')
                        refresh = token_data.get('refreshToken')
                        _set_cookie(cookie_name, access, max_age=access_ttl)
                        if refresh:
                            _set_cookie(refresh_cookie_name, refresh, max_age=refresh_ttl)
                    
                    # Logout mutation - limpiar cookies
                    if 'logout' in query.lower() or op_name == 'Logout':
                        response.delete_cookie(cookie_name, path=path, samesite=samesite)
                        response.delete_cookie(refresh_cookie_name, path=path, samesite=samesite)
                
                except Exception:
                    pass
        
        except Exception:
            # No bloquear la respuesta si falla gestión de cookies
            pass
        
        return response


# ============================================================================
# URL PATTERNS
# ============================================================================

app_name = 'graphql_api'

urlpatterns = [
    # ========================================================================
    # ENDPOINT PRINCIPAL GRAPHQL
    # ========================================================================
    path(
        '',
        csrf_exempt(
            jwt_cookie(
                CustomGraphQLView.as_view(
                    schema=schema,
                    graphiql=settings.DEBUG  # GraphiQL solo en desarrollo
                )
            )
        ),
        name='graphql'
    ),
    
    # ========================================================================
    # ENDPOINT DE PRODUCCIÓN (sin GraphiQL)
    # ========================================================================
    path(
        'api/',
        csrf_exempt(
            jwt_cookie(
                CustomGraphQLView.as_view(
                    schema=schema,
                    graphiql=False
                )
            )
        ),
        name='graphql_api_only'
    ),
    
    # ========================================================================
    # DOCUMENTACIÓN Y PLAYGROUND
    # ========================================================================
    
    # Quickstart - Guía rápida con ejemplos
    path(
        'quickstart/',
        TemplateView.as_view(template_name='graphql/quickstart.html'),
        name='quickstart'
    ),
    
    # Workbench - Entorno de pruebas avanzado
    path(
        'workbench/',
        TemplateView.as_view(template_name='graphql/workbench.html'),
        name='workbench'
    ),
    
    # Redirect de raíz a GraphQL
    path(
        'playground/',
        RedirectView.as_view(url='/graphql/', permanent=False),
        name='playground'
    ),
]


# ============================================================================
# ENDPOINTS DISPONIBLES
# ============================================================================

"""
GRAPHQL ENDPOINTS:

Principal:
  POST   /graphql/                     - Endpoint GraphQL principal
  GET    /graphql/                     - GraphiQL interface (desarrollo)

Producción:
  POST   /graphql/api/                 - Solo API (sin interfaz)

Documentación:
  GET    /graphql/quickstart/          - Guía de inicio rápido
  GET    /graphql/workbench/           - Entorno de pruebas
  GET    /graphql/playground/          - Redirect a GraphiQL

---

QUERIES DISPONIBLES (50+):
  
  Users:
    - me, user, users, usersByRole, searchUsers
  
  Students:
    - student, myStudentProfile, students, eligibleStudents
    - studentsWithoutPractice, searchStudents
  
  Companies:
    - company, companies, activeCompanies, pendingValidationCompanies
    - companiesBySector, searchCompanies
  
  Supervisors:
    - supervisor, mySupervisorProfile, supervisors, companySupervisors
    - availableSupervisors
  
  Practices:
    - practice, practices, myPractices, practicesByStatus
    - studentPractices, companyPractices, supervisorPractices
    - activePractices, pendingApprovalPractices, completedPractices
  
  Documents:
    - document, documents, practiceDocuments, pendingApprovalDocuments
    - myDocuments
  
  Notifications:
    - myNotifications, unreadNotifications, unreadCount
  
  Statistics:
    - dashboardStatistics, practiceStatistics, studentStatistics
    - companyStatistics

---

MUTATIONS DISPONIBLES (30+):
  
  Users:
    - createUser, updateUser, deleteUser, changePassword
  
  Students:
    - createStudent, updateStudent, deleteStudent
  
  Companies:
    - createCompany, updateCompany, validateCompany, deleteCompany
  
  Supervisors:
    - createSupervisor, updateSupervisor, deleteSupervisor
  
  Practices:
    - createPractice, updatePractice, submitPractice, approvePractice
    - rejectPractice, startPractice, completePractice, deletePractice
  
  Documents:
    - createDocument, approveDocument, rejectDocument, deleteDocument
  
  Notifications:
    - markNotificationRead, markAllNotificationsRead
    - deleteNotification, createNotification

---

AUTENTICACIÓN:

Headers requeridos:
  Authorization: JWT <your-token>

O usar cookies HttpOnly (automático):
  JWT=<access-token>
  JWT_REFRESH_TOKEN=<refresh-token>

Obtener token:
  mutation {
    tokenAuth(email: "user@upeu.edu.pe", password: "password") {
      token
      refreshToken
      user { fullName role }
    }
  }

Refrescar token:
  mutation {
    refreshToken(refreshToken: "your-refresh-token") {
      token
      refreshToken
    }
  }

---

EJEMPLO DE USO:

1. Login:
   mutation {
     tokenAuth(email: "admin@upeu.edu.pe", password: "admin123") {
       token
       refreshToken
     }
   }

2. Query con autenticación:
   query {
     me {
       fullName
       role
     }
     myPractices {
       id
       titulo
       status
     }
   }

3. Mutation:
   mutation {
     createStudent(
       email: "2024012345@upeu.edu.pe"
       firstName: "Juan"
       lastName: "Pérez"
       password: "Student123!"
       codigo: "2024012345"
       semestre: 6
       escuelaProfesional: "Ingeniería de Sistemas"
       promedio: 15.5
     ) {
       success
       message
       student {
         id
         codigo
       }
     }
   }

---

DOCUMENTACIÓN COMPLETA:
  - Queries: /src/adapters/primary/graphql_api/README_QUERIES.md
  - Mutations: /src/adapters/primary/graphql_api/README_MUTATIONS.md
  - Types: /src/adapters/primary/graphql_api/types.py
  - Schema: /src/adapters/primary/graphql_api/schema.py
"""
