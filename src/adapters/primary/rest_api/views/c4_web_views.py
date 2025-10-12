"""
Vista web para visualizar los modelos C4 del sistema.
"""

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView
from django.conf import settings
from pathlib import Path
import json


class C4WebVisualizerView(TemplateView):
    """Vista web para visualizar los modelos C4."""
    
    template_name = 'c4/visualizer.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Información básica
        context['title'] = 'Modelos C4 - Sistema de Gestión de Prácticas'
        context['api_endpoints'] = {
            'models': '/api/v1/c4/models/',
            'metadata': '/api/v1/c4/metadata/',
            'diagrams': '/api/v1/c4/diagrams/',
        }
        
        # Tipos de diagramas disponibles
        context['diagram_types'] = [
            {
                'key': 'context',
                'name': 'Contexto del Sistema',
                'description': 'Vista general del sistema y sus usuarios'
            },
            {
                'key': 'containers',
                'name': 'Contenedores',
                'description': 'Aplicaciones, servicios y almacenes de datos'
            },
            {
                'key': 'components',
                'name': 'Componentes',
                'description': 'Arquitectura hexagonal interna'
            },
            {
                'key': 'code',
                'name': 'Código',
                'description': 'Clases del dominio y estructura'
            }
        ]
        
        return context