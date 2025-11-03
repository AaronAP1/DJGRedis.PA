"""
Script para listar escuelas y empresas disponibles para crear carta de presentación.
"""
import os
import django
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.adapters.secondary.database.models import School, Company, StudentProfile

print("=" * 80)
print("ESCUELAS ACTIVAS")
print("=" * 80)
schools = School.objects.filter(estado='ACTIVO')[:5]
for s in schools:
    print(f"ID: {s.id:2d} - {s.nombre} ({s.codigo})")
print(f"\n✅ Total escuelas activas: {School.objects.filter(estado='ACTIVO').count()}")

print("\n" + "=" * 80)
print("EMPRESAS ACTIVAS")
print("=" * 80)
companies = Company.objects.filter(estado='ACTIVO')[:5]
for c in companies:
    print(f"ID: {c.id:2d} - {c.nombre} (RUC: {c.ruc})")
print(f"\n✅ Total empresas activas: {Company.objects.filter(estado='ACTIVO').count()}")

print("\n" + "=" * 80)
print("ESTUDIANTES DISPONIBLES")
print("=" * 80)
students = StudentProfile.objects.all()[:5]
for st in students:
    print(f"Código: {st.codigo_estudiante} - {st.usuario.nombres} {st.usuario.apellidos}")
print(f"\n✅ Total estudiantes: {StudentProfile.objects.count()}")
