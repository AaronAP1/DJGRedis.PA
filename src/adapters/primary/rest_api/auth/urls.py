from django.urls import path
from django.http import JsonResponse


def placeholder(request):
    return JsonResponse({"status": "ok", "module": "auth"})


urlpatterns = [
    path('', placeholder, name='auth-root'),
]
