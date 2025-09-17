from django.urls import path
from django.http import JsonResponse


def placeholder(request):
    return JsonResponse({"status": "ok", "module": "practices"})


urlpatterns = [
    path('', placeholder, name='practices-root'),
]
