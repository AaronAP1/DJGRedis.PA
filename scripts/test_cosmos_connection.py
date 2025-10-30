"""
Script para probar conexión a Cosmos DB Azure
"""

from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

AZURE_URI = os.getenv("AZURE_COSMOS_CONNECTION_STRING")
AZURE_DB = os.getenv("AZURE_COSMOS_DATABASE", "upeu_documents")

def test_connection():
    print("=" * 70)
    print("🧪 TEST DE CONEXIÓN COSMOS DB AZURE")
    print("=" * 70)
    
    try:
        print("\n1️⃣  Conectando a Cosmos DB...")
        client = MongoClient(AZURE_URI, serverSelectionTimeoutMS=10000)
        db = client[AZURE_DB]
        
        print("   ✅ Conexión establecida")
        
        # Listar colecciones
        print("\n2️⃣  Listando colecciones...")
        collections = db.list_collection_names()
        
        if collections:
            print(f"   📦 Encontradas {len(collections)} colecciones:")
            for col in collections:
                count = db[col].count_documents({})
                print(f"      • {col}: {count} documentos")
        else:
            print("   📭 No hay colecciones aún (base de datos vacía)")
        
        # Insertar documento de prueba
        print("\n3️⃣  Insertando documento de prueba...")
        test_collection = db["test_connection"]
        
        test_doc = {
            "test": "connection_test",
            "timestamp": datetime.now().isoformat(),
            "message": "¡Conexión exitosa desde Python!"
        }
        
        result = test_collection.insert_one(test_doc)
        print(f"   ✅ Documento insertado con ID: {result.inserted_id}")
        
        # Leer documento
        print("\n4️⃣  Leyendo documento insertado...")
        doc = test_collection.find_one({"test": "connection_test"})
        print(f"   ✅ Documento leído correctamente:")
        print(f"      Message: {doc['message']}")
        print(f"      Timestamp: {doc['timestamp']}")
        
        # Limpiar documento de prueba
        print("\n5️⃣  Limpiando documento de prueba...")
        test_collection.delete_one({"_id": result.inserted_id})
        print("   ✅ Documento eliminado")
        
        client.close()
        
        print("\n" + "=" * 70)
        print("🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print("=" * 70)
        print("\n✅ Cosmos DB está listo para usar")
        print("✅ Puedes ejecutar: python scripts\\migrate_mongo_to_azure.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\n⚠️  Verifica:")
        print("   • Connection string correcta")
        print("   • Firewall de Azure permite tu IP")
        print("   • pymongo instalado: pip install pymongo")
        return False

if __name__ == "__main__":
    test_connection()
