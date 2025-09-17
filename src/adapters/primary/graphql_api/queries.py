"""
Queries GraphQL para el sistema de gestión de prácticas profesionales.
"""

import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import login_required, permission_required
from django.contrib.auth import get_user_model

from .types import (
    UserType, StudentType, CompanyType, SupervisorType,
    PracticeType, DocumentType, NotificationType
)
from src.adapters.secondary.database.models import (
    Student, Company, Supervisor, Practice, Document, Notification
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

    # ===== RESOLVERS USUARIOS =====
    @login_required
    def resolve_users(self, info, **kwargs):
        """Resuelve la lista de usuarios."""
        user = info.context.user
        # Solo ADMINISTRADOR puede ver listado y no debe verse a sí mismo
        if user.role == 'ADMINISTRADOR':
            return User.objects.exclude(id=user.id).order_by('created_at')
        return User.objects.none()

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

    @login_required
    def resolve_me(self, info):
        """Resuelve el usuario actual."""
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
