from django.db import models

from dataset_api.dataset_access_model_request.models import DatasetAccessModelRequest
from dataset_api.file_paths import _data_request_directory_path
from dataset_api.models import Resource


class DataRequest(models.Model):
    status = models.CharField(max_length=20)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=_data_request_directory_path, blank=True, null=True
    )
    creation_date = models.DateTimeField(auto_now_add=True, null=True)
    reject_reason = models.CharField(max_length=500, blank=True)
    dataset_access_model_request = models.ForeignKey(DatasetAccessModelRequest, on_delete=models.CASCADE)
    user = models.CharField(max_length=50)