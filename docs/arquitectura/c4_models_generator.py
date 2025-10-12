"""
Modelos C4 para el Sistema de Gestión de Prácticas Profesionales.
Versión independiente que genera JSON y PlantUML sin dependencias externas.

Este archivo puede ejecutarse directamente y genera:
1. Archivo JSON con los modelos C4
2. Archivos PlantUML para cada nivel
3. Documentación en Markdown
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


class C4ModelGenerator:
    """Generador de modelos C4 para el sistema de gestión de prácticas."""
    
    def __init__(self):
        self.workspace = {
            "name": "Sistema de Gestión de Prácticas Profesionales",
            "description": "Sistema para gestión integral de prácticas profesionales universitarias",
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "model": {
                "people": [],
                "softwareSystems": [],
                "containers": [],
                "components": [],
                "codeElements": [],
                "relationships": []
            },
            "views": {
                "systemContextViews": [],
                "containerViews": [],
                "componentViews": [],
                "codeViews": []
            }
        }
    
    def add_person(self, id: str, name: str, description: str, location: str = "External"):
        """Agrega una persona al modelo."""
        person = {
            "id": id,
            "name": name,
            "description": description,
            "location": location,
            "type": "Person",
            "tags": "Person"
        }
        self.workspace["model"]["people"].append(person)
        return person
    
    def add_software_system(self, id: str, name: str, description: str, location: str = "Internal"):
        """Agrega un sistema de software al modelo."""
        system = {
            "id": id,
            "name": name,
            "description": description,
            "location": location,
            "type": "SoftwareSystem",
            "tags": "Software System"
        }
        self.workspace["model"]["softwareSystems"].append(system)
        return system
    
    def add_container(self, id: str, name: str, description: str, technology: str, system_id: str):
        """Agrega un contenedor al modelo."""
        container = {
            "id": id,
            "name": name,
            "description": description,
            "technology": technology,
            "systemId": system_id,
            "type": "Container",
            "tags": "Container"
        }
        self.workspace["model"]["containers"].append(container)
        return container
    
    def add_component(self, id: str, name: str, description: str, technology: str, container_id: str, tags: str = ""):
        """Agrega un componente al modelo."""
        component = {
            "id": id,
            "name": name,
            "description": description,
            "technology": technology,
            "containerId": container_id,
            "type": "Component",
            "tags": f"Component,{tags}".strip(",")
        }
        self.workspace["model"]["components"].append(component)
        return component
    
    def add_code_element(self, id: str, name: str, type: str, component_id: str):
        """Agrega un elemento de código al modelo."""
        code_element = {
            "id": id,
            "name": name,
            "type": type,
            "componentId": component_id,
            "tags": "Code Element"
        }
        self.workspace["model"]["codeElements"].append(code_element)
        return code_element
    
    def add_relationship(self, source_id: str, destination_id: str, description: str, technology: str = ""):
        """Agrega una relación entre elementos."""
        relationship = {
            "sourceId": source_id,
            "destinationId": destination_id,
            "description": description,
            "technology": technology
        }
        self.workspace["model"]["relationships"].append(relationship)
        return relationship
    
    def create_complete_model(self):
        """Crea el modelo C4 completo."""
        
        # =========================
        # CONTEXT LEVEL
        # =========================
        
        # Personas
        estudiante = self.add_person(
            "estudiante", "Estudiante", 
            "Estudiante universitario que realiza prácticas profesionales"
        )
        
        supervisor = self.add_person(
            "supervisor", "Supervisor de Empresa",
            "Supervisor designado por la empresa para guiar al practicante"
        )
        
        coordinador = self.add_person(
            "coordinador", "Coordinador Académico",
            "Coordinador académico que supervisa las prácticas desde la universidad"
        )
        
        secretaria = self.add_person(
            "secretaria", "Secretaria Académica",
            "Personal administrativo que gestiona documentación y procesos"
        )
        
        administrador = self.add_person(
            "administrador", "Administrador del Sistema",
            "Administrador técnico del sistema"
        )
        
        # Sistemas
        sistema_practicas = self.add_software_system(
            "sistema_practicas", "Sistema de Gestión de Prácticas",
            "Sistema web para la gestión integral de prácticas profesionales universitarias con arquitectura hexagonal",
            "Internal"
        )
        
        sistema_academico = self.add_software_system(
            "sistema_academico", "Sistema Académico UPEU",
            "Sistema académico universitario con datos de estudiantes y notas",
            "External"
        )
        
        sunat_api = self.add_software_system(
            "sunat_api", "API SUNAT",
            "Servicios web de SUNAT para validación de RUC y datos empresariales",
            "External"
        )
        
        email_service = self.add_software_system(
            "email_service", "Servicio de Email",
            "Servicio externo para envío de notificaciones por correo electrónico",
            "External"
        )
        
        # Relaciones de contexto
        self.add_relationship("estudiante", "sistema_practicas", "Registra prácticas, sube documentos, consulta estado", "HTTPS")
        self.add_relationship("supervisor", "sistema_practicas", "Supervisa practicantes, evalúa desempeño", "HTTPS")
        self.add_relationship("coordinador", "sistema_practicas", "Aprueba prácticas, supervisa proceso académico", "HTTPS")
        self.add_relationship("secretaria", "sistema_practicas", "Gestiona documentación, valida requisitos", "HTTPS")
        self.add_relationship("administrador", "sistema_practicas", "Administra usuarios, configura sistema", "HTTPS")
        
        self.add_relationship("sistema_practicas", "sistema_academico", "Consulta datos académicos de estudiantes", "REST API")
        self.add_relationship("sistema_practicas", "sunat_api", "Valida datos empresariales y RUC", "REST API")
        self.add_relationship("sistema_practicas", "email_service", "Envía notificaciones por email", "SMTP")
        
        # =========================
        # CONTAINER LEVEL
        # =========================
        
        # Contenedores
        web_app = self.add_container(
            "web_app", "Aplicación Web Django",
            "Aplicación web Django con arquitectura hexagonal que expone REST API y GraphQL API",
            "Python, Django 5.0, DRF, Graphene",
            "sistema_practicas"
        )
        
        postgres_db = self.add_container(
            "postgres_db", "Base de Datos PostgreSQL",
            "Almacena datos principales: usuarios, estudiantes, empresas, prácticas",
            "PostgreSQL 15",
            "sistema_practicas"
        )
        
        redis_cache = self.add_container(
            "redis_cache", "Cache Redis",
            "Cache para sesiones, tokens JWT y datos frecuentemente consultados",
            "Redis 7",
            "sistema_practicas"
        )
        
        mongodb = self.add_container(
            "mongodb", "Base de Datos MongoDB",
            "Almacena documentos, archivos y metadata de prácticas",
            "MongoDB 6",
            "sistema_practicas"
        )
        
        celery_worker = self.add_container(
            "celery_worker", "Worker Celery",
            "Procesa tareas asíncronas: envío de emails, validaciones externas",
            "Celery, Redis Broker",
            "sistema_practicas"
        )
        
        # Relaciones de contenedores
        self.add_relationship("estudiante", "web_app", "Accede vía navegador web", "HTTPS")
        self.add_relationship("supervisor", "web_app", "Accede vía navegador web", "HTTPS")
        self.add_relationship("coordinador", "web_app", "Accede vía navegador web", "HTTPS")
        self.add_relationship("secretaria", "web_app", "Accede vía navegador web", "HTTPS")
        self.add_relationship("administrador", "web_app", "Accede vía navegador web", "HTTPS")
        
        self.add_relationship("web_app", "postgres_db", "Lee y escribe datos", "SQL/TCP")
        self.add_relationship("web_app", "redis_cache", "Cache y sesiones", "Redis Protocol")
        self.add_relationship("web_app", "mongodb", "Gestiona documentos", "MongoDB Protocol")
        self.add_relationship("web_app", "celery_worker", "Encola tareas", "Redis Queue")
        
        self.add_relationship("celery_worker", "postgres_db", "Lee datos para procesamiento", "SQL/TCP")
        self.add_relationship("celery_worker", "mongodb", "Procesa documentos", "MongoDB Protocol")
        
        self.add_relationship("web_app", "sistema_academico", "Consulta datos académicos", "REST API")
        self.add_relationship("celery_worker", "sunat_api", "Valida RUC empresas", "REST API")
        self.add_relationship("celery_worker", "email_service", "Envía notificaciones", "SMTP")
        
        # =========================
        # COMPONENT LEVEL (Arquitectura Hexagonal)
        # =========================
        
        # DOMINIO (Core)
        domain_entities = self.add_component(
            "domain_entities", "Entidades del Dominio",
            "User, Student, Company, Supervisor, Practice - Lógica de negocio pura",
            "Python Classes", "web_app", "Domain"
        )
        
        domain_value_objects = self.add_component(
            "domain_value_objects", "Value Objects",
            "Email, RUC, CodigoEstudiante, Telefono - Objetos inmutables",
            "Python Dataclasses", "web_app", "Domain"
        )
        
        domain_enums = self.add_component(
            "domain_enums", "Enumeraciones",
            "UserRole, PracticeStatus, CompanyStatus - Estados del sistema",
            "Python Enums", "web_app", "Domain"
        )
        
        # PUERTOS (Interfaces)
        primary_ports = self.add_component(
            "primary_ports", "Puertos Primarios",
            "Interfaces para casos de uso - Driving adapters",
            "Python ABC", "web_app", "Port"
        )
        
        secondary_ports = self.add_component(
            "secondary_ports", "Puertos Secundarios",
            "Interfaces para repositorios y servicios - Driven adapters",
            "Python ABC", "web_app", "Port"
        )
        
        # APLICACIÓN (Use Cases)
        use_cases = self.add_component(
            "use_cases", "Casos de Uso",
            "AuthenticationUseCase, UserManagementUseCase, PracticeManagementUseCase",
            "Python Classes", "web_app", "UseCase"
        )
        
        dto_layer = self.add_component(
            "dto_layer", "DTOs",
            "Data Transfer Objects para comunicación entre capas",
            "Python Dataclasses", "web_app", "UseCase"
        )
        
        # ADAPTADORES PRIMARIOS (Web Layer)
        rest_api = self.add_component(
            "rest_api", "REST API",
            "Endpoints REST para operaciones CRUD y autenticación",
            "Django REST Framework", "web_app", "PrimaryAdapter"
        )
        
        graphql_api = self.add_component(
            "graphql_api", "GraphQL API",
            "Endpoint GraphQL para consultas flexibles",
            "Graphene Django", "web_app", "PrimaryAdapter"
        )
        
        # ADAPTADORES SECUNDARIOS (Infrastructure)
        user_repository = self.add_component(
            "user_repository", "User Repository",
            "Implementación de persistencia para usuarios",
            "Django ORM", "web_app", "SecondaryAdapter"
        )
        
        practice_repository = self.add_component(
            "practice_repository", "Practice Repository",
            "Implementación de persistencia para prácticas",
            "Django ORM", "web_app", "SecondaryAdapter"
        )
        
        security_service = self.add_component(
            "security_service", "Security Service",
            "Autenticación JWT, encriptación, rate limiting",
            "JWT, bcrypt", "web_app", "SecondaryAdapter"
        )
        
        cache_service = self.add_component(
            "cache_service", "Cache Service",
            "Servicio de cache para optimización",
            "Redis Client", "web_app", "SecondaryAdapter"
        )
        
        logging_service = self.add_component(
            "logging_service", "Logging Service",
            "Servicio de logging y auditoría de seguridad",
            "Python logging", "web_app", "SecondaryAdapter"
        )
        
        # MIDDLEWARE
        auth_middleware = self.add_component(
            "auth_middleware", "Authentication Middleware",
            "Middleware para autenticación JWT y autorización",
            "Django Middleware", "web_app", "Middleware"
        )
        
        rate_limit_middleware = self.add_component(
            "rate_limit_middleware", "Rate Limiting Middleware",
            "Middleware para limitación de tasa de requests",
            "Django Middleware", "web_app", "Middleware"
        )
        
        # Relaciones entre componentes (Arquitectura Hexagonal)
        self.add_relationship("domain_entities", "domain_value_objects", "utiliza")
        self.add_relationship("domain_entities", "domain_enums", "utiliza")
        
        self.add_relationship("use_cases", "domain_entities", "opera sobre")
        self.add_relationship("use_cases", "secondary_ports", "depende de")
        self.add_relationship("use_cases", "dto_layer", "utiliza")
        
        self.add_relationship("rest_api", "primary_ports", "implementa")
        self.add_relationship("rest_api", "use_cases", "invoca")
        self.add_relationship("rest_api", "dto_layer", "utiliza")
        
        self.add_relationship("graphql_api", "primary_ports", "implementa")
        self.add_relationship("graphql_api", "use_cases", "invoca")
        self.add_relationship("graphql_api", "dto_layer", "utiliza")
        
        self.add_relationship("user_repository", "secondary_ports", "implementa")
        self.add_relationship("user_repository", "domain_entities", "persiste")
        
        self.add_relationship("practice_repository", "secondary_ports", "implementa")
        self.add_relationship("practice_repository", "domain_entities", "persiste")
        
        self.add_relationship("security_service", "secondary_ports", "implementa")
        self.add_relationship("cache_service", "secondary_ports", "implementa")
        self.add_relationship("logging_service", "secondary_ports", "implementa")
        
        self.add_relationship("auth_middleware", "security_service", "utiliza")
        self.add_relationship("rate_limit_middleware", "cache_service", "utiliza")
        
        # External connections
        self.add_relationship("user_repository", "postgres_db", "persiste en")
        self.add_relationship("practice_repository", "postgres_db", "persiste en")
        self.add_relationship("cache_service", "redis_cache", "conecta a")
        
        # =========================
        # CODE LEVEL
        # =========================
        
        # Clases principales del dominio
        self.add_code_element("user_class", "User", "Entity", "domain_entities")
        self.add_code_element("student_class", "Student", "Entity", "domain_entities")
        self.add_code_element("company_class", "Company", "Entity", "domain_entities")
        self.add_code_element("supervisor_class", "Supervisor", "Entity", "domain_entities")
        self.add_code_element("practice_class", "Practice", "Entity", "domain_entities")
        self.add_code_element("entity_base_class", "Entity", "ABC", "domain_entities")
        
        # Value Objects principales
        self.add_code_element("email_vo", "Email", "ValueObject", "domain_value_objects")
        self.add_code_element("ruc_vo", "RUC", "ValueObject", "domain_value_objects")
        self.add_code_element("codigo_estudiante_vo", "CodigoEstudiante", "ValueObject", "domain_value_objects")
        self.add_code_element("telefono_vo", "Telefono", "ValueObject", "domain_value_objects")
        self.add_code_element("direccion_vo", "Direccion", "ValueObject", "domain_value_objects")
        
        # Enums principales
        self.add_code_element("user_role_enum", "UserRole", "Enum", "domain_enums")
        self.add_code_element("practice_status_enum", "PracticeStatus", "Enum", "domain_enums")
        self.add_code_element("company_status_enum", "CompanyStatus", "Enum", "domain_enums")
        
        # Use Cases principales
        self.add_code_element("auth_use_case", "AuthenticationUseCase", "UseCase", "use_cases")
        self.add_code_element("user_mgmt_use_case", "UserManagementUseCase", "UseCase", "use_cases")
        self.add_code_element("practice_mgmt_use_case", "PracticeManagementUseCase", "UseCase", "use_cases")
        
        # DTOs principales
        self.add_code_element("user_dto", "UserDTO", "DTO", "dto_layer")
        self.add_code_element("practice_dto", "PracticeDTO", "DTO", "dto_layer")
        self.add_code_element("auth_request_dto", "AuthenticationRequest", "DTO", "dto_layer")
        self.add_code_element("api_response_dto", "ApiResponse", "DTO", "dto_layer")
        
        # Crear vistas
        self.create_views()
        
        return self.workspace
    
    def create_views(self):
        """Crea las vistas C4."""
        
        # Vista de Contexto
        context_view = {
            "key": "SystemContext",
            "title": "Sistema de Gestión de Prácticas - Contexto",
            "description": "Vista general del sistema y sus usuarios",
            "softwareSystemId": "sistema_practicas",
            "elements": [
                {"id": "estudiante", "x": 200, "y": 200},
                {"id": "supervisor", "x": 600, "y": 200},
                {"id": "coordinador", "x": 1000, "y": 200},
                {"id": "secretaria", "x": 200, "y": 600},
                {"id": "administrador", "x": 1000, "y": 600},
                {"id": "sistema_practicas", "x": 600, "y": 400},
                {"id": "sistema_academico", "x": 200, "y": 800},
                {"id": "sunat_api", "x": 600, "y": 800},
                {"id": "email_service", "x": 1000, "y": 800}
            ],
            "relationships": "all"
        }
        self.workspace["views"]["systemContextViews"].append(context_view)
        
        # Vista de Contenedores
        container_view = {
            "key": "Containers",
            "title": "Sistema de Gestión de Prácticas - Contenedores",
            "description": "Aplicaciones, servicios y almacenes de datos",
            "softwareSystemId": "sistema_practicas",
            "elements": [
                {"id": "web_app", "x": 600, "y": 300},
                {"id": "postgres_db", "x": 200, "y": 600},
                {"id": "redis_cache", "x": 600, "y": 600},
                {"id": "mongodb", "x": 1000, "y": 600},
                {"id": "celery_worker", "x": 600, "y": 800}
            ],
            "relationships": "all"
        }
        self.workspace["views"]["containerViews"].append(container_view)
        
        # Vista de Componentes
        component_view = {
            "key": "Components",
            "title": "Aplicación Web Django - Componentes",
            "description": "Componentes internos siguiendo arquitectura hexagonal",
            "containerId": "web_app",
            "elements": [
                {"id": "rest_api", "x": 200, "y": 200},
                {"id": "graphql_api", "x": 400, "y": 200},
                {"id": "use_cases", "x": 300, "y": 400},
                {"id": "domain_entities", "x": 600, "y": 600},
                {"id": "user_repository", "x": 200, "y": 800},
                {"id": "practice_repository", "x": 400, "y": 800}
            ],
            "relationships": "all"
        }
        self.workspace["views"]["componentViews"].append(component_view)
        
        # Vista de Código
        code_view = {
            "key": "DomainClasses",
            "title": "Entidades del Dominio - Clases",
            "description": "Clases principales del dominio de prácticas",
            "componentId": "domain_entities",
            "elements": [
                {"id": "entity_base_class", "x": 400, "y": 200},
                {"id": "user_class", "x": 200, "y": 400},
                {"id": "student_class", "x": 400, "y": 400},
                {"id": "company_class", "x": 600, "y": 400},
                {"id": "practice_class", "x": 400, "y": 600}
            ],
            "relationships": "all"
        }
        self.workspace["views"]["codeViews"].append(code_view)


def generate_plantuml_diagrams(workspace: Dict[str, Any], output_dir: str = "c4_diagrams"):
    """Genera diagramas PlantUML para cada vista."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Diagrama de Contexto
    context_content = """@startuml SystemContext
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml

title Sistema de Gestión de Prácticas - Contexto del Sistema

Person(estudiante, "Estudiante", "Estudiante universitario que realiza prácticas profesionales")
Person(supervisor, "Supervisor de Empresa", "Supervisor designado por la empresa para guiar al practicante")
Person(coordinador, "Coordinador Académico", "Coordinador académico que supervisa las prácticas desde la universidad")
Person(secretaria, "Secretaria Académica", "Personal administrativo que gestiona documentación y procesos")
Person(administrador, "Administrador del Sistema", "Administrador técnico del sistema")

System(sistema_practicas, "Sistema de Gestión de Prácticas", "Sistema web para la gestión integral de prácticas profesionales universitarias con arquitectura hexagonal")

System_Ext(sistema_academico, "Sistema Académico UPEU", "Sistema académico universitario con datos de estudiantes y notas")
System_Ext(sunat_api, "API SUNAT", "Servicios web de SUNAT para validación de RUC y datos empresariales")
System_Ext(email_service, "Servicio de Email", "Servicio externo para envío de notificaciones por correo electrónico")

Rel(estudiante, sistema_practicas, "Registra prácticas, sube documentos, consulta estado")
Rel(supervisor, sistema_practicas, "Supervisa practicantes, evalúa desempeño")
Rel(coordinador, sistema_practicas, "Aprueba prácticas, supervisa proceso académico")
Rel(secretaria, sistema_practicas, "Gestiona documentación, valida requisitos")
Rel(administrador, sistema_practicas, "Administra usuarios, configura sistema")

Rel(sistema_practicas, sistema_academico, "Consulta datos académicos de estudiantes")
Rel(sistema_practicas, sunat_api, "Valida datos empresariales y RUC")
Rel(sistema_practicas, email_service, "Envía notificaciones por email")

SHOW_LEGEND()
@enduml"""
    
    # Diagrama de Contenedores
    container_content = """@startuml Containers
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

title Sistema de Gestión de Prácticas - Vista de Contenedores

Person(user, "Usuario del Sistema", "Cualquier usuario del sistema")

System_Boundary(c1, "Sistema de Gestión de Prácticas") {
    Container(web_app, "Aplicación Web Django", "Python, Django 5.0, DRF, Graphene", "Aplicación web con arquitectura hexagonal que expone REST API y GraphQL API")
    ContainerDb(postgres_db, "Base de Datos PostgreSQL", "PostgreSQL 15", "Almacena datos principales: usuarios, estudiantes, empresas, prácticas")
    ContainerDb(redis_cache, "Cache Redis", "Redis 7", "Cache para sesiones, tokens JWT y datos frecuentemente consultados")
    ContainerDb(mongodb, "Base de Datos MongoDB", "MongoDB 6", "Almacena documentos, archivos y metadata de prácticas")
    Container(celery_worker, "Worker Celery", "Celery, Redis Broker", "Procesa tareas asíncronas: envío de emails, validaciones externas")
}

System_Ext(sistema_academico, "Sistema Académico UPEU", "Sistema académico universitario")
System_Ext(sunat_api, "API SUNAT", "Servicios web de SUNAT")
System_Ext(email_service, "Servicio de Email", "Servicio de notificaciones")

Rel(user, web_app, "Usa", "HTTPS")
Rel(web_app, postgres_db, "Lee y escribe datos", "SQL/TCP")
Rel(web_app, redis_cache, "Cache y sesiones", "Redis Protocol")
Rel(web_app, mongodb, "Gestiona documentos", "MongoDB Protocol")
Rel(web_app, celery_worker, "Encola tareas", "Redis Queue")

Rel(celery_worker, postgres_db, "Lee datos para procesamiento", "SQL/TCP")
Rel(celery_worker, mongodb, "Procesa documentos", "MongoDB Protocol")

Rel(web_app, sistema_academico, "Consulta datos académicos", "REST API")
Rel(celery_worker, sunat_api, "Valida RUC empresas", "REST API")
Rel(celery_worker, email_service, "Envía notificaciones", "SMTP")

SHOW_LEGEND()
@enduml"""
    
    # Diagrama de Componentes
    component_content = """@startuml Components
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title Aplicación Web Django - Vista de Componentes (Arquitectura Hexagonal)

Container(web_app, "Aplicación Web Django", "Django")

Container_Boundary(c1, "Aplicación Web Django") {
    ' Adaptadores Primarios (Driving)
    Component(rest_api, "REST API", "Django REST Framework", "Endpoints REST para operaciones CRUD y autenticación")
    Component(graphql_api, "GraphQL API", "Graphene Django", "Endpoint GraphQL para consultas flexibles")
    
    ' Puertos Primarios
    Component(primary_ports, "Puertos Primarios", "Python ABC", "Interfaces para casos de uso")
    
    ' Capa de Aplicación
    Component(use_cases, "Casos de Uso", "Python Classes", "AuthenticationUseCase, UserManagementUseCase, PracticeManagementUseCase")
    Component(dto_layer, "DTOs", "Python Dataclasses", "Data Transfer Objects para comunicación entre capas")
    
    ' Dominio (Core)
    Component(domain_entities, "Entidades del Dominio", "Python Classes", "User, Student, Company, Supervisor, Practice")
    Component(domain_vo, "Value Objects", "Python Dataclasses", "Email, RUC, CodigoEstudiante, Telefono")
    Component(domain_enums, "Enumeraciones", "Python Enums", "UserRole, PracticeStatus, CompanyStatus")
    
    ' Puertos Secundarios
    Component(secondary_ports, "Puertos Secundarios", "Python ABC", "Interfaces para repositorios y servicios")
    
    ' Adaptadores Secundarios (Driven)
    Component(repositories, "Repositorios", "Django ORM", "User Repository, Practice Repository")
    Component(security_service, "Security Service", "JWT, bcrypt", "Autenticación JWT, encriptación, rate limiting")
    Component(cache_service, "Cache Service", "Redis Client", "Servicio de cache para optimización")
    Component(logging_service, "Logging Service", "Python logging", "Servicio de logging y auditoría")
    
    ' Middleware
    Component(auth_middleware, "Auth Middleware", "Django Middleware", "Autenticación JWT y autorización")
    Component(rate_limit_middleware, "Rate Limit Middleware", "Django Middleware", "Limitación de tasa de requests")
}

ContainerDb(postgres, "PostgreSQL", "Base de datos principal")
ContainerDb(redis, "Redis", "Cache")
ContainerDb(mongodb, "MongoDB", "Documentos")

' Relaciones Hexagonales
Rel(rest_api, primary_ports, "implementa")
Rel(graphql_api, primary_ports, "implementa")
Rel(primary_ports, use_cases, "invoca")

Rel(use_cases, domain_entities, "opera sobre")
Rel(use_cases, secondary_ports, "depende de")
Rel(use_cases, dto_layer, "utiliza")

Rel(domain_entities, domain_vo, "utiliza")
Rel(domain_entities, domain_enums, "utiliza")

Rel(repositories, secondary_ports, "implementa")
Rel(security_service, secondary_ports, "implementa")
Rel(cache_service, secondary_ports, "implementa")
Rel(logging_service, secondary_ports, "implementa")

Rel(repositories, postgres, "persiste en")
Rel(cache_service, redis, "conecta a")
Rel(repositories, mongodb, "almacena documentos en")

Rel(auth_middleware, security_service, "utiliza")
Rel(rate_limit_middleware, cache_service, "utiliza")

SHOW_LEGEND()
@enduml"""
    
    # Diagrama de Código
    code_content = """@startuml DomainClasses
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title Entidades del Dominio - Diagrama de Clases

package "Domain Entities" {
    abstract class Entity {
        +UUID id
        +datetime created_at
        +datetime updated_at
        --
        +__eq__(other)
        +__hash__()
    }
    
    class User {
        +Email email
        +str first_name
        +str last_name
        +UserRole role
        +bool is_active
        +Optional[datetime] last_login
        +Optional[str] password_hash
        --
        +full_name(): str
        +can_perform_action(action: str): bool
        +update_last_login()
        +deactivate()
        +activate()
    }
    
    class Student {
        +User user
        +CodigoEstudiante codigo_estudiante
        +Documento documento
        +Optional[Telefono] telefono
        +Optional[Direccion] direccion
        +Optional[str] carrera
        +Optional[int] semestre_actual
        +Optional[float] promedio_ponderado
        --
        +puede_realizar_practica(): bool
        +actualizar_datos_academicos(semestre: int, promedio: float)
    }
    
    class Company {
        +RUC ruc
        +str razon_social
        +Optional[str] nombre_comercial
        +Optional[Direccion] direccion
        +Optional[Telefono] telefono
        +Optional[Email] email
        +Optional[str] sector_economico
        +Optional[str] tamaño_empresa
        +CompanyStatus status
        +Optional[datetime] fecha_validacion
        --
        +validar_empresa()
        +suspender_empresa(motivo: str)
        +puede_recibir_practicantes(): bool
        +nombre_para_mostrar(): str
    }
    
    class Supervisor {
        +User user
        +Company company
        +Documento documento
        +str cargo
        +Optional[Telefono] telefono
        +Optional[int] años_experiencia
        --
        +puede_supervisar_practica(practice: Practice): bool
    }
    
    class Practice {
        +Student student
        +Company company
        +Optional[Supervisor] supervisor
        +str titulo
        +str descripcion
        +List[str] objetivos
        +Optional[Periodo] periodo
        +int horas_totales
        +str modalidad
        +Optional[str] area_practica
        +PracticeStatus status
        +Optional[Calificacion] calificacion_final
        +str observaciones
        --
        +asignar_supervisor(supervisor: Supervisor)
        +aprobar_practica()
        +iniciar_practica()
        +completar_practica(calificacion: Calificacion)
    }
}

package "Value Objects" {
    class Email {
        +str value
        --
        +is_valid(): bool
    }
    
    class RUC {
        +str value
        --
        +is_valid(): bool
    }
    
    class CodigoEstudiante {
        +str value
        --
        +is_valid(): bool
        +get_year(): int
    }
}

package "Enums" {
    enum UserRole {
        PRACTICANTE
        SUPERVISOR
        COORDINADOR
        SECRETARIA
        ADMINISTRADOR
    }
    
    enum PracticeStatus {
        DRAFT
        PENDING
        APPROVED
        IN_PROGRESS
        COMPLETED
        CANCELLED
    }
    
    enum CompanyStatus {
        PENDING_VALIDATION
        ACTIVE
        SUSPENDED
        INACTIVE
    }
}

' Relaciones
Entity <|-- User
Entity <|-- Student
Entity <|-- Company
Entity <|-- Supervisor
Entity <|-- Practice

Student --> User : user
Supervisor --> User : user
Supervisor --> Company : company
Practice --> Student : student
Practice --> Company : company
Practice --> Supervisor : supervisor

User --> Email : email
User --> UserRole : role
Student --> CodigoEstudiante : codigo_estudiante
Company --> RUC : ruc
Company --> CompanyStatus : status
Practice --> PracticeStatus : status

@enduml"""
    
    # Escribir archivos
    diagrams = {
        "SystemContext.puml": context_content,
        "Containers.puml": container_content,
        "Components.puml": component_content,
        "DomainClasses.puml": code_content
    }
    
    for filename, content in diagrams.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Diagrama PlantUML generado: {filepath}")


def generate_markdown_documentation(workspace: Dict[str, Any], filename: str = "C4_Documentation.md"):
    """Genera documentación en Markdown."""
    
    md_content = f"""# {workspace['name']}

{workspace['description']}

**Versión:** {workspace['version']}  
**Fecha de creación:** {workspace['created']}

## Arquitectura C4 Model

### Nivel 1: Contexto del Sistema

El sistema de gestión de prácticas profesionales es una aplicación web que permite gestionar de manera integral el proceso de prácticas profesionales universitarias.

#### Usuarios del Sistema:
- **Estudiante**: Registra y gestiona sus prácticas profesionales
- **Supervisor de Empresa**: Supervisa y evalúa a los practicantes
- **Coordinador Académico**: Aprueba y supervisa el proceso académico
- **Secretaria Académica**: Gestiona documentación y valida requisitos
- **Administrador del Sistema**: Administra usuarios y configura el sistema

#### Sistemas Externos:
- **Sistema Académico UPEU**: Proporciona datos académicos de estudiantes
- **API SUNAT**: Valida información de empresas mediante RUC
- **Servicio de Email**: Envía notificaciones por correo electrónico

### Nivel 2: Contenedores

#### Aplicación Web Django
- **Tecnología**: Python, Django 5.0, Django REST Framework, Graphene
- **Función**: Aplicación principal con arquitectura hexagonal
- **APIs**: REST API y GraphQL API

#### Almacenamiento de Datos
- **PostgreSQL**: Base de datos principal para entidades del dominio
- **Redis**: Cache para sesiones, tokens JWT y optimización
- **MongoDB**: Almacenamiento de documentos y archivos

#### Procesamiento Asíncrono
- **Celery Worker**: Procesa tareas en segundo plano como envío de emails y validaciones

### Nivel 3: Componentes (Arquitectura Hexagonal)

#### Dominio (Core)
- **Entidades**: User, Student, Company, Supervisor, Practice
- **Value Objects**: Email, RUC, CodigoEstudiante, Telefono, Direccion
- **Enumeraciones**: UserRole, PracticeStatus, CompanyStatus

#### Puertos (Interfaces)
- **Puertos Primarios**: Interfaces para casos de uso (Driving Adapters)
- **Puertos Secundarios**: Interfaces para repositorios y servicios (Driven Adapters)

#### Aplicación
- **Casos de Uso**: AuthenticationUseCase, UserManagementUseCase, PracticeManagementUseCase
- **DTOs**: Data Transfer Objects para comunicación entre capas

#### Adaptadores Primarios (Web Layer)
- **REST API**: Endpoints para operaciones CRUD
- **GraphQL API**: Consultas flexibles y eficientes

#### Adaptadores Secundarios (Infrastructure)
- **Repositorios**: Implementaciones de persistencia
- **Servicios**: Security, Cache, Logging
- **Middleware**: Authentication, Rate Limiting

### Nivel 4: Código

#### Entidades Principales

**User (Usuario)**
- Entidad base para todos los usuarios del sistema
- Roles: PRACTICANTE, SUPERVISOR, COORDINADOR, SECRETARIA, ADMINISTRADOR
- Funciones: autenticación, autorización, gestión de perfiles

**Student (Estudiante)**
- Extiende User con información académica
- Validaciones: semestre mínimo (6to), promedio mínimo (12.0)
- Funciones: gestión de datos académicos, elegibilidad para prácticas

**Company (Empresa)**
- Información de empresas que reciben practicantes
- Validación: RUC válido, estado activo
- Estados: PENDING_VALIDATION, ACTIVE, SUSPENDED, INACTIVE

**Practice (Práctica)**
- Entidad central del sistema
- Estados: DRAFT → PENDING → APPROVED → IN_PROGRESS → COMPLETED
- Validaciones: supervisor asignado, empresa activa, horas mínimas

## Principios de Arquitectura Hexagonal

### Separación de Responsabilidades
- **Dominio**: Lógica de negocio pura, sin dependencias externas
- **Aplicación**: Casos de uso que coordinan el dominio
- **Infraestructura**: Detalles técnicos (BD, APIs, frameworks)

### Inversión de Dependencias
- El dominio no depende de infraestructura
- La infraestructura depende del dominio
- Uso de interfaces (puertos) para desacoplar

### Adaptadores
- **Primarios**: Reciben requests del exterior (REST, GraphQL)
- **Secundarios**: Acceden a recursos externos (BD, APIs, email)

## Patrones de Diseño Utilizados

- **Repository Pattern**: Abstracción del acceso a datos
- **Use Case Pattern**: Encapsulación de lógica de aplicación
- **DTO Pattern**: Transferencia de datos entre capas
- **Value Object Pattern**: Objetos inmutables con validaciones
- **Factory Pattern**: Creación de entidades complejas

## Seguridad

- **Autenticación**: JWT tokens con refresh
- **Autorización**: Role-based access control (RBAC)
- **Validación**: Input validation en todos los niveles
- **Logging**: Auditoría de eventos de seguridad
- **Rate Limiting**: Protección contra ataques de fuerza bruta

## Testing

- **Tests Unitarios**: Dominio y casos de uso
- **Tests de Integración**: Adaptadores y repositorios
- **Tests de API**: Endpoints REST y GraphQL
- **Cobertura mínima**: 80%

---

*Documentación generada automáticamente desde los modelos C4*
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Documentación generada: {filename}")


def create_django_endpoint_view():
    """Genera código para un endpoint Django que sirva los modelos C4."""
    
    endpoint_code = '''"""
Vista Django para servir los modelos C4 del sistema.
Archivo: src/adapters/primary/rest_api/views/c4_views.py
"""

from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
import json
import os
from pathlib import Path

class C4ModelsView(View):
    """Vista para servir los modelos C4 en formato JSON."""
    
    @method_decorator(cache_page(60 * 15))  # Cache por 15 minutos
    def get(self, request, *args, **kwargs):
        """Retorna los modelos C4 completos."""
        try:
            # Cargar modelos desde archivo
            models_file = Path(__file__).parent.parent.parent.parent.parent / "docs" / "arquitectura" / "c4_models_sistema_practicas.json"
            
            if models_file.exists():
                with open(models_file, 'r', encoding='utf-8') as f:
                    models = json.load(f)
                return JsonResponse(models, json_dumps_params={'ensure_ascii': False, 'indent': 2})
            else:
                # Generar modelos dinámicamente
                from docs.arquitectura.c4_models_generator import C4ModelGenerator
                generator = C4ModelGenerator()
                models = generator.create_complete_model()
                return JsonResponse(models, json_dumps_params={'ensure_ascii': False, 'indent': 2})
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class C4DiagramView(View):
    """Vista para servir diagramas PlantUML específicos."""
    
    @method_decorator(cache_page(60 * 30))  # Cache por 30 minutos
    def get(self, request, diagram_type, *args, **kwargs):
        """Retorna un diagrama PlantUML específico."""
        
        diagram_files = {
            'context': 'SystemContext.puml',
            'containers': 'Containers.puml', 
            'components': 'Components.puml',
            'code': 'DomainClasses.puml'
        }
        
        if diagram_type not in diagram_files:
            return JsonResponse({
                'error': 'Tipo de diagrama no válido',
                'valid_types': list(diagram_files.keys())
            }, status=400)
        
        try:
            diagram_file = Path(__file__).parent.parent.parent.parent.parent / "docs" / "arquitectura" / "c4_diagrams" / diagram_files[diagram_type]
            
            if diagram_file.exists():
                with open(diagram_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                return HttpResponse(content, content_type='text/plain; charset=utf-8')
            else:
                return JsonResponse({'error': 'Archivo de diagrama no encontrado'}, status=404)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# URLs para agregar a urls.py
"""
# En src/adapters/primary/rest_api/urls.py

from django.urls import path
from .views.c4_views import C4ModelsView, C4DiagramView

urlpatterns = [
    # ... otras URLs
    path('api/v1/c4/models/', C4ModelsView.as_view(), name='c4-models'),
    path('api/v1/c4/diagrams/<str:diagram_type>/', C4DiagramView.as_view(), name='c4-diagram'),
]
"""

# Ejemplo de uso desde el frontend:
"""
// Obtener modelos C4 completos
fetch('/api/v1/c4/models/')
    .then(response => response.json())
    .then(data => console.log('Modelos C4:', data));

// Obtener diagrama específico
fetch('/api/v1/c4/diagrams/context/')
    .then(response => response.text())
    .then(plantuml => console.log('PlantUML:', plantuml));
"""
'''
    
    return endpoint_code


if __name__ == "__main__":
    print("=" * 80)
    print("GENERADOR DE MODELOS C4 - SISTEMA DE GESTIÓN DE PRÁCTICAS PROFESIONALES")
    print("=" * 80)
    
    # Crear generador
    generator = C4ModelGenerator()
    
    # Generar modelos completos
    print("\n1. Generando modelos C4...")
    workspace = generator.create_complete_model()
    
    # Exportar a JSON
    print("\n2. Exportando a JSON...")
    json_filename = "c4_models_sistema_practicas.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(workspace, f, indent=2, ensure_ascii=False)
    print(f"✓ Modelos exportados: {json_filename}")
    
    # Generar diagramas PlantUML
    print("\n3. Generando diagramas PlantUML...")
    generate_plantuml_diagrams(workspace)
    
    # Generar documentación
    print("\n4. Generando documentación...")
    generate_markdown_documentation(workspace)
    
    # Generar código de endpoint Django
    print("\n5. Generando código de endpoint Django...")
    endpoint_code = create_django_endpoint_view()
    with open("django_c4_endpoint.py", 'w', encoding='utf-8') as f:
        f.write(endpoint_code)
    print("✓ Código de endpoint generado: django_c4_endpoint.py")
    
    print("\n" + "=" * 80)
    print("✅ GENERACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 80)
    
    print(f"""
📁 Archivos generados:
├── {json_filename} (Modelos C4 en JSON)
├── C4_Documentation.md (Documentación completa)
├── django_c4_endpoint.py (Código para endpoint Django)
└── c4_diagrams/
    ├── SystemContext.puml (Diagrama de Contexto)
    ├── Containers.puml (Diagrama de Contenedores)
    ├── Components.puml (Diagrama de Componentes)
    └── DomainClasses.puml (Diagrama de Código)

🚀 Para usar:
1. Instalar extensión PlantUML en VS Code
2. Abrir archivos .puml para visualizar diagramas
3. Implementar endpoint Django copiando código de django_c4_endpoint.py

🌐 Endpoints sugeridos:
- GET /api/v1/c4/models/ → Retorna modelos JSON
- GET /api/v1/c4/diagrams/context/ → Retorna PlantUML de contexto
- GET /api/v1/c4/diagrams/containers/ → Retorna PlantUML de contenedores
- GET /api/v1/c4/diagrams/components/ → Retorna PlantUML de componentes
- GET /api/v1/c4/diagrams/code/ → Retorna PlantUML de código

💡 Tip: Los modelos siguen la arquitectura hexagonal de tu proyecto
    """)