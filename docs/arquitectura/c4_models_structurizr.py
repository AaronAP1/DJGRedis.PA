"""
Modelos C4 para el Sistema de Gestión de Prácticas Profesionales usando Structurizr.

Este archivo define todos los niveles del modelo C4:
- Context: Vista general del sistema y sus usuarios
- Container: Aplicaciones, servicios y almacenes de datos
- Component: Componentes internos siguiendo arquitectura hexagonal
- Code: Clases principales del dominio

Para ejecutar: pip install structurizr-python
"""

from structurizr import Workspace, Person, SoftwareSystem, Container, Component, Tags, Relationship
from structurizr.model import InteractionStyle
from structurizr.view import ViewSet, SystemContextView, ContainerView, ComponentView, CodeView
from structurizr.view import ElementStyle, RelationshipStyle, Configuration
from structurizr.api import StructurizrClient
import os


def create_c4_models():
    """Crea y configura todos los modelos C4 del sistema."""
    
    # Crear workspace
    workspace = Workspace(
        name="Sistema de Gestión de Prácticas Profesionales",
        description="Sistema para gestión integral de prácticas profesionales universitarias"
    )
    
    model = workspace.model
    views = workspace.views
    
    # =========================
    # MODELO DE CONTEXTO (C4 - Context)
    # =========================
    
    # Personas (Actores externos)
    estudiante = model.add_person(
        name="Estudiante",
        description="Estudiante universitario que realiza prácticas profesionales",
        location="External"
    )
    
    supervisor = model.add_person(
        name="Supervisor de Empresa",
        description="Supervisor designado por la empresa para guiar al practicante",
        location="External"
    )
    
    coordinador = model.add_person(
        name="Coordinador Académico",
        description="Coordinador académico que supervisa las prácticas desde la universidad",
        location="External"
    )
    
    secretaria = model.add_person(
        name="Secretaria Académica",
        description="Personal administrativo que gestiona documentación y procesos",
        location="External"
    )
    
    administrador = model.add_person(
        name="Administrador del Sistema",
        description="Administrador técnico del sistema",
        location="External"
    )
    
    # Sistema principal
    sistema_practicas = model.add_software_system(
        name="Sistema de Gestión de Prácticas",
        description="Sistema web para la gestión integral de prácticas profesionales universitarias con arquitectura hexagonal",
        location="Internal"
    )
    
    # Sistemas externos
    sistema_academico = model.add_software_system(
        name="Sistema Académico UPEU",
        description="Sistema académico universitario con datos de estudiantes y notas",
        location="External"
    )
    
    sunat_api = model.add_software_system(
        name="API SUNAT",
        description="Servicios web de SUNAT para validación de RUC y datos empresariales",
        location="External"
    )
    
    email_service = model.add_software_system(
        name="Servicio de Email",
        description="Servicio externo para envío de notificaciones por correo electrónico",
        location="External"
    )
    
    # Relaciones del contexto
    estudiante.uses(sistema_practicas, "Registra prácticas, sube documentos, consulta estado")
    supervisor.uses(sistema_practicas, "Supervisa practicantes, evalúa desempeño")
    coordinador.uses(sistema_practicas, "Aprueba prácticas, supervisa proceso académico")
    secretaria.uses(sistema_practicas, "Gestiona documentación, valida requisitos")
    administrador.uses(sistema_practicas, "Administra usuarios, configura sistema")
    
    sistema_practicas.uses(sistema_academico, "Consulta datos académicos de estudiantes")
    sistema_practicas.uses(sunat_api, "Valida datos empresariales y RUC")
    sistema_practicas.uses(email_service, "Envía notificaciones por email")
    
    # =========================
    # MODELO DE CONTENEDORES (C4 - Container)
    # =========================
    
    # Aplicación web principal
    web_app = sistema_practicas.add_container(
        name="Aplicación Web Django",
        description="Aplicación web Django con arquitectura hexagonal que expone REST API y GraphQL API",
        technology="Python, Django 5.0, DRF, Graphene"
    )
    
    # Base de datos principal
    postgres_db = sistema_practicas.add_container(
        name="Base de Datos PostgreSQL",
        description="Almacena datos principales: usuarios, estudiantes, empresas, prácticas",
        technology="PostgreSQL 15"
    )
    
    # Cache
    redis_cache = sistema_practicas.add_container(
        name="Cache Redis",
        description="Cache para sesiones, tokens JWT y datos frecuentemente consultados",
        technology="Redis 7"
    )
    
    # Base de datos para documentos
    mongodb = sistema_practicas.add_container(
        name="Base de Datos MongoDB",
        description="Almacena documentos, archivos y metadata de prácticas",
        technology="MongoDB 6"
    )
    
    # Cola de tareas
    celery_worker = sistema_practicas.add_container(
        name="Worker Celery",
        description="Procesa tareas asíncronas: envío de emails, validaciones externas",
        technology="Celery, Redis Broker"
    )
    
    # Relaciones de contenedores
    estudiante.uses(web_app, "Accede vía navegador web", "HTTPS")
    supervisor.uses(web_app, "Accede vía navegador web", "HTTPS")
    coordinador.uses(web_app, "Accede vía navegador web", "HTTPS")
    secretaria.uses(web_app, "Accede vía navegador web", "HTTPS")
    administrador.uses(web_app, "Accede vía navegador web", "HTTPS")
    
    web_app.uses(postgres_db, "Lee y escribe datos", "SQL/TCP")
    web_app.uses(redis_cache, "Cache y sesiones", "Redis Protocol")
    web_app.uses(mongodb, "Gestiona documentos", "MongoDB Protocol")
    web_app.uses(celery_worker, "Encola tareas", "Redis Queue")
    
    celery_worker.uses(postgres_db, "Lee datos para procesamiento", "SQL/TCP")
    celery_worker.uses(mongodb, "Procesa documentos", "MongoDB Protocol")
    
    web_app.uses(sistema_academico, "Consulta datos académicos", "REST API")
    celery_worker.uses(sunat_api, "Valida RUC empresas", "REST API")
    celery_worker.uses(email_service, "Envía notificaciones", "SMTP")
    
    # =========================
    # MODELO DE COMPONENTES (C4 - Component) - Arquitectura Hexagonal
    # =========================
    
    # DOMINIO (Core)
    domain_entities = web_app.add_component(
        name="Entidades del Dominio",
        description="User, Student, Company, Supervisor, Practice - Lógica de negocio pura",
        technology="Python Classes"
    )
    
    domain_value_objects = web_app.add_component(
        name="Value Objects",
        description="Email, RUC, CodigoEstudiante, Telefono - Objetos inmutables",
        technology="Python Dataclasses"
    )
    
    domain_enums = web_app.add_component(
        name="Enumeraciones",
        description="UserRole, PracticeStatus, CompanyStatus - Estados del sistema",
        technology="Python Enums"
    )
    
    # PUERTOS (Interfaces)
    primary_ports = web_app.add_component(
        name="Puertos Primarios",
        description="Interfaces para casos de uso - Driving adapters",
        technology="Python ABC"
    )
    
    secondary_ports = web_app.add_component(
        name="Puertos Secundarios",
        description="Interfaces para repositorios y servicios - Driven adapters",
        technology="Python ABC"
    )
    
    # APLICACIÓN (Use Cases)
    use_cases = web_app.add_component(
        name="Casos de Uso",
        description="AuthenticationUseCase, UserManagementUseCase, PracticeManagementUseCase",
        technology="Python Classes"
    )
    
    dto_layer = web_app.add_component(
        name="DTOs",
        description="Data Transfer Objects para comunicación entre capas",
        technology="Python Dataclasses"
    )
    
    # ADAPTADORES PRIMARIOS (Web Layer)
    rest_api = web_app.add_component(
        name="REST API",
        description="Endpoints REST para operaciones CRUD y autenticación",
        technology="Django REST Framework"
    )
    
    graphql_api = web_app.add_component(
        name="GraphQL API",
        description="Endpoint GraphQL para consultas flexibles",
        technology="Graphene Django"
    )
    
    # ADAPTADORES SECUNDARIOS (Infrastructure)
    user_repository = web_app.add_component(
        name="User Repository",
        description="Implementación de persistencia para usuarios",
        technology="Django ORM"
    )
    
    practice_repository = web_app.add_component(
        name="Practice Repository",
        description="Implementación de persistencia para prácticas",
        technology="Django ORM"
    )
    
    security_service = web_app.add_component(
        name="Security Service",
        description="Autenticación JWT, encriptación, rate limiting",
        technology="JWT, bcrypt"
    )
    
    cache_service = web_app.add_component(
        name="Cache Service",
        description="Servicio de cache para optimización",
        technology="Redis Client"
    )
    
    logging_service = web_app.add_component(
        name="Logging Service",
        description="Servicio de logging y auditoría de seguridad",
        technology="Python logging"
    )
    
    # MIDDLEWARE
    auth_middleware = web_app.add_component(
        name="Authentication Middleware",
        description="Middleware para autenticación JWT y autorización",
        technology="Django Middleware"
    )
    
    rate_limit_middleware = web_app.add_component(
        name="Rate Limiting Middleware",
        description="Middleware para limitación de tasa de requests",
        technology="Django Middleware"
    )
    
    # Relaciones entre componentes (Arquitectura Hexagonal)
    
    # Dominio relationships
    domain_entities.uses(domain_value_objects, "utiliza")
    domain_entities.uses(domain_enums, "utiliza")
    
    # Use Cases relationships
    use_cases.uses(domain_entities, "opera sobre")
    use_cases.uses(secondary_ports, "depende de")
    use_cases.uses(dto_layer, "utiliza")
    
    # Primary Adapters relationships
    rest_api.uses(primary_ports, "implementa")
    rest_api.uses(use_cases, "invoca")
    rest_api.uses(dto_layer, "utiliza")
    
    graphql_api.uses(primary_ports, "implementa")
    graphql_api.uses(use_cases, "invoca")
    graphql_api.uses(dto_layer, "utiliza")
    
    # Secondary Adapters relationships
    user_repository.uses(secondary_ports, "implementa")
    user_repository.uses(domain_entities, "persiste")
    
    practice_repository.uses(secondary_ports, "implementa")
    practice_repository.uses(domain_entities, "persiste")
    
    security_service.uses(secondary_ports, "implementa")
    cache_service.uses(secondary_ports, "implementa")
    logging_service.uses(secondary_ports, "implementa")
    
    # Middleware relationships
    auth_middleware.uses(security_service, "utiliza")
    rate_limit_middleware.uses(cache_service, "utiliza")
    
    # External connections
    user_repository.uses(postgres_db, "persiste en")
    practice_repository.uses(postgres_db, "persiste en")
    cache_service.uses(redis_cache, "conecta a")
    
    # =========================
    # MODELO DE CÓDIGO (C4 - Code)
    # =========================
    
    # Clases principales del dominio
    user_class = domain_entities.add_code_element("User")
    student_class = domain_entities.add_code_element("Student")
    company_class = domain_entities.add_code_element("Company")
    supervisor_class = domain_entities.add_code_element("Supervisor")
    practice_class = domain_entities.add_code_element("Practice")
    entity_base_class = domain_entities.add_code_element("Entity")
    
    # Value Objects principales
    email_vo = domain_value_objects.add_code_element("Email")
    ruc_vo = domain_value_objects.add_code_element("RUC")
    codigo_estudiante_vo = domain_value_objects.add_code_element("CodigoEstudiante")
    telefono_vo = domain_value_objects.add_code_element("Telefono")
    direccion_vo = domain_value_objects.add_code_element("Direccion")
    
    # Enums principales
    user_role_enum = domain_enums.add_code_element("UserRole")
    practice_status_enum = domain_enums.add_code_element("PracticeStatus")
    company_status_enum = domain_enums.add_code_element("CompanyStatus")
    
    # Use Cases principales
    auth_use_case = use_cases.add_code_element("AuthenticationUseCase")
    user_mgmt_use_case = use_cases.add_code_element("UserManagementUseCase")
    practice_mgmt_use_case = use_cases.add_code_element("PracticeManagementUseCase")
    
    # DTOs principales
    user_dto = dto_layer.add_code_element("UserDTO")
    practice_dto = dto_layer.add_code_element("PracticeDTO")
    auth_request_dto = dto_layer.add_code_element("AuthenticationRequest")
    api_response_dto = dto_layer.add_code_element("ApiResponse")
    
    # Relaciones entre clases
    user_class.uses(entity_base_class, "hereda de")
    student_class.uses(entity_base_class, "hereda de")
    company_class.uses(entity_base_class, "hereda de")
    supervisor_class.uses(entity_base_class, "hereda de")
    practice_class.uses(entity_base_class, "hereda de")
    
    student_class.uses(user_class, "tiene un")
    supervisor_class.uses(user_class, "tiene un")
    practice_class.uses(student_class, "tiene un")
    practice_class.uses(company_class, "tiene una")
    practice_class.uses(supervisor_class, "tiene un")
    
    user_class.uses(email_vo, "utiliza")
    user_class.uses(user_role_enum, "utiliza")
    student_class.uses(codigo_estudiante_vo, "utiliza")
    student_class.uses(telefono_vo, "utiliza")
    student_class.uses(direccion_vo, "utiliza")
    company_class.uses(ruc_vo, "utiliza")
    company_class.uses(company_status_enum, "utiliza")
    practice_class.uses(practice_status_enum, "utiliza")
    
    # =========================
    # CONFIGURACIÓN DE VISTAS
    # =========================
    
    # Vista de Contexto
    context_view = views.create_system_context_view(
        software_system=sistema_practicas,
        key="SystemContext",
        title="Sistema de Gestión de Prácticas - Contexto",
        description="Vista general del sistema y sus usuarios"
    )
    context_view.add_all_people()
    context_view.add_all_software_systems()
    
    # Vista de Contenedores
    container_view = views.create_container_view(
        software_system=sistema_practicas,
        key="Containers",
        title="Sistema de Gestión de Prácticas - Contenedores",
        description="Aplicaciones, servicios y almacenes de datos"
    )
    container_view.add_all_people()
    container_view.add_all_containers()
    container_view.add_all_external_software_systems()
    
    # Vista de Componentes
    component_view = views.create_component_view(
        container=web_app,
        key="Components",
        title="Aplicación Web Django - Componentes",
        description="Componentes internos siguiendo arquitectura hexagonal"
    )
    component_view.add_all_components()
    component_view.add_all_containers()
    
    # Vista de Código
    code_view = views.create_code_view(
        component=domain_entities,
        key="DomainClasses",
        title="Entidades del Dominio - Clases",
        description="Clases principales del dominio de prácticas"
    )
    code_view.add_all_code_elements()
    
    # =========================
    # ESTILOS Y CONFIGURACIÓN
    # =========================
    
    styles = views.configuration.styles
    
    # Estilos para personas
    styles.add_element_style(Tags.PERSON, background="#1168bd", color="#ffffff", shape="Person")
    
    # Estilos para sistemas
    styles.add_element_style(Tags.SOFTWARE_SYSTEM, background="#1168bd", color="#ffffff")
    styles.add_element_style("External", background="#999999", color="#ffffff")
    
    # Estilos para contenedores
    styles.add_element_style(Tags.CONTAINER, background="#438dd5", color="#ffffff")
    styles.add_element_style("Database", shape="Cylinder", background="#438dd5", color="#ffffff")
    styles.add_element_style("Cache", shape="Cylinder", background="#ff6b6b", color="#ffffff")
    
    # Estilos para componentes
    styles.add_element_style(Tags.COMPONENT, background="#85bbf0", color="#000000")
    styles.add_element_style("Domain", background="#4ecdc4", color="#000000")
    styles.add_element_style("UseCase", background="#45b7d1", color="#000000")
    styles.add_element_style("Adapter", background="#96ceb4", color="#000000")
    
    # Marcar elementos con tags específicos
    postgres_db.add_tags("Database")
    mongodb.add_tags("Database")
    redis_cache.add_tags("Cache")
    
    domain_entities.add_tags("Domain")
    domain_value_objects.add_tags("Domain")
    domain_enums.add_tags("Domain")
    
    use_cases.add_tags("UseCase")
    dto_layer.add_tags("UseCase")
    
    rest_api.add_tags("Adapter")
    graphql_api.add_tags("Adapter")
    user_repository.add_tags("Adapter")
    practice_repository.add_tags("Adapter")
    security_service.add_tags("Adapter")
    cache_service.add_tags("Adapter")
    logging_service.add_tags("Adapter")
    
    sistema_academico.add_tags("External")
    sunat_api.add_tags("External")
    email_service.add_tags("External")
    
    return workspace


def export_to_file(workspace, filename="c4_models.json"):
    """Exporta el workspace a un archivo JSON."""
    import json
    
    # Convertir workspace a diccionario
    workspace_dict = workspace.to_dict()
    
    # Guardar a archivo
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(workspace_dict, f, indent=2, ensure_ascii=False)
    
    print(f"Modelos C4 exportados a: {filename}")


def upload_to_structurizr(workspace, api_key=None, api_secret=None, workspace_id=None):
    """Sube los modelos a Structurizr (requiere cuenta)."""
    
    if not all([api_key, api_secret, workspace_id]):
        print("Para subir a Structurizr, necesitas:")
        print("1. Crear cuenta en https://structurizr.com")
        print("2. Crear un workspace")
        print("3. Obtener API Key, Secret y Workspace ID")
        print("4. Ejecutar: upload_to_structurizr(workspace, 'api_key', 'api_secret', workspace_id)")
        return
    
    try:
        client = StructurizrClient(
            api_key=api_key,
            api_secret=api_secret,
            workspace_id=workspace_id
        )
        
        client.put_workspace(workspace)
        print(f"Workspace subido exitosamente a Structurizr ID: {workspace_id}")
        print(f"Ver en: https://structurizr.com/workspace/{workspace_id}")
        
    except Exception as e:
        print(f"Error al subir a Structurizr: {e}")


def generate_plantumljson(workspace, output_dir="c4_diagrams"):
    """Genera archivos PlantUML para cada vista."""
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Generar para cada vista
    views = workspace.views
    
    for view in views.get_all():
        filename = f"{output_dir}/{view.key}.puml"
        
        # Generar contenido PlantUML básico
        plantuml_content = f"""@startuml {view.key}
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title {view.title}

' {view.description}

"""
        
        # Agregar elementos según el tipo de vista
        if "Context" in view.key:
            plantuml_content += """
Person(estudiante, "Estudiante", "Estudiante universitario que realiza prácticas")
Person(supervisor, "Supervisor", "Supervisor de empresa")
Person(coordinador, "Coordinador", "Coordinador académico")
Person(secretaria, "Secretaria", "Personal administrativo")
Person(administrador, "Administrador", "Administrador del sistema")

System(sistema_practicas, "Sistema de Gestión de Prácticas", "Sistema web para gestión integral de prácticas")
System_Ext(sistema_academico, "Sistema Académico UPEU", "Sistema académico universitario")
System_Ext(sunat_api, "API SUNAT", "Servicios web de SUNAT")
System_Ext(email_service, "Servicio de Email", "Servicio de notificaciones")

Rel(estudiante, sistema_practicas, "Registra prácticas")
Rel(supervisor, sistema_practicas, "Supervisa practicantes")
Rel(coordinador, sistema_practicas, "Aprueba prácticas")
Rel(secretaria, sistema_practicas, "Gestiona documentación")
Rel(administrador, sistema_practicas, "Administra sistema")

Rel(sistema_practicas, sistema_academico, "Consulta datos académicos")
Rel(sistema_practicas, sunat_api, "Valida RUC")
Rel(sistema_practicas, email_service, "Envía notificaciones")
"""
            
        elif "Container" in view.key:
            plantuml_content += """
Person(user, "Usuario", "Usuario del sistema")

System_Boundary(c1, "Sistema de Gestión de Prácticas") {
    Container(web_app, "Aplicación Web Django", "Python, Django, DRF", "API REST y GraphQL con arquitectura hexagonal")
    ContainerDb(postgres, "Base de Datos PostgreSQL", "PostgreSQL", "Datos principales")
    ContainerDb(redis, "Cache Redis", "Redis", "Cache y sesiones")
    ContainerDb(mongodb, "MongoDB", "MongoDB", "Documentos y archivos")
    Container(celery, "Worker Celery", "Celery", "Tareas asíncronas")
}

System_Ext(sistema_academico, "Sistema Académico", "Datos académicos")
System_Ext(sunat_api, "API SUNAT", "Validación RUC")
System_Ext(email_service, "Email Service", "Notificaciones")

Rel(user, web_app, "Usa", "HTTPS")
Rel(web_app, postgres, "Lee/Escribe", "SQL")
Rel(web_app, redis, "Cache", "Redis Protocol")
Rel(web_app, mongodb, "Documentos", "MongoDB Protocol")
Rel(web_app, celery, "Encola tareas")
Rel(celery, email_service, "Envía emails")
Rel(celery, sunat_api, "Valida RUC")
Rel(web_app, sistema_academico, "Consulta datos")
"""
            
        elif "Component" in view.key:
            plantuml_content += """
Container(web_app, "Aplicación Web Django", "Django")

Container_Boundary(c1, "Aplicación Web Django") {
    Component(rest_api, "REST API", "Django REST Framework", "Endpoints REST")
    Component(graphql_api, "GraphQL API", "Graphene Django", "Endpoint GraphQL")
    
    Component(use_cases, "Casos de Uso", "Python", "Lógica de aplicación")
    Component(dto_layer, "DTOs", "Python", "Transfer Objects")
    
    Component(domain_entities, "Entidades", "Python", "Lógica de negocio")
    Component(domain_vo, "Value Objects", "Python", "Objetos inmutables")
    Component(domain_enums, "Enumeraciones", "Python", "Estados del sistema")
    
    Component(repositories, "Repositorios", "Django ORM", "Persistencia")
    Component(security_service, "Security Service", "JWT", "Autenticación")
    Component(cache_service, "Cache Service", "Redis", "Cache")
}

ContainerDb(postgres, "PostgreSQL", "Base de datos principal")
ContainerDb(redis, "Redis", "Cache")

Rel(rest_api, use_cases, "Invoca")
Rel(graphql_api, use_cases, "Invoca")
Rel(use_cases, domain_entities, "Opera sobre")
Rel(use_cases, repositories, "Usa")
Rel(repositories, postgres, "Persiste en")
Rel(cache_service, redis, "Conecta a")
"""
        
        plantuml_content += "\n@enduml"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(plantuml_content)
        
        print(f"Diagrama PlantUML generado: {filename}")


if __name__ == "__main__":
    print("Generando modelos C4 para Sistema de Gestión de Prácticas Profesionales...")
    
    # Crear workspace con todos los modelos C4
    workspace = create_c4_models()
    
    # Exportar a archivo JSON
    export_to_file(workspace, "c4_models_sistema_practicas.json")
    
    # Generar diagramas PlantUML
    generate_plantumljson(workspace)
    
    print("\n" + "="*60)
    print("MODELOS C4 GENERADOS EXITOSAMENTE")
    print("="*60)
    print("\nArchivos generados:")
    print("├── c4_models_sistema_practicas.json (Modelo completo)")
    print("├── c4_diagrams/SystemContext.puml (Diagrama de Contexto)")
    print("├── c4_diagrams/Containers.puml (Diagrama de Contenedores)")
    print("├── c4_diagrams/Components.puml (Diagrama de Componentes)")
    print("└── c4_diagrams/DomainClasses.puml (Diagrama de Código)")
    
    print("\nPara usar:")
    print("1. Instalar dependencias: pip install structurizr-python")
    print("2. Ejecutar: python c4_models_structurizr.py")
    print("3. Abrir diagramas .puml en VS Code con extensión PlantUML")
    print("4. Para Structurizr online: crear cuenta y usar upload_to_structurizr()")
    
    print("\nPara subir a Structurizr:")
    print("workspace = create_c4_models()")
    print("upload_to_structurizr(workspace, 'api_key', 'api_secret', workspace_id)")
    
    print("\nEndpoint local para visualizar (si implementas servidor):")
    print("GET /api/v1/c4/models - Retorna modelos JSON")
    print("GET /api/v1/c4/diagrams/{diagram_type} - Retorna PlantUML")