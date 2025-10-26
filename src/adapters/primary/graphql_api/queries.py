"""
Queries GraphQL Avanzadas para el Sistema de Gestión de Prácticas Profesionales.

Este módulo implementa queries GraphQL con:
- Filtros complejos y búsquedas
- Paginación
- Resolvers optimizados
- Agregaciones y estadísticas
- Permisos basados en roles
"""

import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg, Sum, F, Value, CharField
from django.db.models.functions import Concat
from datetime import datetime, timedelta

from .types import (
    UserType, StudentType, CompanyType, SupervisorType,
    PracticeType, DocumentType, NotificationType,
    SchoolType, BranchType, PracticeEvaluationType, PracticeStatusHistoryType
)
from src.adapters.secondary.database.models import (
    Student, Company, Supervisor, Practice, Document, Notification,
    School, Branch, PracticeEvaluation, PracticeStatusHistory
)
from src.infrastructure.security.permission_helpers import (
    can_view_users, can_view_students, can_view_companies,
    can_view_supervisors, can_view_practices, can_view_documents
)

User = get_user_model()


# ============================================================================
# TIPOS AUXILIARES PARA ESTADÍSTICAS Y AGREGACIONES
# ============================================================================

class PracticeStatisticsType(graphene.ObjectType):
    """Estadísticas de prácticas."""
    total = graphene.Int()
    draft = graphene.Int()
    pending = graphene.Int()
    approved = graphene.Int()
    in_progress = graphene.Int()
    completed = graphene.Int()
    cancelled = graphene.Int()
    average_hours = graphene.Float()
    average_grade = graphene.Float()


class StudentStatisticsType(graphene.ObjectType):
    """Estadísticas de estudiantes."""
    total = graphene.Int()
    eligible = graphene.Int()
    with_practice = graphene.Int()
    without_practice = graphene.Int()
    average_gpa = graphene.Float()
    by_semester = graphene.JSONString()


class CompanyStatisticsType(graphene.ObjectType):
    """Estadísticas de empresas."""
    total = graphene.Int()
    active = graphene.Int()
    pending = graphene.Int()
    suspended = graphene.Int()
    blacklisted = graphene.Int()
    by_sector = graphene.JSONString()
    with_practices = graphene.Int()


class DashboardStatisticsType(graphene.ObjectType):
    """Estadísticas completas del dashboard."""
    practices = graphene.Field(PracticeStatisticsType)
    students = graphene.Field(StudentStatisticsType)
    companies = graphene.Field(CompanyStatisticsType)
    recent_activities = graphene.List(graphene.JSONString)


class PaginationType(graphene.ObjectType):
    """Información de paginación."""
    page = graphene.Int()
    page_size = graphene.Int()
    total_count = graphene.Int()
    total_pages = graphene.Int()
    has_next = graphene.Boolean()
    has_previous = graphene.Boolean()


class UserListType(graphene.ObjectType):
    """Lista paginada de usuarios."""
    items = graphene.List(UserType)
    pagination = graphene.Field(PaginationType)


class StudentListType(graphene.ObjectType):
    """Lista paginada de estudiantes."""
    items = graphene.List(StudentType)
    pagination = graphene.Field(PaginationType)


class CompanyListType(graphene.ObjectType):
    """Lista paginada de empresas."""
    items = graphene.List(CompanyType)
    pagination = graphene.Field(PaginationType)


class PracticeListType(graphene.ObjectType):
    """Lista paginada de prácticas."""
    items = graphene.List(PracticeType)
    pagination = graphene.Field(PaginationType)


# ============================================================================
# QUERY CLASS PRINCIPAL
# ============================================================================

class Query(graphene.ObjectType):
    """
    Queries GraphQL avanzadas del sistema.
    
    Incluye:
    - Queries básicas (single item)
    - Queries de lista con filtros
    - Búsquedas avanzadas
    - Paginación
    - Estadísticas y agregaciones
    """
    
    # ========================================================================
    # USER QUERIES
    # ========================================================================
    
    # Queries básicas
    me = graphene.Field(UserType, description="Usuario autenticado actual")
    user = graphene.Field(
        UserType,
        id=graphene.ID(required=True),
        description="Buscar usuario por ID"
    )
    
    # Queries de lista
    users = graphene.Field(
        UserListType,
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        role=graphene.String(),
        is_active=graphene.Boolean(),
        search=graphene.String(),
        description="Lista paginada de usuarios con filtros"
    )
    
    users_by_role = graphene.List(
        UserType,
        role=graphene.String(required=True),
        description="Usuarios filtrados por rol"
    )
    
    search_users = graphene.List(
        UserType,
        query=graphene.String(required=True),
        description="Búsqueda de usuarios por nombre o email"
    )
    
    # ========================================================================
    # STUDENT QUERIES
    # ========================================================================
    
    # Queries básicas
    student = graphene.Field(
        StudentType,
        id=graphene.ID(),
        codigo=graphene.String(),
        description="Buscar estudiante por ID o código"
    )
    
    my_student_profile = graphene.Field(
        StudentType,
        description="Perfil de estudiante del usuario actual"
    )
    
    # Queries de lista
    students = graphene.Field(
        StudentListType,
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        semestre=graphene.Int(),
        carrera=graphene.String(),
        search=graphene.String(),
        order_by=graphene.String(default_value="-created_at"),
        description="Lista paginada de estudiantes con filtros"
    )
    
    eligible_students = graphene.List(
        StudentType,
        description="Estudiantes elegibles para prácticas (semestre >= 6, promedio >= 12)"
    )
    
    students_without_practice = graphene.List(
        StudentType,
        description="Estudiantes sin práctica asignada"
    )
    
    search_students = graphene.List(
        StudentType,
        query=graphene.String(required=True),
        description="Búsqueda de estudiantes por nombre, código o carrera"
    )
    
    # ========================================================================
    # COMPANY QUERIES
    # ========================================================================
    
    # Queries básicas
    company = graphene.Field(
        CompanyType,
        id=graphene.ID(),
        ruc=graphene.String(),
        description="Buscar empresa por ID o RUC"
    )
    
    # Queries de lista
    companies = graphene.Field(
        CompanyListType,
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        status=graphene.String(),
        sector=graphene.String(),
        search=graphene.String(),
        order_by=graphene.String(default_value="-created_at"),
        description="Lista paginada de empresas con filtros"
    )
    
    active_companies = graphene.List(
        CompanyType,
        description="Empresas activas que pueden recibir practicantes"
    )
    
    pending_validation_companies = graphene.List(
        CompanyType,
        description="Empresas pendientes de validación"
    )
    
    companies_by_sector = graphene.List(
        CompanyType,
        sector=graphene.String(required=True),
        description="Empresas filtradas por sector económico"
    )
    
    search_companies = graphene.List(
        CompanyType,
        query=graphene.String(required=True),
        description="Búsqueda de empresas por nombre, RUC o sector"
    )
    
    # ========================================================================
    # SUPERVISOR QUERIES
    # ========================================================================
    
    # Queries básicas
    supervisor = graphene.Field(
        SupervisorType,
        id=graphene.ID(required=True),
        description="Buscar supervisor por ID"
    )
    
    my_supervisor_profile = graphene.Field(
        SupervisorType,
        description="Perfil de supervisor del usuario actual"
    )
    
    # Queries de lista
    supervisors = graphene.List(
        SupervisorType,
        company_id=graphene.ID(),
        description="Lista de supervisores (opcionalmente filtrado por empresa)"
    )
    
    company_supervisors = graphene.List(
        SupervisorType,
        company_id=graphene.ID(required=True),
        description="Supervisores de una empresa específica"
    )
    
    available_supervisors = graphene.List(
        SupervisorType,
        company_id=graphene.ID(required=True),
        description="Supervisores disponibles de una empresa (con capacidad)"
    )
    
    # ========================================================================
    # PRACTICE QUERIES
    # ========================================================================
    
    # Queries básicas
    practice = graphene.Field(
        PracticeType,
        id=graphene.ID(required=True),
        description="Buscar práctica por ID"
    )
    
    # Queries de lista
    practices = graphene.Field(
        PracticeListType,
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        status=graphene.String(),
        student_id=graphene.ID(),
        company_id=graphene.ID(),
        supervisor_id=graphene.ID(),
        fecha_inicio_from=graphene.Date(),
        fecha_inicio_to=graphene.Date(),
        search=graphene.String(),
        order_by=graphene.String(default_value="-created_at"),
        description="Lista paginada de prácticas con filtros"
    )
    
    my_practices = graphene.List(
        PracticeType,
        description="Prácticas del usuario actual (estudiante o supervisor)"
    )
    
    practices_by_status = graphene.List(
        PracticeType,
        status=graphene.String(required=True),
        description="Prácticas filtradas por estado"
    )
    
    student_practices = graphene.List(
        PracticeType,
        student_id=graphene.ID(required=True),
        description="Prácticas de un estudiante específico"
    )
    
    company_practices = graphene.List(
        PracticeType,
        company_id=graphene.ID(required=True),
        description="Prácticas de una empresa específica"
    )
    
    supervisor_practices = graphene.List(
        PracticeType,
        supervisor_id=graphene.ID(required=True),
        description="Prácticas de un supervisor específico"
    )
    
    active_practices = graphene.List(
        PracticeType,
        description="Prácticas activas (APPROVED o IN_PROGRESS)"
    )
    
    pending_approval_practices = graphene.List(
        PracticeType,
        description="Prácticas pendientes de aprobación"
    )
    
    completed_practices = graphene.List(
        PracticeType,
        year=graphene.Int(),
        description="Prácticas completadas (opcionalmente por año)"
    )
    
    # ========================================================================
    # DOCUMENT QUERIES
    # ========================================================================
    
    # Queries básicas
    document = graphene.Field(
        DocumentType,
        id=graphene.ID(required=True),
        description="Buscar documento por ID"
    )
    
    # Queries de lista
    documents = graphene.List(
        DocumentType,
        practice_id=graphene.ID(),
        tipo=graphene.String(),
        aprobado=graphene.Boolean(),
        description="Lista de documentos con filtros"
    )
    
    practice_documents = graphene.List(
        DocumentType,
        practice_id=graphene.ID(required=True),
        description="Documentos de una práctica específica"
    )
    
    pending_approval_documents = graphene.List(
        DocumentType,
        description="Documentos pendientes de aprobación"
    )
    
    my_documents = graphene.List(
        DocumentType,
        description="Documentos subidos por el usuario actual"
    )
    
    # ========================================================================
    # NOTIFICATION QUERIES
    # ========================================================================
    
    # Queries de lista
    my_notifications = graphene.List(
        NotificationType,
        leida=graphene.Boolean(),
        tipo=graphene.String(),
        limit=graphene.Int(default_value=50),
        description="Notificaciones del usuario actual"
    )
    
    unread_notifications = graphene.List(
        NotificationType,
        description="Notificaciones no leídas del usuario actual"
    )
    
    unread_count = graphene.Int(
        description="Cantidad de notificaciones no leídas"
    )
    
    # ========================================================================
    # STATISTICS & DASHBOARD QUERIES
    # ========================================================================
    
    dashboard_statistics = graphene.Field(
        DashboardStatisticsType,
        description="Estadísticas completas del dashboard"
    )
    
    practice_statistics = graphene.Field(
        PracticeStatisticsType,
        year=graphene.Int(),
        description="Estadísticas de prácticas (opcionalmente por año)"
    )
    
    student_statistics = graphene.Field(
        StudentStatisticsType,
        description="Estadísticas de estudiantes"
    )
    
    company_statistics = graphene.Field(
        CompanyStatisticsType,
        description="Estadísticas de empresas"
    )
    
    # ========================================================================
    # RESOLVERS - USER
    # ========================================================================
    
    @login_required
    def resolve_me(self, info):
        """Resolver: Usuario actual."""
        return info.context.user
    
    @login_required
    def resolve_user(self, info, id):
        """Resolver: Usuario por ID."""
        current_user = info.context.user
        
        # Solo staff puede ver otros usuarios
        if not can_view_users(current_user):
            return None
        
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            return None
    
    @login_required
    def resolve_users(self, info, page=1, page_size=20, role=None, is_active=None, search=None):
        """Resolver: Lista paginada de usuarios."""
        current_user = info.context.user
        
        if not can_view_users(current_user):
            return UserListType(items=[], pagination=None)
        
        # Query base
        queryset = User.objects.all()
        
        # Filtros
        if role:
            queryset = queryset.filter(role=role)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search)
            )
        
        # Ordenamiento
        queryset = queryset.order_by('-created_at')
        
        # Paginación
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        items = list(queryset[start:end])
        
        pagination = PaginationType(
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
        return UserListType(items=items, pagination=pagination)
    
    @login_required
    def resolve_users_by_role(self, info, role):
        """Resolver: Usuarios por rol."""
        current_user = info.context.user
        
        if not can_view_users(current_user):
            return []
        
        return User.objects.filter(role=role, is_active=True).order_by('first_name', 'last_name')
    
    @login_required
    def resolve_search_users(self, info, query):
        """Resolver: Búsqueda de usuarios."""
        current_user = info.context.user
        
        if not can_view_users(current_user):
            return []
        
        return User.objects.filter(
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query)
        ).order_by('first_name', 'last_name')[:20]
    
    # ========================================================================
    # RESOLVERS - STUDENT
    # ========================================================================
    
    @login_required
    def resolve_student(self, info, id=None, codigo=None):
        """Resolver: Estudiante por ID o código."""
        current_user = info.context.user
        
        try:
            if id:
                student = Student.objects.select_related('user').get(id=id)
            elif codigo:
                student = Student.objects.select_related('user').get(codigo_estudiante=codigo)
            else:
                return None
            
            # Verificar permisos
            if can_view_students(current_user):
                return student
            elif current_user.role == 'PRACTICANTE' and student.user.id == current_user.id:
                return student
            elif current_user.role == 'SUPERVISOR':
                # Supervisor puede ver estudiantes de sus prácticas
                supervisor = getattr(current_user, 'supervisor_profile', None)
                if supervisor and student.practices.filter(supervisor=supervisor).exists():
                    return student
            
        except Student.DoesNotExist:
            pass
        
        return None
    
    @login_required
    def resolve_my_student_profile(self, info):
        """Resolver: Perfil de estudiante del usuario actual."""
        current_user = info.context.user
        
        if current_user.role != 'PRACTICANTE':
            return None
        
        return getattr(current_user, 'student_profile', None)
    
    @login_required
    def resolve_students(self, info, page=1, page_size=20, semestre=None, carrera=None, search=None, order_by="-created_at"):
        """Resolver: Lista paginada de estudiantes."""
        current_user = info.context.user
        
        if not can_view_students(current_user):
            return StudentListType(items=[], pagination=None)
        
        # Query base
        queryset = Student.objects.select_related('user').all()
        
        # Filtros
        if semestre:
            queryset = queryset.filter(semestre_actual=semestre)
        if carrera:
            queryset = queryset.filter(carrera__icontains=carrera)
        if search:
            queryset = queryset.filter(
                Q(codigo_estudiante__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(carrera__icontains=search)
            )
        
        # Ordenamiento
        queryset = queryset.order_by(order_by)
        
        # Paginación
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        items = list(queryset[start:end])
        
        pagination = PaginationType(
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
        return StudentListType(items=items, pagination=pagination)
    
    @login_required
    def resolve_eligible_students(self, info):
        """Resolver: Estudiantes elegibles para prácticas."""
        current_user = info.context.user
        
        if not can_view_students(current_user):
            return []
        
        return Student.objects.filter(
            semestre_actual__gte=6,
            promedio_ponderado__gte=12.0,
            user__is_active=True
        ).select_related('user').order_by('-promedio_ponderado')
    
    @login_required
    def resolve_students_without_practice(self, info):
        """Resolver: Estudiantes sin práctica."""
        current_user = info.context.user
        
        if not can_view_students(current_user):
            return []
        
        # Estudiantes elegibles que no tienen prácticas activas
        return Student.objects.filter(
            semestre_actual__gte=6,
            promedio_ponderado__gte=12.0,
            user__is_active=True
        ).exclude(
            practices__status__in=['APPROVED', 'IN_PROGRESS']
        ).select_related('user').order_by('-promedio_ponderado')
    
    @login_required
    def resolve_search_students(self, info, query):
        """Resolver: Búsqueda de estudiantes."""
        current_user = info.context.user
        
        if not can_view_students(current_user):
            return []
        
        return Student.objects.filter(
            Q(codigo_estudiante__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(carrera__icontains=query)
        ).select_related('user').order_by('user__first_name', 'user__last_name')[:20]
    
    # ========================================================================
    # RESOLVERS - COMPANY
    # ========================================================================
    
    @login_required
    def resolve_company(self, info, id=None, ruc=None):
        """Resolver: Empresa por ID o RUC."""
        try:
            if id:
                return Company.objects.get(id=id)
            elif ruc:
                return Company.objects.get(ruc=ruc)
        except Company.DoesNotExist:
            pass
        
        return None
    
    @login_required
    def resolve_companies(self, info, page=1, page_size=20, status=None, sector=None, search=None, order_by="-created_at"):
        """Resolver: Lista paginada de empresas."""
        current_user = info.context.user
        
        # Query base
        queryset = Company.objects.all()
        
        # Si no es staff, solo ver empresas activas
        if not can_view_companies(current_user):
            queryset = queryset.filter(status='ACTIVE')
        
        # Filtros
        if status:
            queryset = queryset.filter(status=status)
        if sector:
            queryset = queryset.filter(sector_economico__icontains=sector)
        if search:
            queryset = queryset.filter(
                Q(razon_social__icontains=search) |
                Q(nombre_comercial__icontains=search) |
                Q(ruc__icontains=search) |
                Q(sector_economico__icontains=search)
            )
        
        # Ordenamiento
        queryset = queryset.order_by(order_by)
        
        # Paginación
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        items = list(queryset[start:end])
        
        pagination = PaginationType(
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
        return CompanyListType(items=items, pagination=pagination)
    
    @login_required
    def resolve_active_companies(self, info):
        """Resolver: Empresas activas."""
        return Company.objects.filter(status='ACTIVE').order_by('razon_social')
    
    @login_required
    def resolve_pending_validation_companies(self, info):
        """Resolver: Empresas pendientes de validación."""
        current_user = info.context.user
        
        if current_user.role not in ['COORDINADOR', 'ADMINISTRADOR']:
            return []
        
        return Company.objects.filter(status='PENDING_VALIDATION').order_by('-created_at')
    
    @login_required
    def resolve_companies_by_sector(self, info, sector):
        """Resolver: Empresas por sector."""
        return Company.objects.filter(
            sector_economico__icontains=sector,
            status='ACTIVE'
        ).order_by('razon_social')
    
    @login_required
    def resolve_search_companies(self, info, query):
        """Resolver: Búsqueda de empresas."""
        return Company.objects.filter(
            Q(razon_social__icontains=query) |
            Q(nombre_comercial__icontains=query) |
            Q(ruc__icontains=query) |
            Q(sector_economico__icontains=query)
        ).order_by('razon_social')[:20]
    
    # ========================================================================
    # RESOLVERS - SUPERVISOR
    # ========================================================================
    
    @login_required
    def resolve_supervisor(self, info, id):
        """Resolver: Supervisor por ID."""
        try:
            return Supervisor.objects.select_related('user', 'company').get(id=id)
        except Supervisor.DoesNotExist:
            return None
    
    @login_required
    def resolve_my_supervisor_profile(self, info):
        """Resolver: Perfil de supervisor del usuario actual."""
        current_user = info.context.user
        
        if current_user.role != 'SUPERVISOR':
            return None
        
        return getattr(current_user, 'supervisor_profile', None)
    
    @login_required
    def resolve_supervisors(self, info, company_id=None):
        """Resolver: Lista de supervisores."""
        current_user = info.context.user
        
        if not can_view_supervisors(current_user):
            return []
        
        queryset = Supervisor.objects.select_related('user', 'company').all()
        
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        
        return queryset.order_by('user__first_name', 'user__last_name')
    
    @login_required
    def resolve_company_supervisors(self, info, company_id):
        """Resolver: Supervisores de una empresa."""
        return Supervisor.objects.filter(
            company_id=company_id,
            user__is_active=True
        ).select_related('user').order_by('user__first_name', 'user__last_name')
    
    @login_required
    def resolve_available_supervisors(self, info, company_id):
        """Resolver: Supervisores disponibles (con capacidad)."""
        # Supervisores con menos de 5 prácticas activas
        return Supervisor.objects.filter(
            company_id=company_id,
            user__is_active=True
        ).annotate(
            active_practices=Count(
                'practices',
                filter=Q(practices__status__in=['APPROVED', 'IN_PROGRESS'])
            )
        ).filter(
            active_practices__lt=5
        ).select_related('user').order_by('active_practices', 'user__first_name')
    
    # ========================================================================
    # RESOLVERS - PRACTICE
    # ========================================================================
    
    @login_required
    def resolve_practice(self, info, id):
        """Resolver: Práctica por ID."""
        current_user = info.context.user
        
        try:
            practice = Practice.objects.select_related(
                'student__user', 'company', 'supervisor__user'
            ).get(id=id)
            
            # Verificar permisos
            if can_view_practices(current_user):
                return practice
            elif current_user.role == 'PRACTICANTE':
                student = getattr(current_user, 'student_profile', None)
                if student and practice.student.id == student.id:
                    return practice
            elif current_user.role == 'SUPERVISOR':
                supervisor = getattr(current_user, 'supervisor_profile', None)
                if supervisor and practice.supervisor and practice.supervisor.id == supervisor.id:
                    return practice
        except Practice.DoesNotExist:
            pass
        
        return None
    
    @login_required
    def resolve_practices(self, info, page=1, page_size=20, status=None, student_id=None, 
                         company_id=None, supervisor_id=None, fecha_inicio_from=None,
                         fecha_inicio_to=None, search=None, order_by="-created_at"):
        """Resolver: Lista paginada de prácticas."""
        current_user = info.context.user
        
        # Query base según permisos
        if can_view_practices(current_user):
            queryset = Practice.objects.select_related('student__user', 'company', 'supervisor__user').all()
        elif current_user.role == 'PRACTICANTE':
            student = getattr(current_user, 'student_profile', None)
            if student:
                queryset = Practice.objects.filter(student=student).select_related('company', 'supervisor__user')
            else:
                return PracticeListType(items=[], pagination=None)
        elif current_user.role == 'SUPERVISOR':
            supervisor = getattr(current_user, 'supervisor_profile', None)
            if supervisor:
                queryset = Practice.objects.filter(supervisor=supervisor).select_related('student__user', 'company')
            else:
                return PracticeListType(items=[], pagination=None)
        else:
            return PracticeListType(items=[], pagination=None)
        
        # Filtros
        if status:
            queryset = queryset.filter(status=status)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        if supervisor_id:
            queryset = queryset.filter(supervisor_id=supervisor_id)
        if fecha_inicio_from:
            queryset = queryset.filter(fecha_inicio__gte=fecha_inicio_from)
        if fecha_inicio_to:
            queryset = queryset.filter(fecha_inicio__lte=fecha_inicio_to)
        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search) |
                Q(area_practica__icontains=search) |
                Q(company__razon_social__icontains=search) |
                Q(student__user__first_name__icontains=search) |
                Q(student__user__last_name__icontains=search)
            )
        
        # Ordenamiento
        queryset = queryset.order_by(order_by)
        
        # Paginación
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        items = list(queryset[start:end])
        
        pagination = PaginationType(
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
        return PracticeListType(items=items, pagination=pagination)
    
    @login_required
    def resolve_my_practices(self, info):
        """Resolver: Prácticas del usuario actual."""
        current_user = info.context.user
        
        if current_user.role == 'PRACTICANTE':
            student = getattr(current_user, 'student_profile', None)
            if student:
                return Practice.objects.filter(student=student).select_related(
                    'company', 'supervisor__user'
                ).order_by('-created_at')
        elif current_user.role == 'SUPERVISOR':
            supervisor = getattr(current_user, 'supervisor_profile', None)
            if supervisor:
                return Practice.objects.filter(supervisor=supervisor).select_related(
                    'student__user', 'company'
                ).order_by('-created_at')
        
        return []
    
    @login_required
    def resolve_practices_by_status(self, info, status):
        """Resolver: Prácticas por estado."""
        current_user = info.context.user
        
        if can_view_practices(current_user):
            return Practice.objects.filter(status=status).select_related(
                'student__user', 'company', 'supervisor__user'
            ).order_by('-created_at')
        elif current_user.role == 'SUPERVISOR':
            supervisor = getattr(current_user, 'supervisor_profile', None)
            if supervisor:
                return Practice.objects.filter(
                    status=status,
                    supervisor=supervisor
                ).select_related('student__user', 'company').order_by('-created_at')
        
        return []
    
    @login_required
    def resolve_student_practices(self, info, student_id):
        """Resolver: Prácticas de un estudiante."""
        current_user = info.context.user
        
        if not can_view_practices(current_user):
            return []
        
        return Practice.objects.filter(student_id=student_id).select_related(
            'company', 'supervisor__user'
        ).order_by('-created_at')
    
    @login_required
    def resolve_company_practices(self, info, company_id):
        """Resolver: Prácticas de una empresa."""
        current_user = info.context.user
        
        if not can_view_practices(current_user):
            return []
        
        return Practice.objects.filter(company_id=company_id).select_related(
            'student__user', 'supervisor__user'
        ).order_by('-created_at')
    
    @login_required
    def resolve_supervisor_practices(self, info, supervisor_id):
        """Resolver: Prácticas de un supervisor."""
        current_user = info.context.user
        
        if not can_view_practices(current_user):
            return []
        
        return Practice.objects.filter(supervisor_id=supervisor_id).select_related(
            'student__user', 'company'
        ).order_by('-created_at')
    
    @login_required
    def resolve_active_practices(self, info):
        """Resolver: Prácticas activas."""
        current_user = info.context.user
        
        if not can_view_practices(current_user):
            return []
        
        return Practice.objects.filter(
            status__in=['APPROVED', 'IN_PROGRESS']
        ).select_related('student__user', 'company', 'supervisor__user').order_by('-fecha_inicio')
    
    @login_required
    def resolve_pending_approval_practices(self, info):
        """Resolver: Prácticas pendientes de aprobación."""
        current_user = info.context.user
        
        if current_user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return []
        
        return Practice.objects.filter(status='PENDING').select_related(
            'student__user', 'company', 'supervisor__user'
        ).order_by('created_at')
    
    @login_required
    def resolve_completed_practices(self, info, year=None):
        """Resolver: Prácticas completadas."""
        current_user = info.context.user
        
        if not can_view_practices(current_user):
            return []
        
        queryset = Practice.objects.filter(status='COMPLETED').select_related(
            'student__user', 'company', 'supervisor__user'
        )
        
        if year:
            queryset = queryset.filter(fecha_fin__year=year)
        
        return queryset.order_by('-fecha_fin')
    
    # ========================================================================
    # RESOLVERS - DOCUMENT
    # ========================================================================
    
    @login_required
    def resolve_document(self, info, id):
        """Resolver: Documento por ID."""
        try:
            return Document.objects.select_related('practice', 'subido_por').get(id=id)
        except Document.DoesNotExist:
            return None
    
    @login_required
    def resolve_documents(self, info, practice_id=None, tipo=None, aprobado=None):
        """Resolver: Lista de documentos."""
        current_user = info.context.user
        
        if not can_view_documents(current_user):
            return []
        
        queryset = Document.objects.select_related('practice', 'subido_por').all()
        
        if practice_id:
            queryset = queryset.filter(practice_id=practice_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if aprobado is not None:
            queryset = queryset.filter(aprobado=aprobado)
        
        return queryset.order_by('-created_at')
    
    @login_required
    def resolve_practice_documents(self, info, practice_id):
        """Resolver: Documentos de una práctica."""
        current_user = info.context.user
        
        try:
            practice = Practice.objects.get(id=practice_id)
            
            # Verificar permisos
            can_view = False
            if can_view_practices(current_user):
                can_view = True
            elif current_user.role == 'PRACTICANTE':
                student = getattr(current_user, 'student_profile', None)
                if student and practice.student.id == student.id:
                    can_view = True
            elif current_user.role == 'SUPERVISOR':
                supervisor = getattr(current_user, 'supervisor_profile', None)
                if supervisor and practice.supervisor and practice.supervisor.id == supervisor.id:
                    can_view = True
            
            if can_view:
                return Document.objects.filter(practice=practice).select_related(
                    'subido_por'
                ).order_by('-created_at')
        except Practice.DoesNotExist:
            pass
        
        return []
    
    @login_required
    def resolve_pending_approval_documents(self, info):
        """Resolver: Documentos pendientes de aprobación."""
        current_user = info.context.user
        
        if current_user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return []
        
        return Document.objects.filter(aprobado=False).select_related(
            'practice__student__user', 'practice__company', 'subido_por'
        ).order_by('created_at')
    
    @login_required
    def resolve_my_documents(self, info):
        """Resolver: Documentos del usuario actual."""
        current_user = info.context.user
        
        return Document.objects.filter(subido_por=current_user).select_related(
            'practice__company'
        ).order_by('-created_at')
    
    # ========================================================================
    # RESOLVERS - NOTIFICATION
    # ========================================================================
    
    @login_required
    def resolve_my_notifications(self, info, leida=None, tipo=None, limit=50):
        """Resolver: Notificaciones del usuario actual."""
        current_user = info.context.user
        
        queryset = Notification.objects.filter(user=current_user)
        
        if leida is not None:
            queryset = queryset.filter(leida=leida)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        return queryset.order_by('-created_at')[:limit]
    
    @login_required
    def resolve_unread_notifications(self, info):
        """Resolver: Notificaciones no leídas."""
        current_user = info.context.user
        
        return Notification.objects.filter(
            user=current_user,
            leida=False
        ).order_by('-created_at')
    
    @login_required
    def resolve_unread_count(self, info):
        """Resolver: Cantidad de notificaciones no leídas."""
        current_user = info.context.user
        
        return Notification.objects.filter(
            user=current_user,
            leida=False
        ).count()
    
    # ========================================================================
    # RESOLVERS - STATISTICS
    # ========================================================================
    
    @login_required
    def resolve_dashboard_statistics(self, info):
        """Resolver: Estadísticas del dashboard."""
        current_user = info.context.user
        
        if current_user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return None
        
        # Estadísticas de prácticas
        practice_stats = Practice.objects.aggregate(
            total=Count('id'),
            draft=Count('id', filter=Q(status='DRAFT')),
            pending=Count('id', filter=Q(status='PENDING')),
            approved=Count('id', filter=Q(status='APPROVED')),
            in_progress=Count('id', filter=Q(status='IN_PROGRESS')),
            completed=Count('id', filter=Q(status='COMPLETED')),
            cancelled=Count('id', filter=Q(status='CANCELLED')),
            avg_hours=Avg('horas_totales'),
            avg_grade=Avg('calificacion_final', filter=Q(calificacion_final__isnull=False))
        )
        
        # Estadísticas de estudiantes
        student_stats = Student.objects.aggregate(
            total=Count('id'),
            eligible=Count('id', filter=Q(semestre_actual__gte=6, promedio_ponderado__gte=12.0)),
            with_practice=Count('id', filter=Q(practices__status__in=['APPROVED', 'IN_PROGRESS'])),
            avg_gpa=Avg('promedio_ponderado')
        )
        student_stats['without_practice'] = student_stats['total'] - student_stats['with_practice']
        
        # Estudiantes por semestre
        by_semester = {}
        for sem in range(1, 13):
            count = Student.objects.filter(semestre_actual=sem).count()
            by_semester[f'semestre_{sem}'] = count
        student_stats['by_semester'] = by_semester
        
        # Estadísticas de empresas
        company_stats = Company.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='ACTIVE')),
            pending=Count('id', filter=Q(status='PENDING_VALIDATION')),
            suspended=Count('id', filter=Q(status='SUSPENDED')),
            blacklisted=Count('id', filter=Q(status='BLACKLISTED')),
            with_practices=Count('id', filter=Q(practices__isnull=False))
        )
        
        # Empresas por sector
        by_sector = {}
        sectors = Company.objects.values_list('sector_economico', flat=True).distinct()
        for sector in sectors:
            if sector:
                count = Company.objects.filter(sector_economico=sector).count()
                by_sector[sector] = count
        company_stats['by_sector'] = by_sector
        
        # Actividades recientes (últimas 10)
        recent_activities = []
        recent_practices = Practice.objects.select_related('student__user', 'company').order_by('-created_at')[:5]
        for practice in recent_practices:
            recent_activities.append({
                'type': 'practice',
                'action': 'created',
                'description': f'Nueva práctica: {practice.titulo}',
                'student': practice.student.user.get_full_name(),
                'company': practice.company.razon_social,
                'timestamp': practice.created_at.isoformat()
            })
        
        recent_documents = Document.objects.select_related('practice__student__user', 'subido_por').order_by('-created_at')[:5]
        for doc in recent_documents:
            recent_activities.append({
                'type': 'document',
                'action': 'uploaded',
                'description': f'Documento subido: {doc.nombre_archivo}',
                'student': doc.practice.student.user.get_full_name(),
                'uploaded_by': doc.subido_por.get_full_name(),
                'timestamp': doc.created_at.isoformat()
            })
        
        # Ordenar por timestamp y tomar los 10 más recientes
        recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)[:10]
        
        return DashboardStatisticsType(
            practices=PracticeStatisticsType(**practice_stats),
            students=StudentStatisticsType(**student_stats),
            companies=CompanyStatisticsType(**company_stats),
            recent_activities=recent_activities
        )
    
    @login_required
    def resolve_practice_statistics(self, info, year=None):
        """Resolver: Estadísticas de prácticas."""
        current_user = info.context.user
        
        if current_user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return None
        
        queryset = Practice.objects.all()
        
        if year:
            queryset = queryset.filter(fecha_inicio__year=year)
        
        stats = queryset.aggregate(
            total=Count('id'),
            draft=Count('id', filter=Q(status='DRAFT')),
            pending=Count('id', filter=Q(status='PENDING')),
            approved=Count('id', filter=Q(status='APPROVED')),
            in_progress=Count('id', filter=Q(status='IN_PROGRESS')),
            completed=Count('id', filter=Q(status='COMPLETED')),
            cancelled=Count('id', filter=Q(status='CANCELLED')),
            average_hours=Avg('horas_totales'),
            average_grade=Avg('calificacion_final', filter=Q(calificacion_final__isnull=False))
        )
        
        return PracticeStatisticsType(**stats)
    
    @login_required
    def resolve_student_statistics(self, info):
        """Resolver: Estadísticas de estudiantes."""
        current_user = info.context.user
        
        if current_user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return None
        
        stats = Student.objects.aggregate(
            total=Count('id'),
            eligible=Count('id', filter=Q(semestre_actual__gte=6, promedio_ponderado__gte=12.0)),
            with_practice=Count('id', filter=Q(practices__status__in=['APPROVED', 'IN_PROGRESS'])),
            average_gpa=Avg('promedio_ponderado')
        )
        
        stats['without_practice'] = stats['total'] - stats['with_practice']
        
        # Por semestre
        by_semester = {}
        for sem in range(1, 13):
            count = Student.objects.filter(semestre_actual=sem).count()
            by_semester[f'semestre_{sem}'] = count
        stats['by_semester'] = by_semester
        
        return StudentStatisticsType(**stats)
    
    @login_required
    def resolve_company_statistics(self, info):
        """Resolver: Estadísticas de empresas."""
        current_user = info.context.user
        
        if current_user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return None
        
        stats = Company.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='ACTIVE')),
            pending=Count('id', filter=Q(status='PENDING_VALIDATION')),
            suspended=Count('id', filter=Q(status='SUSPENDED')),
            blacklisted=Count('id', filter=Q(status='BLACKLISTED')),
            with_practices=Count('id', filter=Q(practices__isnull=False))
        )
        
        # Por sector
        by_sector = {}
        sectors = Company.objects.values_list('sector_economico', flat=True).distinct()
        for sector in sectors:
            if sector:
                count = Company.objects.filter(sector_economico=sector).count()
                by_sector[sector] = count
        stats['by_sector'] = by_sector
        
        return CompanyStatisticsType(**stats)

    # ========================================================================
    # SCHOOL QUERIES (NUEVAS)
    # ========================================================================
    
    school = graphene.Field(
        SchoolType,
        id=graphene.ID(),
        codigo=graphene.String(),
        description="Buscar escuela profesional por ID o código"
    )
    
    schools = graphene.List(
        SchoolType,
        activa=graphene.Boolean(),
        search=graphene.String(),
        description="Lista de escuelas profesionales"
    )
    
    @login_required
    def resolve_school(self, info, id=None, codigo=None):
        """Resolver: Buscar escuela por ID o código."""
        if id:
            return School.objects.get(pk=id)
        elif codigo:
            return School.objects.get(codigo=codigo)
        return None
    
    @login_required
    def resolve_schools(self, info, activa=None, search=None):
        """Resolver: Lista de escuelas profesionales."""
        queryset = School.objects.select_related('coordinador').all()
        
        if activa is not None:
            queryset = queryset.filter(activa=activa)
        
        if search:
            queryset = queryset.filter(
                Q(codigo__icontains=search) |
                Q(nombre__icontains=search) |
                Q(facultad__icontains=search)
            )
        
        return queryset.order_by('codigo')
    
    # ========================================================================
    # BRANCH QUERIES (NUEVAS)
    # ========================================================================
    
    branch = graphene.Field(
        BranchType,
        id=graphene.ID(required=True),
        description="Buscar rama/especialidad por ID"
    )
    
    branches = graphene.List(
        BranchType,
        school_id=graphene.ID(),
        activa=graphene.Boolean(),
        search=graphene.String(),
        description="Lista de ramas/especialidades"
    )
    
    branches_by_school = graphene.List(
        BranchType,
        school_id=graphene.ID(required=True),
        description="Ramas de una escuela específica"
    )
    
    @login_required
    def resolve_branch(self, info, id):
        """Resolver: Buscar rama por ID."""
        return Branch.objects.select_related('school').get(pk=id)
    
    @login_required
    def resolve_branches(self, info, school_id=None, activa=None, search=None):
        """Resolver: Lista de ramas/especialidades."""
        queryset = Branch.objects.select_related('school').all()
        
        if school_id:
            queryset = queryset.filter(school_id=school_id)
        
        if activa is not None:
            queryset = queryset.filter(activa=activa)
        
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(school__nombre__icontains=search)
            )
        
        return queryset.order_by('school__nombre', 'nombre')
    
    @login_required
    def resolve_branches_by_school(self, info, school_id):
        """Resolver: Ramas de una escuela específica."""
        return Branch.objects.filter(
            school_id=school_id,
            activa=True
        ).order_by('nombre')
    
    # ========================================================================
    # PRACTICE EVALUATION QUERIES (NUEVAS)
    # ========================================================================
    
    evaluation = graphene.Field(
        PracticeEvaluationType,
        id=graphene.ID(required=True),
        description="Buscar evaluación por ID"
    )
    
    evaluations = graphene.List(
        PracticeEvaluationType,
        practice_id=graphene.ID(),
        evaluator_id=graphene.ID(),
        tipo_evaluador=graphene.String(),
        periodo_evaluacion=graphene.String(),
        status=graphene.String(),
        description="Lista de evaluaciones de prácticas"
    )
    
    my_evaluations = graphene.List(
        PracticeEvaluationType,
        description="Evaluaciones del usuario actual"
    )
    
    evaluations_by_practice = graphene.List(
        PracticeEvaluationType,
        practice_id=graphene.ID(required=True),
        description="Evaluaciones de una práctica específica"
    )
    
    @login_required
    def resolve_evaluation(self, info, id):
        """Resolver: Buscar evaluación por ID."""
        current_user = info.context.user
        evaluation = PracticeEvaluation.objects.select_related(
            'practice', 'practice__student', 'practice__student__user',
            'evaluator', 'approved_by'
        ).get(pk=id)
        
        # Verificar permisos
        if current_user.role == 'PRACTICANTE':
            if evaluation.practice.student.user != current_user:
                raise Exception("No tienes permiso para ver esta evaluación")
        elif current_user.role == 'SUPERVISOR':
            if evaluation.evaluator != current_user:
                raise Exception("No tienes permiso para ver esta evaluación")
        
        return evaluation
    
    @login_required
    def resolve_evaluations(self, info, practice_id=None, evaluator_id=None, 
                           tipo_evaluador=None, periodo_evaluacion=None, status=None):
        """Resolver: Lista de evaluaciones."""
        current_user = info.context.user
        queryset = PracticeEvaluation.objects.select_related(
            'practice', 'practice__student', 'practice__student__user',
            'evaluator', 'approved_by'
        ).all()
        
        # Filtrar por rol
        if current_user.role == 'PRACTICANTE':
            queryset = queryset.filter(practice__student__user=current_user)
        elif current_user.role == 'SUPERVISOR':
            queryset = queryset.filter(evaluator=current_user)
        
        # Aplicar filtros
        if practice_id:
            queryset = queryset.filter(practice_id=practice_id)
        if evaluator_id:
            queryset = queryset.filter(evaluator_id=evaluator_id)
        if tipo_evaluador:
            queryset = queryset.filter(tipo_evaluador=tipo_evaluador)
        if periodo_evaluacion:
            queryset = queryset.filter(periodo_evaluacion=periodo_evaluacion)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-fecha_evaluacion')
    
    @login_required
    def resolve_my_evaluations(self, info):
        """Resolver: Evaluaciones del usuario actual."""
        current_user = info.context.user
        
        if current_user.role == 'PRACTICANTE':
            return PracticeEvaluation.objects.filter(
                practice__student__user=current_user
            ).select_related('practice', 'evaluator', 'approved_by').order_by('-fecha_evaluacion')
        elif current_user.role == 'SUPERVISOR':
            return PracticeEvaluation.objects.filter(
                evaluator=current_user
            ).select_related('practice', 'practice__student__user', 'approved_by').order_by('-fecha_evaluacion')
        
        return []
    
    @login_required
    def resolve_evaluations_by_practice(self, info, practice_id):
        """Resolver: Evaluaciones de una práctica específica."""
        current_user = info.context.user
        
        # Verificar permiso para ver la práctica
        practice = Practice.objects.select_related('student__user').get(pk=practice_id)
        
        if current_user.role == 'PRACTICANTE' and practice.student.user != current_user:
            raise Exception("No tienes permiso para ver estas evaluaciones")
        
        return PracticeEvaluation.objects.filter(
            practice_id=practice_id
        ).select_related('evaluator', 'approved_by').order_by('periodo_evaluacion')
    
    # ========================================================================
    # PRACTICE STATUS HISTORY QUERIES (NUEVAS)
    # ========================================================================
    
    practice_history = graphene.List(
        PracticeStatusHistoryType,
        practice_id=graphene.ID(required=True),
        description="Historial de cambios de estado de una práctica"
    )
    
    status_changes = graphene.List(
        PracticeStatusHistoryType,
        estado_nuevo=graphene.String(),
        description="Lista de cambios de estado"
    )
    
    @login_required
    def resolve_practice_history(self, info, practice_id):
        """Resolver: Historial de cambios de una práctica."""
        current_user = info.context.user
        
        # Verificar permiso para ver la práctica
        practice = Practice.objects.select_related('student__user').get(pk=practice_id)
        
        if current_user.role == 'PRACTICANTE' and practice.student.user != current_user:
            raise Exception("No tienes permiso para ver este historial")
        elif current_user.role == 'SUPERVISOR' and practice.supervisor.user != current_user:
            raise Exception("No tienes permiso para ver este historial")
        
        return PracticeStatusHistory.objects.filter(
            practice_id=practice_id
        ).select_related('usuario_responsable').order_by('-fecha_cambio')
    
    @login_required
    def resolve_status_changes(self, info, estado_nuevo=None):
        """Resolver: Lista de cambios de estado."""
        current_user = info.context.user
        queryset = PracticeStatusHistory.objects.select_related(
            'practice', 'practice__student__user', 'usuario_responsable'
        ).all()
        
        # Filtrar por rol
        if current_user.role == 'PRACTICANTE':
            queryset = queryset.filter(practice__student__user=current_user)
        elif current_user.role == 'SUPERVISOR':
            queryset = queryset.filter(practice__supervisor__user=current_user)
        
        if estado_nuevo:
            queryset = queryset.filter(estado_nuevo=estado_nuevo)
        
        return queryset.order_by('-fecha_cambio')
