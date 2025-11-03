"""Script para verificar datos de cartas de presentación."""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SERVER_CONFIG', 'development')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.adapters.secondary.database.models import PresentationLetterRequest

print("=" * 80)
print("VERIFICACIÓN DE CARTAS DE PRESENTACIÓN")
print("=" * 80)

letters = PresentationLetterRequest.objects.all()
print(f"\n📊 Total de registros: {letters.count()}")

for letter in letters:
    print(f"\n{'=' * 80}")
    print(f"ID: {letter.id}")
    print(f"Student Code: {letter.student_code}")
    print(f"Student Full Name: {letter.student_full_name}")
    print(f"Escuela ID: {letter.escuela_id}")
    print(f"Escuela objeto: {letter.escuela}")
    if letter.escuela:
        print(f"  → Nombre: {letter.escuela.nombre}")
    print(f"Empresa ID: {letter.empresa_id}")
    print(f"Empresa objeto: {letter.empresa}")
    if letter.empresa:
        print(f"  → Nombre: {letter.empresa.nombre}")
    print(f"Practice Area: {letter.practice_area}")
    print(f"Status: {letter.status}")
    print(f"Created At: {letter.created_at}")
    
    # Verificar si tiene student
    print(f"Student objeto: {letter.student}")

print("\n" + "=" * 80)
