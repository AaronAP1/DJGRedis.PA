"""
Mutations GraphQL completas para el sistema de gestión de prácticas profesionales.

Este módulo implementa todas las mutations necesarias para:
- CRUD de todas las entidades (User, Student, Company, Supervisor, Practice, Document, Notification)
- Operaciones especiales (aprobar, rechazar, cambiar estado, etc.)
- Integración con sistema de permisos (decorators de Fase 1)
- Validaciones de negocio completas
- Notificaciones automáticas

Mutations implementadas: 30+
"""

import graphene
from graphql_jwt.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from graphql import GraphQLError

from .types import (
    UserType, StudentType, CompanyType, SupervisorType,
    PracticeType, DocumentType, NotificationType
)
from src.adapters.secondary.database.models import (
    Student, Company, Supervisor, Practice, Document, Notification
)
from src.infrastructure.security.decorators import (
    staff_required, role_required, administrador_required,
    coordinador_required
)
from src.infrastructure.security.permission_helpers import (
    can_create_student, can_update_student, can_create_company,
    can_update_company, can_validate_company, can_create_supervisor,
    can_update_supervisor, can_create_practice, can_update_practice,
    can_approve_practice, can_upload_document, can_approve_document,
    is_staff
)

User = get_user_model()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_notification(user, tipo, titulo, mensaje, practice=None, document=None):
    """Helper para crear notificaciones."""
    return Notification.objects.create(
        user=user,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        related_practice=practice,
        related_document=document,
        leido=False
    )


def validate_practice_status_transition(current_status, new_status):
    """Valida transiciones de estado de prácticas."""
    valid_transitions = {
        'DRAFT': ['PENDING'],
        'PENDING': ['APPROVED', 'CANCELLED'],
        'APPROVED': ['IN_PROGRESS', 'CANCELLED'],
        'IN_PROGRESS': ['COMPLETED', 'SUSPENDED', 'CANCELLED'],
        'SUSPENDED': ['IN_PROGRESS', 'CANCELLED'],
        'COMPLETED': [],
        'CANCELLED': []
    }
    
    if new_status not in valid_transitions.get(current_status, []):
        raise GraphQLError(
            f'No se puede cambiar de {current_status} a {new_status}'
        )


# ============================================================================
# USER MUTATIONS
# ============================================================================

class CreateUserMutation(graphene.Mutation):
    """Crear nuevo usuario (Admin/Secretaria)."""
    
    class Arguments:
        email = graphene.String(required=True)
        username = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        password = graphene.String(required=True)
        role = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    user = graphene.Field(UserType)
    
    @staticmethod
    @login_required
    @staff_required
    def mutate(root, info, email, username, first_name, last_name, password, role):
        """Crear usuario."""
        try:
            # Validar que el email no exista
            if User.objects.filter(email=email).exists():
                return CreateUserMutation(
                    success=False,
                    message='El email ya está registrado'
                )
            
            # Validar rol
            valid_roles = ['PRACTICANTE', 'SUPERVISOR', 'COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']
            if role not in valid_roles:
                return CreateUserMutation(
                    success=False,
                    message=f'Rol inválido. Opciones: {", ".join(valid_roles)}'
                )
            
            # Crear usuario
            user = User.objects.create_user(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                role=role
            )
            
            return CreateUserMutation(
                success=True,
                message='Usuario creado exitosamente',
                user=user
            )
            
        except Exception as e:
            return CreateUserMutation(
                success=False,
                message=f'Error al crear usuario: {str(e)}'
            )


class UpdateUserMutation(graphene.Mutation):
    """Actualizar usuario."""
    
    class Arguments:
        user_id = graphene.ID(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        is_active = graphene.Boolean()
        role = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    user = graphene.Field(UserType)
    
    @staticmethod
    @login_required
    def mutate(root, info, user_id, **kwargs):
        """Actualizar usuario."""
        current_user = info.context.user
        
        try:
            user = User.objects.get(id=user_id)
            
            # Solo Admin/Secretaria pueden editar otros usuarios
            if user.id != current_user.id and not is_staff(current_user):
                return UpdateUserMutation(
                    success=False,
                    message='No tienes permiso para editar este usuario'
                )
            
            # Actualizar campos
            if 'first_name' in kwargs:
                user.first_name = kwargs['first_name']
            if 'last_name' in kwargs:
                user.last_name = kwargs['last_name']
            
            # Solo staff puede cambiar is_active y role
            if is_staff(current_user):
                if 'is_active' in kwargs:
                    user.is_active = kwargs['is_active']
                if 'role' in kwargs:
                    user.role = kwargs['role']
            
            user.save()
            
            return UpdateUserMutation(
                success=True,
                message='Usuario actualizado exitosamente',
                user=user
            )
            
        except User.DoesNotExist:
            return UpdateUserMutation(
                success=False,
                message='Usuario no encontrado'
            )
        except Exception as e:
            return UpdateUserMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class DeleteUserMutation(graphene.Mutation):
    """Eliminar usuario (solo Admin)."""
    
    class Arguments:
        user_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    @login_required
    @administrador_required
    def mutate(root, info, user_id):
        """Eliminar usuario."""
        try:
            user = User.objects.get(id=user_id)
            user_email = user.email
            user.delete()
            
            return DeleteUserMutation(
                success=True,
                message=f'Usuario {user_email} eliminado exitosamente'
            )
            
        except User.DoesNotExist:
            return DeleteUserMutation(
                success=False,
                message='Usuario no encontrado'
            )
        except Exception as e:
            return DeleteUserMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class ChangePasswordMutation(graphene.Mutation):
    """Cambiar contraseña."""
    
    class Arguments:
        old_password = graphene.String(required=True)
        new_password = graphene.String(required=True)
        new_password_confirm = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, old_password, new_password, new_password_confirm):
        """Cambiar contraseña del usuario actual."""
        user = info.context.user
        
        try:
            # Validar contraseña actual
            if not user.check_password(old_password):
                return ChangePasswordMutation(
                    success=False,
                    message='Contraseña actual incorrecta'
                )
            
            # Validar que las nuevas coincidan
            if new_password != new_password_confirm:
                return ChangePasswordMutation(
                    success=False,
                    message='Las contraseñas nuevas no coinciden'
                )
            
            # Validar longitud mínima
            if len(new_password) < 8:
                return ChangePasswordMutation(
                    success=False,
                    message='La contraseña debe tener al menos 8 caracteres'
                )
            
            # Cambiar contraseña
            user.set_password(new_password)
            user.save()
            
            return ChangePasswordMutation(
                success=True,
                message='Contraseña actualizada exitosamente'
            )
            
        except Exception as e:
            return ChangePasswordMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


# ============================================================================
# STUDENT MUTATIONS
# ============================================================================

class CreateStudentMutation(graphene.Mutation):
    """Crear nuevo estudiante (crea User + Student)."""
    
    class Arguments:
        email = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        password = graphene.String(required=True)
        codigo_estudiante = graphene.String(required=True)
        escuela = graphene.String(required=True)
        semestre_actual = graphene.Int(required=True)
        promedio_ponderado = graphene.Float(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    student = graphene.Field(StudentType)
    
    @staticmethod
    @login_required
    def mutate(root, info, **kwargs):
        """Crear estudiante."""
        current_user = info.context.user
        
        # Validar permisos
        if not can_create_student(current_user):
            return CreateStudentMutation(
                success=False,
                message='No tienes permiso para crear estudiantes'
            )
        
        try:
            with transaction.atomic():
                # Validar email @upeu.edu.pe
                email = kwargs['email']
                if not email.endswith('@upeu.edu.pe'):
                    return CreateStudentMutation(
                        success=False,
                        message='El email debe ser @upeu.edu.pe'
                    )
                
                # Validar código formato YYYYNNNNNN
                codigo = kwargs['codigo_estudiante']
                if len(codigo) != 10 or not codigo.isdigit():
                    return CreateStudentMutation(
                        success=False,
                        message='Código debe tener formato YYYYNNNNNN (2020000001)'
                    )
                
                # Validar semestre
                semestre = kwargs['semestre_actual']
                if semestre < 1 or semestre > 12:
                    return CreateStudentMutation(
                        success=False,
                        message='Semestre debe estar entre 1 y 12'
                    )
                
                # Validar promedio
                promedio = kwargs['promedio_ponderado']
                if promedio < 0 or promedio > 20:
                    return CreateStudentMutation(
                        success=False,
                        message='Promedio debe estar entre 0 y 20'
                    )
                
                # Crear usuario
                user = User.objects.create_user(
                    email=email,
                    username=codigo,
                    first_name=kwargs['first_name'],
                    last_name=kwargs['last_name'],
                    password=kwargs['password'],
                    role='PRACTICANTE'
                )
                
                # Crear estudiante
                student = Student.objects.create(
                    user=user,
                    codigo_estudiante=codigo,
                    escuela=kwargs['escuela'],
                    semestre_actual=semestre,
                    promedio_ponderado=promedio
                )
                
                return CreateStudentMutation(
                    success=True,
                    message='Estudiante creado exitosamente',
                    student=student
                )
                
        except Exception as e:
            return CreateStudentMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class UpdateStudentMutation(graphene.Mutation):
    """Actualizar datos de estudiante."""
    
    class Arguments:
        student_id = graphene.ID(required=True)
        escuela = graphene.String()
        semestre_actual = graphene.Int()
        promedio_ponderado = graphene.Float()
    
    success = graphene.Boolean()
    message = graphene.String()
    student = graphene.Field(StudentType)
    
    @staticmethod
    @login_required
    def mutate(root, info, student_id, **kwargs):
        """Actualizar estudiante."""
        current_user = info.context.user
        
        try:
            student = Student.objects.get(id=student_id)
            
            # Validar permisos
            if not can_update_student(current_user, student):
                return UpdateStudentMutation(
                    success=False,
                    message='No tienes permiso para actualizar este estudiante'
                )
            
            # Actualizar campos
            if 'escuela' in kwargs:
                student.escuela = kwargs['escuela']
            
            if 'semestre_actual' in kwargs:
                semestre = kwargs['semestre_actual']
                if semestre < 1 or semestre > 12:
                    return UpdateStudentMutation(
                        success=False,
                        message='Semestre debe estar entre 1 y 12'
                    )
                student.semestre_actual = semestre
            
            if 'promedio_ponderado' in kwargs:
                promedio = kwargs['promedio_ponderado']
                if promedio < 0 or promedio > 20:
                    return UpdateStudentMutation(
                        success=False,
                        message='Promedio debe estar entre 0 y 20'
                    )
                student.promedio_ponderado = promedio
            
            student.save()
            
            return UpdateStudentMutation(
                success=True,
                message='Estudiante actualizado exitosamente',
                student=student
            )
            
        except Student.DoesNotExist:
            return UpdateStudentMutation(
                success=False,
                message='Estudiante no encontrado'
            )
        except Exception as e:
            return UpdateStudentMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class DeleteStudentMutation(graphene.Mutation):
    """Eliminar estudiante (solo Admin)."""
    
    class Arguments:
        student_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    @login_required
    @administrador_required
    def mutate(root, info, student_id):
        """Eliminar estudiante."""
        try:
            student = Student.objects.get(id=student_id)
            codigo = student.codigo_estudiante
            student.delete()
            
            return DeleteStudentMutation(
                success=True,
                message=f'Estudiante {codigo} eliminado exitosamente'
            )
            
        except Student.DoesNotExist:
            return DeleteStudentMutation(
                success=False,
                message='Estudiante no encontrado'
            )
        except Exception as e:
            return DeleteStudentMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


# ============================================================================
# COMPANY MUTATIONS
# ============================================================================

class CreateCompanyMutation(graphene.Mutation):
    """Crear nueva empresa."""
    
    class Arguments:
        ruc = graphene.String(required=True)
        razon_social = graphene.String(required=True)
        nombre_comercial = graphene.String()
        direccion = graphene.String(required=True)
        telefono = graphene.String(required=True)
        email = graphene.String(required=True)
        sector_economico = graphene.String(required=True)
        tamaño_empresa = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    company = graphene.Field(CompanyType)
    
    @staticmethod
    @login_required
    def mutate(root, info, **kwargs):
        """Crear empresa."""
        current_user = info.context.user
        
        # Validar permisos
        if not can_create_company(current_user):
            return CreateCompanyMutation(
                success=False,
                message='No tienes permiso para crear empresas'
            )
        
        try:
            # Validar RUC (11 dígitos)
            ruc = kwargs['ruc']
            if len(ruc) != 11 or not ruc.isdigit():
                return CreateCompanyMutation(
                    success=False,
                    message='RUC debe tener 11 dígitos numéricos'
                )
            
            # Validar RUC único
            if Company.objects.filter(ruc=ruc).exists():
                return CreateCompanyMutation(
                    success=False,
                    message='El RUC ya está registrado'
                )
            
            # Validar tamaño empresa
            valid_sizes = ['MICRO', 'PEQUEÑA', 'MEDIANA', 'GRANDE']
            if kwargs['tamaño_empresa'] not in valid_sizes:
                return CreateCompanyMutation(
                    success=False,
                    message=f'Tamaño inválido. Opciones: {", ".join(valid_sizes)}'
                )
            
            # Crear empresa con estado PENDING_VALIDATION
            company = Company.objects.create(
                status='PENDING_VALIDATION',
                **kwargs
            )
            
            # Notificar a coordinadores
            coordinadores = User.objects.filter(role='COORDINADOR', is_active=True)
            for coord in coordinadores:
                create_notification(
                    user=coord,
                    tipo='INFO',
                    titulo='Nueva empresa registrada',
                    mensaje=f'La empresa {company.razon_social} está pendiente de validación'
                )
            
            return CreateCompanyMutation(
                success=True,
                message='Empresa creada exitosamente (pendiente de validación)',
                company=company
            )
            
        except Exception as e:
            return CreateCompanyMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class UpdateCompanyMutation(graphene.Mutation):
    """Actualizar empresa."""
    
    class Arguments:
        company_id = graphene.ID(required=True)
        razon_social = graphene.String()
        nombre_comercial = graphene.String()
        direccion = graphene.String()
        telefono = graphene.String()
        email = graphene.String()
        sector_economico = graphene.String()
        tamaño_empresa = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    company = graphene.Field(CompanyType)
    
    @staticmethod
    @login_required
    def mutate(root, info, company_id, **kwargs):
        """Actualizar empresa."""
        current_user = info.context.user
        
        try:
            company = Company.objects.get(id=company_id)
            
            # Validar permisos
            if not can_update_company(current_user, company):
                return UpdateCompanyMutation(
                    success=False,
                    message='No tienes permiso para actualizar esta empresa'
                )
            
            # Actualizar campos
            for field, value in kwargs.items():
                setattr(company, field, value)
            
            company.save()
            
            return UpdateCompanyMutation(
                success=True,
                message='Empresa actualizada exitosamente',
                company=company
            )
            
        except Company.DoesNotExist:
            return UpdateCompanyMutation(
                success=False,
                message='Empresa no encontrada'
            )
        except Exception as e:
            return UpdateCompanyMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class ValidateCompanyMutation(graphene.Mutation):
    """Validar o rechazar empresa (solo Coordinador)."""
    
    class Arguments:
        company_id = graphene.ID(required=True)
        status = graphene.String(required=True)
        observaciones = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    company = graphene.Field(CompanyType)
    
    @staticmethod
    @login_required
    @coordinador_required
    def mutate(root, info, company_id, status, observaciones=None):
        """Validar empresa."""
        try:
            company = Company.objects.get(id=company_id)
            
            # Validar status
            valid_statuses = ['ACTIVE', 'SUSPENDED', 'BLACKLISTED']
            if status not in valid_statuses:
                return ValidateCompanyMutation(
                    success=False,
                    message=f'Estado inválido. Opciones: {", ".join(valid_statuses)}'
                )
            
            company.status = status
            company.save()
            
            # Notificar (si la empresa tiene contacto registrado)
            # TODO: Implementar notificación a empresa si tiene usuario contacto
            
            return ValidateCompanyMutation(
                success=True,
                message=f'Empresa validada como {status}',
                company=company
            )
            
        except Company.DoesNotExist:
            return ValidateCompanyMutation(
                success=False,
                message='Empresa no encontrada'
            )
        except Exception as e:
            return ValidateCompanyMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class DeleteCompanyMutation(graphene.Mutation):
    """Eliminar empresa (solo Admin)."""
    
    class Arguments:
        company_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    @login_required
    @administrador_required
    def mutate(root, info, company_id):
        """Eliminar empresa."""
        try:
            company = Company.objects.get(id=company_id)
            razon_social = company.razon_social
            company.delete()
            
            return DeleteCompanyMutation(
                success=True,
                message=f'Empresa {razon_social} eliminada exitosamente'
            )
            
        except Company.DoesNotExist:
            return DeleteCompanyMutation(
                success=False,
                message='Empresa no encontrada'
            )
        except Exception as e:
            return DeleteCompanyMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


# ============================================================================
# SUPERVISOR MUTATIONS
# ============================================================================

class CreateSupervisorMutation(graphene.Mutation):
    """Crear nuevo supervisor (crea User + Supervisor)."""
    
    class Arguments:
        email = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        password = graphene.String(required=True)
        company_id = graphene.ID(required=True)
        documento_tipo = graphene.String(required=True)
        documento_numero = graphene.String(required=True)
        cargo = graphene.String(required=True)
        telefono = graphene.String(required=True)
        años_experiencia = graphene.Int()
    
    success = graphene.Boolean()
    message = graphene.String()
    supervisor = graphene.Field(SupervisorType)
    
    @staticmethod
    @login_required
    def mutate(root, info, company_id, **kwargs):
        """Crear supervisor."""
        current_user = info.context.user
        
        # Validar permisos
        if not can_create_supervisor(current_user):
            return CreateSupervisorMutation(
                success=False,
                message='No tienes permiso para crear supervisores'
            )
        
        try:
            with transaction.atomic():
                # Validar empresa
                try:
                    company = Company.objects.get(id=company_id)
                    if company.status not in ['ACTIVE', 'PENDING_VALIDATION']:
                        return CreateSupervisorMutation(
                            success=False,
                            message='La empresa no puede recibir supervisores'
                        )
                except Company.DoesNotExist:
                    return CreateSupervisorMutation(
                        success=False,
                        message='Empresa no encontrada'
                    )
                
                # Validar años experiencia
                años_exp = kwargs.get('años_experiencia')
                if años_exp and (años_exp < 0 or años_exp > 60):
                    return CreateSupervisorMutation(
                        success=False,
                        message='Años de experiencia debe estar entre 0 y 60'
                    )
                
                # Crear usuario
                user = User.objects.create_user(
                    email=kwargs['email'],
                    username=kwargs['email'].split('@')[0],
                    first_name=kwargs['first_name'],
                    last_name=kwargs['last_name'],
                    password=kwargs['password'],
                    role='SUPERVISOR'
                )
                
                # Crear supervisor
                supervisor = Supervisor.objects.create(
                    user=user,
                    company=company,
                    documento_tipo=kwargs['documento_tipo'],
                    documento_numero=kwargs['documento_numero'],
                    cargo=kwargs['cargo'],
                    telefono=kwargs['telefono'],
                    años_experiencia=años_exp
                )
                
                return CreateSupervisorMutation(
                    success=True,
                    message='Supervisor creado exitosamente',
                    supervisor=supervisor
                )
                
        except Exception as e:
            return CreateSupervisorMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class UpdateSupervisorMutation(graphene.Mutation):
    """Actualizar supervisor."""
    
    class Arguments:
        supervisor_id = graphene.ID(required=True)
        documento_tipo = graphene.String()
        documento_numero = graphene.String()
        cargo = graphene.String()
        telefono = graphene.String()
        años_experiencia = graphene.Int()
    
    success = graphene.Boolean()
    message = graphene.String()
    supervisor = graphene.Field(SupervisorType)
    
    @staticmethod
    @login_required
    def mutate(root, info, supervisor_id, **kwargs):
        """Actualizar supervisor."""
        current_user = info.context.user
        
        try:
            supervisor = Supervisor.objects.get(id=supervisor_id)
            
            # Validar permisos
            if not can_update_supervisor(current_user, supervisor):
                return UpdateSupervisorMutation(
                    success=False,
                    message='No tienes permiso para actualizar este supervisor'
                )
            
            # Validar años experiencia
            if 'años_experiencia' in kwargs:
                años_exp = kwargs['años_experiencia']
                if años_exp and (años_exp < 0 or años_exp > 60):
                    return UpdateSupervisorMutation(
                        success=False,
                        message='Años de experiencia debe estar entre 0 y 60'
                    )
            
            # Actualizar campos
            for field, value in kwargs.items():
                setattr(supervisor, field, value)
            
            supervisor.save()
            
            return UpdateSupervisorMutation(
                success=True,
                message='Supervisor actualizado exitosamente',
                supervisor=supervisor
            )
            
        except Supervisor.DoesNotExist:
            return UpdateSupervisorMutation(
                success=False,
                message='Supervisor no encontrado'
            )
        except Exception as e:
            return UpdateSupervisorMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class DeleteSupervisorMutation(graphene.Mutation):
    """Eliminar supervisor (solo Admin)."""
    
    class Arguments:
        supervisor_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    @login_required
    @administrador_required
    def mutate(root, info, supervisor_id):
        """Eliminar supervisor."""
        try:
            supervisor = Supervisor.objects.get(id=supervisor_id)
            nombre = supervisor.user.get_full_name()
            supervisor.delete()
            
            return DeleteSupervisorMutation(
                success=True,
                message=f'Supervisor {nombre} eliminado exitosamente'
            )
            
        except Supervisor.DoesNotExist:
            return DeleteSupervisorMutation(
                success=False,
                message='Supervisor no encontrado'
            )
        except Exception as e:
            return DeleteSupervisorMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


# ============================================================================
# PRACTICE MUTATIONS
# ============================================================================

class CreatePracticeMutation(graphene.Mutation):
    """Crear nueva práctica."""
    
    class Arguments:
        student_id = graphene.ID(required=True)
        company_id = graphene.ID(required=True)
        supervisor_id = graphene.ID(required=True)
        tipo = graphene.String(required=True)
        area = graphene.String(required=True)
        fecha_inicio = graphene.Date(required=True)
        fecha_fin = graphene.Date(required=True)
        horas_requeridas = graphene.Int(required=True)
        descripcion_actividades = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    practice = graphene.Field(PracticeType)
    
    @staticmethod
    @login_required
    def mutate(root, info, student_id, company_id, supervisor_id, **kwargs):
        """Crear práctica."""
        current_user = info.context.user
        
        # Validar permisos
        if not can_create_practice(current_user):
            return CreatePracticeMutation(
                success=False,
                message='No tienes permiso para crear prácticas'
            )
        
        try:
            with transaction.atomic():
                # Validar student
                try:
                    student = Student.objects.get(id=student_id)
                    if student.user.id != current_user.id and current_user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
                        return CreatePracticeMutation(
                            success=False,
                            message='No puedes crear prácticas para otro estudiante'
                        )
                except Student.DoesNotExist:
                    return CreatePracticeMutation(
                        success=False,
                        message='Estudiante no encontrado'
                    )
                
                # Validar company
                try:
                    company = Company.objects.get(id=company_id)
                    if company.status != 'ACTIVE':
                        return CreatePracticeMutation(
                            success=False,
                            message='La empresa debe estar activa'
                        )
                except Company.DoesNotExist:
                    return CreatePracticeMutation(
                        success=False,
                        message='Empresa no encontrada'
                    )
                
                # Validar supervisor
                try:
                    supervisor = Supervisor.objects.get(id=supervisor_id)
                    if supervisor.company.id != company.id:
                        return CreatePracticeMutation(
                            success=False,
                            message='El supervisor debe pertenecer a la empresa'
                        )
                except Supervisor.DoesNotExist:
                    return CreatePracticeMutation(
                        success=False,
                        message='Supervisor no encontrado'
                    )
                
                # Validar tipo
                valid_tipos = ['PREPROFESIONAL', 'PROFESIONAL']
                if kwargs['tipo'] not in valid_tipos:
                    return CreatePracticeMutation(
                        success=False,
                        message=f'Tipo inválido. Opciones: {", ".join(valid_tipos)}'
                    )
                
                # Validar horas
                horas = kwargs['horas_requeridas']
                if horas < 480 or horas > 2000:
                    return CreatePracticeMutation(
                        success=False,
                        message='Horas requeridas debe estar entre 480 y 2000'
                    )
                
                # Crear práctica con status DRAFT
                practice = Practice.objects.create(
                    student=student,
                    company=company,
                    supervisor=supervisor,
                    status='DRAFT',
                    **kwargs
                )
                
                # Notificar al coordinador
                coordinadores = User.objects.filter(role='COORDINADOR', is_active=True)
                for coord in coordinadores:
                    create_notification(
                        user=coord,
                        tipo='INFO',
                        titulo='Nueva práctica registrada',
                        mensaje=f'{student.user.get_full_name()} ha registrado una nueva práctica'
                    )
                
                return CreatePracticeMutation(
                    success=True,
                    message='Práctica creada exitosamente',
                    practice=practice
                )
                
        except Exception as e:
            return CreatePracticeMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class UpdatePracticeMutation(graphene.Mutation):
    """Actualizar práctica."""
    
    class Arguments:
        practice_id = graphene.ID(required=True)
        area = graphene.String()
        fecha_inicio = graphene.Date()
        fecha_fin = graphene.Date()
        horas_requeridas = graphene.Int()
        descripcion_actividades = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    practice = graphene.Field(PracticeType)
    
    @staticmethod
    @login_required
    def mutate(root, info, practice_id, **kwargs):
        """Actualizar práctica."""
        current_user = info.context.user
        
        try:
            practice = Practice.objects.get(id=practice_id)
            
            # Validar permisos
            if not can_update_practice(current_user, practice):
                return UpdatePracticeMutation(
                    success=False,
                    message='No tienes permiso para actualizar esta práctica'
                )
            
            # No permitir actualización si ya está aprobada o en progreso
            if practice.status in ['APPROVED', 'IN_PROGRESS', 'COMPLETED']:
                return UpdatePracticeMutation(
                    success=False,
                    message='No se puede actualizar una práctica aprobada o en progreso'
                )
            
            # Actualizar campos
            for field, value in kwargs.items():
                setattr(practice, field, value)
            
            practice.save()
            
            return UpdatePracticeMutation(
                success=True,
                message='Práctica actualizada exitosamente',
                practice=practice
            )
            
        except Practice.DoesNotExist:
            return UpdatePracticeMutation(
                success=False,
                message='Práctica no encontrada'
            )
        except Exception as e:
            return UpdatePracticeMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class SubmitPracticeMutation(graphene.Mutation):
    """Enviar práctica a revisión (DRAFT → PENDING)."""
    
    class Arguments:
        practice_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    practice = graphene.Field(PracticeType)
    
    @staticmethod
    @login_required
    def mutate(root, info, practice_id):
        """Enviar práctica."""
        current_user = info.context.user
        
        try:
            practice = Practice.objects.get(id=practice_id)
            
            # Solo el estudiante puede enviar
            if practice.student.user.id != current_user.id:
                return SubmitPracticeMutation(
                    success=False,
                    message='Solo el estudiante puede enviar la práctica'
                )
            
            # Validar transición
            if not validate_practice_status_transition(practice.status, 'PENDING'):
                return SubmitPracticeMutation(
                    success=False,
                    message=f'No se puede enviar desde estado {practice.status}'
                )
            
            practice.status = 'PENDING'
            practice.save()
            
            # Notificar coordinadores
            coordinadores = User.objects.filter(role='COORDINADOR', is_active=True)
            for coord in coordinadores:
                create_notification(
                    user=coord,
                    tipo='ALERTA',
                    titulo='Práctica pendiente de aprobación',
                    mensaje=f'{practice.student.user.get_full_name()} ha enviado una práctica para revisión'
                )
            
            return SubmitPracticeMutation(
                success=True,
                message='Práctica enviada a revisión',
                practice=practice
            )
            
        except Practice.DoesNotExist:
            return SubmitPracticeMutation(
                success=False,
                message='Práctica no encontrada'
            )
        except Exception as e:
            return SubmitPracticeMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class ApprovePracticeMutation(graphene.Mutation):
    """Aprobar práctica (PENDING → APPROVED) - Solo Coordinador."""
    
    class Arguments:
        practice_id = graphene.ID(required=True)
        observaciones = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    practice = graphene.Field(PracticeType)
    
    @staticmethod
    @login_required
    @coordinador_required
    def mutate(root, info, practice_id, observaciones=None):
        """Aprobar práctica."""
        try:
            practice = Practice.objects.get(id=practice_id)
            
            # Validar transición
            if not validate_practice_status_transition(practice.status, 'APPROVED'):
                return ApprovePracticeMutation(
                    success=False,
                    message=f'No se puede aprobar desde estado {practice.status}'
                )
            
            practice.status = 'APPROVED'
            practice.save()
            
            # Notificar estudiante
            create_notification(
                user=practice.student.user,
                tipo='EXITO',
                titulo='Práctica aprobada',
                mensaje=f'Tu práctica en {practice.company.razon_social} ha sido aprobada. {observaciones or ""}'
            )
            
            return ApprovePracticeMutation(
                success=True,
                message='Práctica aprobada exitosamente',
                practice=practice
            )
            
        except Practice.DoesNotExist:
            return ApprovePracticeMutation(
                success=False,
                message='Práctica no encontrada'
            )
        except Exception as e:
            return ApprovePracticeMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class RejectPracticeMutation(graphene.Mutation):
    """Rechazar práctica (PENDING → DRAFT) - Solo Coordinador."""
    
    class Arguments:
        practice_id = graphene.ID(required=True)
        observaciones = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    practice = graphene.Field(PracticeType)
    
    @staticmethod
    @login_required
    @coordinador_required
    def mutate(root, info, practice_id, observaciones):
        """Rechazar práctica."""
        try:
            practice = Practice.objects.get(id=practice_id)
            
            # Validar transición
            if practice.status != 'PENDING':
                return RejectPracticeMutation(
                    success=False,
                    message='Solo se pueden rechazar prácticas pendientes'
                )
            
            practice.status = 'DRAFT'
            practice.save()
            
            # Notificar estudiante
            create_notification(
                user=practice.student.user,
                tipo='ALERTA',
                titulo='Práctica rechazada',
                mensaje=f'Tu práctica necesita correcciones: {observaciones}'
            )
            
            return RejectPracticeMutation(
                success=True,
                message='Práctica rechazada, devuelta a borrador',
                practice=practice
            )
            
        except Practice.DoesNotExist:
            return RejectPracticeMutation(
                success=False,
                message='Práctica no encontrada'
            )
        except Exception as e:
            return RejectPracticeMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class StartPracticeMutation(graphene.Mutation):
    """Iniciar práctica (APPROVED → IN_PROGRESS)."""
    
    class Arguments:
        practice_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    practice = graphene.Field(PracticeType)
    
    @staticmethod
    @login_required
    def mutate(root, info, practice_id):
        """Iniciar práctica."""
        current_user = info.context.user
        
        try:
            practice = Practice.objects.get(id=practice_id)
            
            # Solo coordinador o el estudiante pueden iniciar
            if current_user.role != 'COORDINADOR' and practice.student.user.id != current_user.id:
                return StartPracticeMutation(
                    success=False,
                    message='No tienes permiso para iniciar esta práctica'
                )
            
            # Validar transición
            if not validate_practice_status_transition(practice.status, 'IN_PROGRESS'):
                return StartPracticeMutation(
                    success=False,
                    message=f'No se puede iniciar desde estado {practice.status}'
                )
            
            practice.status = 'IN_PROGRESS'
            practice.save()
            
            # Notificar estudiante y supervisor
            create_notification(
                user=practice.student.user,
                tipo='INFO',
                titulo='Práctica iniciada',
                mensaje=f'Tu práctica en {practice.company.razon_social} ha iniciado'
            )
            
            create_notification(
                user=practice.supervisor.user,
                tipo='INFO',
                titulo='Práctica iniciada',
                mensaje=f'La práctica de {practice.student.user.get_full_name()} ha iniciado'
            )
            
            return StartPracticeMutation(
                success=True,
                message='Práctica iniciada exitosamente',
                practice=practice
            )
            
        except Practice.DoesNotExist:
            return StartPracticeMutation(
                success=False,
                message='Práctica no encontrada'
            )
        except Exception as e:
            return StartPracticeMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class CompletePracticeMutation(graphene.Mutation):
    """Completar práctica (IN_PROGRESS → COMPLETED)."""
    
    class Arguments:
        practice_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    practice = graphene.Field(PracticeType)
    
    @staticmethod
    @login_required
    @coordinador_required
    def mutate(root, info, practice_id):
        """Completar práctica."""
        try:
            practice = Practice.objects.get(id=practice_id)
            
            # Validar transición
            if not validate_practice_status_transition(practice.status, 'COMPLETED'):
                return CompletePracticeMutation(
                    success=False,
                    message=f'No se puede completar desde estado {practice.status}'
                )
            
            practice.status = 'COMPLETED'
            practice.save()
            
            # Notificar estudiante
            create_notification(
                user=practice.student.user,
                tipo='EXITO',
                titulo='Práctica completada',
                mensaje=f'¡Felicitaciones! Has completado tu práctica en {practice.company.razon_social}'
            )
            
            return CompletePracticeMutation(
                success=True,
                message='Práctica completada exitosamente',
                practice=practice
            )
            
        except Practice.DoesNotExist:
            return CompletePracticeMutation(
                success=False,
                message='Práctica no encontrada'
            )
        except Exception as e:
            return CompletePracticeMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class DeletePracticeMutation(graphene.Mutation):
    """Eliminar práctica (solo Admin o si está en DRAFT)."""
    
    class Arguments:
        practice_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, practice_id):
        """Eliminar práctica."""
        current_user = info.context.user
        
        try:
            practice = Practice.objects.get(id=practice_id)
            
            # Solo Admin o el estudiante (si está en DRAFT) pueden eliminar
            if current_user.role != 'ADMINISTRADOR':
                if practice.student.user.id != current_user.id:
                    return DeletePracticeMutation(
                        success=False,
                        message='No tienes permiso para eliminar esta práctica'
                    )
                if practice.status != 'DRAFT':
                    return DeletePracticeMutation(
                        success=False,
                        message='Solo se pueden eliminar prácticas en borrador'
                    )
            
            practice.delete()
            
            return DeletePracticeMutation(
                success=True,
                message='Práctica eliminada exitosamente'
            )
            
        except Practice.DoesNotExist:
            return DeletePracticeMutation(
                success=False,
                message='Práctica no encontrada'
            )
        except Exception as e:
            return DeletePracticeMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


# ============================================================================
# DOCUMENT MUTATIONS
# ============================================================================

class CreateDocumentMutation(graphene.Mutation):
    """Crear/subir nuevo documento."""
    
    class Arguments:
        practice_id = graphene.ID(required=True)
        tipo_documento = graphene.String(required=True)
        nombre = graphene.String(required=True)
        archivo_url = graphene.String(required=True)
        observaciones = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    document = graphene.Field(DocumentType)
    
    @staticmethod
    @login_required
    def mutate(root, info, practice_id, **kwargs):
        """Crear documento."""
        current_user = info.context.user
        
        try:
            # Validar práctica
            try:
                practice = Practice.objects.get(id=practice_id)
                
                # Solo el estudiante puede subir documentos
                if practice.student.user.id != current_user.id:
                    return CreateDocumentMutation(
                        success=False,
                        message='Solo el estudiante puede subir documentos'
                    )
            except Practice.DoesNotExist:
                return CreateDocumentMutation(
                    success=False,
                    message='Práctica no encontrada'
                )
            
            # Validar tipo documento
            valid_tipos = [
                'PLAN_TRABAJO',
                'INFORME_MENSUAL',
                'INFORME_FINAL',
                'CERTIFICADO',
                'CONSTANCIA',
                'EVALUACION',
                'OTRO'
            ]
            if kwargs['tipo_documento'] not in valid_tipos:
                return CreateDocumentMutation(
                    success=False,
                    message=f'Tipo inválido. Opciones: {", ".join(valid_tipos)}'
                )
            
            # Crear documento con status PENDING
            document = Document.objects.create(
                practice=practice,
                status='PENDING',
                **kwargs
            )
            
            # Notificar coordinador
            coordinadores = User.objects.filter(role='COORDINADOR', is_active=True)
            for coord in coordinadores:
                create_notification(
                    user=coord,
                    tipo='INFO',
                    titulo='Nuevo documento subido',
                    mensaje=f'{practice.student.user.get_full_name()} ha subido un documento de tipo {document.tipo_documento}'
                )
            
            return CreateDocumentMutation(
                success=True,
                message='Documento subido exitosamente',
                document=document
            )
            
        except Exception as e:
            return CreateDocumentMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class ApproveDocumentMutation(graphene.Mutation):
    """Aprobar documento - Solo Coordinador."""
    
    class Arguments:
        document_id = graphene.ID(required=True)
        observaciones = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    document = graphene.Field(DocumentType)
    
    @staticmethod
    @login_required
    @coordinador_required
    def mutate(root, info, document_id, observaciones=None):
        """Aprobar documento."""
        try:
            document = Document.objects.get(id=document_id)
            
            document.status = 'APPROVED'
            document.save()
            
            # Notificar estudiante
            create_notification(
                user=document.practice.student.user,
                tipo='EXITO',
                titulo='Documento aprobado',
                mensaje=f'Tu documento {document.nombre} ha sido aprobado. {observaciones or ""}'
            )
            
            return ApproveDocumentMutation(
                success=True,
                message='Documento aprobado exitosamente',
                document=document
            )
            
        except Document.DoesNotExist:
            return ApproveDocumentMutation(
                success=False,
                message='Documento no encontrado'
            )
        except Exception as e:
            return ApproveDocumentMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class RejectDocumentMutation(graphene.Mutation):
    """Rechazar documento - Solo Coordinador."""
    
    class Arguments:
        document_id = graphene.ID(required=True)
        observaciones = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    document = graphene.Field(DocumentType)
    
    @staticmethod
    @login_required
    @coordinador_required
    def mutate(root, info, document_id, observaciones):
        """Rechazar documento."""
        try:
            document = Document.objects.get(id=document_id)
            
            document.status = 'REJECTED'
            document.save()
            
            # Notificar estudiante
            create_notification(
                user=document.practice.student.user,
                tipo='ALERTA',
                titulo='Documento rechazado',
                mensaje=f'Tu documento {document.nombre} necesita correcciones: {observaciones}'
            )
            
            return RejectDocumentMutation(
                success=True,
                message='Documento rechazado',
                document=document
            )
            
        except Document.DoesNotExist:
            return RejectDocumentMutation(
                success=False,
                message='Documento no encontrado'
            )
        except Exception as e:
            return RejectDocumentMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class DeleteDocumentMutation(graphene.Mutation):
    """Eliminar documento."""
    
    class Arguments:
        document_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, document_id):
        """Eliminar documento."""
        current_user = info.context.user
        
        try:
            document = Document.objects.get(id=document_id)
            
            # Solo el estudiante (si está PENDING) o Admin pueden eliminar
            if current_user.role != 'ADMINISTRADOR':
                if document.practice.student.user.id != current_user.id:
                    return DeleteDocumentMutation(
                        success=False,
                        message='No tienes permiso para eliminar este documento'
                    )
                if document.status != 'PENDING':
                    return DeleteDocumentMutation(
                        success=False,
                        message='Solo se pueden eliminar documentos pendientes'
                    )
            
            document.delete()
            
            return DeleteDocumentMutation(
                success=True,
                message='Documento eliminado exitosamente'
            )
            
        except Document.DoesNotExist:
            return DeleteDocumentMutation(
                success=False,
                message='Documento no encontrado'
            )
        except Exception as e:
            return DeleteDocumentMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


# ============================================================================
# NOTIFICATION MUTATIONS
# ============================================================================

class MarkNotificationAsReadMutation(graphene.Mutation):
    """Marcar notificación como leída."""
    
    class Arguments:
        notification_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    notification = graphene.Field(NotificationType)
    
    @staticmethod
    @login_required
    def mutate(root, info, notification_id):
        """Marcar notificación como leída."""
        current_user = info.context.user
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=current_user
            )
            
            notification.leido = True
            notification.save()
            
            return MarkNotificationAsReadMutation(
                success=True,
                message='Notificación marcada como leída',
                notification=notification
            )
            
        except Notification.DoesNotExist:
            return MarkNotificationAsReadMutation(
                success=False,
                message='Notificación no encontrada'
            )
        except Exception as e:
            return MarkNotificationAsReadMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class MarkAllNotificationsReadMutation(graphene.Mutation):
    """Marcar todas las notificaciones como leídas."""
    
    success = graphene.Boolean()
    message = graphene.String()
    count = graphene.Int()
    
    @staticmethod
    @login_required
    def mutate(root, info):
        """Marcar todas como leídas."""
        current_user = info.context.user
        
        try:
            count = Notification.objects.filter(
                user=current_user,
                leido=False
            ).update(leido=True)
            
            return MarkAllNotificationsReadMutation(
                success=True,
                message=f'{count} notificaciones marcadas como leídas',
                count=count
            )
            
        except Exception as e:
            return MarkAllNotificationsReadMutation(
                success=False,
                message=f'Error: {str(e)}',
                count=0
            )


class DeleteNotificationMutation(graphene.Mutation):
    """Eliminar notificación."""
    
    class Arguments:
        notification_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, notification_id):
        """Eliminar notificación."""
        current_user = info.context.user
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=current_user
            )
            
            notification.delete()
            
            return DeleteNotificationMutation(
                success=True,
                message='Notificación eliminada exitosamente'
            )
            
        except Notification.DoesNotExist:
            return DeleteNotificationMutation(
                success=False,
                message='Notificación no encontrada'
            )
        except Exception as e:
            return DeleteNotificationMutation(
                success=False,
                message=f'Error: {str(e)}'
            )


class CreateNotificationMutation(graphene.Mutation):
    """Crear notificación manual (solo Admin/Coordinador)."""
    
    class Arguments:
        user_ids = graphene.List(graphene.ID, required=True)
        tipo = graphene.String(required=True)
        titulo = graphene.String(required=True)
        mensaje = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    count = graphene.Int()
    
    @staticmethod
    @login_required
    @staff_required
    def mutate(root, info, user_ids, tipo, titulo, mensaje):
        """Crear notificaciones."""
        try:
            # Validar tipo
            valid_tipos = ['INFO', 'ALERTA', 'EXITO', 'ERROR']
            if tipo not in valid_tipos:
                return CreateNotificationMutation(
                    success=False,
                    message=f'Tipo inválido. Opciones: {", ".join(valid_tipos)}',
                    count=0
                )
            
            # Crear notificaciones
            count = 0
            for user_id in user_ids:
                try:
                    user = User.objects.get(id=user_id)
                    create_notification(
                        user=user,
                        tipo=tipo,
                        titulo=titulo,
                        mensaje=mensaje
                    )
                    count += 1
                except User.DoesNotExist:
                    continue
            
            return CreateNotificationMutation(
                success=True,
                message=f'{count} notificaciones creadas exitosamente',
                count=count
            )
            
        except Exception as e:
            return CreateNotificationMutation(
                success=False,
                message=f'Error: {str(e)}',
                count=0
            )


# ============================================================================
# SCHEMA FINAL - REGISTRO DE TODAS LAS MUTATIONS
# ============================================================================

class Mutation(graphene.ObjectType):
    """Registro de todas las mutations del sistema."""
    
    # User mutations
    create_user = CreateUserMutation.Field()
    update_user = UpdateUserMutation.Field()
    delete_user = DeleteUserMutation.Field()
    change_password = ChangePasswordMutation.Field()
    
    # Student mutations
    create_student = CreateStudentMutation.Field()
    update_student = UpdateStudentMutation.Field()
    delete_student = DeleteStudentMutation.Field()
    
    # Company mutations
    create_company = CreateCompanyMutation.Field()
    update_company = UpdateCompanyMutation.Field()
    validate_company = ValidateCompanyMutation.Field()
    delete_company = DeleteCompanyMutation.Field()
    
    # Supervisor mutations
    create_supervisor = CreateSupervisorMutation.Field()
    update_supervisor = UpdateSupervisorMutation.Field()
    delete_supervisor = DeleteSupervisorMutation.Field()
    
    # Practice mutations
    create_practice = CreatePracticeMutation.Field()
    update_practice = UpdatePracticeMutation.Field()
    submit_practice = SubmitPracticeMutation.Field()
    approve_practice = ApprovePracticeMutation.Field()
    reject_practice = RejectPracticeMutation.Field()
    start_practice = StartPracticeMutation.Field()
    complete_practice = CompletePracticeMutation.Field()
    delete_practice = DeletePracticeMutation.Field()
    
    # Document mutations
    create_document = CreateDocumentMutation.Field()
    approve_document = ApproveDocumentMutation.Field()
    reject_document = RejectDocumentMutation.Field()
    delete_document = DeleteDocumentMutation.Field()
    
    # Notification mutations
    mark_notification_read = MarkNotificationAsReadMutation.Field()
    mark_all_notifications_read = MarkAllNotificationsReadMutation.Field()
    delete_notification = DeleteNotificationMutation.Field()
    create_notification = CreateNotificationMutation.Field()

