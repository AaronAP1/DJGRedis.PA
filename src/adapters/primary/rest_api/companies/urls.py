from django.urls import path
from django.http import JsonResponse


def placeholder(request):
    return JsonResponse({"status": "ok", "module": "companies"})


urlpatterns = [
    path('', placeholder, name='companies-root'),
]
