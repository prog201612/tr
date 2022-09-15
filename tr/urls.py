"""tr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from atelier.urls import atelier_patterns
from atelier.urls_api import api_patterns

urlpatterns = [
    path('api/', include(api_patterns)),
    path('atelier/', include(atelier_patterns)),
    path('', admin.site.urls),
    #path('admin/', admin.site.urls),
]

# Custom titles for admin
admin.site.site_header = "Atelier"
# Custom sub-title
admin.site.index_title = "Administración de Atelier"
# Pestanya del navegador
admin.site.site_title = "Atelier"
