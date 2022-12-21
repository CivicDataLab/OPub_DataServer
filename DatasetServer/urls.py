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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from graphene_file_upload.django import FileUploadGraphQLView

from DatasetServer import settings
from dataset_api import resource_file, organization_logo, license_file
from dataset_api.data_access_model import contract_file
from dataset_api.data_request import data_request_file
from dataset_api.api_resource import api_fetch
from dataset_api.data_preview import data_preview

urlpatterns = [
    path("admin/", admin.site.urls),
    # re_path(r'^download/(?P<resource_id>\d+)/', resource_file.download),
    path("download/request/<uuid:data_request_id>/", data_request_file.download),
    # path("getresource/", data_request_file.get_resource),
    # path("update_data/", data_request_file.update_data),
    path("get_dist_data/", data_request_file.get_dist_data),
    path("refresh_data_token/", data_request_file.refresh_data_token),
    path("refreshtoken/", data_request_file.refresh_token),
    path("download/<int:resource_id>/", resource_file.download),
    path("logo/<int:organization_id>/", organization_logo.logo),
    path("download/license/<int:license_id>/", license_file.download),
    path("download/contract/<int:model_id>/", contract_file.download),
    path("api_preview/<int:resource_id>/", api_fetch.preview),
    path("api_schema/<int:resource_id>/", api_fetch.schema),
    path("data_preview/<int:resource_id>/", data_preview.preview),
    path("resource_preview/<int:resource_id>/", api_fetch.preview),
    path("graphql", csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True))),
    path("", include("dataset_api.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
