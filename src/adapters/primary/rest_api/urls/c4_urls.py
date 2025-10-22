"""
URLs para los endpoints de modelos C4.
Archivo: src/adapters/primary/rest_api/urls/c4_urls.py
"""

from django.urls import path
from ..views.c4_views import (
    C4ModelsAPIView,
    C4DiagramAPIView, 
    C4DiagramRawView,
    C4MetadataAPIView
)
from ..views.c4_web_views import (
    C4WebVisualizerView
)

app_name = 'c4'

urlpatterns = [
    # Vista web principal para visualizar modelos C4
    path('', C4WebVisualizerView.as_view(), name='visualizer'),
    
    # API Endpoints
    # Endpoint principal para obtener modelos C4 completos
    path('models/', C4ModelsAPIView.as_view(), name='models'),
    
    # Endpoints para diagramas específicos (JSON response)
    path('diagrams/<str:diagram_type>/', C4DiagramAPIView.as_view(), name='diagram'),
    
    # Endpoints para diagramas como texto plano (para visualizadores)
    path('diagrams/<str:diagram_type>/raw/', C4DiagramRawView.as_view(), name='diagram-raw'),
    
    # Metadatos sobre los modelos C4 disponibles
    path('metadata/', C4MetadataAPIView.as_view(), name='metadata'),
]

"""
Para incluir estas URLs en el proyecto principal, agregar en:
src/adapters/primary/rest_api/urls.py o config/urls.py:

from django.urls import path, include

urlpatterns = [
    # ... otras URLs
    path('api/v1/c4/', include('src.adapters.primary.rest_api.urls.c4_urls')),
]

Esto creará los siguientes endpoints:

GET /api/v1/c4/models/
    - Retorna los modelos C4 completos en JSON
    - Requiere autenticación
    - Cache: 15 minutos

GET /api/v1/c4/diagrams/{type}/
    - Retorna diagrama específico como JSON
    - Tipos: context, containers, components, code
    - Requiere autenticación
    - Cache: 30 minutos

GET /api/v1/c4/diagrams/{type}/raw/
    - Retorna diagrama específico como texto plano
    - Para visualizadores PlantUML
    - Cache: 30 minutos

GET /api/v1/c4/metadata/
    - Retorna metadatos sobre modelos disponibles
    - Estadísticas y información general
    - Requiere autenticación

Ejemplos de uso:

# Obtener modelos completos
curl -H "Authorization: Bearer $TOKEN" \\
     http://localhost:8000/api/v1/c4/models/

# Obtener diagrama de contexto
curl -H "Authorization: Bearer $TOKEN" \\
     http://localhost:8000/api/v1/c4/diagrams/context/

# Obtener PlantUML raw para visualizador
curl http://localhost:8000/api/v1/c4/diagrams/context/raw/

# Obtener metadatos
curl -H "Authorization: Bearer $TOKEN" \\
     http://localhost:8000/api/v1/c4/metadata/
"""