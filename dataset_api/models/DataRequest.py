from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

from dataset_api.models.DatasetAccessModelRequest import DatasetAccessModelRequest
from dataset_api.file_paths import _data_request_directory_path
from dataset_api.models.Resource import Resource
import uuid

fs = FileSystemStorage(location=settings.PRIVATE_FILE_LOCATION, base_url=settings.PRIVATE_FILE_URL)


class DataRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=_data_request_directory_path, blank=True, null=True
    )
    creation_date = models.DateTimeField(auto_now_add=True, null=True)
    reject_reason = models.CharField(max_length=500, blank=True)
    dataset_access_model_request = models.ForeignKey(DatasetAccessModelRequest, on_delete=models.CASCADE)
    user = models.CharField(max_length=50, blank=True, null=True)
    default = models.BooleanField(default=False, db_index=True)
