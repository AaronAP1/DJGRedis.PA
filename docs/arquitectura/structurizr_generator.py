"""
Generador de modelos C4 usando Structurizr
"""
import json
import os
from structurizr import Workspace, Person, SoftwareSystem, Container, Component, Relationship, Tags
from structurizr.view import SystemContextView, ContainerView, ComponentView, Configuration, Styles
from structurizr.view.automatic_layout import RankDirection, AutomaticLayout

class StructurizrC4Generator:
    """Generador de diagramas C4 usando Structurizr"""
    
    def __init__(self):
        self.workspace = Workspace(
            name="Sistema de Gestión de Prácticas Profesionales",
            description="Arquitectura del sistema documentada con modelo C4 usando arquitectura hexagonal"
        )
        self.model = self.workspace.model
        self.views = self.workspace.views
        
        # Configurar estilos
        self._configure_styles()
        
    def generate_complete_model(self):
        """Genera el modelo C4 completo"""
        # Crear elementos del modelo
        self._create_people()
        self._create_systems()
        self._create_containers()
        self._create_components()
        self._create_relationships()
        
        # Crear vistas
        self._create_views()
        
        return self.workspace
    
    def _configure_styles(self):
        """Configura los estilos visuales"""
        styles = self.views.configuration.styles
        
        # Estilo para personas
        styles.add_element_style(tag=Tags.PERSON).shape("Person").background("#1a237e").color("#ffffff")
        
        # Estilo para sistemas de software
        styles.add_element_style(tag=Tags.SOFTWARE_SYSTEM).background("#0d47a1").color("#ffffff")
        
        # Estilo para sistemas externos
        styles.add_element_style(tag="External System").background("#6c757d").color("#ffffff")
        
        # Estilo para contenedores
        styles.add_element_style(tag=Tags.CONTAINER).background("#2196f3").color("#ffffff")
        
        # Estilo para componentes
        styles.add_element_style(tag=Tags.COMPONENT).background("#64b5f6").color("#000000")
        
        # Estilo para bases de datos
        styles.add_element_style(tag="Database").shape("Cylinder").background("#388e3c").color("#ffffff")
        
        # Estilo para APIs
        styles.add_element_style(tag="API").background("#ff9800").color("#ffffff")
        
    def _create_people(self):
        """Crea las personas del sistema"""
        self.practicante = self.model.add_person(
            name="Practicante",
            description="Estudiante que realiza prácticas profesionales"
        )
        
        self.supervisor = self.model.add_person(
            name="Supervisor",
            description="Supervisor de empresa que guía al practicante"
        )
        
        self.coordinador = self.model.add_person(
            name="Coordinador",
            description="Coordinador académico de prácticas"
        )
        
        self.secretaria = self.model.add_person(
            name="Secretaria",
            description="Personal administrativo"
        )
        
        self.administrador = self.model.add_person(
            name="Administrador",
            description="Administrador del sistema"
        )
    
    def _create_systems(self):
        """Crea los sistemas de software"""
        # Sistema principal
        self.sistema_practicas = self.model.add_software_system(
            name="Sistema de Gestión de Prácticas",
            description="Sistema web para gestionar prácticas profesionales con arquitectura hexagonal"
        )
        
        # Sistemas externos
        self.email_system = self.model.add_software_system(
            name="Sistema de Email",
            description="Servicio de envío de correos electrónicos"
        )
        self.email_system.add_tags("External System")
        
        self.reniec_system = self.model.add_software_system(
            name="API RENIEC",
            description="Servicio de validación de identidad"
        )
        self.reniec_system.add_tags("External System")
        
        self.sunat_system = self.model.add_software_system(
            name="API SUNAT",
            description="Servicio de validación de empresas"
        )
        self.sunat_system.add_tags("External System")
    
    def _create_containers(self):
        """Crea los contenedores del sistema principal"""
        # Web Application
        self.web_app = self.sistema_practicas.add_container(
            name="Aplicación Web",
            description="Aplicación Django con REST API y GraphQL",
            technology="Django 5.0, Python"
        )
        self.web_app.add_tags("API")
        
        # Base de datos principal
        self.database = self.sistema_practicas.add_container(
            name="Base de Datos Principal",
            description="Almacena información de usuarios, empresas y prácticas",
            technology="PostgreSQL"
        )
        self.database.add_tags("Database")
        
        # Cache
        self.cache = self.sistema_practicas.add_container(
            name="Cache",
            description="Cache para mejorar rendimiento",
            technology="Redis"
        )
        self.cache.add_tags("Database")
        
        # Base de datos de documentos
        self.document_db = self.sistema_practicas.add_container(
            name="Base de Datos de Documentos",
            description="Almacena documentos y reportes",
            technology="MongoDB"
        )
        self.document_db.add_tags("Database")
        
        # Procesador de tareas
        self.task_processor = self.sistema_practicas.add_container(
            name="Procesador de Tareas",
            description="Procesa tareas asíncronas y notificaciones",
            technology="Celery"
        )
    
    def _create_components(self):
        """Crea los componentes usando arquitectura hexagonal"""
        # Dominio
        self.domain = self.web_app.add_component(
            name="Dominio",
            description="Entidades, Value Objects y lógica de negocio pura",
            technology="Python Classes"
        )
        
        # Puertos
        self.ports = self.web_app.add_component(
            name="Puertos",
            description="Interfaces que definen contratos para adaptadores",
            technology="Python Interfaces"
        )
        
        # Casos de uso
        self.use_cases = self.web_app.add_component(
            name="Casos de Uso",
            description="Lógica de aplicación y DTOs",
            technology="Python Classes"
        )
        
        # Adaptadores Primarios - REST API
        self.rest_adapter = self.web_app.add_component(
            name="Adaptador REST API",
            description="API REST para comunicación con clientes",
            technology="Django REST Framework"
        )
        
        # Adaptadores Primarios - GraphQL
        self.graphql_adapter = self.web_app.add_component(
            name="Adaptador GraphQL",
            description="API GraphQL para consultas flexibles",
            technology="Graphene-Django"
        )
        
        # Adaptadores Secundarios - Repositorios
        self.repository_adapter = self.web_app.add_component(
            name="Adaptador Repositorio",
            description="Implementación de repositorios para persistencia",
            technology="Django ORM"
        )
        
        # Adaptadores Secundarios - Servicios Externos
        self.external_adapter = self.web_app.add_component(
            name="Adaptador Servicios Externos",
            description="Integración con APIs externas",
            technology="HTTP Clients"
        )
        
        # Middleware de Seguridad
        self.security = self.web_app.add_component(
            name="Middleware de Seguridad",
            description="Autenticación, autorización y validaciones",
            technology="JWT, Django Auth"
        )
    
    def _create_relationships(self):
        """Crea las relaciones entre elementos"""
        # Personas -> Sistema Principal
        self.practicante.uses(self.sistema_practicas, "Gestiona sus prácticas profesionales")
        self.supervisor.uses(self.sistema_practicas, "Supervisa y evalúa practicantes")
        self.coordinador.uses(self.sistema_practicas, "Coordina y aprueba prácticas")
        self.secretaria.uses(self.sistema_practicas, "Administra documentación")
        self.administrador.uses(self.sistema_practicas, "Administra el sistema")
        
        # Sistema Principal -> Sistemas Externos
        self.sistema_practicas.uses(self.email_system, "Envía notificaciones por email")
        self.sistema_practicas.uses(self.reniec_system, "Valida identidad de usuarios")
        self.sistema_practicas.uses(self.sunat_system, "Valida información de empresas")
        
        # Personas -> Contenedores
        self.practicante.uses(self.web_app, "Interactúa a través de la interfaz web")
        self.supervisor.uses(self.web_app, "Accede al sistema web")
        self.coordinador.uses(self.web_app, "Usa la aplicación web")
        self.secretaria.uses(self.web_app, "Utiliza la interfaz web")
        self.administrador.uses(self.web_app, "Administra a través de la web")
        
        # Contenedores -> Contenedores
        self.web_app.uses(self.database, "Lee y escribe datos", "SQL")
        self.web_app.uses(self.cache, "Cachea datos frecuentes", "Redis Protocol")
        self.web_app.uses(self.document_db, "Almacena documentos", "MongoDB Protocol")
        self.web_app.uses(self.task_processor, "Envía tareas asíncronas", "Message Queue")
        self.task_processor.uses(self.database, "Consulta datos", "SQL")
        
        # Contenedores -> Sistemas Externos
        self.web_app.uses(self.email_system, "Envía emails", "SMTP")
        self.web_app.uses(self.reniec_system, "Consulta datos de identidad", "HTTPS")
        self.web_app.uses(self.sunat_system, "Valida RUC de empresas", "HTTPS")
        
        # Componentes (Arquitectura Hexagonal)
        # Adaptadores Primarios -> Casos de Uso
        self.rest_adapter.uses(self.use_cases, "Ejecuta casos de uso")
        self.graphql_adapter.uses(self.use_cases, "Ejecuta casos de uso")
        
        # Casos de Uso -> Dominio
        self.use_cases.uses(self.domain, "Usa entidades y lógica de dominio")
        
        # Casos de Uso -> Puertos
        self.use_cases.uses(self.ports, "Define contratos")
        
        # Adaptadores Secundarios -> Puertos
        self.repository_adapter.uses(self.ports, "Implementa interfaces de repositorio")
        self.external_adapter.uses(self.ports, "Implementa interfaces de servicios externos")
        
        # Middleware -> Todos los componentes
        self.security.uses(self.rest_adapter, "Protege endpoints REST")
        self.security.uses(self.graphql_adapter, "Protege consultas GraphQL")
        
        # Adaptadores Secundarios -> Contenedores
        self.repository_adapter.uses(self.database, "Persiste datos", "Django ORM")
        self.repository_adapter.uses(self.cache, "Cachea consultas", "Redis")
        self.external_adapter.uses(self.email_system, "Envía notificaciones")
    
    def _create_views(self):
        """Crea las vistas del modelo C4"""
        # Vista de Contexto
        context_view = self.views.create_system_context_view(
            software_system=self.sistema_practicas,
            key="SystemContext",
            title="Sistema de Gestión de Prácticas - Contexto",
            description="Vista general del sistema y sus usuarios"
        )
        context_view.add_all_people()
        context_view.add_all_software_systems()
        context_view.automatic_layout = AutomaticLayout(
            rank_direction=RankDirection.TopBottom,
            rank_separation=100,
            node_separation=100
        )
        
        # Vista de Contenedores
        container_view = self.views.create_container_view(
            software_system=self.sistema_practicas,
            key="Containers",
            title="Sistema de Gestión de Prácticas - Contenedores",
            description="Arquitectura de contenedores del sistema"
        )
        container_view.add_all_people()
        container_view.add_all_software_systems()
        container_view.automatic_layout = AutomaticLayout(
            rank_direction=RankDirection.TopBottom,
            rank_separation=100,
            node_separation=100
        )
        
        # Vista de Componentes
        component_view = self.views.create_component_view(
            container=self.web_app,
            key="Components",
            title="Aplicación Web - Componentes (Arquitectura Hexagonal)",
            description="Componentes internos siguiendo arquitectura hexagonal"
        )
        component_view.add_all_containers()
        component_view.add_all_components()
        component_view.automatic_layout = AutomaticLayout(
            rank_direction=RankDirection.TopBottom,
            rank_separation=100,
            node_separation=100
        )
    
    def export_to_json(self, output_path):
        """Exporta el workspace a JSON"""
        workspace_json = self.workspace.to_dict()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workspace_json, f, indent=2, ensure_ascii=False)
        
        return workspace_json
    
    def export_to_dsl(self, output_path):
        """Exporta el workspace a formato DSL de Structurizr"""
        # Nota: structurizr-python no tiene exportación directa a DSL
        # Por ahora exportamos a JSON y creamos un DSL simplificado
        
        dsl_content = f"""workspace "{self.workspace.name}" "{self.workspace.description}" {{
    
    model {{
        # Personas
        practicante = person "Practicante" "Estudiante que realiza prácticas profesionales"
        supervisor = person "Supervisor" "Supervisor de empresa que guía al practicante"  
        coordinador = person "Coordinador" "Coordinador académico de prácticas"
        secretaria = person "Secretaria" "Personal administrativo"
        administrador = person "Administrador" "Administrador del sistema"
        
        # Sistemas de Software
        sistemaPracticas = softwareSystem "Sistema de Gestión de Prácticas" "Sistema web para gestionar prácticas profesionales con arquitectura hexagonal" {{
            
            webApp = container "Aplicación Web" "Aplicación Django con REST API y GraphQL" "Django 5.0, Python"
            database = container "Base de Datos Principal" "Almacena información de usuarios, empresas y prácticas" "PostgreSQL" "Database"
            cache = container "Cache" "Cache para mejorar rendimiento" "Redis" "Database"  
            documentDb = container "Base de Datos de Documentos" "Almacena documentos y reportes" "MongoDB" "Database"
            taskProcessor = container "Procesador de Tareas" "Procesa tareas asíncronas y notificaciones" "Celery"
            
            webApp {{
                dominio = component "Dominio" "Entidades, Value Objects y lógica de negocio pura" "Python Classes"
                puertos = component "Puertos" "Interfaces que definen contratos para adaptadores" "Python Interfaces"
                useCases = component "Casos de Uso" "Lógica de aplicación y DTOs" "Python Classes"
                restAdapter = component "Adaptador REST API" "API REST para comunicación con clientes" "Django REST Framework"
                graphqlAdapter = component "Adaptador GraphQL" "API GraphQL para consultas flexibles" "Graphene-Django"
                repositoryAdapter = component "Adaptador Repositorio" "Implementación de repositorios para persistencia" "Django ORM"
                externalAdapter = component "Adaptador Servicios Externos" "Integración con APIs externas" "HTTP Clients"
                security = component "Middleware de Seguridad" "Autenticación, autorización y validaciones" "JWT, Django Auth"
            }}
        }}
        
        emailSystem = softwareSystem "Sistema de Email" "Servicio de envío de correos electrónicos" "External System"
        reniecSystem = softwareSystem "API RENIEC" "Servicio de validación de identidad" "External System"
        sunatSystem = softwareSystem "API SUNAT" "Servicio de validación de empresas" "External System"
        
        # Relaciones principales
        practicante -> sistemaPracticas "Gestiona sus prácticas profesionales"
        supervisor -> sistemaPracticas "Supervisa y evalúa practicantes"
        coordinador -> sistemaPracticas "Coordina y aprueba prácticas"
        
        sistemaPracticas -> emailSystem "Envía notificaciones por email"
        sistemaPracticas -> reniecSystem "Valida identidad de usuarios"
        sistemaPracticas -> sunatSystem "Valida información de empresas"
    }}
    
    views {{
        systemContext sistemaPracticas "SystemContext" {{
            include *
            autoLayout tb
        }}
        
        container sistemaPracticas "Containers" {{
            include *
            autoLayout tb
        }}
        
        component webApp "Components" {{
            include *
            autoLayout tb
        }}
        
        styles {{
            element "Person" {{
                shape Person
                background #1a237e
                color #ffffff
            }}
            element "Software System" {{
                background #0d47a1
                color #ffffff
            }}
            element "External System" {{
                background #6c757d
                color #ffffff
            }}
            element "Container" {{
                background #2196f3
                color #ffffff
            }}
            element "Component" {{
                background #64b5f6
                color #000000
            }}
            element "Database" {{
                shape Cylinder
                background #388e3c
                color #ffffff
            }}
        }}
    }}
}}"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dsl_content)
        
        return dsl_content

def main():
    """Función principal para generar los modelos"""
    generator = StructurizrC4Generator()
    workspace = generator.generate_complete_model()
    
    # Crear directorio de salida
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Exportar a JSON
    json_path = os.path.join(output_dir, "structurizr_models.json")
    generator.export_to_json(json_path)
    print(f"✅ Modelo JSON exportado: {json_path}")
    
    # Exportar a DSL
    dsl_path = os.path.join(output_dir, "structurizr_workspace.dsl")
    generator.export_to_dsl(dsl_path)
    print(f"✅ Workspace DSL exportado: {dsl_path}")
    
    return workspace

if __name__ == "__main__":
    main()