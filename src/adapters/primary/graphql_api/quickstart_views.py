"""
Vista para el GraphiQL Quickstart del sistema JWT PURO.
"""

from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class GraphiQLQuickstartView(TemplateView):
    """
    Vista para mostrar el GraphiQL Quickstart.
    Permite probar fácilmente el sistema JWT PURO.
    """
    template_name = 'graphql/quickstart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'GraphiQL Quickstart - Sistema JWT PURO',
            'description': 'Herramienta para probar el sistema de autenticación JWT PURO',
        })
        return context
