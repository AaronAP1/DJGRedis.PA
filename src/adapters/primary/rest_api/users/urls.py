from django.urls import path
from django.http import JsonResponse
from .import_views import (
    ImportTemplateXLSXView,
    ImportPreviewView,
    ImportConfirmView,
)
from .export_views import (
    ExportUsersXLSXView,
)


def placeholder(request):
    return JsonResponse({"status": "ok", "module": "users"})


urlpatterns = [
    path('', placeholder, name='users-root'),
    path('import/template.xlsx', ImportTemplateXLSXView.as_view(), name='users-import-template-xlsx'),
    path('import/preview', ImportPreviewView.as_view(), name='users-import-preview'),
    path('import/confirm', ImportConfirmView.as_view(), name='users-import-confirm'),
    path('export.xlsx', ExportUsersXLSXView.as_view(), name='users-export-xlsx'),
]
