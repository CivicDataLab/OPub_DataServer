from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

from .Resource import Resource
from ..file_paths import _resource_directory_path

fs = FileSystemStorage(location=settings.PRIVATE_FILE_LOCATION, base_url=settings.PRIVATE_FILE_URL)


class FileDetails(models.Model):
    resource = models.OneToOneField(
        Resource, on_delete=models.CASCADE, primary_key=True
    )
    format = models.CharField(max_length=15)
    file = models.FileField(storage=fs, upload_to=_resource_directory_path, blank=True)
    remote_url = models.URLField(blank=True)
