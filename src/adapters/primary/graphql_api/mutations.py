"""
Mutations GraphQL para el sistema de gestión de prácticas profesionales.
"""

import graphene
from graphql_jwt.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .types import (
    UserType, StudentType, CompanyType, SupervisorType,
    PracticeType, DocumentType, NotificationType,
    UserInput, StudentInput, CompanyInput, SupervisorInput,
    PracticeInput, DocumentInput
)
from src.adapters.secondary.database.models import (
    Student, Company, Supervisor, Practice, Document, Notification
)
from src.domain.enums import UserRole, PracticeStatus, CompanyStatus

User = get_user_model()


# ===== MUTATIONS PARA USUARIOS =====
class CreateUser(graphene.Mutation):
    """Mutation para crear un usuario."""
    
    class Arguments:
        input = UserInput(required=True)
    
    success = graphene.Boolean()
    user = graphene.Field(UserType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, input):
        user = info.context.user
        if user.role not in ['COORDINADOR', 'ADMINISTRADOR']:
            return CreateUser(success=False, message="Sin permisos para crear usuarios")
        
        try:
            with transaction.atomic():
                new_user = User.objects.create_user(
                    email=input.email,
                    password=input.password,
                    first_name=input.first_name,
                    last_name=input.last_name,
                    role=input.role,
                    is_active=True
                )
                
                return CreateUser(
                    success=True,
                    user=new_user,
                    message="Usuario creado exitosamente"
                )
        except Exception as e:
            return CreateUser(success=False, message=f"Error al crear usuario: {str(e)}")


class UpdateUser(graphene.Mutation):
    """Mutation para actualizar un usuario."""
    
    class Arguments:
        id = graphene.ID(required=True)
        input = UserInput(required=True)
    
    success = graphene.Boolean()
    user = graphene.Field(UserType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, id, input):
        user = info.context.user
        if user.role not in ['COORDINADOR', 'ADMINISTRADOR']:
            return UpdateUser(success=False, message="Sin permisos para actualizar usuarios")
        
        try:
            target_user = User.objects.get(id=id)
            
            # Actualizar campos
            if input.email:
                target_user.email = input.email
            if input.first_name:
                target_user.first_name = input.first_name
            if input.last_name:
                target_user.last_name = input.last_name
            if input.role:
                target_user.role = input.role
            if input.password:
                target_user.set_password(input.password)
            
            target_user.save()
            
            return UpdateUser(
                success=True,
                user=target_user,
                message="Usuario actualizado exitosamente"
            )
        except User.DoesNotExist:
            return UpdateUser(success=False, message="Usuario no encontrado")
        except Exception as e:
            return UpdateUser(success=False, message=f"Error al actualizar usuario: {str(e)}")


# ===== MUTATIONS PARA ESTUDIANTES =====
class CreateStudent(graphene.Mutation):
    """Mutation para crear un estudiante."""
    
    class Arguments:
        input = StudentInput(required=True)
    
    success = graphene.Boolean()
    student = graphene.Field(StudentType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, input):
        user = info.context.user
        if user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return CreateStudent(success=False, message="Sin permisos para crear estudiantes")
        
        try:
            with transaction.atomic():
                target_user = User.objects.get(id=input.user_id)
                if target_user.role != UserRole.PRACTICANTE.value:
                    return CreateStudent(success=False, message="El usuario debe tener rol PRACTICANTE")
                
                student = Student.objects.create(
                    user=target_user,
                    codigo_estudiante=input.codigo_estudiante,
                    dni=input.dni,
                    fecha_nacimiento=input.fecha_nacimiento,
                    telefono=input.telefono,
                    direccion=input.direccion,
                    carrera=input.carrera,
                    semestre_actual=input.semestre_actual,
                    promedio_ponderado=input.promedio_ponderado,
                    fecha_ingreso=input.fecha_ingreso
                )
                
                return CreateStudent(
                    success=True,
                    student=student,
                    message="Estudiante creado exitosamente"
                )
        except User.DoesNotExist:
            return CreateStudent(success=False, message="Usuario no encontrado")
        except Exception as e:
            return CreateStudent(success=False, message=f"Error al crear estudiante: {str(e)}")


# ===== MUTATIONS PARA EMPRESAS =====
class CreateCompany(graphene.Mutation):
    """Mutation para crear una empresa."""
    
    class Arguments:
        input = CompanyInput(required=True)
    
    success = graphene.Boolean()
    company = graphene.Field(CompanyType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, input):
        user = info.context.user
        if user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return CreateCompany(success=False, message="Sin permisos para crear empresas")
        
        try:
            with transaction.atomic():
                company = Company.objects.create(
                    nombre=input.nombre,
                    ruc=input.ruc,
                    direccion=input.direccion,
                    telefono=input.telefono,
                    email=input.email,
                    sector=input.sector,
                    descripcion=input.descripcion,
                    status=CompanyStatus.PENDING_VALIDATION.value
                )
                
                return CreateCompany(
                    success=True,
                    company=company,
                    message="Empresa creada exitosamente"
                )
        except Exception as e:
            return CreateCompany(success=False, message=f"Error al crear empresa: {str(e)}")


class ValidateCompany(graphene.Mutation):
    """Mutation para validar una empresa."""
    
    class Arguments:
        company_id = graphene.ID(required=True)
        approve = graphene.Boolean(required=True)
        observations = graphene.String()
    
    success = graphene.Boolean()
    company = graphene.Field(CompanyType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, company_id, approve, observations=None):
        user = info.context.user
        if user.role not in ['COORDINADOR', 'ADMINISTRADOR']:
            return ValidateCompany(success=False, message="Sin permisos para validar empresas")
        
        try:
            company = Company.objects.get(id=company_id)
            
            if approve:
                company.status = CompanyStatus.ACTIVE.value
                company.fecha_aprobacion = timezone.now()
                company.aprobado_por = user
                message = "Empresa aprobada exitosamente"
            else:
                company.status = CompanyStatus.SUSPENDED.value
                message = "Empresa rechazada"
            
            if observations:
                company.observaciones = observations
            
            company.save()
            
            return ValidateCompany(
                success=True,
                company=company,
                message=message
            )
        except Company.DoesNotExist:
            return ValidateCompany(success=False, message="Empresa no encontrada")
        except Exception as e:
            return ValidateCompany(success=False, message=f"Error al validar empresa: {str(e)}")


# ===== MUTATIONS PARA PRÁCTICAS =====
class CreatePractice(graphene.Mutation):
    """Mutation para crear una práctica."""
    
    class Arguments:
        input = PracticeInput(required=True)
    
    success = graphene.Boolean()
    practice = graphene.Field(PracticeType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, input):
        user = info.context.user
        
        try:
            with transaction.atomic():
                # Verificar permisos
                if user.role == UserRole.PRACTICANTE.value:
                    # El estudiante puede crear su propia práctica
                    student = getattr(user, 'student_profile', None)
                    if not student or str(student.id) != input.student_id:
                        return CreatePractice(success=False, message="Solo puedes crear tu propia práctica")
                elif user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
                    return CreatePractice(success=False, message="Sin permisos para crear prácticas")
                
                # Obtener objetos relacionados
                student = Student.objects.get(id=input.student_id)
                company = Company.objects.get(id=input.company_id)
                supervisor = None
                if input.supervisor_id:
                    supervisor = Supervisor.objects.get(id=input.supervisor_id)
                
                # Validar elegibilidad del estudiante
                if student.semestre_actual < 6:
                    return CreatePractice(success=False, message="Estudiante debe estar en semestre 6 o superior")
                
                if student.promedio_ponderado < 12.0:
                    return CreatePractice(success=False, message="Estudiante debe tener promedio mínimo de 12.0")
                
                # Crear práctica
                practice = Practice.objects.create(
                    student=student,
                    company=company,
                    supervisor=supervisor,
                    titulo=input.titulo,
                    descripcion=input.descripcion,
                    fecha_inicio=input.fecha_inicio,
                    fecha_fin=input.fecha_fin,
                    horas_requeridas=input.horas_requeridas or 480,
                    status=PracticeStatus.DRAFT.value,
                    creado_por=user
                )
                
                return CreatePractice(
                    success=True,
                    practice=practice,
                    message="Práctica creada exitosamente"
                )
        except (Student.DoesNotExist, Company.DoesNotExist, Supervisor.DoesNotExist):
            return CreatePractice(success=False, message="Objeto relacionado no encontrado")
        except Exception as e:
            return CreatePractice(success=False, message=f"Error al crear práctica: {str(e)}")


class UpdatePracticeStatus(graphene.Mutation):
    """Mutation para actualizar el estado de una práctica."""
    
    class Arguments:
        practice_id = graphene.ID(required=True)
        status = graphene.String(required=True)
        observations = graphene.String()
    
    success = graphene.Boolean()
    practice = graphene.Field(PracticeType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, practice_id, status, observations=None):
        user = info.context.user
        
        try:
            practice = Practice.objects.get(id=practice_id)
            
            # Verificar permisos según el estado y rol
            if status == PracticeStatus.PENDING.value:
                # Solo el estudiante puede enviar a revisión
                if user.role != UserRole.PRACTICANTE.value:
                    return UpdatePracticeStatus(success=False, message="Solo el estudiante puede enviar a revisión")
                if practice.student.user.id != user.id:
                    return UpdatePracticeStatus(success=False, message="Solo puedes modificar tu propia práctica")
            
            elif status in [PracticeStatus.APPROVED.value, PracticeStatus.CANCELLED.value]:
                # Solo coordinadores pueden aprobar/cancelar
                if user.role not in ['COORDINADOR', 'ADMINISTRADOR']:
                    return UpdatePracticeStatus(success=False, message="Sin permisos para aprobar/cancelar prácticas")
            
            elif status == PracticeStatus.IN_PROGRESS.value:
                # El supervisor puede marcar como en progreso
                if user.role == UserRole.SUPERVISOR.value:
                    supervisor = getattr(user, 'supervisor_profile', None)
                    if not supervisor or practice.supervisor.id != supervisor.id:
                        return UpdatePracticeStatus(success=False, message="Solo el supervisor asignado puede modificar")
                elif user.role not in ['COORDINADOR', 'ADMINISTRADOR']:
                    return UpdatePracticeStatus(success=False, message="Sin permisos")
            
            # Actualizar estado
            practice.status = status
            if observations:
                practice.observaciones = observations
            
            # Registrar fecha de aprobación
            if status == PracticeStatus.APPROVED.value:
                practice.fecha_aprobacion = timezone.now()
                practice.aprobado_por = user
            
            practice.save()
            
            return UpdatePracticeStatus(
                success=True,
                practice=practice,
                message=f"Estado actualizado a {status}"
            )
            
        except Practice.DoesNotExist:
            return UpdatePracticeStatus(success=False, message="Práctica no encontrada")
        except Exception as e:
            return UpdatePracticeStatus(success=False, message=f"Error al actualizar estado: {str(e)}")


# ===== MUTATIONS PARA DOCUMENTOS =====
class UploadDocument(graphene.Mutation):
    """Mutation para subir un documento."""
    
    class Arguments:
        input = DocumentInput(required=True)
    
    success = graphene.Boolean()
    document = graphene.Field(DocumentType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, input):
        user = info.context.user
        
        try:
            practice = Practice.objects.get(id=input.practice_id)
            
            # Verificar permisos
            can_upload = False
            if user.role in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
                can_upload = True
            elif user.role == UserRole.PRACTICANTE.value:
                student = getattr(user, 'student_profile', None)
                if student and practice.student.id == student.id:
                    can_upload = True
            elif user.role == UserRole.SUPERVISOR.value:
                supervisor = getattr(user, 'supervisor_profile', None)
                if supervisor and practice.supervisor and practice.supervisor.id == supervisor.id:
                    can_upload = True
            
            if not can_upload:
                return UploadDocument(success=False, message="Sin permisos para subir documentos")
            
            document = Document.objects.create(
                practice=practice,
                tipo=input.tipo,
                nombre=input.nombre,
                descripcion=input.descripcion,
                archivo_url=input.archivo_url,
                subido_por=user
            )
            
            return UploadDocument(
                success=True,
                document=document,
                message="Documento subido exitosamente"
            )
            
        except Practice.DoesNotExist:
            return UploadDocument(success=False, message="Práctica no encontrada")
        except Exception as e:
            return UploadDocument(success=False, message=f"Error al subir documento: {str(e)}")


# ===== MUTATIONS PARA NOTIFICACIONES =====
class MarkNotificationAsRead(graphene.Mutation):
    """Mutation para marcar una notificación como leída."""
    
    class Arguments:
        notification_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    notification = graphene.Field(NotificationType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, notification_id):
        user = info.context.user
        
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.leida = True
            notification.fecha_lectura = timezone.now()
            notification.save()
            
            return MarkNotificationAsRead(
                success=True,
                notification=notification,
                message="Notificación marcada como leída"
            )
            
        except Notification.DoesNotExist:
            return MarkNotificationAsRead(success=False, message="Notificación no encontrada")
        except Exception as e:
            return MarkNotificationAsRead(success=False, message=f"Error: {str(e)}")


# ===== MUTATION PRINCIPAL =====
class Mutation(graphene.ObjectType):
    """Mutations principales del sistema."""
    
    # Usuarios
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    
    # Estudiantes
    create_student = CreateStudent.Field()
    
    # Empresas
    create_company = CreateCompany.Field()
    validate_company = ValidateCompany.Field()
    
    # Prácticas
    create_practice = CreatePractice.Field()
    update_practice_status = UpdatePracticeStatus.Field()
    
    # Documentos
    upload_document = UploadDocument.Field()
    
    # Notificaciones
    mark_notification_as_read = MarkNotificationAsRead.Field()
