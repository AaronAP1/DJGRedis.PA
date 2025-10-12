"""
Queries GraphQL para el sistema de gestión de prácticas profesionales.
"""

import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import login_required, permission_required
from django.contrib.auth import get_user_model

from .types import (
    UserType, StudentType, CompanyType, PracticeType, DocumentType, NotificationType,
    PermissionType, RoleType, UserPermissionType, UserPermissionsInfo, AvatarType, EmpresaRucType,
    SupervisorType
)
from src.adapters.secondary.database.models import (
    Student, Company, Supervisor, Practice, Document, Notification,
    Permission, Role, UserPermission, Avatar
)

User = get_user_model()


class Query(graphene.ObjectType):
    """Queries principales del sistema."""
    
    # ===== USUARIOS =====
    users = DjangoFilterConnectionField(UserType)
    user = graphene.Field(UserType, id=graphene.ID(required=True))
    me = graphene.Field(UserType)
    
    # ===== ESTUDIANTES =====
    students = DjangoFilterConnectionField(StudentType)
    student = graphene.Field(StudentType, id=graphene.ID(required=True))
    eligible_students = graphene.List(StudentType)
    
    # ===== EMPRESAS =====
    companies = DjangoFilterConnectionField(CompanyType)
    company = graphene.Field(CompanyType, id=graphene.ID(required=True))
    active_companies = graphene.List(CompanyType)
    
    # ===== SUPERVISORES =====
    supervisors = DjangoFilterConnectionField(SupervisorType)
    supervisor = graphene.Field(SupervisorType, id=graphene.ID(required=True))
    company_supervisors = graphene.List(SupervisorType, company_id=graphene.ID(required=True))
    
    # ===== PRÁCTICAS =====
    practices = DjangoFilterConnectionField(PracticeType)
    practice = graphene.Field(PracticeType, id=graphene.ID(required=True))
    my_practices = graphene.List(PracticeType)
    practices_by_status = graphene.List(PracticeType, status=graphene.String(required=True))
    
    # ===== DOCUMENTOS =====
    documents = DjangoFilterConnectionField(DocumentType)
    document = graphene.Field(DocumentType, id=graphene.ID(required=True))
    practice_documents = graphene.List(DocumentType, practice_id=graphene.ID(required=True))
    
    # ===== NOTIFICACIONES =====
    notifications = DjangoFilterConnectionField(NotificationType)
    my_notifications = graphene.List(NotificationType)
    unread_notifications = graphene.List(NotificationType)
    
    # ===== ESTADÍSTICAS =====
    statistics = graphene.Field(graphene.JSONString)
    
    # ===== ROLES Y PERMISOS =====
    permissions = graphene.List(PermissionType, module=graphene.String())
    permission = graphene.Field(PermissionType, id=graphene.ID(required=True))
    roles = graphene.List(RoleType, is_active=graphene.Boolean())
    role = graphene.Field(RoleType, id=graphene.ID(required=True))
    user_permissions_info = graphene.Field(UserPermissionsInfo, user_id=graphene.ID(required=True))
    my_permissions_info = graphene.Field(UserPermissionsInfo)
    
    # ===== AVATARES =====
    avatars_by_role = graphene.List(AvatarType)
    list_avatars = graphene.List(AvatarType, role=graphene.String())
    
    # ===== BUSCAR EMPRESA POR RUC =====
    buscar_empresa_ruc = graphene.Field(EmpresaRucType, ruc=graphene.String(required=True))

    # ===== RESOLVERS USUARIOS =====
    @login_required
    def resolve_users(self, info, **kwargs):
        """Resuelve la lista de usuarios."""
        user = info.context.user
        # Solo ADMINISTRADOR puede ver listado y no debe verse a sí mismo
        if user.role == 'ADMINISTRADOR':
            return User.objects.exclude(id=user.id).order_by('created_at')
        
        # Lanzar error claro para usuarios sin permisos
        from graphql import GraphQLError
        raise GraphQLError(
            "No tienes permisos para ver la lista de usuarios",
            extensions={
                'code': 'INSUFFICIENT_PERMISSIONS',
                'required_role': 'ADMINISTRADOR',
                'current_role': user.role
            }
        )

    @login_required
    def resolve_user(self, info, id):
        """Resuelve un usuario específico."""
        user = info.context.user
        if user.role in ['COORDINADOR', 'ADMINISTRADOR']:
            try:
                return User.objects.get(id=id)
            except User.DoesNotExist:
                return None
        return None

    def resolve_me(self, info):
        """Resuelve el usuario actual."""
        # Verificar si hay usuario autenticado
        if not hasattr(info.context, 'user') or not info.context.user.is_authenticated:
            from graphql import GraphQLError
            raise GraphQLError(
                "No ha iniciado sesión. Por favor, inicie sesión para acceder a su perfil.",
                extensions={
                    'code': 'UNAUTHENTICATED',
                    'action': 'LOGIN_REQUIRED'
                }
            )
        
        return info.context.user

    # ===== RESOLVERS ESTUDIANTES =====
    @login_required
    def resolve_students(self, info, **kwargs):
        """Resuelve la lista de estudiantes."""
        user = info.context.user
        if user.role in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return Student.objects.select_related('user').all()
        elif user.role == 'SUPERVISOR':
            # Supervisores pueden ver estudiantes de sus empresas
            supervisor = getattr(user, 'supervisor_profile', None)
            if supervisor:
                return Student.objects.filter(
                    practices__company=supervisor.company
                ).distinct()
        return Student.objects.none()

    @login_required
    def resolve_student(self, info, id):
        """Resuelve un estudiante específico."""
        user = info.context.user
        try:
            student = Student.objects.select_related('user').get(id=id)
            
            # Verificar permisos
            if user.role in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
                return student
            elif user.role == 'PRACTICANTE' and user.id == student.user.id:
                return student
            elif user.role == 'SUPERVISOR':
                supervisor = getattr(user, 'supervisor_profile', None)
                if supervisor and student.practices.filter(company=supervisor.company).exists():
                    return student
        except Student.DoesNotExist:
            pass
        return None

    @login_required
    def resolve_eligible_students(self, info):
        """Resuelve estudiantes elegibles para prácticas."""
        user = info.context.user
        if user.role in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return Student.objects.filter(
                semestre_actual__gte=6,
                promedio_ponderado__gte=12.0
            ).select_related('user')
        return Student.objects.none()

    # ===== RESOLVERS EMPRESAS =====
    @login_required
    def resolve_companies(self, info, **kwargs):
        """Resuelve la lista de empresas."""
        user = info.context.user
        if user.role in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return Company.objects.all()
        elif user.role == 'SUPERVISOR':
            supervisor = getattr(user, 'supervisor_profile', None)
            if supervisor:
                return Company.objects.filter(id=supervisor.company.id)
        return Company.objects.filter(status='ACTIVE')

    @login_required
    def resolve_company(self, info, id):
        """Resuelve una empresa específica."""
        try:
            return Company.objects.get(id=id)
        except Company.DoesNotExist:
            return None

    @login_required
    def resolve_active_companies(self, info):
        """Resuelve empresas activas."""
        return Company.objects.filter(status='ACTIVE')

    # ===== RESOLVERS SUPERVISORES =====
    @login_required
    def resolve_supervisors(self, info, **kwargs):
        """Resuelve la lista de supervisores."""
        user = info.context.user
        if user.role in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return Supervisor.objects.select_related('user', 'company').all()
        return Supervisor.objects.none()

    @login_required
    def resolve_supervisor(self, info, id):
        """Resuelve un supervisor específico."""
        try:
            return Supervisor.objects.select_related('user', 'company').get(id=id)
        except Supervisor.DoesNotExist:
            return None

    @login_required
    def resolve_company_supervisors(self, info, company_id):
        """Resuelve supervisores de una empresa."""
        return Supervisor.objects.filter(company_id=company_id).select_related('user')

    # ===== RESOLVERS PRÁCTICAS =====
    @login_required
    def resolve_practices(self, info, **kwargs):
        """Resuelve la lista de prácticas."""
        user = info.context.user
        if user.role in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return Practice.objects.select_related('student__user', 'company', 'supervisor__user').all()
        elif user.role == 'SUPERVISOR':
            supervisor = getattr(user, 'supervisor_profile', None)
            if supervisor:
                return Practice.objects.filter(supervisor=supervisor).select_related('student__user', 'company')
        elif user.role == 'PRACTICANTE':
            student = getattr(user, 'student_profile', None)
            if student:
                return Practice.objects.filter(student=student).select_related('company', 'supervisor__user')
        return Practice.objects.none()

    @login_required
    def resolve_practice(self, info, id):
        """Resuelve una práctica específica."""
        user = info.context.user
        try:
            practice = Practice.objects.select_related(
                'student__user', 'company', 'supervisor__user'
            ).get(id=id)
            
            # Verificar permisos
            if user.role in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
                return practice
            elif user.role == 'PRACTICANTE':
                student = getattr(user, 'student_profile', None)
                if student and practice.student.id == student.id:
                    return practice
            elif user.role == 'SUPERVISOR':
                supervisor = getattr(user, 'supervisor_profile', None)
                if supervisor and practice.supervisor and practice.supervisor.id == supervisor.id:
                    return practice
        except Practice.DoesNotExist:
            pass
        return None

    @login_required
    def resolve_my_practices(self, info):
        """Resuelve las prácticas del usuario actual."""
        user = info.context.user
        if user.role == 'PRACTICANTE':
            student = getattr(user, 'student_profile', None)
            if student:
                return Practice.objects.filter(student=student).select_related('company', 'supervisor__user')
        elif user.role == 'SUPERVISOR':
            supervisor = getattr(user, 'supervisor_profile', None)
            if supervisor:
                return Practice.objects.filter(supervisor=supervisor).select_related('student__user', 'company')
        return Practice.objects.none()

    @login_required
    def resolve_practices_by_status(self, info, status):
        """Resuelve prácticas por estado."""
        user = info.context.user
        base_query = Practice.objects.filter(status=status).select_related('student__user', 'company', 'supervisor__user')
        
        if user.role in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return base_query
        elif user.role == 'SUPERVISOR':
            supervisor = getattr(user, 'supervisor_profile', None)
            if supervisor:
                return base_query.filter(supervisor=supervisor)
        return Practice.objects.none()

    # ===== RESOLVERS DOCUMENTOS =====
    @login_required
    def resolve_documents(self, info, **kwargs):
        """Resuelve la lista de documentos."""
        user = info.context.user
        if user.role in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return Document.objects.select_related('practice', 'subido_por').all()
        return Document.objects.none()

    @login_required
    def resolve_document(self, info, id):
        """Resuelve un documento específico."""
        try:
            return Document.objects.select_related('practice', 'subido_por').get(id=id)
        except Document.DoesNotExist:
            return None

    @login_required
    def resolve_practice_documents(self, info, practice_id):
        """Resuelve documentos de una práctica."""
        user = info.context.user
        try:
            practice = Practice.objects.get(id=practice_id)
            
            # Verificar permisos para ver la práctica
            can_view = False
            if user.role in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
                can_view = True
            elif user.role == 'PRACTICANTE':
                student = getattr(user, 'student_profile', None)
                if student and practice.student.id == student.id:
                    can_view = True
            elif user.role == 'SUPERVISOR':
                supervisor = getattr(user, 'supervisor_profile', None)
                if supervisor and practice.supervisor and practice.supervisor.id == supervisor.id:
                    can_view = True
            
            if can_view:
                return Document.objects.filter(practice=practice).select_related('subido_por')
        except Practice.DoesNotExist:
            pass
        return Document.objects.none()

    # ===== RESOLVERS NOTIFICACIONES =====
    @login_required
    def resolve_notifications(self, info, **kwargs):
        """Resuelve la lista de notificaciones."""
        user = info.context.user
        if user.role in ['ADMINISTRADOR']:
            return Notification.objects.select_related('user').all()
        return Notification.objects.none()

    @login_required
    def resolve_my_notifications(self, info):
        """Resuelve las notificaciones del usuario actual."""
        return Notification.objects.filter(user=info.context.user).order_by('-created_at')

    @login_required
    def resolve_unread_notifications(self, info):
        """Resuelve las notificaciones no leídas del usuario actual."""
        return Notification.objects.filter(
            user=info.context.user, 
            leida=False
        ).order_by('-created_at')

    # ===== RESOLVERS ESTADÍSTICAS =====
    @login_required
    def resolve_statistics(self, info):
        """Resuelve estadísticas del sistema."""
        user = info.context.user
        if user.role not in ['COORDINADOR', 'ADMINISTRADOR']:
            return None
        
        from django.db.models import Count, Q
        
        stats = {
            'total_users': User.objects.count(),
            'total_students': Student.objects.count(),
            'total_companies': Company.objects.count(),
            'total_practices': Practice.objects.count(),
            'active_practices': Practice.objects.filter(status='IN_PROGRESS').count(),
            'completed_practices': Practice.objects.filter(status='COMPLETED').count(),
            'pending_practices': Practice.objects.filter(status='PENDING').count(),
            'practices_by_status': {
                'draft': Practice.objects.filter(status='DRAFT').count(),
                'pending': Practice.objects.filter(status='PENDING').count(),
                'approved': Practice.objects.filter(status='APPROVED').count(),
                'in_progress': Practice.objects.filter(status='IN_PROGRESS').count(),
                'completed': Practice.objects.filter(status='COMPLETED').count(),
                'cancelled': Practice.objects.filter(status='CANCELLED').count(),
            },
            'companies_by_status': {
                'active': Company.objects.filter(status='ACTIVE').count(),
                'pending': Company.objects.filter(status='PENDING_VALIDATION').count(),
                'suspended': Company.objects.filter(status='SUSPENDED').count(),
            }
        }
        
        return stats
    
    # ===== RESOLVERS ROLES Y PERMISOS =====
    @login_required
    def resolve_permissions(self, info, module=None):
        """Resuelve la lista de permisos."""
        user = info.context.user
        
        # DEBUG: Imprimir información del usuario
        print(f"🔍 DEBUG resolve_permissions:")
        print(f"   - Usuario: {user.username}")
        print(f"   - Email: {user.email}")
        print(f"   - Rol: {user.role}")
        print(f"   - Es activo: {user.is_active}")
        
        # Solo administradores pueden ver permisos
        if user.role != 'ADMINISTRADOR':
            print(f"❌ Usuario {user.username} con rol {user.role} intentó acceder a permisos")
            from graphql import GraphQLError
            raise GraphQLError(
                "No tienes permisos para ver la lista de permisos",
                extensions={
                    'code': 'INSUFFICIENT_PERMISSIONS',
                    'required_role': 'ADMINISTRADOR',
                    'current_role': user.role
                }
            )
        
        print(f"✅ Usuario ADMINISTRADOR accediendo a permisos")
        queryset = Permission.objects.filter(is_active=True)
        if module:
            queryset = queryset.filter(module=module)
        
        permissions_count = queryset.count()
        print(f"📊 Total de permisos encontrados: {permissions_count}")
        
        return queryset.order_by('module', 'code')
    
    @login_required
    def resolve_permission(self, info, id):
        """Resuelve un permiso específico."""
        user = info.context.user
        
        if user.role != 'ADMINISTRADOR':
            from graphql import GraphQLError
            raise GraphQLError(
                "No tienes permisos para ver información de permisos",
                extensions={
                    'code': 'INSUFFICIENT_PERMISSIONS',
                    'required_role': 'ADMINISTRADOR',
                    'current_role': user.role
                }
            )
        
        try:
            return Permission.objects.get(pk=id)
        except Permission.DoesNotExist:
            return None
    
    @login_required
    def resolve_roles(self, info, is_active=None):
        """Resuelve la lista de roles."""
        user = info.context.user
        
        # DEBUG: Imprimir información del usuario
        print(f"🔍 DEBUG resolve_roles:")
        print(f"   - Usuario: {user.username}")
        print(f"   - Rol: {user.role}")
        
        # Solo administradores pueden ver roles
        if user.role == 'ADMINISTRADOR':
            print(f"✅ Usuario ADMINISTRADOR accediendo a roles")
            queryset = Role.objects.all()
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active)
            roles_count = queryset.count()
            print(f"📊 Total de roles encontrados: {roles_count}")
            return queryset.order_by('name')
        
        # Lanzar error claro para usuarios sin permisos
        from graphql import GraphQLError
        raise GraphQLError(
            "No tienes permisos para ver la lista de roles",
            extensions={
                'code': 'INSUFFICIENT_PERMISSIONS',
                'required_role': 'ADMINISTRADOR',
                'current_role': user.role
            }
        )
    
    @login_required
    def resolve_role(self, info, id):
        """Resuelve un rol específico."""
        user = info.context.user
        
        if not user.is_administrador and not user.is_superuser:
            return None
        
        try:
            return Role.objects.get(pk=id)
        except Role.DoesNotExist:
            return None
    
    @login_required
    def resolve_user_permissions_info(self, info, user_id):
        """Resuelve información de permisos de un usuario."""
        admin_user = info.context.user
        
        # Solo administradores pueden ver permisos de otros usuarios
        if not admin_user.is_administrador and not admin_user.is_superuser:
            return None
        
        try:
            target_user = User.objects.get(pk=user_id)
            
            role_perms = []
            if target_user.role_obj:
                role_perms = list(target_user.role_obj.permissions.filter(is_active=True))
            
            custom_perms = list(target_user.custom_permissions.filter(
                permission__is_active=True
            ))
            
            return UserPermissionsInfo(
                role=target_user.role_obj,
                role_permissions=role_perms,
                custom_permissions=custom_perms,
                all_permissions=target_user.get_all_permissions()
            )
        except User.DoesNotExist:
            return None
    
    @login_required
    def resolve_my_permissions_info(self, info):
        """Resuelve información de permisos del usuario autenticado."""
        user = info.context.user
        
        role_perms = []
        if user.role_obj:
            role_perms = list(user.role_obj.permissions.filter(is_active=True))
        
        custom_perms = list(user.custom_permissions.filter(
            permission__is_active=True
        ))
        
        return UserPermissionsInfo(
            role=user.role_obj,
            role_permissions=role_perms,
            custom_permissions=custom_perms,
            all_permissions=user.get_all_permissions()
        )
    
    # ===== RESOLVERS AVATARES =====
    @login_required
    def resolve_avatars_by_role(self, info):
        """Resuelve avatares según el rol del usuario autenticado desde la base de datos."""
        user = info.context.user
        user_role = user.role
        
        # Obtener avatares activos para el rol del usuario desde la BD
        avatars = Avatar.objects.filter(
            role=user_role,
            is_active=True
        ).order_by('created_at')
        
        return avatars
    
    @login_required
    def resolve_list_avatars(self, info, role=None):
        """Resuelve lista de avatares para administradores (con filtro opcional por rol)."""
        user = info.context.user
        
        # Solo ADMINISTRADOR puede listar todos los avatares
        if user.role != 'ADMINISTRADOR':
            from graphql import GraphQLError
            raise GraphQLError(
                "No tienes permisos para listar avatares",
                extensions={
                    'code': 'INSUFFICIENT_PERMISSIONS',
                    'required_role': 'ADMINISTRADOR',
                    'current_role': user.role
                }
            )
        
        # Filtrar por rol si se especifica
        queryset = Avatar.objects.all()
        if role:
            queryset = queryset.filter(role=role)
        
        return queryset.order_by('role', 'created_at')
    
    # ===== RESOLVERS BUSCAR EMPRESA =====
    @login_required
    def resolve_buscar_empresa_ruc(self, info, ruc):
        """Busca información de empresa por RUC usando API externa."""
        user = info.context.user
        
        # Solo ADMINISTRADOR y PRACTICANTE pueden buscar empresas
        if user.role not in ['ADMINISTRADOR', 'PRACTICANTE']:
            from graphql import GraphQLError
            raise GraphQLError(
                "No tienes permisos para buscar empresas",
                extensions={
                    'code': 'INSUFFICIENT_PERMISSIONS',
                    'required_roles': ['ADMINISTRADOR', 'PRACTICANTE'],
                    'current_role': user.role
                }
            )
        
        # Validar formato de RUC (11 dígitos)
        if not ruc or len(ruc) != 11 or not ruc.isdigit():
            from graphql import GraphQLError
            raise GraphQLError(
                "RUC debe tener exactamente 11 dígitos",
                extensions={
                    'code': 'INVALID_RUC_FORMAT',
                    'ruc': ruc
                }
            )
        
        try:
            import requests
            
            # API Token
            api_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6InByYWN0aWNhc2dlc3Rpb241QGdtYWlsLmNvbSJ9.JeW3jVctA3mDkU9IZSl_ATzO0AwZiHo53YChh3_ZUyI"
            
            # Llamar a la API
            url = f"https://dniruc.apisperu.com/api/v1/ruc/{ruc}?token={api_token}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extraer solo los campos necesarios
                return EmpresaRucType(
                    ruc=data.get('ruc'),
                    razon_social=data.get('razonSocial'),
                    nombre_comercial=data.get('nombreComercial'),
                    direccion=data.get('direccion'),
                    departamento=data.get('departamento'),
                    provincia=data.get('provincia'),
                    distrito=data.get('distrito'),
                    estado=data.get('estado'),
                    condicion=data.get('condicion')
                )
            else:
                from graphql import GraphQLError
                raise GraphQLError(
                    f"Error al consultar RUC: {response.status_code}",
                    extensions={
                        'code': 'API_ERROR',
                        'status_code': response.status_code,
                        'ruc': ruc
                    }
                )
                
        except requests.exceptions.Timeout:
            from graphql import GraphQLError
            raise GraphQLError(
                "Timeout al consultar la API de RUC",
                extensions={
                    'code': 'API_TIMEOUT',
                    'ruc': ruc
                }
            )
        except requests.exceptions.RequestException as e:
            from graphql import GraphQLError
            raise GraphQLError(
                f"Error de conexión con la API: {str(e)}",
                extensions={
                    'code': 'CONNECTION_ERROR',
                    'ruc': ruc
                }
            )
        except Exception as e:
            from graphql import GraphQLError
            raise GraphQLError(
                f"Error inesperado: {str(e)}",
                extensions={
                    'code': 'UNEXPECTED_ERROR',
                    'ruc': ruc
                }
            )
