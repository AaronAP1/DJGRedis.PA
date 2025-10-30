"""
Script para migrar MongoDB local a Cosmos DB Azure
Autor: Sistema PPP UPeU
Fecha: 2025-10-30
"""

from pymongo import MongoClient
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ==========================================
# CONFIGURACIÓN
# ==========================================

# MongoDB Local (Docker)
LOCAL_USER = os.getenv("MONGODB_USER", "upeu_admin")
LOCAL_PASSWORD = os.getenv("MONGODB_PASSWORD")
LOCAL_HOST = os.getenv("MONGODB_HOST", "localhost")
LOCAL_PORT = os.getenv("MONGODB_PORT", "27017")
LOCAL_DB = os.getenv("MONGODB_DATABASE", "upeu_mongodb")
LOCAL_URI = f"mongodb://{LOCAL_USER}:{LOCAL_PASSWORD}@{LOCAL_HOST}:{LOCAL_PORT}/?authSource=admin"

# Cosmos DB Azure
AZURE_URI = os.getenv("AZURE_COSMOS_CONNECTION_STRING")
AZURE_DB = os.getenv("AZURE_COSMOS_DATABASE", "upeu_documents")

# ==========================================
# FUNCIONES
# ==========================================

def print_separator():
    print("=" * 70)

def migrate_collection(collection_name, clean_target=True):
    """
    Migrar una colección específica de local a Azure
    
    Args:
        collection_name: Nombre de la colección
        clean_target: Si True, limpia la colección en Azure antes de migrar
    """
    print(f"\n📦 [{collection_name}]")
    print("   Conectando a MongoDB local...")
    
    try:
        # Conectar a MongoDB Local
        local_client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=5000)
        local_db = local_client[LOCAL_DB]
        local_collection = local_db[collection_name]
        
        # Contar documentos
        total_docs = local_collection.count_documents({})
        print(f"   📊 Documentos encontrados: {total_docs}")
        
        if total_docs == 0:
            print(f"   ⏭️  Colección vacía, saltando...")
            local_client.close()
            return True
        
        # Conectar a Cosmos DB
        print("   Conectando a Cosmos DB Azure...")
        azure_client = MongoClient(AZURE_URI, serverSelectionTimeoutMS=10000)
        azure_db = azure_client[AZURE_DB]
        azure_collection = azure_db[collection_name]
        
        # Limpiar colección en Azure si se solicita
        if clean_target:
            existing_docs = azure_collection.count_documents({})
            if existing_docs > 0:
                print(f"   🗑️  Eliminando {existing_docs} documentos existentes...")
                azure_collection.delete_many({})
        
        # Obtener documentos de local
        print(f"   📥 Extrayendo documentos de MongoDB local...")
        documents = list(local_collection.find({}))
        
        # Insertar en Azure
        print(f"   📤 Insertando documentos en Cosmos DB...")
        result = azure_collection.insert_many(documents)
        
        print(f"   ✅ Migrados {len(result.inserted_ids)} documentos exitosamente")
        
        local_client.close()
        azure_client.close()
        
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def list_local_collections():
    """Listar todas las colecciones en MongoDB local"""
    try:
        client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=5000)
        db = client[LOCAL_DB]
        collections = db.list_collection_names()
        client.close()
        return collections
    except Exception as e:
        print(f"❌ Error al conectar con MongoDB local: {str(e)}")
        print(f"   Verifica que MongoDB esté corriendo en localhost:27017")
        return []

def test_azure_connection():
    """Probar conexión a Cosmos DB"""
    print("\n🔍 Probando conexión a Cosmos DB Azure...")
    try:
        client = MongoClient(AZURE_URI, serverSelectionTimeoutMS=10000)
        db = client[AZURE_DB]
        # Intentar una operación simple
        db.list_collection_names()
        client.close()
        print("   ✅ Conexión exitosa!")
        return True
    except Exception as e:
        print(f"   ❌ Error de conexión: {str(e)}")
        return False

def migrate_all():
    """Migrar todas las colecciones"""
    print_separator()
    print("🚀 MIGRACIÓN MONGODB LOCAL → COSMOS DB AZURE")
    print_separator()
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔹 Origen:  {LOCAL_URI} [{LOCAL_DB}]")
    print(f"🔹 Destino: Cosmos DB Azure [{AZURE_DB}]")
    print_separator()
    
    # Probar conexión a Azure
    if not test_azure_connection():
        print("\n❌ No se pudo conectar a Cosmos DB. Abortando...")
        return
    
    # Listar colecciones locales
    print("\n📋 Listando colecciones en MongoDB local...")
    collections = list_local_collections()
    
    if not collections:
        print("❌ No se encontraron colecciones para migrar")
        return
    
    print(f"   Encontradas {len(collections)} colecciones:")
    for col in collections:
        print(f"      • {col}")
    
    # Confirmar migración
    print("\n⚠️  ADVERTENCIA: Se eliminarán los datos existentes en Azure")
    confirm = input("\n¿Continuar con la migración? (Y/N): ")
    
    if confirm.upper() != 'Y':
        print("\n❌ Migración cancelada")
        return
    
    # Migrar cada colección
    print("\n" + "=" * 70)
    print("INICIANDO MIGRACIÓN")
    print("=" * 70)
    
    success_count = 0
    failed_count = 0
    
    for collection_name in collections:
        if migrate_collection(collection_name):
            success_count += 1
        else:
            failed_count += 1
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE MIGRACIÓN")
    print("=" * 70)
    print(f"✅ Exitosas: {success_count}")
    print(f"❌ Fallidas:  {failed_count}")
    print(f"📦 Total:     {len(collections)}")
    print("=" * 70)
    
    if failed_count == 0:
        print("\n🎉 ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
    else:
        print("\n⚠️  Migración completada con errores")

# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    try:
        migrate_all()
    except KeyboardInterrupt:
        print("\n\n❌ Migración interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        sys.exit(1)
