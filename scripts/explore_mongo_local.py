"""
Script para explorar MongoDB local y ver todas las bases de datos y colecciones
"""

from pymongo import MongoClient

# Credenciales MongoDB Local
LOCAL_USER = "upeu_admin"
LOCAL_PASSWORD = "upeu_contra_2024"
LOCAL_HOST = "localhost"
LOCAL_PORT = "27017"
LOCAL_URI = f"mongodb://{LOCAL_USER}:{LOCAL_PASSWORD}@{LOCAL_HOST}:{LOCAL_PORT}/?authSource=admin"

print("=" * 70)
print("🔍 EXPLORANDO MONGODB LOCAL")
print("=" * 70)

try:
    # Conectar
    print("\n📡 Conectando a MongoDB local...")
    client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=5000)
    
    # Listar todas las bases de datos
    print("\n📊 BASES DE DATOS DISPONIBLES:")
    print("-" * 70)
    
    db_names = client.list_database_names()
    
    for db_name in db_names:
        db = client[db_name]
        collections = db.list_collection_names()
        
        print(f"\n🗄️  Database: {db_name}")
        print(f"   Colecciones: {len(collections)}")
        
        if collections:
            for col_name in collections:
                collection = db[col_name]
                count = collection.count_documents({})
                print(f"      • {col_name}: {count} documentos")
        else:
            print("      (vacía)")
    
    print("\n" + "=" * 70)
    print("✅ EXPLORACIÓN COMPLETADA")
    print("=" * 70)
    
    # Pedir al usuario qué base de datos quiere migrar
    print("\n💡 RECOMENDACIÓN:")
    print("   Edita scripts/migrate_mongo_to_azure.py")
    print("   Cambia la línea: LOCAL_DB = \"upeu_mongodb\"")
    print("   Por la base de datos que contenga tus datos")
    
    client.close()
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
