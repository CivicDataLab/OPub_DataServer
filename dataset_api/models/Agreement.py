from django.db import models as models

from dataset_api.file_paths import _agreement_directory_path
from dataset_api.license.enums import AgreementStatus
from dataset_api.models import DatasetAccessModelRequest
from dataset_api.models.DatasetAccessModel import DatasetAccessModel


class Agreement(models.Model):
    dataset_access_model = models.ForeignKey(DatasetAccessModel, on_delete=models.CASCADE, related_name="agreements")
    status = models.CharField(choices=AgreementStatus.choices, max_length=15)
    accepted_agreement = models.FileField(upload_to=_agreement_directory_path, blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    dataset_access_model_request = models.ForeignKey(DatasetAccessModelRequest, on_delete=models.CASCADE)
