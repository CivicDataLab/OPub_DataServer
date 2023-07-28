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
from django.urls import path, include, re_path
from django.views.decorators.csrf import csrf_exempt
from graphene_file_upload.django import FileUploadGraphQLView

from DatasetServer import settings
from activity_log.views import login_logout_activity
from dataset_api import resource_file, organization_logo, license_file, public_download
from dataset_api.data_access_model import contract_file
from dataset_api.data_request import data_request_file
from dataset_api.dataset_access_model_request.token_management import reset_token
from dataset_api.policy import policy_file
from dataset_api.api_resource import api_fetch
from dataset_api.data_preview import data_preview
from dataset_api.dataset import contact_provider
from dataset_api.dataset import dataset_show
from payment.views import initiate_payment, process_payment
from dataset_api.dataset import contact_consumer, remind_dpa

urlpatterns = [
    path("pmu/", admin.site.urls),
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
    path("download/policy/<int:policy_id>/", policy_file.download),
    path("api_preview/<int:resource_id>/", api_fetch.preview),
    path("api_schema/<int:resource_id>/", api_fetch.schema),
    path("data_preview", data_preview.preview),
    path("resource_preview/<int:resource_id>/", api_fetch.preview),
    path("contact_provider", contact_provider.contact_provider),
    path("contact_consumer", contact_consumer.contact_consumer),
    path("subscribe", contact_provider.subscribe),
    path("remind_dpa", remind_dpa.remind_dpa),
    path("graphql", csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True))),
    path("cms/<path:file_path>", public_download.cmsdownload),
    path("public/<path:file_path>", public_download.download),
    path("", include("dataset_api.urls")),
    path('payment/initiatepayment/<int:dataset_access_model_request_id>', initiate_payment),
    path('dataset_show/<int:dataset_id>/', dataset_show.dataset_show),
    path('resettoken/<int:dam_request_id>', reset_token),
    path('payment/process/', process_payment),
    re_path(r'activity/(?P<action>\bloggedin\b|\bloggedout\b)', login_logout_activity, name='case'),
    # path("payment/", include("payment.urls"))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
