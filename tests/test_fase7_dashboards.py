"""
Script de testing rápido para Fase 7 - Dashboard Endpoints.

Verifica que los endpoints estén correctamente configurados.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from src.domain.models import User, Student, Company, Practice


class DashboardEndpointsTest(TestCase):
    """Tests para endpoints de dashboard."""
    
    def setUp(self):
        """Configuración inicial."""
        self.client = APIClient()
        
        # Crear usuario coordinador
        self.coordinador = User.objects.create_user(
            email='coord@upeu.edu.pe',
            password='test123',
            first_name='Test',
            last_name='Coordinador',
            role='COORDINADOR'
        )
        
        # Crear usuario estudiante
        self.estudiante_user = User.objects.create_user(
            email='estudiante@upeu.edu.pe',
            password='test123',
            first_name='Test',
            last_name='Estudiante',
            role='PRACTICANTE'
        )
        
        self.estudiante = Student.objects.create(
            user=self.estudiante_user,
            codigo_estudiante='2024012345',
            escuela_profesional='Ingeniería de Sistemas',
            semestre_actual=7,
            promedio_ponderado=15.5
        )
    
    def test_dashboard_general_requires_auth(self):
        """Verificar que dashboard general requiere autenticación."""
        url = '/api/v2/dashboards/general/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_dashboard_general_coordinador(self):
        """Verificar que coordinador puede acceder a dashboard general."""
        self.client.force_authenticate(user=self.coordinador)
        url = '/api/v2/dashboards/general/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.json())
    
    def test_dashboard_student(self):
        """Verificar dashboard de estudiante."""
        self.client.force_authenticate(user=self.estudiante_user)
        url = '/api/v2/dashboards/student/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('profile', data['data'])
        self.assertEqual(data['data']['profile']['codigo'], '2024012345')
    
    def test_reports_practices_requires_permission(self):
        """Verificar que reportes requieren permisos."""
        self.client.force_authenticate(user=self.estudiante_user)
        url = '/api/v2/reports/practices/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_charts_endpoint(self):
        """Verificar endpoint de gráficas."""
        self.client.force_authenticate(user=self.coordinador)
        url = '/api/v2/dashboards/charts/?type=practices_status'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('chart_type', data)
        self.assertIn('data', data)


class ReportsEndpointsTest(TestCase):
    """Tests para endpoints de reportes."""
    
    def setUp(self):
        """Configuración inicial."""
        self.client = APIClient()
        
        self.coordinador = User.objects.create_user(
            email='coord@upeu.edu.pe',
            password='test123',
            first_name='Test',
            last_name='Coordinador',
            role='COORDINADOR'
        )
    
    def test_practices_report_json(self):
        """Verificar reporte de prácticas en JSON."""
        self.client.force_authenticate(user=self.coordinador)
        url = '/api/v2/reports/practices/?format=json'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.json())
    
    def test_students_report(self):
        """Verificar reporte de estudiantes."""
        self.client.force_authenticate(user=self.coordinador)
        url = '/api/v2/reports/students/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_companies_report(self):
        """Verificar reporte de empresas."""
        self.client.force_authenticate(user=self.coordinador)
        url = '/api/v2/reports/companies/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_statistics_summary(self):
        """Verificar resumen estadístico."""
        self.client.force_authenticate(user=self.coordinador)
        url = '/api/v2/reports/statistics_summary/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertIn('practices', data)
        self.assertIn('students', data)
        self.assertIn('companies', data)


if __name__ == '__main__':
    import django
    import os
    import sys
    
    # Configurar Django
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    # Ejecutar tests
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['__main__'])
    
    print("\n" + "="*60)
    print("✅ FASE 7 - TESTS COMPLETADOS")
    print("="*60)
    if failures:
        print(f"❌ {failures} tests fallaron")
    else:
        print("✅ Todos los tests pasaron exitosamente")
