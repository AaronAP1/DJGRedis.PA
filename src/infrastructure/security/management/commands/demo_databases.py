"""
Comando para demostrar el funcionamiento de las 3 bases de datos:
PostgreSQL, MongoDB (simulado) y Redis.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
import time
import json

from src.adapters.secondary.database.models import (
    User, Student, Company, Practice, Document
)

User = get_user_model()


class Command(BaseCommand):
    help = "Demuestra el funcionamiento de PostgreSQL, MongoDB y Redis"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('🎯 DEMOSTRACIÓN DE LAS 3 BASES DE DATOS'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        # 1. PostgreSQL
        self.demo_postgresql()
        
        # 2. Redis
        self.demo_redis()
        
        # 3. MongoDB (simulado)
        self.demo_mongodb()
        
        # 4. Integración
        self.demo_integration()

    def demo_postgresql(self):
        """Demuestra operaciones en PostgreSQL."""
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('🐘 PARTE 1: PostgreSQL (Base de Datos Principal)'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        self.stdout.write(self.style.WARNING('📋 Uso: Datos relacionales estructurados\n'))
        
        # Consulta simple
        self.stdout.write('1️⃣  Consulta Simple:')
        start = time.time()
        users = User.objects.all()[:5]
        elapsed = (time.time() - start) * 1000
        
        for user in users:
            self.stdout.write(f'   • {user.email} - Rol: {user.role}')
        self.stdout.write(f'   ⏱️  Tiempo: {elapsed:.2f}ms\n')
        
        # Consulta con JOIN
        self.stdout.write('2️⃣  Consulta con JOIN (relacionando tablas):')
        start = time.time()
        students = Student.objects.select_related('user').all()[:3]
        elapsed = (time.time() - start) * 1000
        
        for student in students:
            self.stdout.write(f'   • {student.user.first_name} {student.user.last_name}')
            self.stdout.write(f'     - Código: {student.codigo_estudiante}')
            self.stdout.write(f'     - Carrera: {student.carrera}')
            self.stdout.write(f'     - Promedio: {student.promedio}')
        self.stdout.write(f'   ⏱️  Tiempo: {elapsed:.2f}ms\n')
        
        # Consulta compleja con múltiples JOINs
        self.stdout.write('3️⃣  Consulta Compleja (múltiples JOINs):')
        start = time.time()
        practices = Practice.objects.select_related(
            'student__user', 'company', 'supervisor__user'
        ).prefetch_related('documents').all()[:3]
        elapsed = (time.time() - start) * 1000
        
        for practice in practices:
            self.stdout.write(f'\n   📝 Práctica: {practice.titulo}')
            self.stdout.write(f'      - Estudiante: {practice.student.user.get_full_name()}')
            self.stdout.write(f'      - Empresa: {practice.company.nombre_comercial}')
            self.stdout.write(f'      - Supervisor: {practice.supervisor.user.get_full_name()}')
            self.stdout.write(f'      - Estado: {practice.status}')
            self.stdout.write(f'      - Horas: {practice.horas_completadas}/{practice.horas_requeridas}')
            self.stdout.write(f'      - Documentos: {practice.documents.count()}')
        self.stdout.write(f'\n   ⏱️  Tiempo: {elapsed:.2f}ms\n')
        
        # Transacción
        self.stdout.write('4️⃣  Transacción (ACID):')
        self.stdout.write('   ✅ PostgreSQL garantiza:')
        self.stdout.write('      - Atomicidad: Todo o nada')
        self.stdout.write('      - Consistencia: Reglas de integridad')
        self.stdout.write('      - Aislamiento: Transacciones concurrentes')
        self.stdout.write('      - Durabilidad: Datos persistentes\n')
        
        # Estadísticas SQL
        self.stdout.write('5️⃣  Estadísticas de la BD:')
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    COUNT(*) as total_tables
                FROM pg_tables 
                WHERE schemaname = 'public'
                GROUP BY schemaname
            """)
            result = cursor.fetchone()
            if result:
                self.stdout.write(f'   • Tablas en schema public: {result[1]}')
        
        total_records = sum([
            User.objects.count(),
            Student.objects.count(),
            Company.objects.count(),
            Practice.objects.count(),
            Document.objects.count()
        ])
        self.stdout.write(f'   • Total registros: {total_records}\n')

    def demo_redis(self):
        """Demuestra operaciones en Redis."""
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('📦 PARTE 2: Redis (Cache y Broker de Mensajes)'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        self.stdout.write(self.style.WARNING('📋 Uso: Cache en memoria, sesiones, tareas asíncronas\n'))
        
        # 1. Cache simple
        self.stdout.write('1️⃣  Cache Simple (SET/GET):')
        cache_key = 'demo:user_count'
        user_count = User.objects.count()
        
        cache.set(cache_key, user_count, timeout=60)
        cached_value = cache.get(cache_key)
        
        self.stdout.write(f'   • Guardado en cache: {cache_key} = {user_count}')
        self.stdout.write(f'   • Recuperado de cache: {cached_value}')
        self.stdout.write(f'   • TTL: 60 segundos\n')
        
        # 2. Cache de objetos complejos
        self.stdout.write('2️⃣  Cache de Objetos Complejos:')
        stats = {
            'total_users': User.objects.count(),
            'total_students': Student.objects.count(),
            'total_companies': Company.objects.count(),
            'total_practices': Practice.objects.count(),
            'timestamp': time.time()
        }
        
        cache.set('stats:dashboard', stats, timeout=300)
        cached_stats = cache.get('stats:dashboard')
        
        self.stdout.write(f'   • Objeto cacheado: {json.dumps(stats, indent=6)}')
        self.stdout.write(f'   • TTL: 5 minutos\n')
        
        # 3. Comparación de velocidad
        self.stdout.write('3️⃣  Comparación de Velocidad (Cache vs DB):')
        
        # Sin cache
        cache.delete('demo:companies')
        start = time.time()
        companies_db = list(Company.objects.all().values('id', 'nombre_comercial', 'ruc'))
        time_db = (time.time() - start) * 1000
        
        # Con cache
        cache.set('demo:companies', companies_db, timeout=60)
        start = time.time()
        companies_cache = cache.get('demo:companies')
        time_cache = (time.time() - start) * 1000
        
        self.stdout.write(f'   • Consulta a PostgreSQL: {time_db:.2f}ms')
        self.stdout.write(f'   • Consulta a Redis Cache: {time_cache:.2f}ms')
        self.stdout.write(f'   • 🚀 Mejora: {(time_db/time_cache):.1f}x más rápido\n')
        
        # 4. Cache de sesiones
        self.stdout.write('4️⃣  Cache de Sesiones JWT:')
        self.stdout.write('   • Redis almacena tokens JWT blacklisted')
        self.stdout.write('   • Tokens de refresh activos')
        self.stdout.write('   • Sesiones de usuario\n')
        
        # 5. Celery Broker
        self.stdout.write('5️⃣  Broker para Celery (Tareas Asíncronas):')
        self.stdout.write('   • Redis actúa como broker de mensajes')
        self.stdout.write('   • Celery usa Redis para encolar tareas:')
        self.stdout.write('     - Envío de emails')
        self.stdout.write('     - Validaciones SUNAT')
        self.stdout.write('     - Generación de reportes')
        self.stdout.write('     - Procesamiento de archivos\n')
        
        # 6. Operaciones múltiples
        self.stdout.write('6️⃣  Operaciones Múltiples (MSET/MGET):')
        cache.set_many({
            'user:1:name': 'Juan',
            'user:2:name': 'María',
            'user:3:name': 'Carlos'
        }, timeout=60)
        
        values = cache.get_many(['user:1:name', 'user:2:name', 'user:3:name'])
        self.stdout.write(f'   • Valores recuperados: {values}\n')

    def demo_mongodb(self):
        """Demuestra el uso de MongoDB (simulado)."""
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('🍃 PARTE 3: MongoDB (Base de Datos Documental)'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        self.stdout.write(self.style.WARNING('📋 Uso: Documentos binarios, logs, datos no estructurados\n'))
        
        # 1. Estructura de documentos
        self.stdout.write('1️⃣  Colecciones MongoDB (según mongodb_init.js):')
        collections = [
            {'name': 'documents_storage', 'desc': 'Archivos binarios (PDF, imágenes)'},
            {'name': 'graphql_logs', 'desc': 'Logs de queries GraphQL'},
            {'name': 'system_metrics', 'desc': 'Métricas de rendimiento'},
            {'name': 'temp_notifications', 'desc': 'Notificaciones temporales (TTL)'},
            {'name': 'graphql_schema_cache', 'desc': 'Cache de schema GraphQL'},
            {'name': 'security_analysis', 'desc': 'Análisis de seguridad'}
        ]
        
        for coll in collections:
            self.stdout.write(f'   • {coll["name"]}: {coll["desc"]}')
        self.stdout.write('')
        
        # 2. Ejemplo de documento
        self.stdout.write('2️⃣  Ejemplo de Documento (documents_storage):')
        document_example = {
            "practica_id": 1,
            "file_metadata": {
                "original_name": "plan_practica.pdf",
                "size": 1024000,
                "mime_type": "application/pdf",
                "hash": "sha256:abc123...",
                "compressed": True,
                "encrypted": False
            },
            "upload_info": {
                "uploaded_by": 5,
                "upload_date": "2025-10-24T10:30:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0..."
            },
            "file_data": "<binary_data>",
            "virus_scan": {
                "scanned": True,
                "clean": True,
                "scan_date": "2025-10-24T10:30:05Z"
            }
        }
        
        self.stdout.write(f'{json.dumps(document_example, indent=6)}\n')
        
        # 3. Ventajas de MongoDB
        self.stdout.write('3️⃣  Ventajas para este Proyecto:')
        self.stdout.write('   ✅ Almacena archivos binarios grandes')
        self.stdout.write('   ✅ Schema flexible (logs con campos variables)')
        self.stdout.write('   ✅ TTL automático (limpieza de logs antiguos)')
        self.stdout.write('   ✅ Alto rendimiento para escritura (logs)')
        self.stdout.write('   ✅ Ideal para datos no relacionales\n')
        
        # 4. Índices
        self.stdout.write('4️⃣  Índices Creados (23 índices):')
        indexes = [
            'practica_id (documents_storage)',
            'timestamp (graphql_logs) - TTL 30 días',
            'query_complexity (graphql_logs)',
            'timestamp (system_metrics) - TTL 90 días',
            'schema_version (graphql_schema_cache)'
        ]
        
        for idx in indexes:
            self.stdout.write(f'   • {idx}')
        self.stdout.write('')
        
        # 5. Simulación con PostgreSQL
        self.stdout.write('5️⃣  Simulación Actual:')
        documents = Document.objects.all()[:3]
        
        for doc in documents:
            self.stdout.write(f'\n   📄 Documento: {doc.titulo}')
            self.stdout.write(f'      - Tipo: {doc.tipo_documento}')
            self.stdout.write(f'      - Tamaño: {doc.tamaño_bytes / 1024:.1f} KB')
            self.stdout.write(f'      - URL: {doc.archivo_url}')
            self.stdout.write(f'      - En MongoDB guardaría: archivo binario completo')
        self.stdout.write('')

    def demo_integration(self):
        """Demuestra la integración de las 3 BDs."""
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('🔗 PARTE 4: Integración de las 3 Bases de Datos'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        self.stdout.write('📊 Flujo Completo - Crear Práctica:\n')
        
        self.stdout.write('1️⃣  Usuario hace login:')
        self.stdout.write('   • PostgreSQL: Valida credenciales')
        self.stdout.write('   • Redis: Cachea sesión JWT')
        self.stdout.write('   • MongoDB: Registra evento de login\n')
        
        self.stdout.write('2️⃣  Usuario crea práctica:')
        self.stdout.write('   • PostgreSQL: Guarda registro de práctica')
        self.stdout.write('   • Redis: Invalida cache de estadísticas')
        self.stdout.write('   • MongoDB: Log de operación GraphQL\n')
        
        self.stdout.write('3️⃣  Usuario sube documento:')
        self.stdout.write('   • PostgreSQL: Metadata del documento')
        self.stdout.write('   • MongoDB: Archivo binario completo')
        self.stdout.write('   • Redis: Cache de URL del archivo\n')
        
        self.stdout.write('4️⃣  Sistema envía notificación:')
        self.stdout.write('   • Redis: Celery encola tarea')
        self.stdout.write('   • PostgreSQL: Lee datos del supervisor')
        self.stdout.write('   • MongoDB: Guarda notificación temporal\n')
        
        self.stdout.write('5️⃣  Usuario consulta dashboard:')
        self.stdout.write('   • Redis: Verifica cache (HIT)')
        self.stdout.write('   • Si cache MISS:')
        self.stdout.write('     - PostgreSQL: Consulta datos')
        self.stdout.write('     - Redis: Cachea resultado')
        self.stdout.write('     - MongoDB: Log de la query\n')
        
        # Ejemplo práctico
        self.stdout.write(self.style.WARNING('🎯 EJEMPLO PRÁCTICO:\n'))
        
        # Simular consulta con cache
        cache_key = 'practice:1:details'
        
        # Primera consulta (sin cache)
        self.stdout.write('Primera consulta (Cache MISS):')
        start = time.time()
        practice = Practice.objects.select_related(
            'student__user', 'company', 'supervisor__user'
        ).first()
        
        if practice:
            practice_data = {
                'id': practice.id,
                'titulo': practice.titulo,
                'estudiante': practice.student.user.get_full_name(),
                'empresa': practice.company.nombre_comercial,
                'supervisor': practice.supervisor.user.get_full_name(),
                'status': practice.status
            }
            time_db = (time.time() - start) * 1000
            
            # Cachear
            cache.set(cache_key, practice_data, timeout=300)
            
            self.stdout.write(f'   ⏱️  PostgreSQL: {time_db:.2f}ms')
            self.stdout.write(f'   💾 Datos cacheados en Redis\n')
            
            # Segunda consulta (con cache)
            self.stdout.write('Segunda consulta (Cache HIT):')
            start = time.time()
            cached_practice = cache.get(cache_key)
            time_cache = (time.time() - start) * 1000
            
            self.stdout.write(f'   ⏱️  Redis Cache: {time_cache:.2f}ms')
            self.stdout.write(f'   🚀 Mejora: {(time_db/time_cache):.1f}x más rápido\n')
        
        # Resumen
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE ARQUITECTURA\n'))
        
        summary = {
            'PostgreSQL': {
                'Fortaleza': 'ACID, relaciones, integridad',
                'Usa para': 'Usuarios, prácticas, empresas, evaluaciones'
            },
            'Redis': {
                'Fortaleza': 'Velocidad, pub/sub, TTL',
                'Usa para': 'Cache, sesiones, broker Celery'
            },
            'MongoDB': {
                'Fortaleza': 'Flexible, binarios, alto volumen',
                'Usa para': 'Documentos, logs, métricas, archivos'
            }
        }
        
        for db, info in summary.items():
            self.stdout.write(f'\n{db}:')
            for key, value in info.items():
                self.stdout.write(f'  • {key}: {value}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('✅ DEMOSTRACIÓN COMPLETADA\n'))
        self.stdout.write('💡 Esta arquitectura Polyglot Persistence usa la BD correcta')
        self.stdout.write('   para cada tipo de dato, optimizando rendimiento y escalabilidad.\n')
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
