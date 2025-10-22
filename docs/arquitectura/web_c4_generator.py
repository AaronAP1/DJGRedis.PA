"""
Generador de diagramas C4 simplificado para visualización web
Genera tanto JSON como diagramas SVG usando bibliotecas web compatibles
"""
import json
import os
import base64
from typing import Dict, List, Any

class WebC4Generator:
    """Generador de diagramas C4 optimizado para visualización web"""
    
    def __init__(self):
        self.model_data = {
            "workspace": {
                "name": "Sistema de Gestión de Prácticas Profesionales",
                "description": "Arquitectura documentada con modelo C4 usando arquitectura hexagonal",
                "version": "2.0"
            },
            "model": {
                "people": [],
                "software_systems": [],
                "containers": [],
                "components": [],
                "relationships": []
            },
            "views": {
                "context": None,
                "containers": None,
                "components": None,
                "code": None
            },
            "diagrams": {}
        }
        
    def generate_complete_model(self):
        """Genera el modelo C4 completo"""
        self._create_people()
        self._create_systems()
        self._create_containers() 
        self._create_components()
        self._create_relationships()
        self._create_views()
        self._generate_diagrams()
        
        return self.model_data
    
    def _create_people(self):
        """Crea las personas del sistema"""
        people = [
            {
                "id": "practicante",
                "name": "Practicante", 
                "description": "Estudiante que realiza prácticas profesionales",
                "external": False
            },
            {
                "id": "supervisor",
                "name": "Supervisor",
                "description": "Supervisor de empresa que guía al practicante", 
                "external": True
            },
            {
                "id": "coordinador",
                "name": "Coordinador",
                "description": "Coordinador académico de prácticas",
                "external": False
            },
            {
                "id": "secretaria", 
                "name": "Secretaria",
                "description": "Personal administrativo",
                "external": False
            },
            {
                "id": "administrador",
                "name": "Administrador",
                "description": "Administrador del sistema",
                "external": False
            }
        ]
        self.model_data["model"]["people"] = people
    
    def _create_systems(self):
        """Crea los sistemas de software"""
        systems = [
            {
                "id": "sistema_practicas",
                "name": "Sistema de Gestión de Prácticas",
                "description": "Sistema web para gestionar prácticas profesionales con arquitectura hexagonal",
                "technology": "Django 5.0, Python",
                "external": False
            },
            {
                "id": "email_system", 
                "name": "Sistema de Email",
                "description": "Servicio de envío de correos electrónicos",
                "technology": "SMTP",
                "external": True
            },
            {
                "id": "reniec_system",
                "name": "API RENIEC", 
                "description": "Servicio de validación de identidad",
                "technology": "REST API",
                "external": True
            },
            {
                "id": "sunat_system",
                "name": "API SUNAT",
                "description": "Servicio de validación de empresas", 
                "technology": "REST API",
                "external": True
            }
        ]
        self.model_data["model"]["software_systems"] = systems
    
    def _create_containers(self):
        """Crea los contenedores del sistema principal"""
        containers = [
            {
                "id": "web_app",
                "name": "Aplicación Web",
                "description": "Aplicación Django con REST API y GraphQL",
                "technology": "Django 5.0, Python",
                "system_id": "sistema_practicas"
            },
            {
                "id": "database",
                "name": "Base de Datos Principal", 
                "description": "Almacena información de usuarios, empresas y prácticas",
                "technology": "PostgreSQL",
                "system_id": "sistema_practicas"
            },
            {
                "id": "cache",
                "name": "Cache",
                "description": "Cache para mejorar rendimiento", 
                "technology": "Redis",
                "system_id": "sistema_practicas"
            },
            {
                "id": "document_db",
                "name": "Base de Datos de Documentos",
                "description": "Almacena documentos y reportes",
                "technology": "MongoDB", 
                "system_id": "sistema_practicas"
            },
            {
                "id": "task_processor",
                "name": "Procesador de Tareas",
                "description": "Procesa tareas asíncronas y notificaciones",
                "technology": "Celery",
                "system_id": "sistema_practicas"
            }
        ]
        self.model_data["model"]["containers"] = containers
    
    def _create_components(self):
        """Crea los componentes usando arquitectura hexagonal"""
        components = [
            # Dominio
            {
                "id": "domain",
                "name": "Dominio",
                "description": "Entidades, Value Objects y lógica de negocio pura",
                "technology": "Python Classes",
                "container_id": "web_app",
                "layer": "domain"
            },
            {
                "id": "ports", 
                "name": "Puertos",
                "description": "Interfaces que definen contratos para adaptadores",
                "technology": "Python Interfaces",
                "container_id": "web_app",
                "layer": "ports"
            },
            
            # Aplicación
            {
                "id": "use_cases",
                "name": "Casos de Uso",
                "description": "Lógica de aplicación y DTOs",
                "technology": "Python Classes", 
                "container_id": "web_app",
                "layer": "application"
            },
            
            # Adaptadores Primarios
            {
                "id": "rest_adapter",
                "name": "Adaptador REST API",
                "description": "API REST para comunicación con clientes",
                "technology": "Django REST Framework",
                "container_id": "web_app",
                "layer": "adapters_primary"
            },
            {
                "id": "graphql_adapter",
                "name": "Adaptador GraphQL", 
                "description": "API GraphQL para consultas flexibles",
                "technology": "Graphene-Django",
                "container_id": "web_app",
                "layer": "adapters_primary"
            },
            
            # Adaptadores Secundarios
            {
                "id": "repository_adapter",
                "name": "Adaptador Repositorio",
                "description": "Implementación de repositorios para persistencia",
                "technology": "Django ORM",
                "container_id": "web_app",
                "layer": "adapters_secondary"
            },
            {
                "id": "external_adapter",
                "name": "Adaptador Servicios Externos",
                "description": "Integración con APIs externas", 
                "technology": "HTTP Clients",
                "container_id": "web_app",
                "layer": "adapters_secondary"
            },
            
            # Infraestructura
            {
                "id": "security",
                "name": "Middleware de Seguridad",
                "description": "Autenticación, autorización y validaciones",
                "technology": "JWT, Django Auth",
                "container_id": "web_app",
                "layer": "infrastructure"
            }
        ]
        self.model_data["model"]["components"] = components
    
    def _create_relationships(self):
        """Crea las relaciones entre elementos"""
        relationships = [
            # Personas -> Sistema Principal
            {"from": "practicante", "to": "sistema_practicas", "description": "Gestiona sus prácticas profesionales", "technology": "HTTPS"},
            {"from": "supervisor", "to": "sistema_practicas", "description": "Supervisa y evalúa practicantes", "technology": "HTTPS"},
            {"from": "coordinador", "to": "sistema_practicas", "description": "Coordina y aprueba prácticas", "technology": "HTTPS"},
            {"from": "secretaria", "to": "sistema_practicas", "description": "Administra documentación", "technology": "HTTPS"},
            {"from": "administrador", "to": "sistema_practicas", "description": "Administra el sistema", "technology": "HTTPS"},
            
            # Sistema Principal -> Sistemas Externos  
            {"from": "sistema_practicas", "to": "email_system", "description": "Envía notificaciones por email", "technology": "SMTP"},
            {"from": "sistema_practicas", "to": "reniec_system", "description": "Valida identidad de usuarios", "technology": "HTTPS"},
            {"from": "sistema_practicas", "to": "sunat_system", "description": "Valida información de empresas", "technology": "HTTPS"},
            
            # Personas -> Contenedores
            {"from": "practicante", "to": "web_app", "description": "Interactúa a través de la interfaz web", "technology": "HTTPS"},
            {"from": "supervisor", "to": "web_app", "description": "Accede al sistema web", "technology": "HTTPS"},
            {"from": "coordinador", "to": "web_app", "description": "Usa la aplicación web", "technology": "HTTPS"},
            
            # Contenedores -> Contenedores
            {"from": "web_app", "to": "database", "description": "Lee y escribe datos", "technology": "SQL"},
            {"from": "web_app", "to": "cache", "description": "Cachea datos frecuentes", "technology": "Redis Protocol"},
            {"from": "web_app", "to": "document_db", "description": "Almacena documentos", "technology": "MongoDB Protocol"},
            {"from": "web_app", "to": "task_processor", "description": "Envía tareas asíncronas", "technology": "Message Queue"},
            
            # Componentes (Arquitectura Hexagonal)
            {"from": "rest_adapter", "to": "use_cases", "description": "Ejecuta casos de uso", "technology": "Python"},
            {"from": "graphql_adapter", "to": "use_cases", "description": "Ejecuta casos de uso", "technology": "Python"},
            {"from": "use_cases", "to": "domain", "description": "Usa entidades y lógica de dominio", "technology": "Python"},
            {"from": "use_cases", "to": "ports", "description": "Define contratos", "technology": "Python"},
            {"from": "repository_adapter", "to": "ports", "description": "Implementa interfaces de repositorio", "technology": "Python"},
            {"from": "external_adapter", "to": "ports", "description": "Implementa interfaces de servicios externos", "technology": "Python"},
            {"from": "security", "to": "rest_adapter", "description": "Protege endpoints REST", "technology": "Python"},
            {"from": "security", "to": "graphql_adapter", "description": "Protege consultas GraphQL", "technology": "Python"}
        ]
        self.model_data["model"]["relationships"] = relationships
    
    def _create_views(self):
        """Crea las definiciones de vistas"""
        self.model_data["views"] = {
            "context": {
                "title": "Sistema de Gestión de Prácticas - Contexto",
                "description": "Vista general del sistema y sus usuarios externos",
                "elements": ["practicante", "supervisor", "coordinador", "secretaria", "administrador", 
                           "sistema_practicas", "email_system", "reniec_system", "sunat_system"],
                "layout": "hierarchical"
            },
            "containers": {
                "title": "Sistema de Gestión de Prácticas - Contenedores", 
                "description": "Arquitectura de contenedores del sistema",
                "elements": ["web_app", "database", "cache", "document_db", "task_processor"],
                "layout": "hierarchical"
            },
            "components": {
                "title": "Aplicación Web - Componentes (Arquitectura Hexagonal)",
                "description": "Componentes internos siguiendo arquitectura hexagonal",
                "elements": ["domain", "ports", "use_cases", "rest_adapter", "graphql_adapter", 
                           "repository_adapter", "external_adapter", "security"],
                "layout": "hexagonal"
            },
            "code": {
                "title": "Estructura de Clases del Dominio",
                "description": "Clases principales del dominio y sus relaciones",
                "elements": ["User", "Student", "Company", "Practice", "Supervisor", "Coordinator"],
                "layout": "class_diagram"
            }
        }
    
    def _generate_diagrams(self):
        """Genera diagramas en diferentes formatos"""
        # Generar diagramas PlantUML para cada vista
        self.model_data["diagrams"] = {
            "context": self._generate_context_plantuml(),
            "containers": self._generate_containers_plantuml(), 
            "components": self._generate_components_plantuml(),
            "code": self._generate_code_plantuml()
        }
    
    def _generate_context_plantuml(self):
        """Genera diagrama PlantUML para vista de contexto"""
        plantuml = """@startuml
!define RECTANGLE class

title Sistema de Gestión de Prácticas - Contexto del Sistema

actor "Practicante" as prac #1a237e
actor "Supervisor" as sup #1a237e  
actor "Coordinador" as coord #1a237e
actor "Secretaria" as sec #1a237e
actor "Administrador" as admin #1a237e

rectangle "Sistema de Gestión\\nde Prácticas" as sys #0d47a1
rectangle "Sistema de Email" as email #6c757d
rectangle "API RENIEC" as reniec #6c757d
rectangle "API SUNAT" as sunat #6c757d

prac --> sys : Gestiona sus\\nprácticas profesionales
sup --> sys : Supervisa y evalúa\\npracticantes  
coord --> sys : Coordina y aprueba\\nprácticas
sec --> sys : Administra\\ndocumentación
admin --> sys : Administra\\nel sistema

sys --> email : Envía notificaciones\\npor email
sys --> reniec : Valida identidad\\nde usuarios
sys --> sunat : Valida información\\nde empresas

@enduml"""
        return plantuml
    
    def _generate_containers_plantuml(self):
        """Genera diagrama PlantUML para vista de contenedores"""
        plantuml = """@startuml
!define RECTANGLE class

title Sistema de Gestión de Prácticas - Contenedores

actor "Usuarios" as users #1a237e

package "Sistema de Gestión de Prácticas" {
    rectangle "Aplicación Web\\n[Django 5.0, Python]" as webapp #2196f3
    database "Base de Datos Principal\\n[PostgreSQL]" as db #388e3c
    database "Cache\\n[Redis]" as cache #388e3c  
    database "Base de Datos de Documentos\\n[MongoDB]" as docdb #388e3c
    rectangle "Procesador de Tareas\\n[Celery]" as tasks #2196f3
}

rectangle "Sistema de Email" as email #6c757d
rectangle "API RENIEC" as reniec #6c757d
rectangle "API SUNAT" as sunat #6c757d

users --> webapp : Accede vía HTTPS
webapp --> db : Lee/escribe datos\\n[SQL]
webapp --> cache : Cachea datos\\n[Redis Protocol]  
webapp --> docdb : Almacena documentos\\n[MongoDB Protocol]
webapp --> tasks : Envía tareas\\n[Message Queue]
tasks --> db : Consulta datos\\n[SQL]

webapp --> email : Envía emails\\n[SMTP]
webapp --> reniec : Consulta identidad\\n[HTTPS]
webapp --> sunat : Valida empresas\\n[HTTPS]

@enduml"""
        return plantuml
    
    def _generate_components_plantuml(self):
        """Genera diagrama PlantUML para vista de componentes (Arquitectura Hexagonal)"""
        plantuml = """@startuml
!define RECTANGLE class

title Aplicación Web - Componentes (Arquitectura Hexagonal)

package "Adaptadores Primarios" #e8eaf6 {
    rectangle "REST API\\n[Django REST Framework]" as rest #ff9800
    rectangle "GraphQL API\\n[Graphene-Django]" as graphql #ff9800
}

package "Aplicación" #e3f2fd {
    rectangle "Casos de Uso\\n[Python Classes]" as usecase #2196f3
}

package "Dominio" #e8f5e8 {
    rectangle "Entidades\\n[Python Classes]" as domain #4caf50
    rectangle "Puertos\\n[Python Interfaces]" as ports #4caf50
}

package "Adaptadores Secundarios" #fff3e0 {
    rectangle "Repositorio\\n[Django ORM]" as repo #ff9800
    rectangle "Servicios Externos\\n[HTTP Clients]" as external #ff9800
}

package "Infraestructura" #fce4ec {
    rectangle "Seguridad\\n[JWT, Django Auth]" as security #e91e63
}

rest --> usecase : Ejecuta casos de uso
graphql --> usecase : Ejecuta casos de uso
usecase --> domain : Usa entidades y\\nlógica de dominio
usecase --> ports : Define contratos
repo --> ports : Implementa interfaces\\nde repositorio
external --> ports : Implementa interfaces\\nde servicios externos
security --> rest : Protege endpoints
security --> graphql : Protege consultas

@enduml"""
        return plantuml
    
    def _generate_code_plantuml(self):
        """Genera diagrama PlantUML para vista de código"""
        plantuml = """@startuml
!define RECTANGLE class

title Estructura de Clases del Dominio

class User {
    +id: UUID
    +email: str
    +role: UserRole
    +is_active: bool
    +created_at: datetime
    --
    +authenticate()
    +change_password()
    +deactivate()
}

class Student {
    +student_code: str
    +semester: int
    +gpa: float
    +career: str
    --
    +is_eligible_for_practice()
    +calculate_hours_completed()
}

class Company {
    +ruc: str
    +business_name: str
    +legal_representative: str
    +status: CompanyStatus
    --
    +validate_ruc()
    +activate()
    +deactivate()
}

class Practice {
    +id: UUID
    +student: Student
    +company: Company
    +supervisor: Supervisor
    +status: PracticeStatus
    +start_date: date
    +end_date: date
    +total_hours: int
    --
    +approve()
    +start()
    +complete()
    +calculate_progress()
}

class Supervisor {
    +professional_license: str
    +years_experience: int
    +specialization: str
    --
    +assign_to_practice()
    +evaluate_student()
}

class Coordinator {
    +department: str
    +academic_level: str
    --
    +approve_practice()
    +assign_supervisor()
    +generate_reports()
}

User <|-- Student
User <|-- Supervisor  
User <|-- Coordinator
Student ||--o{ Practice
Company ||--o{ Practice
Supervisor ||--o{ Practice
Practice }o--|| Coordinator

@enduml"""
        return plantuml
    
    def export_to_json(self, output_path):
        """Exporta el modelo a JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.model_data, f, indent=2, ensure_ascii=False)
        
        return self.model_data
    
    def export_plantuml_files(self, output_dir):
        """Exporta archivos PlantUML individuales"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for view_name, plantuml_code in self.model_data["diagrams"].items():
            file_path = os.path.join(output_dir, f"{view_name}.puml")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(plantuml_code)
            print(f"✅ Diagrama PlantUML exportado: {file_path}")

def main():
    """Función principal"""
    generator = WebC4Generator()
    model = generator.generate_complete_model()
    
    # Directorio de salida
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Exportar JSON
    json_path = os.path.join(output_dir, "web_c4_models.json")
    generator.export_to_json(json_path)
    print(f"✅ Modelo JSON exportado: {json_path}")
    
    # Exportar archivos PlantUML
    plantuml_dir = os.path.join(output_dir, "plantuml_diagrams")
    generator.export_plantuml_files(plantuml_dir)
    
    # Mostrar estadísticas
    print(f"\n📊 Estadísticas del modelo:")
    print(f"   - Personas: {len(model['model']['people'])}")
    print(f"   - Sistemas: {len(model['model']['software_systems'])}")
    print(f"   - Contenedores: {len(model['model']['containers'])}")
    print(f"   - Componentes: {len(model['model']['components'])}")
    print(f"   - Relaciones: {len(model['model']['relationships'])}")
    print(f"   - Vistas: {len(model['views'])}")
    
    return model

if __name__ == "__main__":
    main()