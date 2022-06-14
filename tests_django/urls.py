"""Django test project URLs"""
from django.urls import include, path


urlpatterns = [
    path("", include("social_django.urls", namespace="social")),
]
