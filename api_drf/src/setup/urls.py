"""
URL configuration for setup project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include
from rest_framework.settings import settings
from src.api_core.views import api_root


urlpatterns = [
    path('api/v1/', include('src.auth.urls')),
    path('api/v1/', include('src.identity.urls')),
    path('api/v1/', include('src.permission.urls')),
    path('api/v1/', include('src.pizza.urls')),
]


if settings.DEBUG:
    urlpatterns = [path('api/v1', api_root, name='api-root')] + urlpatterns
