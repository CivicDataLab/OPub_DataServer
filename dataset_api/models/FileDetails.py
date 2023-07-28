from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.contrib.postgres.fields import ArrayField

from .Resource import Resource
from ..file_paths import _resource_directory_path

fs = FileSystemStorage(location=settings.PRIVATE_FILE_LOCATION, base_url=settings.PRIVATE_FILE_URL)


class FileDetails(models.Model):
    resource = models.OneToOneField(
        Resource, on_delete=models.CASCADE, primary_key=True
    )
    format = models.CharField(max_length=50)
    file = models.FileField(upload_to=_resource_directory_path, blank=True, max_length=1000)
    remote_url = models.URLField(blank=True)
    source_file_name = models.CharField(max_length=100)
    supported_formats = ArrayField(models.CharField(max_length=25, blank=False), blank=True, null=True)
