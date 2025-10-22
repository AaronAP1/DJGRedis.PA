"""
Dashboard ViewSets para estadísticas y métricas en tiempo real.

Este módulo implementa endpoints especializados para dashboards según rol:
- Coordinador: Vista completa del sistema
- Estudiante: Progreso personal
- Supervisor: Prácticas asignadas
- Secretaría: Métricas administrativas

Arquitectura: Hexagonal (Adaptador Primario)
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q, Sum, Max, Min, F
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from drf_spectacular.utils import (
    extend_schema, 
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes

from src.domain.entities import (
    User, Student, Company, Supervisor, Practice, 
    Document, Notification
)
from src.domain.enums import UserRole
from src.infrastructure.security.permissions import (
    IsCoordinador, IsPracticante, IsSupervisor, 
    IsSecretaria, IsAdministrador
)


@extend_schema_view(
    general_dashboard=extend_schema(
        tags=['Dashboards'],
        summary='Dashboard General del Sistema',
        description='''
        Dashboard completo con todas las métricas del sistema.
        
        **Permisos requeridos**: COORDINADOR o ADMINISTRADOR
        
        **Retorna**:
        - Estadísticas de prácticas (total, activas, completadas, pendientes)
        - Estadísticas de estudiantes (total, por carrera, con prácticas)
        - Estadísticas de empresas (total, validadas, por sector)
        - Estadísticas de documentos (pendientes, aprobados, rechazados)
        - Notificaciones pendientes
        - Actividades recientes del sistema
        ''',
        responses={
            200: OpenApiResponse(
                description='Dashboard general exitoso',
                response=OpenApiTypes.OBJECT,
            ),
            403: OpenApiResponse(description='Sin permisos de coordinador/admin'),
        },
    ),
)
class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para dashboards y estadísticas del sistema.
    
    Proporciona endpoints especializados para cada rol con métricas en tiempo real:
    
    **Dashboards disponibles**:
    - `general`: Vista completa del sistema (Coordinador/Admin)
    - `student`: Dashboard personal del estudiante
    - `supervisor`: Vista de prácticas asignadas
    - `secretary`: Métricas administrativas
    - `statistics`: Estadísticas avanzadas con filtros
    - `charts`: Datos formateados para gráficos (Chart.js)
    
    **Características**:
    - Datos en tiempo real
    - Optimización con agregaciones Django ORM
    - Caché recomendado para producción
    - Compatible con Chart.js, Recharts, ApexCharts
    """
    
    permission_classes = [IsAuthenticated]

    # ========================================================================
    # Dashboard General (Coordinador/Administrador)
    # ========================================================================

    @extend_schema(
        tags=['Dashboards'],
        summary='Dashboard General (Coordinador/Admin)',
        description='''
        Dashboard principal con vista completa del sistema.
        
        Requiere rol de **COORDINADOR** o **ADMINISTRADOR**.
        
        Incluye:
        - 📊 Estadísticas de prácticas (total, por estado)
        - 👨‍🎓 Estadísticas de estudiantes (total, por carrera)
        - 🏢 Estadísticas de empresas (validadas, por sector)
        - 📄 Estadísticas de documentos (pendientes de validación)
        - 🔔 Notificaciones sin leer
        - 📋 Últimas 10 actividades del sistema
        ''',
        responses={
            200: OpenApiResponse(
                description='Dashboard exitoso',
                examples=[
                    OpenApiExample(
                        'Dashboard Ejemplo',
                        value={
                            'success': True,
                            'data': {
                                'practices': {
                                    'total': 120,
                                    'active': 45,
                                    'completed': 60,
                                    'pending_approval': 8,
                                },
                                'students': {
                                    'total': 250,
                                    'with_practice': 120,
                                    'by_career': {
                                        'Ingeniería de Sistemas': 80,
                                        'Ingeniería Civil': 40,
                                    },
                                },
                                'companies': {
                                    'total': 35,
                                    'validated': 30,
                                    'by_sector': {
                                        'Tecnología': 15,
                                        'Construcción': 10,
                                    },
                                },
                            },
                        },
                    ),
                ],
            ),
            403: OpenApiResponse(description='Sin permisos de coordinador/admin'),
        },
    )
    @action(
        detail=False, 
        methods=['get'],
        permission_classes=[IsAuthenticated, IsCoordinador | IsAdministrador],
        url_path='general'
    )
    def general_dashboard(self, request):
        """
        Dashboard general del sistema con todas las métricas.
        
        GET /api/v2/dashboards/general/
        
        Requiere: COORDINADOR o ADMINISTRADOR
        
        Returns:
            - practices: Estadísticas de prácticas
            - students: Estadísticas de estudiantes
            - companies: Estadísticas de empresas
            - documents: Estadísticas de documentos
            - notifications: Notificaciones pendientes
            - recent_activities: Actividades recientes
        """
        try:
            # Prácticas
            practices_stats = self._get_practices_statistics()
            
            # Estudiantes
            students_stats = self._get_students_statistics()
            
            # Empresas
            companies_stats = self._get_companies_statistics()
            
            # Documentos
            documents_stats = self._get_documents_statistics()
            
            # Notificaciones pendientes
            notifications_count = Notification.objects.filter(
                is_read=False
            ).count()
            
            # Actividades recientes (últimas 10)
            recent_activities = self._get_recent_activities(limit=10)
            
            return Response({
                'success': True,
                'data': {
                    'practices': practices_stats,
                    'students': students_stats,
                    'companies': companies_stats,
                    'documents': documents_stats,
                    'notifications': {
                        'unread_count': notifications_count
                    },
                    'recent_activities': recent_activities,
                    'generated_at': timezone.now().isoformat()
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error al obtener dashboard general: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ========================================================================
    # Dashboard Estudiante
    # ========================================================================

    @extend_schema(
        tags=['Dashboards'],
        summary='Dashboard del Estudiante',
        description='''
        Dashboard personalizado para estudiantes con información de sus prácticas.
        
        Requiere rol de **PRACTICANTE**.
        
        Incluye:
        - 👤 Perfil del estudiante (código, carrera, semestre, promedio)
        - 📋 Práctica actual (en progreso o pendiente)
        - 📊 Progreso de la práctica (porcentaje completado)
        - 📄 Documentos pendientes de entrega
        - 🔔 Notificaciones no leídas
        - ⏱️ Resumen de horas trabajadas
        ''',
        responses={
            200: OpenApiResponse(
                description='Dashboard del estudiante',
                examples=[
                    OpenApiExample(
                        'Dashboard Estudiante',
                        value={
                            'success': True,
                            'data': {
                                'profile': {
                                    'codigo': '2020123456',
                                    'carrera': 'Ingeniería de Sistemas',
                                    'semestre': 8,
                                    'promedio': 14.5,
                                    'estado': 'ACTIVE',
                                    'elegible_practicas': True,
                                },
                                'current_practice': {
                                    'id': 'uuid',
                                    'titulo': 'Desarrollo Web',
                                    'company': {'id': 'uuid', 'razon_social': 'Tech Corp'},
                                    'estado': 'IN_PROGRESS',
                                    'fecha_inicio': '2024-01-15',
                                },
                                'practice_progress': {
                                    'horas_completadas': 240,
                                    'horas_totales': 480,
                                    'porcentaje': 50.0,
                                },
                                'pending_documents': 2,
                                'notifications': {'unread_count': 5},
                            },
                        },
                    ),
                ],
            ),
            403: OpenApiResponse(description='Sin permisos de practicante'),
            404: OpenApiResponse(description='Perfil de estudiante no encontrado'),
        },
    )
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, IsPracticante],
        url_path='student'
    )
    def student_dashboard(self, request):
        """
        Dashboard personalizado para estudiantes.
        
        GET /api/v2/dashboards/student/
        
        Requiere: PRACTICANTE
        
        Returns:
            - profile: Información del perfil
            - current_practice: Práctica actual
            - practice_progress: Progreso de práctica
            - pending_documents: Documentos pendientes
            - notifications: Notificaciones no leídas
            - hours_summary: Resumen de horas
        """
        try:
            user = request.user
            
            # Obtener perfil de estudiante
            try:
                student = Student.objects.select_related('user').get(user=user)
            except Student.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Perfil de estudiante no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Información del perfil
            profile_data = {
                'codigo': student.codigo_estudiante,
                'carrera': student.escuela_profesional,
                'semestre': student.semestre_actual,
                'promedio': float(student.promedio_ponderado),
                'estado': student.estado,
                'elegible_practicas': student.is_eligible_for_practice()
            }
            
            # Práctica actual (en progreso)
            current_practice = Practice.objects.filter(
                student=student,
                estado__in=['PENDING', 'APPROVED', 'IN_PROGRESS']
            ).select_related('company', 'supervisor').first()
            
            current_practice_data = None
            practice_progress = None
            hours_summary = None
            
            if current_practice:
                current_practice_data = {
                    'id': current_practice.id,
                    'titulo': current_practice.titulo,
                    'company': {
                        'id': current_practice.company.id,
                        'razon_social': current_practice.company.razon_social
                    },
                    'supervisor': {
                        'id': current_practice.supervisor.id,
                        'nombre': current_practice.supervisor.user.get_full_name()
                    } if current_practice.supervisor else None,
                    'estado': current_practice.estado,
                    'fecha_inicio': current_practice.fecha_inicio.isoformat() if current_practice.fecha_inicio else None,
                    'fecha_fin': current_practice.fecha_fin.isoformat() if current_practice.fecha_fin else None,
                    'horas_totales': current_practice.horas_totales,
                    'horas_completadas': current_practice.horas_completadas or 0
                }
                
                # Progreso de la práctica
                if current_practice.horas_totales > 0:
                    horas_completadas = current_practice.horas_completadas or 0
                    porcentaje_completado = (horas_completadas / current_practice.horas_totales) * 100
                    
                    practice_progress = {
                        'horas_completadas': horas_completadas,
                        'horas_totales': current_practice.horas_totales,
                        'horas_restantes': current_practice.horas_totales - horas_completadas,
                        'porcentaje_completado': round(porcentaje_completado, 2)
                    }
                    
                    # Resumen de horas (comentado temporalmente - PracticeHours no implementado)
                    # hours_by_month = PracticeHours.objects.filter(
                    #     practice=current_practice
                    # ).annotate(
                    #     month=TruncMonth('fecha')
                    # ).values('month').annotate(
                    #     total_horas=Sum('horas')
                    # ).order_by('month')
                    
                    hours_summary = {
                        'horas_completadas': horas_completadas,
                        'horas_totales': current_practice.horas_totales,
                        'porcentaje': round(porcentaje_completado, 2)
                        # 'by_month': [],  # Deshabilitado hasta implementar PracticeHours
                        # 'promedio_semanal': 0
                    }
            
            # Documentos pendientes
            pending_documents = Document.objects.filter(
                practice__student=student,
                estado='PENDING'
            ).count()
            
            # Notificaciones no leídas
            unread_notifications = Notification.objects.filter(
                user=user,
                is_read=False
            ).order_by('-created_at')[:5]
            
            notifications_data = [
                {
                    'id': notif.id,
                    'tipo': notif.tipo,
                    'mensaje': notif.mensaje,
                    'created_at': notif.created_at.isoformat()
                }
                for notif in unread_notifications
            ]
            
            return Response({
                'success': True,
                'data': {
                    'profile': profile_data,
                    'current_practice': current_practice_data,
                    'practice_progress': practice_progress,
                    'pending_documents': pending_documents,
                    'notifications': {
                        'unread_count': unread_notifications.count(),
                        'recent': notifications_data
                    },
                    'hours_summary': hours_summary,
                    'generated_at': timezone.now().isoformat()
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error al obtener dashboard de estudiante: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ========================================================================
    # Dashboard Supervisor
    # ========================================================================

    @extend_schema(
        tags=['Dashboards'],
        summary='Dashboard del Supervisor',
        description='''
        Dashboard para supervisores de empresa con gestión de practicantes.
        
        Requiere rol de **SUPERVISOR**.
        
        Incluye:
        - 👤 Perfil del supervisor (cargo, empresa)
        - 👨‍🎓 Prácticas asignadas (estudiantes a cargo)
        - ✅ Evaluaciones pendientes
        - 🏢 Información de la empresa
        - 📊 Rendimiento de estudiantes supervisados
        - 📄 Documentos pendientes de validación
        ''',
        responses={
            200: OpenApiResponse(
                description='Dashboard del supervisor',
                examples=[
                    OpenApiExample(
                        'Dashboard Supervisor',
                        value={
                            'success': True,
                            'data': {
                                'profile': {
                                    'nombre_completo': 'Juan Pérez',
                                    'cargo': 'Jefe de Desarrollo',
                                    'email': 'juan@techcorp.com',
                                },
                                'company_info': {
                                    'razon_social': 'Tech Corp SAC',
                                    'ruc': '20123456789',
                                    'sector': 'Tecnología',
                                },
                                'assigned_practices': {
                                    'total': 5,
                                    'activas': 3,
                                    'completadas': 2,
                                },
                                'pending_evaluations': 2,
                                'students_performance': [
                                    {'student': 'María García', 'progress': 75.0},
                                ],
                            },
                        },
                    ),
                ],
            ),
            403: OpenApiResponse(description='Sin permisos de supervisor'),
            404: OpenApiResponse(description='Perfil de supervisor no encontrado'),
        },
    )
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, IsSupervisor],
        url_path='supervisor'
    )
    def supervisor_dashboard(self, request):
        """
        Dashboard personalizado para supervisores.
        
        GET /api/v2/dashboards/supervisor/
        
        Requiere: SUPERVISOR
        
        Returns:
            - profile: Información del perfil
            - assigned_practices: Prácticas asignadas
            - pending_evaluations: Evaluaciones pendientes
            - company_info: Información de la empresa
            - students_performance: Rendimiento de estudiantes
        """
        try:
            user = request.user
            
            # Obtener perfil de supervisor
            try:
                supervisor = Supervisor.objects.select_related(
                    'user', 'company'
                ).get(user=user)
            except Supervisor.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Perfil de supervisor no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Información del perfil
            profile_data = {
                'nombre': user.get_full_name(),
                'cargo': supervisor.cargo,
                'email': user.email,
                'telefono': supervisor.telefono,
                'company': {
                    'id': supervisor.company.id,
                    'razon_social': supervisor.company.razon_social,
                    'sector': supervisor.company.sector_economico
                }
            }
            
            # Prácticas asignadas
            assigned_practices = Practice.objects.filter(
                supervisor=supervisor
            ).select_related('student__user', 'company').order_by('-fecha_inicio')
            
            # Estadísticas de prácticas
            practices_by_status = assigned_practices.values('estado').annotate(
                count=Count('id')
            )
            
            practices_stats = {
                'total': assigned_practices.count(),
                'by_status': {item['estado']: item['count'] for item in practices_by_status}
            }
            
            # Prácticas activas
            active_practices = assigned_practices.filter(
                estado='IN_PROGRESS'
            )[:10]
            
            active_practices_data = [
                {
                    'id': practice.id,
                    'titulo': practice.titulo,
                    'student': {
                        'id': practice.student.id,
                        'nombre': practice.student.user.get_full_name(),
                        'codigo': practice.student.codigo_estudiante
                    },
                    'fecha_inicio': practice.fecha_inicio.isoformat() if practice.fecha_inicio else None,
                    'horas_completadas': practice.horas_completadas or 0,
                    'horas_totales': practice.horas_totales,
                    'progreso': round((practice.horas_completadas or 0) / practice.horas_totales * 100, 2) if practice.horas_totales > 0 else 0
                }
                for practice in active_practices
            ]
            
            # Evaluaciones pendientes (documentos pendientes de aprobar)
            pending_evaluations = Document.objects.filter(
                practice__supervisor=supervisor,
                estado='PENDING'
            ).select_related('practice__student__user').count()
            
            # Rendimiento de estudiantes
            students_performance = self._get_students_performance_for_supervisor(supervisor)
            
            return Response({
                'success': True,
                'data': {
                    'profile': profile_data,
                    'practices_statistics': practices_stats,
                    'active_practices': active_practices_data,
                    'pending_evaluations': pending_evaluations,
                    'students_performance': students_performance,
                    'generated_at': timezone.now().isoformat()
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error al obtener dashboard de supervisor: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ========================================================================
    # Dashboard Secretaría
    # ========================================================================

    @extend_schema(
        tags=['Dashboards'],
        summary='Dashboard de Secretaría',
        description='''
        Dashboard administrativo para personal de secretaría.
        
        Requiere rol de **SECRETARIA**.
        
        Incluye:
        - ✅ Validaciones pendientes (empresas, documentos)
        - 📝 Registros recientes (últimas 24 horas)
        - 📄 Estado de documentos por tipo
        - 📊 Estadísticas rápidas del sistema
        - 🔔 Tareas administrativas pendientes
        ''',
        responses={
            200: OpenApiResponse(
                description='Dashboard de secretaría',
                examples=[
                    OpenApiExample(
                        'Dashboard Secretaría',
                        value={
                            'success': True,
                            'data': {
                                'pending_validations': {
                                    'companies': 3,
                                    'documents': 8,
                                    'total': 11,
                                },
                                'recent_registrations': {
                                    'students': 5,
                                    'companies': 2,
                                    'practices': 4,
                                },
                                'documents_status': {
                                    'PENDING': 8,
                                    'APPROVED': 45,
                                    'REJECTED': 2,
                                },
                                'quick_stats': {
                                    'total_students': 250,
                                    'total_companies': 35,
                                    'active_practices': 45,
                                },
                            },
                        },
                    ),
                ],
            ),
            403: OpenApiResponse(description='Sin permisos de secretaría'),
        },
    )
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, IsSecretaria],
        url_path='secretary'
    )
    def secretary_dashboard(self, request):
        """
        Dashboard para personal administrativo (secretaría).
        
        GET /api/v2/dashboards/secretary/
        
        Requiere: SECRETARIA
        
        Returns:
            - pending_validations: Validaciones pendientes
            - recent_registrations: Registros recientes
            - documents_status: Estado de documentos
            - quick_stats: Estadísticas rápidas
        """
        try:
            # Validaciones pendientes
            pending_companies = Company.objects.filter(
                validated=False
            ).count()
            
            pending_documents = Document.objects.filter(
                estado='PENDING'
            ).count()
            
            pending_practices = Practice.objects.filter(
                estado='PENDING'
            ).count()
            
            # Registros recientes (últimos 7 días)
            seven_days_ago = timezone.now() - timedelta(days=7)
            
            recent_students = Student.objects.filter(
                user__date_joined__gte=seven_days_ago
            ).count()
            
            recent_companies = Company.objects.filter(
                fecha_registro__gte=seven_days_ago
            ).count()
            
            recent_practices = Practice.objects.filter(
                fecha_registro__gte=seven_days_ago
            ).count()
            
            # Estado de documentos
            documents_by_status = Document.objects.values('estado').annotate(
                count=Count('id')
            )
            
            documents_status = {
                item['estado']: item['count'] 
                for item in documents_by_status
            }
            
            # Empresas que requieren validación (detalles)
            companies_to_validate = Company.objects.filter(
                validated=False
            ).order_by('-fecha_registro')[:10]
            
            companies_data = [
                {
                    'id': company.id,
                    'razon_social': company.razon_social,
                    'ruc': company.ruc,
                    'sector': company.sector_economico,
                    'fecha_registro': company.fecha_registro.isoformat()
                }
                for company in companies_to_validate
            ]
            
            return Response({
                'success': True,
                'data': {
                    'pending_validations': {
                        'companies': pending_companies,
                        'documents': pending_documents,
                        'practices': pending_practices,
                        'total': pending_companies + pending_documents + pending_practices
                    },
                    'recent_registrations': {
                        'students': recent_students,
                        'companies': recent_companies,
                        'practices': recent_practices,
                        'period': '7 days'
                    },
                    'documents_status': documents_status,
                    'companies_to_validate': companies_data,
                    'generated_at': timezone.now().isoformat()
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error al obtener dashboard de secretaría: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ========================================================================
    # Estadísticas Completas
    # ========================================================================

    @extend_schema(
        tags=['Dashboards'],
        summary='Estadísticas Completas del Sistema',
        description='''
        Estadísticas avanzadas con filtros de período y fechas personalizadas.
        
        Requiere rol de **COORDINADOR** o **ADMINISTRADOR**.
        
        Permite filtrar por:
        - `period`: month (30 días) | quarter (90 días) | year (365 días)
        - `start_date`: Fecha inicial (formato YYYY-MM-DD)
        - `end_date`: Fecha final (formato YYYY-MM-DD)
        
        Incluye:
        - 📈 Timeline de prácticas por estado
        - 👨‍🎓 Distribución de estudiantes por carrera
        - 🏢 Análisis de empresas por sector
        - 📊 Métricas de rendimiento (promedios, tasas de éxito)
        - 📄 Estadísticas de documentos por tipo
        ''',
        parameters=[
            OpenApiParameter(
                name='period',
                description='Período de análisis',
                required=False,
                type=OpenApiTypes.STR,
                enum=['month', 'quarter', 'year'],
                default='month',
            ),
            OpenApiParameter(
                name='start_date',
                description='Fecha de inicio del período (formato YYYY-MM-DD)',
                required=False,
                type=OpenApiTypes.DATE,
            ),
            OpenApiParameter(
                name='end_date',
                description='Fecha de fin del período (formato YYYY-MM-DD)',
                required=False,
                type=OpenApiTypes.DATE,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Estadísticas completas',
                examples=[
                    OpenApiExample(
                        'Estadísticas Mensuales',
                        value={
                            'success': True,
                            'data': {
                                'period': {'start': '2024-01-01', 'end': '2024-01-31'},
                                'practices_timeline': {
                                    'DRAFT': 5,
                                    'PENDING': 8,
                                    'IN_PROGRESS': 30,
                                    'COMPLETED': 15,
                                },
                                'students_by_career': {
                                    'Ingeniería de Sistemas': 80,
                                    'Ingeniería Civil': 40,
                                },
                                'companies_by_sector': {
                                    'Tecnología': 15,
                                    'Construcción': 10,
                                },
                            },
                        },
                    ),
                ],
            ),
            403: OpenApiResponse(description='Sin permisos de coordinador/admin'),
        },
    )
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, IsCoordinador | IsAdministrador],
        url_path='statistics'
    )
    def complete_statistics(self, request):
        """
        Estadísticas completas del sistema.
        
        GET /api/v2/dashboards/statistics/
        ?period=month|quarter|year
        &start_date=YYYY-MM-DD
        &end_date=YYYY-MM-DD
        
        Requiere: COORDINADOR o ADMINISTRADOR
        
        Returns: Estadísticas detalladas por período
        """
        try:
            # Obtener parámetros
            period = request.query_params.get('period', 'month')
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            
            # Determinar rango de fechas
            if start_date_str and end_date_str:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
            else:
                end_date = timezone.now()
                if period == 'month':
                    start_date = end_date - timedelta(days=30)
                elif period == 'quarter':
                    start_date = end_date - timedelta(days=90)
                elif period == 'year':
                    start_date = end_date - timedelta(days=365)
                else:
                    start_date = end_date - timedelta(days=30)
            
            # Prácticas por período
            practices_timeline = Practice.objects.filter(
                fecha_registro__range=[start_date, end_date]
            ).annotate(
                period=TruncMonth('fecha_registro')
            ).values('period').annotate(
                count=Count('id')
            ).order_by('period')
            
            # Estudiantes por carrera
            students_by_career = Student.objects.values(
                'escuela_profesional'
            ).annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Empresas por sector
            companies_by_sector = Company.objects.filter(
                validated=True
            ).values('sector_economico').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Tasa de completación
            total_practices = Practice.objects.count()
            completed_practices = Practice.objects.filter(
                estado='COMPLETED'
            ).count()
            
            completion_rate = (completed_practices / total_practices * 100) if total_practices > 0 else 0
            
            # Promedio de horas
            avg_hours = Practice.objects.filter(
                estado='COMPLETED'
            ).aggregate(
                avg=Avg('horas_totales')
            )['avg'] or 0
            
            # Satisfacción (basado en calificaciones de documentos)
            avg_calification = Document.objects.filter(
                estado='APPROVED',
                calificacion__isnull=False
            ).aggregate(
                avg=Avg('calificacion')
            )['avg'] or 0
            
            return Response({
                'success': True,
                'data': {
                    'period': {
                        'type': period,
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    },
                    'practices_timeline': [
                        {
                            'period': item['period'].strftime('%Y-%m'),
                            'count': item['count']
                        }
                        for item in practices_timeline
                    ],
                    'students_by_career': [
                        {
                            'career': item['escuela_profesional'],
                            'count': item['count']
                        }
                        for item in students_by_career
                    ],
                    'companies_by_sector': [
                        {
                            'sector': item['sector_economico'],
                            'count': item['count']
                        }
                        for item in companies_by_sector
                    ],
                    'completion_rate': round(completion_rate, 2),
                    'average_hours': round(avg_hours, 2),
                    'average_satisfaction': round(float(avg_calification), 2),
                    'generated_at': timezone.now().isoformat()
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error al obtener estadísticas: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ========================================================================
    # Datos para Gráficas
    # ========================================================================

    @extend_schema(
        tags=['Dashboards'],
        summary='Datos para Gráficas',
        description='''
        Datos formateados listos para librerías de gráficos JavaScript.
        
        Compatible con: **Chart.js**, **Recharts**, **ApexCharts**, **D3.js**
        
        Tipos de gráficas disponibles:
        - `practices_status`: Estado de prácticas (Pie/Donut)
        - `students_career`: Estudiantes por carrera (Bar/Column)
        - `companies_sector`: Empresas por sector (Pie/Donut)
        - `practices_timeline`: Timeline de prácticas (Line/Area)
        
        El formato de respuesta incluye:
        - `labels`: Array de etiquetas
        - `datasets`: Array de conjuntos de datos con valores y colores
        - `colors`: Paleta de colores sugerida
        ''',
        parameters=[
            OpenApiParameter(
                name='type',
                description='Tipo de gráfica a generar',
                required=False,
                type=OpenApiTypes.STR,
                enum=['practices_status', 'students_career', 'companies_sector', 'practices_timeline'],
                default='practices_status',
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Datos para gráfica',
                examples=[
                    OpenApiExample(
                        'Gráfica Estado Prácticas',
                        value={
                            'success': True,
                            'chart_type': 'practices_status',
                            'data': {
                                'labels': ['En Progreso', 'Completadas', 'Pendientes', 'Borrador'],
                                'datasets': [{
                                    'label': 'Prácticas por Estado',
                                    'data': [45, 60, 8, 7],
                                    'backgroundColor': [
                                        'rgba(54, 162, 235, 0.8)',
                                        'rgba(75, 192, 192, 0.8)',
                                        'rgba(255, 206, 86, 0.8)',
                                        'rgba(201, 203, 207, 0.8)',
                                    ],
                                }],
                            },
                        },
                    ),
                    OpenApiExample(
                        'Gráfica Estudiantes por Carrera',
                        value={
                            'success': True,
                            'chart_type': 'students_career',
                            'data': {
                                'labels': ['Ing. Sistemas', 'Ing. Civil', 'Contabilidad'],
                                'datasets': [{
                                    'label': 'Estudiantes',
                                    'data': [80, 40, 30],
                                }],
                            },
                        },
                    ),
                ],
            ),
            400: OpenApiResponse(description='Tipo de gráfica no válido'),
        },
    )
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='charts'
    )
    def charts_data(self, request):
        """
        Datos formateados para gráficas (Chart.js, Recharts, etc).
        
        GET /api/v2/dashboards/charts/
        ?type=practices_status|students_career|companies_sector|practices_timeline
        
        Returns: Datos en formato compatible con librerías de gráficas
        """
        try:
            chart_type = request.query_params.get('type', 'practices_status')
            
            if chart_type == 'practices_status':
                data = self._get_practices_status_chart()
            elif chart_type == 'students_career':
                data = self._get_students_career_chart()
            elif chart_type == 'companies_sector':
                data = self._get_companies_sector_chart()
            elif chart_type == 'practices_timeline':
                data = self._get_practices_timeline_chart()
            else:
                return Response({
                    'success': False,
                    'error': 'Tipo de gráfica no válido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'chart_type': chart_type,
                'data': data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error al obtener datos de gráfica: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ========================================================================
    # Métodos Auxiliares Privados
    # ========================================================================

    def _get_practices_statistics(self):
        """Obtiene estadísticas de prácticas."""
        practices_by_status = Practice.objects.values('estado').annotate(
            count=Count('id')
        )
        
        return {
            'total': Practice.objects.count(),
            'by_status': {item['estado']: item['count'] for item in practices_by_status},
            'pending_approval': Practice.objects.filter(estado='PENDING').count(),
            'in_progress': Practice.objects.filter(estado='IN_PROGRESS').count(),
            'completed': Practice.objects.filter(estado='COMPLETED').count()
        }

    def _get_students_statistics(self):
        """Obtiene estadísticas de estudiantes."""
        total_students = Student.objects.count()
        eligible = Student.objects.filter(
            semestre_actual__gte=6,
            promedio_ponderado__gte=Decimal('12.0')
        ).count()
        
        with_practice = Student.objects.filter(
            practices__isnull=False
        ).distinct().count()
        
        return {
            'total': total_students,
            'eligible': eligible,
            'with_practice': with_practice,
            'without_practice': total_students - with_practice
        }

    def _get_companies_statistics(self):
        """Obtiene estadísticas de empresas."""
        companies_by_status = Company.objects.values('estado').annotate(
            count=Count('id')
        )
        
        return {
            'total': Company.objects.count(),
            'validated': Company.objects.filter(validated=True).count(),
            'active': Company.objects.filter(estado='ACTIVE').count(),
            'by_sector': list(
                Company.objects.values('sector_economico').annotate(
                    count=Count('id')
                ).order_by('-count')[:5]
            )
        }

    def _get_documents_statistics(self):
        """Obtiene estadísticas de documentos."""
        documents_by_status = Document.objects.values('estado').annotate(
            count=Count('id')
        )
        
        return {
            'total': Document.objects.count(),
            'by_status': {item['estado']: item['count'] for item in documents_by_status},
            'pending_approval': Document.objects.filter(estado='PENDING').count()
        }

    def _get_recent_activities(self, limit=10):
        """Obtiene actividades recientes del sistema."""
        # Prácticas recientes
        recent_practices = Practice.objects.order_by('-fecha_registro')[:limit]
        
        activities = []
        for practice in recent_practices:
            activities.append({
                'type': 'practice',
                'action': 'created',
                'description': f'Nueva práctica: {practice.titulo}',
                'user': practice.student.user.get_full_name(),
                'timestamp': practice.fecha_registro.isoformat()
            })
        
        return sorted(activities, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def _calculate_weekly_average(self, practice):
        """Calcula el promedio semanal de horas de una práctica."""
        total_hours = practice.horas_completadas or 0
        
        if practice.fecha_inicio:
            weeks = (timezone.now().date() - practice.fecha_inicio).days / 7
            if weeks > 0:
                return round(total_hours / weeks, 2)
        
        return 0

    def _get_students_performance_for_supervisor(self, supervisor):
        """Obtiene el rendimiento de estudiantes asignados a un supervisor."""
        practices = Practice.objects.filter(
            supervisor=supervisor,
            estado__in=['IN_PROGRESS', 'COMPLETED']
        ).select_related('student__user')
        
        performance = []
        for practice in practices:
            if practice.horas_totales > 0:
                horas_completadas = practice.horas_completadas or 0
                progreso = (horas_completadas / practice.horas_totales) * 100
                
                performance.append({
                    'student_name': practice.student.user.get_full_name(),
                    'practice_title': practice.titulo,
                    'progress': round(progreso, 2),
                    'status': practice.estado
                })
        
        return performance

    def _get_practices_status_chart(self):
        """Datos para gráfica de estado de prácticas (pie/donut chart)."""
        data = Practice.objects.values('estado').annotate(
            count=Count('id')
        )
        
        return {
            'labels': [item['estado'] for item in data],
            'datasets': [{
                'data': [item['count'] for item in data],
                'backgroundColor': [
                    '#FF6384', '#36A2EB', '#FFCE56', 
                    '#4BC0C0', '#9966FF', '#FF9F40'
                ]
            }]
        }

    def _get_students_career_chart(self):
        """Datos para gráfica de estudiantes por carrera (bar chart)."""
        data = Student.objects.values('escuela_profesional').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return {
            'labels': [item['escuela_profesional'] for item in data],
            'datasets': [{
                'label': 'Estudiantes',
                'data': [item['count'] for item in data],
                'backgroundColor': '#36A2EB'
            }]
        }

    def _get_companies_sector_chart(self):
        """Datos para gráfica de empresas por sector (bar chart)."""
        data = Company.objects.filter(
            validated=True
        ).values('sector_economico').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return {
            'labels': [item['sector_economico'] for item in data],
            'datasets': [{
                'label': 'Empresas',
                'data': [item['count'] for item in data],
                'backgroundColor': '#4BC0C0'
            }]
        }

    def _get_practices_timeline_chart(self):
        """Datos para gráfica de línea temporal de prácticas."""
        six_months_ago = timezone.now() - timedelta(days=180)
        
        data = Practice.objects.filter(
            fecha_registro__gte=six_months_ago
        ).annotate(
            month=TruncMonth('fecha_registro')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        return {
            'labels': [item['month'].strftime('%Y-%m') for item in data],
            'datasets': [{
                'label': 'Prácticas Registradas',
                'data': [item['count'] for item in data],
                'borderColor': '#FF6384',
                'fill': False
            }]
        }
