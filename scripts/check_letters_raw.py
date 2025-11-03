"""Script para verificar datos RAW de cartas."""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SERVER_CONFIG', 'development')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT 
            id,
            student_id,
            student_code,
            student_full_name,
            escuela_id,
            empresa_id,
            practice_area,
            status
        FROM presentation_letter_requests
        ORDER BY id
    """)
    
    print("=" * 100)
    print("DATOS RAW DE PRESENTATION_LETTER_REQUESTS")
    print("=" * 100)
    
    for row in cursor.fetchall():
        print(f"\nID: {row[0]}")
        print(f"  student_id: {row[1]}")
        print(f"  student_code: {row[2]}")
        print(f"  student_full_name: {row[3]}")
        print(f"  escuela_id: {row[4]}")
        print(f"  empresa_id: {row[5]}")
        print(f"  practice_area: {row[6]}")
        print(f"  status: {row[7]}")
