"""
Comando para poblar la base de datos con datos de prueba completos.
Demuestra el uso de PostgreSQL, MongoDB y Redis.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.cache import cache
from datetime import datetime, timedelta
import random

from src.adapters.secondary.database.models import (
    Role, Permission, RolePermission, 
    Student, Company, Supervisor, Practice,
    Document, School, Branch, PracticeEvaluation, PracticeStatusHistory
)
from src.domain.enums import (
    UserRole, CompanyStatus, PracticeStatus,
    DocumentStatus
)

User = get_user_model()


class Command(BaseCommand):
    help = "Puebla la base de datos con datos de prueba completos"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpia datos existentes antes de poblar',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🚀 POBLANDO BASE DE DATOS - Sistema PPP UPeU'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        if options['clear']:
            self.clear_data()

        # 1. Crear roles y permisos (PostgreSQL)
        self.create_roles_and_permissions()
        
        # 2. Crear usuarios (PostgreSQL + Redis para cache)
        users = self.create_users()
        
        # 2.1 Crear escuelas profesionales (PostgreSQL)
        schools = self.create_schools(users)
        
        # 2.2 Crear ramas/especialidades (PostgreSQL)
        branches = self.create_branches(schools)
        
        # 3. Crear empresas (PostgreSQL)
        companies = self.create_companies()
        
        # 4. Crear supervisores (PostgreSQL)
        supervisors = self.create_supervisors(users, companies)
        
        # 5. Crear estudiantes (PostgreSQL)
        students = self.create_students(users, schools, branches)
        
        # 6. Crear prácticas (PostgreSQL)
        practices = self.create_practices(students, companies, supervisors, users)
        
        # 7. Crear documentos (PostgreSQL + MongoDB simulado)
        self.create_documents(practices)
        
        # 8. Crear evaluaciones (PostgreSQL)
        self.create_evaluations(practices, supervisors)
        
        # 9. Demostrar uso de Redis cache
        self.demonstrate_cache()
        
        # 10. Estadísticas finales
        self.show_statistics()

    def clear_data(self):
        """Limpia datos de prueba existentes."""
        self.stdout.write(self.style.WARNING('\n🗑️  Limpiando datos existentes...\n'))
        
        with transaction.atomic():
            PracticeStatusHistory.objects.all().delete()
            PracticeEvaluation.objects.all().delete()
            Document.objects.all().delete()
            Practice.objects.all().delete()
            Student.objects.all().delete()
            Supervisor.objects.all().delete()
            Company.objects.all().delete()
            Branch.objects.all().delete()
            School.objects.all().delete()
            RolePermission.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            
        cache.clear()
        self.stdout.write(self.style.SUCCESS('  ✅ Datos limpiados\n'))

    def create_roles_and_permissions(self):
        """Crea roles y permisos básicos."""
        self.stdout.write(self.style.SUCCESS('📋 PASO 1: Creando Roles y Permisos (PostgreSQL)\n'))
        
        roles_data = {
            'ADMINISTRADOR': ['users.*', 'roles.*', 'permissions.*', 'students.*', 
                             'companies.*', 'practices.*', 'reports.*', 'system.*'],
            'COORDINADOR': ['practices.*', 'students.view', 'companies.*', 
                           'supervisors.*', 'reports.*'],
            'SECRETARIA': ['students.*', 'documents.*', 'reports.view'],
            'SUPERVISOR': ['practices.view', 'students.view', 'evaluations.*'],
            'PRACTICANTE': ['profile.*', 'documents.view', 'practices.view']
        }
        
        created_permissions = 0
        created_roles = 0
        
        with transaction.atomic():
            for role_code, permissions in roles_data.items():
                role, created = Role.objects.get_or_create(
                    code=role_code,
                    defaults={
                        'name': role_code.title(),
                        'description': f'Rol de {role_code.lower()}',
                        'is_active': True
                    }
                )
                if created:
                    created_roles += 1
                
                for perm_code in permissions:
                    permission, perm_created = Permission.objects.get_or_create(
                        code=perm_code,
                        defaults={
                            'name': perm_code.replace('.', ' ').title(),
                            'description': f'Permiso para {perm_code}',
                            'is_active': True
                        }
                    )
                    if perm_created:
                        created_permissions += 1
                    
                    RolePermission.objects.get_or_create(
                        role=role,
                        permission=permission
                    )
        
        self.stdout.write(f'  ✅ {created_roles} roles creados')
        self.stdout.write(f'  ✅ {created_permissions} permisos creados\n')

    def create_users(self):
        """Crea usuarios de prueba para cada rol."""
        self.stdout.write(self.style.SUCCESS('👥 PASO 2: Creando Usuarios (PostgreSQL)\n'))
        
        users_data = [
            {'email': 'admin@upeu.edu.pe', 'role': 'ADMINISTRADOR', 'first_name': 'Juan', 'last_name': 'Administrador'},
            {'email': 'coordinador@upeu.edu.pe', 'role': 'COORDINADOR', 'first_name': 'María', 'last_name': 'Coordinadora'},
            {'email': 'secretaria@upeu.edu.pe', 'role': 'SECRETARIA', 'first_name': 'Ana', 'last_name': 'Secretaria'},
            {'email': 'estudiante1@upeu.edu.pe', 'role': 'PRACTICANTE', 'first_name': 'Carlos', 'last_name': 'Pérez'},
            {'email': 'estudiante2@upeu.edu.pe', 'role': 'PRACTICANTE', 'first_name': 'Lucía', 'last_name': 'García'},
            {'email': 'estudiante3@upeu.edu.pe', 'role': 'PRACTICANTE', 'first_name': 'Diego', 'last_name': 'Rodríguez'},
            {'email': 'supervisor1@empresa.com', 'role': 'SUPERVISOR', 'first_name': 'Roberto', 'last_name': 'Supervisor'},
            {'email': 'supervisor2@empresa.com', 'role': 'SUPERVISOR', 'first_name': 'Patricia', 'last_name': 'Jefa'},
        ]
        
        users = {}
        created_count = 0
        
        with transaction.atomic():
            for user_data in users_data:
                user, created = User.objects.get_or_create(
                    email=user_data['email'],
                    defaults={
                        'username': user_data['email'].split('@')[0],
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'role': user_data['role'],
                        'is_active': True,
                        'email_verified': True
                    }
                )
                if created:
                    user.set_password('Test1234')
                    user.save()
                    created_count += 1
                
                users[user_data['role'] + str(len([u for u in users.values() if hasattr(u, 'role') and u.role == user_data['role']]))] = user
        
        self.stdout.write(f'  ✅ {created_count} usuarios creados')
        self.stdout.write(f'  🔑 Password para todos: Test1234\n')
        
        return users

    def create_schools(self, users):
        """Crea escuelas profesionales."""
        self.stdout.write(self.style.SUCCESS('🎓 PASO 2.1: Creando Escuelas Profesionales (PostgreSQL)\n'))
        
        # Obtener coordinador
        coordinador = None
        for user in users.values():
            if hasattr(user, 'role') and user.role == 'COORDINADOR':
                coordinador = user
                break
        
        schools_data = [
            {
                'codigo': 'EP-IS',
                'nombre': 'Ingeniería de Sistemas',
                'facultad': 'Facultad de Ingeniería y Arquitectura',
                'activa': True
            },
            {
                'codigo': 'EP-CC',
                'nombre': 'Ciencias de la Computación',
                'facultad': 'Facultad de Ingeniería y Arquitectura',
                'activa': True
            },
            {
                'codigo': 'EP-SW',
                'nombre': 'Ingeniería de Software',
                'facultad': 'Facultad de Ingeniería y Arquitectura',
                'activa': True
            }
        ]
        
        schools = []
        created_count = 0
        
        with transaction.atomic():
            for school_data in schools_data:
                school, created = School.objects.get_or_create(
                    codigo=school_data['codigo'],
                    defaults={
                        'nombre': school_data['nombre'],
                        'facultad': school_data['facultad'],
                        'coordinador': coordinador,
                        'activa': school_data['activa']
                    }
                )
                if created:
                    created_count += 1
                schools.append(school)
        
        self.stdout.write(f'  ✅ {created_count} escuelas profesionales creadas\n')
        return schools

    def create_branches(self, schools):
        """Crea ramas/especialidades de las escuelas."""
        self.stdout.write(self.style.SUCCESS('🌿 PASO 2.2: Creando Ramas/Especialidades (PostgreSQL)\n'))
        
        branches_data = [
            # Ingeniería de Sistemas
            {'school_index': 0, 'nombre': 'Desarrollo de Software', 'activa': True},
            {'school_index': 0, 'nombre': 'Redes y Comunicaciones', 'activa': True},
            {'school_index': 0, 'nombre': 'Sistemas de Información', 'activa': True},
            
            # Ciencias de la Computación
            {'school_index': 1, 'nombre': 'Inteligencia Artificial', 'activa': True},
            {'school_index': 1, 'nombre': 'Ciencia de Datos', 'activa': True},
            
            # Ingeniería de Software
            {'school_index': 2, 'nombre': 'Desarrollo Web', 'activa': True},
            {'school_index': 2, 'nombre': 'Desarrollo Móvil', 'activa': True},
        ]
        
        branches = []
        created_count = 0
        
        with transaction.atomic():
            for branch_data in branches_data:
                school = schools[branch_data['school_index']]
                branch, created = Branch.objects.get_or_create(
                    school=school,
                    nombre=branch_data['nombre'],
                    defaults={
                        'activa': branch_data['activa']
                    }
                )
                if created:
                    created_count += 1
                branches.append(branch)
        
        self.stdout.write(f'  ✅ {created_count} ramas/especialidades creadas\n')
        return branches

    def create_companies(self):
        """Crea empresas de prueba."""
        self.stdout.write(self.style.SUCCESS('🏢 PASO 3: Creando Empresas (PostgreSQL)\n'))
        
        companies_data = [
            {
                'ruc': '20123456789',
                'razon_social': 'Tecnología y Soluciones S.A.C.',
                'nombre_comercial': 'TechSol',
                'sector_economico': 'TECNOLOGIA',
                'tamaño_empresa': 'MEDIANA',
                'direccion': 'Av. Tecnológica 123, Lima',
                'telefono': '987654321',
                'email': 'contacto@techsol.com'
            },
            {
                'ruc': '20987654321',
                'razon_social': 'Servicios Profesionales E.I.R.L.',
                'nombre_comercial': 'ServPro',
                'sector_economico': 'SERVICIOS',
                'tamaño_empresa': 'PEQUEÑA',
                'direccion': 'Jr. Profesionales 456, Lima',
                'telefono': '912345678',
                'email': 'info@servpro.com'
            },
            {
                'ruc': '20555666777',
                'razon_social': 'Desarrollo Software Perú S.A.',
                'nombre_comercial': 'DevSoft Perú',
                'sector_economico': 'TECNOLOGIA',
                'tamaño_empresa': 'GRANDE',
                'direccion': 'Av. República 789, Lima',
                'telefono': '998877665',
                'email': 'rrhh@devsoftperu.com'
            }
        ]
        
        companies = []
        created_count = 0
        
        with transaction.atomic():
            for company_data in companies_data:
                company, created = Company.objects.get_or_create(
                    ruc=company_data['ruc'],
                    defaults={
                        **company_data,
                        'status': CompanyStatus.ACTIVE.value,
                        'is_validated': True
                    }
                )
                if created:
                    created_count += 1
                companies.append(company)
        
        self.stdout.write(f'  ✅ {created_count} empresas creadas\n')
        return companies

    def create_supervisors(self, users, companies):
        """Crea supervisores de empresa."""
        self.stdout.write(self.style.SUCCESS('👔 PASO 4: Creando Supervisores (PostgreSQL)\n'))
        
        supervisors_data = [
            {
                'user_email': 'supervisor1@empresa.com',
                'company_index': 0,
                'documento_tipo': 'DNI',
                'documento_numero': '12345678',
                'cargo': 'Jefe de Desarrollo',
                'telefono': '987654321',
                'años_experiencia': 8
            },
            {
                'user_email': 'supervisor2@empresa.com',
                'company_index': 1,
                'documento_tipo': 'DNI',
                'documento_numero': '87654321',
                'cargo': 'Gerente de Proyectos',
                'telefono': '912345678',
                'años_experiencia': 12
            }
        ]
        
        supervisors = []
        created_count = 0
        
        with transaction.atomic():
            for sup_data in supervisors_data:
                user = User.objects.get(email=sup_data['user_email'])
                company = companies[sup_data['company_index']]
                
                supervisor, created = Supervisor.objects.get_or_create(
                    user=user,
                    defaults={
                        'company': company,
                        'documento_tipo': sup_data['documento_tipo'],
                        'documento_numero': sup_data['documento_numero'],
                        'cargo': sup_data['cargo'],
                        'telefono': sup_data['telefono'],
                        'años_experiencia': sup_data['años_experiencia']
                    }
                )
                if created:
                    created_count += 1
                supervisors.append(supervisor)
        
        self.stdout.write(f'  ✅ {created_count} supervisores creados\n')
        return supervisors

    def create_students(self, users, schools, branches):
        """Crea estudiantes de prueba."""
        self.stdout.write(self.style.SUCCESS('🎓 PASO 5: Creando Estudiantes (PostgreSQL)\n'))
        
        students_data = [
            {
                'user_email': 'estudiante1@upeu.edu.pe',
                'codigo_estudiante': '2020001234',
                'documento_tipo': 'DNI',
                'documento_numero': '71234567',
                'telefono': '987111222',
                'carrera': 'INGENIERIA_SISTEMAS',
                'semestre_actual': 8,
                'promedio': 15.5,
                'school_index': 0,  # Ingeniería de Sistemas
                'branch_index': 0,  # Desarrollo de Software
                'estado_academico': 'REGULAR'
            },
            {
                'user_email': 'estudiante2@upeu.edu.pe',
                'codigo_estudiante': '2020005678',
                'documento_tipo': 'DNI',
                'documento_numero': '71234568',
                'telefono': '987333444',
                'carrera': 'INGENIERIA_SISTEMAS',
                'semestre_actual': 9,
                'promedio': 16.2,
                'school_index': 0,  # Ingeniería de Sistemas
                'branch_index': 1,  # Redes y Comunicaciones
                'estado_academico': 'REGULAR'
            },
            {
                'user_email': 'estudiante3@upeu.edu.pe',
                'codigo_estudiante': '2019009876',
                'documento_tipo': 'DNI',
                'documento_numero': '71234569',
                'telefono': '987555666',
                'carrera': 'INGENIERIA_SISTEMAS',
                'semestre_actual': 10,
                'promedio': 14.8,
                'school_index': 1,  # Ciencias de la Computación
                'branch_index': 3,  # Inteligencia Artificial
                'estado_academico': 'REGULAR'
            }
        ]
        
        students = []
        created_count = 0
        
        with transaction.atomic():
            for student_data in students_data:
                user = User.objects.get(email=student_data['user_email'])
                school = schools[student_data['school_index']]
                branch = branches[student_data['branch_index']]
                
                student, created = Student.objects.get_or_create(
                    user=user,
                    defaults={
                        'codigo_estudiante': student_data['codigo_estudiante'],
                        'documento_tipo': student_data['documento_tipo'],
                        'documento_numero': student_data['documento_numero'],
                        'telefono': student_data['telefono'],
                        'carrera': student_data['carrera'],
                        'semestre_actual': student_data['semestre_actual'],
                        'promedio': student_data['promedio'],
                        'school': school,
                        'branch': branch,
                        'estado_academico': student_data.get('estado_academico', 'REGULAR')
                    }
                )
                if created:
                    created_count += 1
                students.append(student)
        
        self.stdout.write(f'  ✅ {created_count} estudiantes creados\n')
        return students

    def create_practices(self, students, companies, supervisors, users):
        """Crea prácticas de prueba."""
        self.stdout.write(self.style.SUCCESS('📝 PASO 6: Creando Prácticas (PostgreSQL)\n'))
        
        # Obtener coordinador y secretaria
        coordinador = None
        secretaria = None
        for user in users.values():
            if hasattr(user, 'role') and user.role == 'COORDINADOR':
                coordinador = user
            elif hasattr(user, 'role') and user.role == 'SECRETARIA':
                secretaria = user
        
        practices_data = [
            {
                'student_index': 0,
                'company_index': 0,
                'supervisor_index': 0,
                'titulo': 'Desarrollo de Sistema Web',
                'descripcion': 'Desarrollo de aplicación web con Django y React',
                'horas_requeridas': 480,
                'status': PracticeStatus.IN_PROGRESS.value,
                'fecha_inicio': datetime.now() - timedelta(days=30),
                'fecha_fin': datetime.now() + timedelta(days=60),
                'remunerada': True,
                'monto_remuneracion': 1000.00
            },
            {
                'student_index': 1,
                'company_index': 1,
                'supervisor_index': 1,
                'titulo': 'Soporte Técnico IT',
                'descripcion': 'Soporte técnico y mantenimiento de sistemas',
                'horas_requeridas': 480,
                'status': PracticeStatus.APPROVED.value,
                'fecha_inicio': datetime.now() + timedelta(days=7),
                'fecha_fin': datetime.now() + timedelta(days=97),
                'remunerada': False,
                'monto_remuneracion': None
            },
            {
                'student_index': 2,
                'company_index': 2,
                'supervisor_index': 0,
                'titulo': 'Análisis de Datos',
                'descripcion': 'Análisis de datos con Python y visualización',
                'horas_requeridas': 480,
                'status': PracticeStatus.PENDING.value,
                'fecha_inicio': None,
                'fecha_fin': None,
                'remunerada': True,
                'monto_remuneracion': 800.00
            }
        ]
        
        practices = []
        created_count = 0
        
        with transaction.atomic():
            for practice_data in practices_data:
                student = students[practice_data['student_index']]
                company = companies[practice_data['company_index']]
                supervisor = supervisors[practice_data['supervisor_index']]
                
                practice, created = Practice.objects.get_or_create(
                    student=student,
                    titulo=practice_data['titulo'],
                    defaults={
                        'company': company,
                        'supervisor': supervisor,
                        'coordinador': coordinador,
                        'secretaria': secretaria,
                        'descripcion': practice_data['descripcion'],
                        'horas_requeridas': practice_data['horas_requeridas'],
                        'horas_completadas': random.randint(0, 200) if practice_data['status'] == PracticeStatus.IN_PROGRESS.value else 0,
                        'remunerada': practice_data.get('remunerada', False),
                        'monto_remuneracion': practice_data.get('monto_remuneracion'),
                        'status': practice_data['status'],
                        'fecha_inicio': practice_data['fecha_inicio'],
                        'fecha_fin': practice_data['fecha_fin']
                    }
                )
                if created:
                    created_count += 1
                practices.append(practice)
        
        self.stdout.write(f'  ✅ {created_count} prácticas creadas\n')
        return practices

    def create_documents(self, practices):
        """Crea documentos de prueba (PostgreSQL + MongoDB simulado)."""
        self.stdout.write(self.style.SUCCESS('📄 PASO 7: Creando Documentos (PostgreSQL + MongoDB)\n'))
        
        documents_data = [
            {
                'practice_index': 0,
                'titulo': 'Plan de Práctica',
                'descripcion': 'Plan detallado de actividades',
                'tipo_documento': 'PLAN',
                'tamaño_bytes': 1024000
            },
            {
                'practice_index': 0,
                'titulo': 'Informe Mensual - Mes 1',
                'descripcion': 'Reporte de avances del primer mes',
                'tipo_documento': 'INFORME',
                'tamaño_bytes': 512000
            },
            {
                'practice_index': 1,
                'titulo': 'Carta de Presentación',
                'descripcion': 'Carta de presentación a la empresa',
                'tipo_documento': 'CARTA',
                'tamaño_bytes': 256000
            }
        ]
        
        created_count = 0
        
        with transaction.atomic():
            for doc_data in documents_data:
                practice = practices[doc_data['practice_index']]
                
                document, created = Document.objects.get_or_create(
                    practice=practice,
                    titulo=doc_data['titulo'],
                    defaults={
                        'descripcion': doc_data['descripcion'],
                        'tipo_documento': doc_data['tipo_documento'],
                        'archivo_nombre': f"{doc_data['titulo']}.pdf",
                        'archivo_url': f"/media/documents/{practice.id}/{doc_data['titulo']}.pdf",
                        'tamaño_bytes': doc_data['tamaño_bytes'],
                        'status': DocumentStatus.APPROVED.value
                    }
                )
                if created:
                    created_count += 1
        
        self.stdout.write(f'  ✅ {created_count} documentos creados')
        self.stdout.write(f'  💾 En producción, archivos binarios se guardan en MongoDB\n')

    def create_evaluations(self, practices, supervisors):
        """Crea evaluaciones de prácticas."""
        self.stdout.write(self.style.SUCCESS('⭐ PASO 8: Creando Evaluaciones (PostgreSQL)\n'))
        
        evaluations_data = [
            {
                'practice_index': 0,
                'supervisor_index': 0,
                'tipo_evaluador': 'SUPERVISOR',
                'periodo_evaluacion': 'MENSUAL_1',
                'puntaje_total': 85.0,
                'comentarios': 'Excelente desempeño, muy proactivo y responsable',
                'recomendaciones': 'Continuar con el mismo nivel de dedicación',
                'fortalezas': 'Buena capacidad de aprendizaje, trabajo en equipo',
                'areas_mejora': 'Mejorar gestión del tiempo'
            },
            {
                'practice_index': 0,
                'supervisor_index': 0,
                'tipo_evaluador': 'SUPERVISOR',
                'periodo_evaluacion': 'FINAL',
                'puntaje_total': 90.0,
                'comentarios': 'Cumplió con todos los objetivos planteados',
                'recomendaciones': 'Apto para continuar en el área',
                'fortalezas': 'Dominio técnico, iniciativa propia',
                'areas_mejora': 'Ninguna observación'
            }
        ]
        
        created_count = 0
        
        with transaction.atomic():
            for eval_data in evaluations_data:
                practice = practices[eval_data['practice_index']]
                supervisor = supervisors[eval_data['supervisor_index']]
                
                evaluation, created = PracticeEvaluation.objects.get_or_create(
                    practice=practice,
                    periodo_evaluacion=eval_data['periodo_evaluacion'],
                    tipo_evaluador=eval_data['tipo_evaluador'],
                    defaults={
                        'evaluator': supervisor.user,
                        'puntaje_total': eval_data['puntaje_total'],
                        'comentarios': eval_data['comentarios'],
                        'recomendaciones': eval_data.get('recomendaciones', ''),
                        'fortalezas': eval_data.get('fortalezas', ''),
                        'areas_mejora': eval_data.get('areas_mejora', ''),
                        'status': 'APPROVED'
                    }
                )
                if created:
                    created_count += 1
        
        self.stdout.write(f'  ✅ {created_count} evaluaciones creadas\n')

    def demonstrate_cache(self):
        """Demuestra el uso de Redis cache."""
        self.stdout.write(self.style.SUCCESS('🚀 PASO 9: Demostrando Cache Redis\n'))
        
        # Cachear contadores
        total_users = User.objects.count()
        total_students = Student.objects.count()
        total_companies = Company.objects.count()
        total_practices = Practice.objects.count()
        
        # Guardar en cache con TTL de 5 minutos
        cache.set('stats:total_users', total_users, 300)
        cache.set('stats:total_students', total_students, 300)
        cache.set('stats:total_companies', total_companies, 300)
        cache.set('stats:total_practices', total_practices, 300)
        
        self.stdout.write(f'  ✅ Estadísticas cacheadas en Redis (TTL: 5 min)')
        self.stdout.write(f'  📊 Total usuarios: {total_users}')
        self.stdout.write(f'  🎓 Total estudiantes: {total_students}')
        self.stdout.write(f'  🏢 Total empresas: {total_companies}')
        self.stdout.write(f'  📝 Total prácticas: {total_practices}\n')

    def show_statistics(self):
        """Muestra estadísticas finales."""
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('📊 ESTADÍSTICAS FINALES - BASES DE DATOS\n'))
        
        # PostgreSQL
        self.stdout.write(self.style.SUCCESS('🐘 PostgreSQL (Base de Datos Principal):'))
        stats = {
            'Usuarios': User.objects.count(),
            'Roles': Role.objects.count(),
            'Permisos': Permission.objects.count(),
            'Escuelas': School.objects.count(),
            'Ramas': Branch.objects.count(),
            'Estudiantes': Student.objects.count(),
            'Empresas': Company.objects.count(),
            'Supervisores': Supervisor.objects.count(),
            'Prácticas': Practice.objects.count(),
            'Documentos': Document.objects.count(),
            'Evaluaciones': PracticeEvaluation.objects.count(),
            'Historial Estados': PracticeStatusHistory.objects.count()
        }
        
        for key, value in stats.items():
            self.stdout.write(f'  • {key}: {value}')
        
        # Redis
        self.stdout.write(self.style.SUCCESS('\n📦 Redis (Cache):'))
        cached_keys = ['stats:total_users', 'stats:total_students', 
                      'stats:total_companies', 'stats:total_practices']
        for key in cached_keys:
            value = cache.get(key)
            if value is not None:
                self.stdout.write(f'  • {key}: {value} (cached)')
        
        # MongoDB (simulado)
        self.stdout.write(self.style.SUCCESS('\n🍃 MongoDB (Documentos - Simulado):'))
        self.stdout.write(f'  • Archivos binarios: {Document.objects.count()} registros')
        self.stdout.write(f'  • Espacio estimado: {Document.objects.count() * 500}KB')
        self.stdout.write(f'  • En producción: Archivos PDF, imágenes, etc.')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('✅ BASE DE DATOS POBLADA EXITOSAMENTE\n'))
        
        # Información de acceso
        self.stdout.write(self.style.WARNING('🔑 CREDENCIALES DE PRUEBA:'))
        self.stdout.write('  • Admin: admin@upeu.edu.pe / Test1234')
        self.stdout.write('  • Coordinador: coordinador@upeu.edu.pe / Test1234')
        self.stdout.write('  • Secretaria: secretaria@upeu.edu.pe / Test1234')
        self.stdout.write('  • Estudiante: estudiante1@upeu.edu.pe / Test1234')
        self.stdout.write('  • Supervisor: supervisor1@empresa.com / Test1234\n')
        
        self.stdout.write(self.style.WARNING('🌐 PROBAR APIS:'))
        self.stdout.write('  • REST API: http://localhost:8000/api/')
        self.stdout.write('  • GraphQL: http://localhost:8000/graphql/')
        self.stdout.write('  • Swagger: http://localhost:8000/api/docs/')
        self.stdout.write('  • Admin: http://localhost:8000/admin/\n')
        
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
