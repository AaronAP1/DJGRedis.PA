"""
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
