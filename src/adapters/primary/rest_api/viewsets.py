"""
ViewSets REST completos para todas las entidades del sistema.

Este módulo implementa ViewSets con:
- CRUD completo (list, retrieve, create, update, partial_update, destroy)
- Custom actions (@action) para operaciones especiales
- Permisos basados en roles
- Filtros y búsquedas
- Paginación
- Manejo de errores

ViewSets incluidos:
- UserViewSet: Gestión de usuarios
- StudentViewSet: Gestión de estudiantes
- CompanyViewSet: Gestión de empresas
- SupervisorViewSet: Gestión de supervisores
- PracticeViewSet: Gestión de prácticas
- DocumentViewSet: Gestión de documentos
- NotificationViewSet: Gestión de notificaciones
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import datetime

from src.adapters.secondary.database.models import (
    Student, Company, Supervisor, Practice, Document, Notification, Avatar
)
from .serializers import (
    # Avatar serializers
    AvatarSerializer,
    # User serializers
    UserListSerializer, UserDetailSerializer, UserCreateSerializer,
    UserUpdateSerializer, ChangePasswordSerializer,
    # Student serializers
    StudentListSerializer, StudentDetailSerializer, StudentCreateSerializer,
    StudentUpdateSerializer, StudentSearchSerializer,
    # Company serializers
    CompanyListSerializer, CompanyDetailSerializer, CompanyCreateSerializer,
    CompanyUpdateSerializer, CompanyValidateSerializer, CompanySearchSerializer,
    # Supervisor serializers
    SupervisorListSerializer, SupervisorDetailSerializer, SupervisorCreateSerializer,
    SupervisorUpdateSerializer,
    # Practice serializers
    PracticeListSerializer, PracticeDetailSerializer, PracticeCreateSerializer,
    PracticeUpdateSerializer, PracticeStatusSerializer, PracticeSearchSerializer,
    # Document serializers
    DocumentListSerializer, DocumentDetailSerializer, DocumentCreateSerializer,
    DocumentUpdateSerializer, DocumentApproveSerializer,
    # Notification serializers
    NotificationListSerializer, NotificationDetailSerializer, NotificationCreateSerializer,
    NotificationMarkAsReadSerializer,
    # Stats serializers
    DashboardStatsSerializer,
)
from src.infrastructure.security.permissions import (
    # User permissions
    IsAdministrador, IsStaffMember, IsPracticante, IsSupervisor, IsCoordinador, IsSecretaria,
    # Company permissions
    CanManageCompanies, CanValidateCompany, CanViewCompany,
    # Student permissions
    CanManageStudents, CanViewStudent,
    # Practice permissions
    CanCreatePractice, CanUpdatePractice, CanViewPractice, CanApprovePractice,
    # Document permissions
    CanUploadDocument, CanApproveDocument, CanViewDocument,
    # Notification permissions
    CanViewNotification,
)

User = get_user_model()


# ============================================================================
# USER VIEWSET
# ============================================================================

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios.
    
    Endpoints:
    - GET /api/users/ - Listar usuarios
    - GET /api/users/{id}/ - Ver usuario
    - POST /api/users/ - Crear usuario (Admin/Secretaria)
    - PUT/PATCH /api/users/{id}/ - Actualizar usuario
    - DELETE /api/users/{id}/ - Eliminar usuario (Admin)
    - POST /api/users/{id}/change_password/ - Cambiar contraseña
    - GET /api/users/me/ - Perfil del usuario actual
    """
    
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['email', 'username', 'first_name', 'last_name']
    filterset_fields = ['role', 'is_active']
    ordering_fields = ['date_joined', 'last_login', 'email']
    ordering = ['-date_joined']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'retrieve' or self.action == 'me':
            return UserDetailSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        return UserDetailSerializer
    
    def get_permissions(self):
        """Permisos según la acción."""
        if self.action == 'create':
            # Solo Admin y Secretaria pueden crear usuarios directamente
            permission_classes = [IsAuthenticated, IsStaffMember]
        elif self.action == 'destroy':
            # Solo Admin puede eliminar
            permission_classes = [IsAuthenticated, IsAdministrador]
        elif self.action in ['update', 'partial_update']:
            # Usuario puede editar su propio perfil, Admin y Secretaria pueden editar cualquiera
            permission_classes = [IsAuthenticated]
        elif self.action == 'me':
            permission_classes = [IsAuthenticated]
        else:
            # Listar y ver requieren autenticación
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar usuarios según el rol del solicitante."""
        user = self.request.user
        queryset = User.objects.all()
        
        # Administradores y Secretarias ven todos
        if user.is_administrador or user.is_secretaria:
            return queryset
        
        # Coordinadores ven practicantes, supervisores y coordinadores
        if user.is_coordinador:
            return queryset.filter(
                role__in=['PRACTICANTE', 'SUPERVISOR', 'COORDINADOR']
            )
        
        # Otros solo ven su propio perfil
        return queryset.filter(id=user.id)
    
    def perform_update(self, serializer):
        """Validar que usuario solo pueda editar su propio perfil (excepto staff)."""
        user = self.request.user
        instance = self.get_object()
        
        # Admin y Secretaria pueden editar cualquiera
        if user.is_administrador or user.is_secretaria:
            serializer.save()
        # Usuario puede editar solo su perfil
        elif instance.id == user.id:
            serializer.save()
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('No tienes permiso para editar este usuario')
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        GET /api/users/me/
        Retorna el perfil del usuario actual.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request, pk=None):
        """
        POST /api/users/{id}/change_password/
        Cambiar contraseña del usuario.
        
        Body:
        {
            "old_password": "string",
            "new_password": "string",
            "new_password_confirm": "string"
        }
        """
        user = self.get_object()
        
        # Validar que sea el mismo usuario o Admin
        if request.user.id != user.id and not request.user.is_administrador:
            return Response(
                {'error': 'No tienes permiso para cambiar esta contraseña'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validar contraseña actual (no requerido para Admin)
        if request.user.id == user.id:
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Contraseña actual incorrecta'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Cambiar contraseña
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response(
            {'message': 'Contraseña actualizada exitosamente'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_permissions(self, request):
        """
        GET /api/users/my-permissions/
        Retorna los permisos efectivos del usuario actual.
        
        Combina:
        - Permisos del rol del usuario
        - Permisos específicos otorgados (GRANT)
        - Permisos revocados (REVOKE)
        
        Returns:
            Response con lista de permisos y su origen.
        """
        user = request.user
        permissions_data = []
        
        # Permisos del rol (si tiene role_obj)
        if hasattr(user, 'role_obj') and user.role_obj:
            role_permissions = user.role_obj.permissions.filter(is_active=True)
            for perm in role_permissions:
                permissions_data.append({
                    'code': perm.code,
                    'name': perm.name,
                    'description': perm.description,
                    'module': perm.module,
                    'source': 'role',
                    'role': user.role_obj.name
                })
        
        # Permisos específicos del usuario (overrides)
        from src.adapters.secondary.database.models import UserPermission
        from django.utils import timezone
        
        user_permissions = UserPermission.objects.filter(
            user=user,
            permission__is_active=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).select_related('permission')
        
        for user_perm in user_permissions:
            permissions_data.append({
                'code': user_perm.permission.code,
                'name': user_perm.permission.name,
                'description': user_perm.permission.description,
                'module': user_perm.permission.module,
                'source': 'user_override',
                'type': user_perm.permission_type,
                'granted_at': user_perm.granted_at,
                'expires_at': user_perm.expires_at,
                'reason': user_perm.reason
            })
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name(),
                'role': user.role
            },
            'permissions_count': len(permissions_data),
            'permissions': permissions_data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def available_avatars(self, request):
        """
        GET /api/users/available-avatars/
        Retorna los avatares disponibles para el rol del usuario actual.
        
        Returns:
            Response con lista de avatares del rol del usuario.
        """
        user_role = request.user.role
        
        avatars = Avatar.objects.filter(
            role=user_role,
            is_active=True
        ).order_by('-created_at')
        
        serializer = AvatarSerializer(avatars, many=True)
        
        return Response({
            'user_role': user_role,
            'avatars_count': avatars.count(),
            'avatars': serializer.data
        })
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def effective_permissions(self, request, pk=None):
        """
        GET /api/v2/users/{id}/effective-permissions/
        Retorna los permisos efectivos de un usuario específico (admin only).
        
        Combina:
        - Permisos del rol del usuario
        - Permisos específicos otorgados (GRANT)
        - Permisos revocados (REVOKE)
        
        Returns:
            Response con lista de permisos efectivos y su origen.
        """
        user = self.get_object()
        permissions_data = []
        permissions_codes = set()
        
        # Permisos del rol (si tiene role_obj)
        if hasattr(user, 'role_obj') and user.role_obj:
            role_permissions = user.role_obj.permissions.filter(is_active=True)
            for perm in role_permissions:
                permissions_codes.add(perm.code)
                permissions_data.append({
                    'code': perm.code,
                    'name': perm.name,
                    'description': perm.description,
                    'module': perm.module,
                    'source': 'role',
                    'role': user.role_obj.name,
                    'status': 'active'
                })
        
        # Permisos específicos del usuario (overrides)
        from src.adapters.secondary.database.models import UserPermission
        from django.utils import timezone
        
        user_permissions = UserPermission.objects.filter(
            user=user,
            permission__is_active=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).select_related('permission')
        
        for user_perm in user_permissions:
            perm_code = user_perm.permission.code
            
            if user_perm.permission_type == 'GRANT':
                # Agregar permiso adicional
                if perm_code not in permissions_codes:
                    permissions_codes.add(perm_code)
                    permissions_data.append({
                        'code': perm_code,
                        'name': user_perm.permission.name,
                        'description': user_perm.permission.description,
                        'module': user_perm.permission.module,
                        'source': 'user_grant',
                        'granted_at': user_perm.granted_at,
                        'expires_at': user_perm.expires_at,
                        'reason': user_perm.reason,
                        'status': 'granted'
                    })
            
            elif user_perm.permission_type == 'REVOKE':
                # Marcar como revocado
                permissions_codes.discard(perm_code)
                # Buscar y marcar en permissions_data
                for perm in permissions_data:
                    if perm['code'] == perm_code:
                        perm['status'] = 'revoked'
                        perm['revoked_reason'] = user_perm.reason
                        break
        
        # Filtrar los revocados de la lista final
        effective_permissions = [p for p in permissions_data if p.get('status') != 'revoked']
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name(),
                'role': user.role
            },
            'effective_permissions_count': len(effective_permissions),
            'permissions': effective_permissions,
            'revoked_permissions': [p for p in permissions_data if p.get('status') == 'revoked']
        })



# ============================================================================
# STUDENT VIEWSET
# ============================================================================

class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de estudiantes.
    
    Endpoints:
    - GET /api/students/ - Listar estudiantes
    - GET /api/students/{id}/ - Ver estudiante
    - POST /api/students/ - Crear estudiante
    - PUT/PATCH /api/students/{id}/ - Actualizar estudiante
    - DELETE /api/students/{id}/ - Eliminar estudiante
    - GET /api/students/search/ - Búsqueda avanzada
    - GET /api/students/{id}/practices/ - Prácticas del estudiante
    """
    
    queryset = Student.objects.select_related('user').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['codigo_estudiante', 'carrera', 'user__email', 'user__first_name', 'user__last_name']
    filterset_fields = ['carrera', 'semestre_actual']
    ordering_fields = ['created_at', 'promedio_ponderado', 'semestre_actual']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'list':
            return StudentListSerializer
        elif self.action == 'retrieve':
            return StudentDetailSerializer
        elif self.action == 'create':
            return StudentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StudentUpdateSerializer
        elif self.action == 'search':
            return StudentSearchSerializer
        return StudentDetailSerializer
    
    def get_permissions(self):
        """Permisos según la acción."""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, CanManageStudents]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, CanManageStudents]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsAdministrador]
        else:
            permission_classes = [IsAuthenticated, CanViewStudent]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar estudiantes según el rol."""
        user = self.request.user
        queryset = Student.objects.select_related('user').all()
        
        # Practicante solo ve su propio perfil
        if user.is_practicante:
            return queryset.filter(user=user)
        
        # Supervisores ven estudiantes de sus prácticas
        if user.is_supervisor:
            try:
                supervisor = Supervisor.objects.get(user=user)
                practice_student_ids = Practice.objects.filter(
                    supervisor=supervisor
                ).values_list('student_id', flat=True)
                return queryset.filter(id__in=practice_student_ids)
            except Supervisor.DoesNotExist:
                return queryset.none()
        
        # Staff ve todos
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search(self, request):
        """
        GET /api/students/search/
        Búsqueda avanzada de estudiantes.
        
        Query params:
        - codigo: Código del estudiante
        - escuela: Escuela profesional
        - semestre_min: Semestre mínimo
        - promedio_min: Promedio mínimo
        - puede_realizar_practica: Boolean
        """
        serializer = StudentSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset()
        
        # Aplicar filtros
        filters = serializer.validated_data
        
        if filters.get('codigo'):
            queryset = queryset.filter(codigo_estudiante__icontains=filters['codigo'])
        
        if filters.get('escuela'):
            queryset = queryset.filter(escuela__icontains=filters['escuela'])
        
        if filters.get('semestre_min'):
            queryset = queryset.filter(semestre_actual__gte=filters['semestre_min'])
        
        if filters.get('promedio_min'):
            queryset = queryset.filter(promedio_ponderado__gte=filters['promedio_min'])
        
        if filters.get('puede_realizar_practica') is not None:
            if filters['puede_realizar_practica']:
                queryset = queryset.filter(
                    semestre_actual__gte=6,
                    promedio_ponderado__gte=12.0
                )
            else:
                queryset = queryset.exclude(
                    semestre_actual__gte=6,
                    promedio_ponderado__gte=12.0
                )
        
        # Paginar
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = StudentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = StudentListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def practices(self, request, pk=None):
        """
        GET /api/students/{id}/practices/
        Retorna las prácticas del estudiante.
        """
        student = self.get_object()
        practices = Practice.objects.filter(student=student).select_related(
            'company', 'supervisor', 'supervisor__user'
        )
        
        # Aplicar filtros opcionales
        status_filter = request.query_params.get('status')
        if status_filter:
            practices = practices.filter(status=status_filter)
        
        serializer = PracticeListSerializer(practices, many=True)
        return Response(serializer.data)


# ============================================================================
# COMPANY VIEWSET
# ============================================================================

class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de empresas.
    
    Endpoints:
    - GET /api/companies/ - Listar empresas
    - GET /api/companies/{id}/ - Ver empresa
    - POST /api/companies/ - Crear empresa
    - PUT/PATCH /api/companies/{id}/ - Actualizar empresa
    - DELETE /api/companies/{id}/ - Eliminar empresa
    - POST /api/companies/{id}/validate/ - Validar empresa (Coordinador)
    - POST /api/companies/{id}/suspend/ - Suspender empresa (Coordinador)
    - GET /api/companies/search/ - Búsqueda avanzada
    - GET /api/companies/{id}/practices/ - Prácticas de la empresa
    - GET /api/companies/{id}/supervisors/ - Supervisores de la empresa
    """
    
    queryset = Company.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['ruc', 'razon_social', 'nombre_comercial', 'sector_economico']
    filterset_fields = ['status', 'sector_economico', 'tamaño_empresa']
    ordering_fields = ['created_at', 'razon_social']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'list':
            return CompanyListSerializer
        elif self.action == 'retrieve':
            return CompanyDetailSerializer
        elif self.action == 'create':
            return CompanyCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CompanyUpdateSerializer
        elif self.action in ['validate', 'suspend']:
            return CompanyValidateSerializer
        elif self.action == 'search':
            return CompanySearchSerializer
        return CompanyDetailSerializer
    
    def get_permissions(self):
        """Permisos según la acción."""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, CanManageCompanies]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, CanManageCompanies]
        elif self.action in ['validate', 'suspend']:
            permission_classes = [IsAuthenticated, CanValidateCompany]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsAdministrador]
        else:
            permission_classes = [IsAuthenticated, CanViewCompany]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar empresas según el rol."""
        user = self.request.user
        queryset = Company.objects.all()
        
        # Supervisores solo ven su empresa
        if user.is_supervisor:
            try:
                supervisor = Supervisor.objects.get(user=user)
                return queryset.filter(id=supervisor.company_id)
            except Supervisor.DoesNotExist:
                return queryset.none()
        
        # Practicantes ven empresas activas
        if user.is_practicante:
            return queryset.filter(status='ACTIVE')
        
        # Staff ve todas
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanValidateCompany])
    def validate(self, request, pk=None):
        """
        POST /api/companies/{id}/validate/
        Validar o rechazar una empresa (solo Coordinador).
        
        Body:
        {
            "status": "ACTIVE|SUSPENDED|BLACKLISTED",
            "observaciones": "string"
        }
        """
        company = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Actualizar estado
        company.status = serializer.validated_data['status']
        if serializer.validated_data.get('observaciones'):
            # Puedes guardar observaciones en un campo de la empresa si existe
            pass
        company.save()
        
        # Crear notificación (si la empresa tiene contacto)
        # TODO: Implementar notificación a contacto de empresa
        
        return Response(
            {
                'message': f'Empresa {company.razon_social} validada como {company.status}',
                'company': CompanyDetailSerializer(company).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanValidateCompany])
    def suspend(self, request, pk=None):
        """
        POST /api/companies/{id}/suspend/
        Suspender una empresa (solo Coordinador).
        """
        company = self.get_object()
        company.status = 'SUSPENDED'
        company.save()
        
        return Response(
            {'message': f'Empresa {company.razon_social} suspendida'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search(self, request):
        """
        GET /api/companies/search/
        Búsqueda avanzada de empresas.
        
        Query params:
        - ruc: RUC de la empresa
        - sector: Sector económico
        - status: Estado
        - puede_recibir_practicantes: Boolean
        """
        serializer = CompanySearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset()
        filters = serializer.validated_data
        
        if filters.get('ruc'):
            queryset = queryset.filter(ruc__icontains=filters['ruc'])
        
        if filters.get('sector'):
            queryset = queryset.filter(sector_economico__icontains=filters['sector'])
        
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        if filters.get('puede_recibir_practicantes') is not None:
            if filters['puede_recibir_practicantes']:
                queryset = queryset.filter(status='ACTIVE')
            else:
                queryset = queryset.exclude(status='ACTIVE')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CompanyListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CompanyListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def practices(self, request, pk=None):
        """
        GET /api/companies/{id}/practices/
        Retorna las prácticas de la empresa.
        """
        company = self.get_object()
        practices = Practice.objects.filter(company=company).select_related(
            'student', 'student__user', 'supervisor'
        )
        
        status_filter = request.query_params.get('status')
        if status_filter:
            practices = practices.filter(status=status_filter)
        
        serializer = PracticeListSerializer(practices, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def supervisors(self, request, pk=None):
        """
        GET /api/companies/{id}/supervisors/
        Retorna los supervisores de la empresa.
        """
        company = self.get_object()
        supervisors = Supervisor.objects.filter(company=company).select_related('user')
        
        serializer = SupervisorListSerializer(supervisors, many=True)
        return Response(serializer.data)


# ============================================================================
# SUPERVISOR VIEWSET
# ============================================================================

class SupervisorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de supervisores.
    
    Endpoints:
    - GET /api/supervisors/ - Listar supervisores
    - GET /api/supervisors/{id}/ - Ver supervisor
    - POST /api/supervisors/ - Crear supervisor
    - PUT/PATCH /api/supervisors/{id}/ - Actualizar supervisor
    - DELETE /api/supervisors/{id}/ - Eliminar supervisor
    - GET /api/supervisors/{id}/practices/ - Prácticas supervisadas
    """
    
    queryset = Supervisor.objects.select_related('user', 'company').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'cargo', 'documento_numero']
    filterset_fields = ['company', 'documento_tipo']
    ordering_fields = ['created_at', 'años_experiencia']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'list':
            return SupervisorListSerializer
        elif self.action == 'retrieve':
            return SupervisorDetailSerializer
        elif self.action == 'create':
            return SupervisorCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SupervisorUpdateSerializer
        return SupervisorDetailSerializer
    
    def get_permissions(self):
        """Permisos según la acción."""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, CanManageCompanies]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, CanManageCompanies]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsAdministrador]
        else:
            permission_classes = [IsAuthenticated, CanViewCompany]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar supervisores según el rol."""
        user = self.request.user
        queryset = Supervisor.objects.select_related('user', 'company').all()
        
        # Supervisor solo ve su propio perfil
        if user.is_supervisor:
            return queryset.filter(user=user)
        
        # Practicantes ven supervisores de sus prácticas
        if user.is_practicante:
            try:
                student = Student.objects.get(user=user)
                supervisor_ids = Practice.objects.filter(
                    student=student
                ).values_list('supervisor_id', flat=True)
                return queryset.filter(id__in=supervisor_ids)
            except Student.DoesNotExist:
                return queryset.none()
        
        # Staff ve todos
        return queryset
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def practices(self, request, pk=None):
        """
        GET /api/supervisors/{id}/practices/
        Retorna las prácticas supervisadas.
        """
        supervisor = self.get_object()
        practices = Practice.objects.filter(supervisor=supervisor).select_related(
            'student', 'student__user', 'company'
        )
        
        status_filter = request.query_params.get('status')
        if status_filter:
            practices = practices.filter(status=status_filter)
        
        serializer = PracticeListSerializer(practices, many=True)
        return Response(serializer.data)


# ============================================================================
# PRACTICE VIEWSET
# ============================================================================

class PracticeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de prácticas profesionales.
    
    Endpoints:
    - GET /api/practices/ - Listar prácticas
    - GET /api/practices/{id}/ - Ver práctica
    - POST /api/practices/ - Crear práctica
    - PUT/PATCH /api/practices/{id}/ - Actualizar práctica
    - DELETE /api/practices/{id}/ - Eliminar práctica
    - POST /api/practices/{id}/change_status/ - Cambiar estado
    - POST /api/practices/{id}/submit/ - Enviar a aprobación
    - POST /api/practices/{id}/approve/ - Aprobar (Coordinador)
    - POST /api/practices/{id}/reject/ - Rechazar (Coordinador)
    - POST /api/practices/{id}/start/ - Iniciar práctica
    - POST /api/practices/{id}/complete/ - Completar práctica
    - GET /api/practices/search/ - Búsqueda avanzada
    - GET /api/practices/my_practices/ - Mis prácticas (según rol)
    """
    
    queryset = Practice.objects.select_related(
        'student', 'student__user', 'company', 'supervisor', 'supervisor__user'
    ).all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = [
        'titulo', 'area_practica', 'student__codigo_estudiante',
        'company__razon_social', 'company__ruc'
    ]
    filterset_fields = ['status', 'modalidad', 'company', 'student']
    ordering_fields = ['created_at', 'fecha_inicio', 'fecha_fin']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'list' or self.action == 'my_practices':
            return PracticeListSerializer
        elif self.action == 'retrieve':
            return PracticeDetailSerializer
        elif self.action == 'create':
            return PracticeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PracticeUpdateSerializer
        elif self.action in ['change_status', 'submit', 'approve', 'reject', 'start', 'complete']:
            return PracticeStatusSerializer
        elif self.action == 'search':
            return PracticeSearchSerializer
        return PracticeDetailSerializer
    
    def get_permissions(self):
        """Permisos según la acción."""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, CanCreatePractice]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, CanUpdatePractice]
        elif self.action in ['approve', 'reject']:
            permission_classes = [IsAuthenticated, CanApprovePractice]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsAdministrador]
        else:
            permission_classes = [IsAuthenticated, CanViewPractice]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar prácticas según el rol."""
        user = self.request.user
        queryset = Practice.objects.select_related(
            'student', 'student__user', 'company', 'supervisor', 'supervisor__user'
        ).all()
        
        # Practicante solo ve sus prácticas
        if user.is_practicante:
            try:
                student = Student.objects.get(user=user)
                return queryset.filter(student=student)
            except Student.DoesNotExist:
                return queryset.none()
        
        # Supervisor ve las prácticas que supervisa
        if user.is_supervisor:
            try:
                supervisor = Supervisor.objects.get(user=user)
                return queryset.filter(supervisor=supervisor)
            except Supervisor.DoesNotExist:
                return queryset.none()
        
        # Staff ve todas
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanUpdatePractice])
    def change_status(self, request, pk=None):
        """
        POST /api/practices/{id}/change_status/
        Cambiar el estado de una práctica.
        
        Body:
        {
            "status": "DRAFT|PENDING|APPROVED|IN_PROGRESS|COMPLETED|CANCELLED|SUSPENDED",
            "observaciones": "string",
            "calificacion_final": "decimal"  // solo si status=COMPLETED
        }
        """
        practice = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            context={'practice': practice, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Actualizar estado
        nuevo_estado = serializer.validated_data['status']
        observaciones = serializer.validated_data.get('observaciones', '')
        calificacion = serializer.validated_data.get('calificacion_final')
        
        practice.status = nuevo_estado
        if observaciones:
            practice.observaciones = observaciones
        if calificacion is not None:
            practice.calificacion_final = calificacion
        practice.save()
        
        # Crear notificación al estudiante
        Notification.objects.create(
            user=practice.student.user,
            tipo='INFO',
            titulo=f'Estado de práctica actualizado',
            mensaje=f'Tu práctica "{practice.titulo}" cambió a estado {nuevo_estado}',
            related_practice=practice
        )
        
        return Response(
            {
                'message': f'Práctica actualizada a estado {nuevo_estado}',
                'practice': PracticeDetailSerializer(practice).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        """
        POST /api/practices/{id}/submit/
        Enviar práctica a aprobación (DRAFT → PENDING).
        """
        practice = self.get_object()
        
        # Validar que sea el estudiante dueño
        if not hasattr(request.user, 'student_profile') or practice.student != request.user.student_profile:
            return Response(
                {'error': 'Solo el estudiante puede enviar su práctica'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if practice.status != 'DRAFT':
            return Response(
                {'error': f'Solo se pueden enviar prácticas en estado DRAFT. Estado actual: {practice.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        practice.status = 'PENDING'
        practice.save()
        
        # Notificar a coordinadores
        coordinadores = User.objects.filter(role='COORDINADOR', is_active=True)
        for coord in coordinadores:
            Notification.objects.create(
                user=coord,
                tipo='INFO',
                titulo='Nueva práctica pendiente de aprobación',
                mensaje=f'El estudiante {practice.student.user.get_full_name()} envió una práctica para aprobación',
                related_practice=practice
            )
        
        return Response(
            {'message': 'Práctica enviada a aprobación', 'practice': PracticeDetailSerializer(practice).data},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanApprovePractice])
    def approve(self, request, pk=None):
        """
        POST /api/practices/{id}/approve/
        Aprobar una práctica (PENDING → APPROVED) - Solo Coordinador.
        """
        practice = self.get_object()
        
        if practice.status != 'PENDING':
            return Response(
                {'error': f'Solo se pueden aprobar prácticas en estado PENDING. Estado actual: {practice.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        practice.status = 'APPROVED'
        practice.save()
        
        # Notificar al estudiante
        Notification.objects.create(
            user=practice.student.user,
            tipo='SUCCESS',
            titulo='Práctica aprobada',
            mensaje=f'Tu práctica "{practice.titulo}" ha sido aprobada. Puedes iniciarla cuando estés listo.',
            related_practice=practice
        )
        
        return Response(
            {'message': 'Práctica aprobada', 'practice': PracticeDetailSerializer(practice).data},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanApprovePractice])
    def reject(self, request, pk=None):
        """
        POST /api/practices/{id}/reject/
        Rechazar una práctica (PENDING → CANCELLED) - Solo Coordinador.
        
        Body:
        {
            "observaciones": "Motivo del rechazo"
        }
        """
        practice = self.get_object()
        
        observaciones = request.data.get('observaciones', '')
        if not observaciones:
            return Response(
                {'error': 'Debe proporcionar observaciones para el rechazo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if practice.status != 'PENDING':
            return Response(
                {'error': f'Solo se pueden rechazar prácticas en estado PENDING. Estado actual: {practice.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        practice.status = 'CANCELLED'
        practice.observaciones = observaciones
        practice.save()
        
        # Notificar al estudiante
        Notification.objects.create(
            user=practice.student.user,
            tipo='WARNING',
            titulo='Práctica rechazada',
            mensaje=f'Tu práctica "{practice.titulo}" fue rechazada. Motivo: {observaciones}',
            related_practice=practice
        )
        
        return Response(
            {'message': 'Práctica rechazada', 'practice': PracticeDetailSerializer(practice).data},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def start(self, request, pk=None):
        """
        POST /api/practices/{id}/start/
        Iniciar práctica (APPROVED → IN_PROGRESS).
        """
        practice = self.get_object()
        
        # Validar que sea el estudiante
        if not hasattr(request.user, 'student_profile') or practice.student != request.user.student_profile:
            return Response(
                {'error': 'Solo el estudiante puede iniciar su práctica'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if practice.status != 'APPROVED':
            return Response(
                {'error': f'Solo se pueden iniciar prácticas APPROVED. Estado actual: {practice.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        practice.status = 'IN_PROGRESS'
        practice.save()
        
        # Notificar a supervisor y coordinadores
        if practice.supervisor:
            Notification.objects.create(
                user=practice.supervisor.user,
                tipo='INFO',
                titulo='Práctica iniciada',
                mensaje=f'El estudiante {practice.student.user.get_full_name()} inició su práctica',
                related_practice=practice
            )
        
        return Response(
            {'message': 'Práctica iniciada', 'practice': PracticeDetailSerializer(practice).data},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanApprovePractice])
    def complete(self, request, pk=None):
        """
        POST /api/practices/{id}/complete/
        Completar práctica con calificación (IN_PROGRESS → COMPLETED).
        
        Body:
        {
            "calificacion_final": 18.5,
            "observaciones": "Excelente desempeño"
        }
        """
        practice = self.get_object()
        
        calificacion = request.data.get('calificacion_final')
        if not calificacion:
            return Response(
                {'error': 'Debe proporcionar la calificación final'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            calificacion = float(calificacion)
            if calificacion < 0 or calificacion > 20:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {'error': 'La calificación debe ser un número entre 0 y 20'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if practice.status != 'IN_PROGRESS':
            return Response(
                {'error': f'Solo se pueden completar prácticas IN_PROGRESS. Estado actual: {practice.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        practice.status = 'COMPLETED'
        practice.calificacion_final = calificacion
        practice.observaciones = request.data.get('observaciones', '')
        practice.save()
        
        # Notificar al estudiante
        Notification.objects.create(
            user=practice.student.user,
            tipo='SUCCESS',
            titulo='Práctica completada',
            mensaje=f'Tu práctica "{practice.titulo}" ha sido completada con calificación {calificacion}',
            related_practice=practice
        )
        
        return Response(
            {'message': 'Práctica completada', 'practice': PracticeDetailSerializer(practice).data},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search(self, request):
        """
        GET /api/practices/search/
        Búsqueda avanzada de prácticas.
        
        Query params:
        - student_codigo: Código del estudiante
        - company_ruc: RUC de la empresa
        - status: Estado de la práctica
        - modalidad: Modalidad
        - fecha_inicio_desde, fecha_inicio_hasta: Rango de fecha inicio
        - fecha_fin_desde, fecha_fin_hasta: Rango de fecha fin
        - area_practica: Área de práctica
        """
        serializer = PracticeSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset()
        filters = serializer.validated_data
        
        if filters.get('student_codigo'):
            queryset = queryset.filter(student__codigo_estudiante__icontains=filters['student_codigo'])
        
        if filters.get('company_ruc'):
            queryset = queryset.filter(company__ruc__icontains=filters['company_ruc'])
        
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        if filters.get('modalidad'):
            queryset = queryset.filter(modalidad=filters['modalidad'])
        
        if filters.get('fecha_inicio_desde'):
            queryset = queryset.filter(fecha_inicio__gte=filters['fecha_inicio_desde'])
        
        if filters.get('fecha_inicio_hasta'):
            queryset = queryset.filter(fecha_inicio__lte=filters['fecha_inicio_hasta'])
        
        if filters.get('fecha_fin_desde'):
            queryset = queryset.filter(fecha_fin__gte=filters['fecha_fin_desde'])
        
        if filters.get('fecha_fin_hasta'):
            queryset = queryset.filter(fecha_fin__lte=filters['fecha_fin_hasta'])
        
        if filters.get('area_practica'):
            queryset = queryset.filter(area_practica__icontains=filters['area_practica'])
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PracticeListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PracticeListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_practices(self, request):
        """
        GET /api/practices/my_practices/
        Retorna las prácticas del usuario actual según su rol.
        """
        queryset = self.get_queryset()
        
        # Aplicar filtro de estado si se proporciona
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        serializer = PracticeListSerializer(queryset, many=True)
        return Response(serializer.data)


# ============================================================================
# DOCUMENT VIEWSET
# ============================================================================

class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de documentos.
    
    Endpoints:
    - GET /api/documents/ - Listar documentos
    - GET /api/documents/{id}/ - Ver documento
    - POST /api/documents/ - Subir documento
    - PUT/PATCH /api/documents/{id}/ - Actualizar documento
    - DELETE /api/documents/{id}/ - Eliminar documento
    - POST /api/documents/{id}/approve/ - Aprobar documento
    - POST /api/documents/{id}/reject/ - Rechazar documento
    - GET /api/documents/{id}/download/ - Descargar archivo
    """
    
    queryset = Document.objects.select_related(
        'practice', 'practice__student', 'practice__company',
        'uploaded_by', 'approved_by'
    ).all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nombre_archivo', 'tipo']
    filterset_fields = ['practice', 'tipo', 'aprobado']
    ordering_fields = ['created_at', 'fecha_aprobacion']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action == 'retrieve':
            return DocumentDetailSerializer
        elif self.action == 'create':
            return DocumentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentUpdateSerializer
        elif self.action in ['approve', 'reject']:
            return DocumentApproveSerializer
        return DocumentDetailSerializer
    
    def get_permissions(self):
        """Permisos según la acción."""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, CanUploadDocument]
        elif self.action in ['approve', 'reject']:
            permission_classes = [IsAuthenticated, CanApproveDocument]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, CanViewDocument]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar documentos según el rol."""
        user = self.request.user
        queryset = Document.objects.select_related(
            'practice', 'practice__student', 'uploaded_by'
        ).all()
        
        # Practicante ve documentos de sus prácticas
        if user.is_practicante:
            try:
                student = Student.objects.get(user=user)
                return queryset.filter(practice__student=student)
            except Student.DoesNotExist:
                return queryset.none()
        
        # Supervisor ve documentos de prácticas que supervisa
        if user.is_supervisor:
            try:
                supervisor = Supervisor.objects.get(user=user)
                return queryset.filter(practice__supervisor=supervisor)
            except Supervisor.DoesNotExist:
                return queryset.none()
        
        # Staff ve todos
        return queryset
    
    def perform_destroy(self, instance):
        """Solo el uploader o admin pueden eliminar."""
        user = self.request.user
        
        if instance.uploaded_by != user and not user.is_administrador:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Solo puedes eliminar tus propios documentos')
        
        instance.delete()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanApproveDocument])
    def approve(self, request, pk=None):
        """
        POST /api/documents/{id}/approve/
        Aprobar un documento (solo Coordinador/Secretaria).
        
        Body:
        {
            "observaciones": "Documento correcto"
        }
        """
        document = self.get_object()
        
        if document.aprobado:
            return Response(
                {'error': 'El documento ya está aprobado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document.aprobado = True
        document.approved_by = request.user
        document.fecha_aprobacion = datetime.now()
        document.observaciones = request.data.get('observaciones', '')
        document.save()
        
        # Notificar al estudiante
        Notification.objects.create(
            user=document.practice.student.user,
            tipo='SUCCESS',
            titulo='Documento aprobado',
            mensaje=f'Tu documento "{document.nombre_archivo}" ha sido aprobado',
            related_document=document,
            related_practice=document.practice
        )
        
        return Response(
            {'message': 'Documento aprobado', 'document': DocumentDetailSerializer(document).data},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanApproveDocument])
    def reject(self, request, pk=None):
        """
        POST /api/documents/{id}/reject/
        Rechazar un documento (solo Coordinador/Secretaria).
        
        Body:
        {
            "observaciones": "Motivo del rechazo"
        }
        """
        document = self.get_object()
        
        observaciones = request.data.get('observaciones', '')
        if not observaciones:
            return Response(
                {'error': 'Debe proporcionar observaciones para el rechazo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document.aprobado = False
        document.observaciones = observaciones
        document.save()
        
        # Notificar al estudiante
        Notification.objects.create(
            user=document.practice.student.user,
            tipo='WARNING',
            titulo='Documento rechazado',
            mensaje=f'Tu documento "{document.nombre_archivo}" fue rechazado. Motivo: {observaciones}',
            related_document=document,
            related_practice=document.practice
        )
        
        return Response(
            {'message': 'Documento rechazado', 'document': DocumentDetailSerializer(document).data},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def download(self, request, pk=None):
        """
        GET /api/documents/{id}/download/
        Descargar el archivo del documento.
        """
        document = self.get_object()
        
        if not document.archivo:
            return Response(
                {'error': 'El documento no tiene archivo asociado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Django FileResponse para streaming
        from django.http import FileResponse
        import os
        
        try:
            response = FileResponse(
                document.archivo.open('rb'),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{document.nombre_archivo}"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Error al descargar el archivo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# NOTIFICATION VIEWSET
# ============================================================================

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de notificaciones.
    
    Endpoints:
    - GET /api/notifications/ - Listar notificaciones del usuario
    - GET /api/notifications/{id}/ - Ver notificación
    - POST /api/notifications/ - Crear notificación (solo Admin)
    - DELETE /api/notifications/{id}/ - Eliminar notificación
    - POST /api/notifications/{id}/mark_read/ - Marcar como leída
    - POST /api/notifications/mark_all_read/ - Marcar todas como leídas
    - GET /api/notifications/unread/ - Solo no leídas
    - GET /api/notifications/unread_count/ - Contador de no leídas
    """
    
    queryset = Notification.objects.select_related('user').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['titulo', 'mensaje']
    filterset_fields = ['tipo', 'leida']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'list' or self.action in ['unread', 'unread_count']:
            return NotificationListSerializer
        elif self.action == 'retrieve':
            return NotificationDetailSerializer
        elif self.action == 'create':
            return NotificationCreateSerializer
        elif self.action in ['mark_read', 'mark_all_read']:
            return NotificationMarkAsReadSerializer
        return NotificationDetailSerializer
    
    def get_permissions(self):
        """Permisos según la acción."""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, IsAdministrador]
        else:
            permission_classes = [IsAuthenticated, CanViewNotification]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Solo ver notificaciones propias."""
        return Notification.objects.filter(user=self.request.user).select_related(
            'related_practice', 'related_document'
        )
    
    def perform_destroy(self, instance):
        """Solo el usuario puede eliminar sus notificaciones."""
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Solo puedes eliminar tus propias notificaciones')
        
        instance.delete()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_read(self, request, pk=None):
        """
        POST /api/notifications/{id}/mark_read/
        Marcar notificación como leída.
        """
        notification = self.get_object()
        
        if notification.leido:
            return Response(
                {'message': 'La notificación ya estaba marcada como leída'},
                status=status.HTTP_200_OK
            )
        
        notification.leido = True
        notification.fecha_leido = datetime.now()
        notification.save()
        
        return Response(
            {'message': 'Notificación marcada como leída'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_all_read(self, request):
        """
        POST /api/notifications/mark_all_read/
        Marcar todas las notificaciones como leídas.
        """
        updated = Notification.objects.filter(
            user=request.user,
            leido=False
        ).update(
            leido=True,
            fecha_leido=datetime.now()
        )
        
        return Response(
            {'message': f'{updated} notificaciones marcadas como leídas'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def unread(self, request):
        """
        GET /api/notifications/unread/
        Retorna solo notificaciones no leídas.
        """
        queryset = self.get_queryset().filter(leido=False)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NotificationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = NotificationListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def unread_count(self, request):
        """
        GET /api/notifications/unread_count/
        Retorna el contador de notificaciones no leídas.
        """
        count = self.get_queryset().filter(leido=False).count()
        
        return Response({'unread_count': count}, status=status.HTTP_200_OK)


# ============================================================================
# FIN DE VIEWSETS
# ============================================================================
