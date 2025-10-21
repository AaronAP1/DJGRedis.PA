"""
Views module para dashboards y reportes.

Expone los ViewSets de la Fase 7:
- DashboardViewSet: Dashboards por rol
- ReportsViewSet: Reportes y exportación
"""

from .dashboards import DashboardViewSet
from .reports import ReportsViewSet

__all__ = [
    'DashboardViewSet',
    'ReportsViewSet',
]
