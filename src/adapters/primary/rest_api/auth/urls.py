from django.urls import path
from django.http import JsonResponse
from .views import LogoutView


def placeholder(request):
    return JsonResponse({"status": "ok", "module": "auth"})


urlpatterns = [
    path('', placeholder, name='auth-root'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
]
