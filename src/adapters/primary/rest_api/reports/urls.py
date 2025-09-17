from django.urls import path
from django.http import JsonResponse


def placeholder(request):
    return JsonResponse({"status": "ok", "module": "reports"})


urlpatterns = [
    path('', placeholder, name='reports-root'),
]
