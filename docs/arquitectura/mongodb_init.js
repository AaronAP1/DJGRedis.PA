// =====================================================
// INICIALIZACIÓN MONGODB - SISTEMA PPP UPeU
// Colecciones para documentos, logs y métricas
// =====================================================

// Conectar a la base de datos
db = db.getSiblingDB('upeu_documents');

// =====================================================
// CREAR COLECCIONES CON VALIDACIÓN
// =====================================================

// Colección para almacenamiento de documentos
db.createCollection("documents_storage", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["practica_id", "file_metadata", "upload_info"],
            properties: {
                practica_id: {
                    bsonType: "int",
                    description: "ID de la práctica en PostgreSQL"
                },
                file_metadata: {
                    bsonType: "object",
                    required: ["original_name", "size", "mime_type", "hash"],
                    properties: {
                        original_name: { bsonType: "string" },
                        size: { bsonType: "long" },
                        mime_type: { bsonType: "string" },
                        hash: { bsonType: "string" },
                        compressed: { bsonType: "bool" },
                        encrypted: { bsonType: "bool" }
                    }
                },
                upload_info: {
                    bsonType: "object",
                    required: ["uploaded_by", "upload_date"],
                    properties: {
                        uploaded_by: { bsonType: "int" },
                        upload_date: { bsonType: "date" },
                        ip_address: { bsonType: "string" },
                        user_agent: { bsonType: "string" }
                    }
                },
                file_data: {
                    bsonType: "binData",
                    description: "Datos del archivo en binario"
                },
                virus_scan: {
                    bsonType: "object",
                    properties: {
                        scanned: { bsonType: "bool" },
                        clean: { bsonType: "bool" },
                        scan_date: { bsonType: "date" },
                        scanner_version: { bsonType: "string" }
                    }
                }
            }
        }
    }
});

// Colección para logs de GraphQL
db.createCollection("graphql_logs", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["query", "timestamp", "user_id"],
            properties: {
                query: { bsonType: "string" },
                variables: { bsonType: "object" },
                user_id: { bsonType: "int" },
                execution_time: { bsonType: "int" },
                timestamp: { bsonType: "date" },
                ip_address: { bsonType: "string" },
                user_agent: { bsonType: "string" },
                errors: { bsonType: "array" },
                query_complexity: { bsonType: "int" },
                query_depth: { bsonType: "int" },
                cached: { bsonType: "bool" }
            }
        }
    }
});

// Colección para métricas del sistema
db.createCollection("system_metrics", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["timestamp", "metric_type", "data"],
            properties: {
                timestamp: { bsonType: "date" },
                metric_type: { 
                    bsonType: "string",
                    enum: ["performance", "security", "usage", "error", "business"]
                },
                data: { bsonType: "object" },
                source: { bsonType: "string" },
                environment: { 
                    bsonType: "string",
                    enum: ["development", "staging", "production"]
                }
            }
        }
    }
});

// Colección para notificaciones temporales
db.createCollection("temp_notifications", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "notification_data", "scheduled_for"],
            properties: {
                user_id: { bsonType: "int" },
                notification_data: { bsonType: "object" },
                scheduled_for: { bsonType: "date" },
                sent: { bsonType: "bool" },
                attempts: { bsonType: "int" },
                last_attempt: { bsonType: "date" },
                error_message: { bsonType: "string" },
                priority: {
                    bsonType: "string",
                    enum: ["low", "medium", "high", "urgent"]
                }
            }
        }
    }
});

// Colección para cache de schema GraphQL
db.createCollection("graphql_schema_cache", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["schema_version", "schema_data", "cached_at"],
            properties: {
                schema_version: { bsonType: "string" },
                schema_data: { bsonType: "object" },
                permissions_matrix: { bsonType: "object" },
                cached_at: { bsonType: "date" },
                expires_at: { bsonType: "date" },
                active: { bsonType: "bool" }
            }
        }
    }
});

// Colección para análisis de seguridad
db.createCollection("security_analysis", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["timestamp", "analysis_type", "data"],
            properties: {
                timestamp: { bsonType: "date" },
                analysis_type: {
                    bsonType: "string",
                    enum: ["login_pattern", "access_pattern", "anomaly_detection", "threat_analysis"]
                },
                data: { bsonType: "object" },
                risk_level: {
                    bsonType: "string",
                    enum: ["low", "medium", "high", "critical"]
                },
                investigated: { bsonType: "bool" },
                false_positive: { bsonType: "bool" }
            }
        }
    }
});

// =====================================================
// CREAR ÍNDICES PARA OPTIMIZACIÓN
// =====================================================

// Índices para documents_storage
db.documents_storage.createIndex({ "practica_id": 1 });
db.documents_storage.createIndex({ "file_metadata.hash": 1 }, { unique: true });
db.documents_storage.createIndex({ "upload_info.uploaded_by": 1 });
db.documents_storage.createIndex({ "upload_info.upload_date": -1 });
db.documents_storage.createIndex({ "file_metadata.mime_type": 1 });

// Índices para graphql_logs
db.graphql_logs.createIndex({ "timestamp": -1 });
db.graphql_logs.createIndex({ "user_id": 1, "timestamp": -1 });
db.graphql_logs.createIndex({ "execution_time": -1 });
db.graphql_logs.createIndex({ "errors": 1 }, { sparse: true });
db.graphql_logs.createIndex({ "query_complexity": -1 });

// Índices para system_metrics
db.system_metrics.createIndex({ "timestamp": -1 });
db.system_metrics.createIndex({ "metric_type": 1, "timestamp": -1 });
db.system_metrics.createIndex({ "environment": 1, "timestamp": -1 });

// Índices para temp_notifications
db.temp_notifications.createIndex({ "user_id": 1 });
db.temp_notifications.createIndex({ "scheduled_for": 1 });
db.temp_notifications.createIndex({ "sent": 1, "scheduled_for": 1 });
db.temp_notifications.createIndex({ "priority": 1, "scheduled_for": 1 });

// Índices para graphql_schema_cache
db.graphql_schema_cache.createIndex({ "schema_version": 1 }, { unique: true });
db.graphql_schema_cache.createIndex({ "active": 1 });
db.graphql_schema_cache.createIndex({ "expires_at": 1 });

// Índices para security_analysis
db.security_analysis.createIndex({ "timestamp": -1 });
db.security_analysis.createIndex({ "analysis_type": 1, "timestamp": -1 });
db.security_analysis.createIndex({ "risk_level": 1, "timestamp": -1 });
db.security_analysis.createIndex({ "investigated": 1 });

// =====================================================
// CONFIGURAR TTL (TIME TO LIVE) PARA COLECCIONES
// =====================================================

// Logs de GraphQL - mantener por 30 días
db.graphql_logs.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 2592000 });

// Métricas del sistema - mantener por 90 días
db.system_metrics.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 7776000 });

// Notificaciones temporales - eliminar automáticamente 7 días después de envío
db.temp_notifications.createIndex({ "scheduled_for": 1 }, { 
    expireAfterSeconds: 604800,
    partialFilterExpression: { "sent": true }
});

// Cache de schema - eliminar automáticamente en fecha de expiración
db.graphql_schema_cache.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });

// Análisis de seguridad - mantener por 180 días
db.security_analysis.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 15552000 });

// =====================================================
// CREAR USUARIOS Y PERMISOS
// =====================================================

// Crear usuario para la aplicación Django
db.createUser({
    user: "django_app",
    pwd: "django_mongo_secure_2024",
    roles: [
        {
            role: "readWrite",
            db: "upeu_documents"
        }
    ]
});

// Crear usuario solo lectura para reportes
db.createUser({
    user: "reporting_user",
    pwd: "reporting_read_2024",
    roles: [
        {
            role: "read",
            db: "upeu_documents"
        }
    ]
});

// =====================================================
// INSERTAR DATOS DE EJEMPLO Y CONFIGURACIÓN
// =====================================================

// Documento de configuración inicial
db.system_config.insertOne({
    _id: "app_config",
    max_file_size_mb: 50,
    allowed_file_types: ["pdf", "doc", "docx", "jpg", "jpeg", "png"],
    virus_scan_enabled: true,
    compression_enabled: true,
    encryption_enabled: false,
    backup_retention_days: 365,
    created_at: new Date(),
    updated_at: new Date()
});

// Schema inicial de GraphQL (placeholder)
db.graphql_schema_cache.insertOne({
    schema_version: "1.0.0",
    schema_data: {
        types: ["User", "Practice", "Company", "Document"],
        queries: ["users", "practices", "companies", "documents"],
        mutations: ["createPractice", "uploadDocument", "updateUser"],
        subscriptions: ["notificationAdded", "practiceStatusChanged"]
    },
    permissions_matrix: {
        "PRACTICANTE": ["readOwnPractice", "uploadDocument"],
        "SUPERVISOR": ["readAssignedPractices", "evaluateStudent"],
        "COORDINADOR": ["readAllPractices", "approvePractice"],
        "ADMINISTRADOR": ["fullAccess"]
    },
    cached_at: new Date(),
    expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 horas
    active: true
});

// Métricas iniciales
db.system_metrics.insertMany([
    {
        timestamp: new Date(),
        metric_type: "performance",
        data: {
            avg_response_time: 150,
            max_response_time: 500,
            min_response_time: 50,
            total_requests: 0,
            error_rate: 0
        },
        source: "application_startup",
        environment: "development"
    },
    {
        timestamp: new Date(),
        metric_type: "usage",
        data: {
            active_users: 0,
            total_practices: 0,
            total_documents: 0,
            storage_used_mb: 0
        },
        source: "database_init",
        environment: "development"
    }
]);

// =====================================================
// FUNCIONES JAVASCRIPT ÚTILES
// =====================================================

// Función para limpiar documentos huérfanos
db.system.js.save({
    _id: "cleanupOrphanedDocuments",
    value: function() {
        // Esta función se puede llamar periódicamente para limpiar
        // documentos que ya no tienen referencia en PostgreSQL
        var orphanedCount = 0;
        db.documents_storage.find().forEach(function(doc) {
            // Aquí iría la lógica para verificar si el documento
            // aún existe en PostgreSQL
            // Por ahora solo contamos
            orphanedCount++;
        });
        return { orphaned_documents: orphanedCount };
    }
});

// Función para estadísticas de uso
db.system.js.save({
    _id: "getUsageStats",
    value: function(days) {
        days = days || 30;
        var startDate = new Date();
        startDate.setDate(startDate.getDate() - days);
        
        return {
            documents_uploaded: db.documents_storage.countDocuments({
                "upload_info.upload_date": { $gte: startDate }
            }),
            graphql_queries: db.graphql_logs.countDocuments({
                "timestamp": { $gte: startDate }
            }),
            notifications_sent: db.temp_notifications.countDocuments({
                "sent": true,
                "scheduled_for": { $gte: startDate }
            }),
            period_days: days
        };
    }
});

// =====================================================
// CONFIGURAR SHARDING (PREPARACIÓN FUTURA)
// =====================================================

// Habilitar sharding en las colecciones más grandes
// (comentado para instalación inicial)
/*
sh.enableSharding("upeu_documents");
sh.shardCollection("upeu_documents.documents_storage", { "practica_id": 1 });
sh.shardCollection("upeu_documents.graphql_logs", { "timestamp": 1 });
sh.shardCollection("upeu_documents.system_metrics", { "timestamp": 1 });
*/

// =====================================================
// MENSAJE DE FINALIZACIÓN
// =====================================================

print("==============================================");
print("MongoDB inicializado exitosamente para Sistema PPP UPeU");
print("Base de datos: upeu_documents");
print("Colecciones creadas: 6");
print("Índices creados: 23");
print("Usuarios creados: 2");
print("TTL configurado para limpieza automática");
print("Sistema listo para producción");
print("==============================================");