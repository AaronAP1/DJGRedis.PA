"""
Vista Django para servir los modelos C4 del sistema.
Implementación para src/adapters/primary/rest_api/views/c4_views.py
"""

from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import json
import os
from pathlib import Path
from typing import Dict, Any


class C4ModelsAPIView(APIView):
    """Vista API para servir los modelos C4 completos."""
    
    # Comentar para permitir acceso sin autenticación durante desarrollo
    # permission_classes = [IsAuthenticated]
    permission_classes = []  # Sin autenticación para facilitar visualización
    
    @method_decorator(cache_page(60 * 15))  # Cache por 15 minutos
    def get(self, request, *args, **kwargs):
        """
        Retorna los modelos C4 completos del sistema.
        
        Returns:
            200: Modelos C4 en formato JSON
            404: Archivo no encontrado
            500: Error interno
        """
        try:
            # Ruta al archivo de modelos C4
            models_file = self._get_models_file_path()
            
            if models_file.exists():
                with open(models_file, 'r', encoding='utf-8') as f:
                    models = json.load(f)
                
                return Response({
                    'success': True,
                    'data': models,
                    'message': 'Modelos C4 obtenidos exitosamente'
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Archivo de modelos C4 no encontrado',
                    'path': str(models_file)
                }, status=status.HTTP_404_NOT_FOUND)
                
        except json.JSONDecodeError as e:
            return Response({
                'success': False,
                'error': f'Error al decodificar JSON: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_models_file_path(self) -> Path:
        """Obtiene la ruta al archivo de modelos C4."""
        base_dir = Path(settings.BASE_DIR)
        
        # Intentar cargar el nuevo archivo web_c4_models.json primero
        web_models_file = base_dir / 'docs' / 'arquitectura' / 'web_c4_models.json'
        if web_models_file.exists():
            return web_models_file
            
        # Fallback al archivo original
        original_file = base_dir / 'docs' / 'arquitectura' / 'c4_models_sistema_practicas.json'
        return original_file


class C4DiagramAPIView(APIView):
    """Vista API para servir diagramas PlantUML específicos."""
    
    # Comentar para permitir acceso sin autenticación durante desarrollo
    # permission_classes = [IsAuthenticated]
    permission_classes = []  # Sin autenticación para facilitar visualización
    
    DIAGRAM_TYPES = {
        'context': 'SystemContext.puml',
        'containers': 'Containers.puml', 
        'components': 'Components.puml',
        'code': 'DomainClasses.puml'
    }
    
    @method_decorator(cache_page(60 * 30))  # Cache por 30 minutos
    def get(self, request, diagram_type, *args, **kwargs):
        """
        Retorna un diagrama PlantUML específico.
        
        Args:
            diagram_type: Tipo de diagrama (context, containers, components, code)
            
        Returns:
            200: Contenido PlantUML
            400: Tipo de diagrama inválido
            404: Archivo no encontrado
            500: Error interno
        """
        
        if diagram_type not in self.DIAGRAM_TYPES:
            return Response({
                'success': False,
                'error': 'Tipo de diagrama no válido',
                'valid_types': list(self.DIAGRAM_TYPES.keys()),
                'provided': diagram_type
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            diagram_file = self._get_diagram_file_path(diagram_type)
            
            if diagram_file.exists():
                with open(diagram_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return Response({
                    'success': True,
                    'data': {
                        'type': diagram_type,
                        'filename': self.DIAGRAM_TYPES[diagram_type],
                        'content': content
                    },
                    'message': f'Diagrama {diagram_type} obtenido exitosamente'
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Archivo de diagrama no encontrado',
                    'path': str(diagram_file)
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_diagram_file_path(self, diagram_type: str) -> Path:
        """Obtiene la ruta al archivo de diagrama específico."""
        base_dir = Path(settings.BASE_DIR)
        
        # Intentar cargar desde el nuevo directorio plantuml_diagrams primero
        new_diagram_file = base_dir / 'docs' / 'arquitectura' / 'plantuml_diagrams' / f'{diagram_type}.puml'
        if new_diagram_file.exists():
            return new_diagram_file
            
        # Fallback al archivo original
        filename = self.DIAGRAM_TYPES[diagram_type]
        return base_dir / 'docs' / 'arquitectura' / 'c4_diagrams' / filename


class C4DiagramRawView(View):
    """Vista para servir diagramas PlantUML como texto plano (para visualizadores)."""
    
    DIAGRAM_TYPES = {
        'context': 'SystemContext.puml',
        'containers': 'Containers.puml', 
        'components': 'Components.puml',
        'code': 'DomainClasses.puml'
    }
    
    @method_decorator(cache_page(60 * 30))
    def get(self, request, diagram_type, *args, **kwargs):
        """Retorna diagrama PlantUML como texto plano."""
        
        if diagram_type not in self.DIAGRAM_TYPES:
            return JsonResponse({
                'error': 'Tipo de diagrama no válido',
                'valid_types': list(self.DIAGRAM_TYPES.keys())
            }, status=400)
        
        try:
            # Obtener ruta del diagrama usando el método actualizado
            diagram_file = self._get_diagram_file_path_raw(diagram_type)
            
            if diagram_file.exists():
                with open(diagram_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                return HttpResponse(content, content_type='text/plain; charset=utf-8')
            else:
                return JsonResponse({'error': 'Archivo no encontrado'}, status=404)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def _get_diagram_file_path_raw(self, diagram_type: str) -> Path:
        """Obtiene la ruta al archivo de diagrama para vista raw."""
        base_dir = Path(settings.BASE_DIR)
        
        # Intentar cargar desde el nuevo directorio plantuml_diagrams primero
        new_diagram_file = base_dir / 'docs' / 'arquitectura' / 'plantuml_diagrams' / f'{diagram_type}.puml'
        if new_diagram_file.exists():
            return new_diagram_file
            
        # Fallback al archivo original
        filename = self.DIAGRAM_TYPES[diagram_type]
        return base_dir / 'docs' / 'arquitectura' / 'c4_diagrams' / filename


class C4MetadataAPIView(APIView):
    """Vista API para obtener metadatos de los modelos C4."""
    
    # Comentar para permitir acceso sin autenticación durante desarrollo
    # permission_classes = [IsAuthenticated]
    permission_classes = []  # Sin autenticación para facilitar visualización
    
    def get(self, request, *args, **kwargs):
        """
        Retorna metadatos sobre los modelos C4 disponibles.
        
        Returns:
            200: Metadatos de los modelos C4
        """
        try:
            models_file = Path(settings.BASE_DIR) / "docs" / "arquitectura" / "c4_models_sistema_practicas.json"
            diagrams_dir = Path(settings.BASE_DIR) / "docs" / "arquitectura" / "c4_diagrams"
            
            # Verificar archivos disponibles
            models_available = models_file.exists()
            available_diagrams = []
            
            if diagrams_dir.exists():
                for diagram_type, filename in C4DiagramAPIView.DIAGRAM_TYPES.items():
                    diagram_path = diagrams_dir / filename
                    if diagram_path.exists():
                        available_diagrams.append({
                            'type': diagram_type,
                            'filename': filename,
                            'size': diagram_path.stat().st_size,
                            'modified': diagram_path.stat().st_mtime
                        })
            
            # Obtener información básica del modelo
            model_info = {}
            if models_available:
                try:
                    with open(models_file, 'r', encoding='utf-8') as f:
                        models_data = json.load(f)
                    
                    model_info = {
                        'name': models_data.get('name', ''),
                        'description': models_data.get('description', ''),
                        'version': models_data.get('version', ''),
                        'created': models_data.get('created', ''),
                        'stats': {
                            'people': len(models_data.get('model', {}).get('people', [])),
                            'software_systems': len(models_data.get('model', {}).get('softwareSystems', [])),
                            'containers': len(models_data.get('model', {}).get('containers', [])),
                            'components': len(models_data.get('model', {}).get('components', [])),
                            'code_elements': len(models_data.get('model', {}).get('codeElements', [])),
                            'relationships': len(models_data.get('model', {}).get('relationships', []))
                        }
                    }
                except:
                    pass
            
            return Response({
                'success': True,
                'data': {
                    'models_available': models_available,
                    'diagrams_available': len(available_diagrams),
                    'available_diagram_types': list(C4DiagramAPIView.DIAGRAM_TYPES.keys()),
                    'diagrams': available_diagrams,
                    'model_info': model_info,
                    'endpoints': {
                        'models': '/api/v1/c4/models/',
                        'diagrams': '/api/v1/c4/diagrams/{type}/',
                        'raw_diagrams': '/api/v1/c4/diagrams/{type}/raw/',
                        'metadata': '/api/v1/c4/metadata/'
                    }
                },
                'message': 'Metadatos C4 obtenidos exitosamente'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error al obtener metadatos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)