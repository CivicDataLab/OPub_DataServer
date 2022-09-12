"""DatasetServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.urls import path, re_path, include
from django.views.decorators.csrf import csrf_exempt
from graphene_file_upload.django import FileUploadGraphQLView

from dataset_api import resource_file

urlpatterns = [
    path('admin/', admin.site.urls),
    # re_path(r'^download/(?P<resource_id>\d+)/', resource_file.download),
    path('download/<int:resource_id>/', resource_file.download),
    path("graphql", csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True))),
    path('', include('dataset_api.urls')),
]
