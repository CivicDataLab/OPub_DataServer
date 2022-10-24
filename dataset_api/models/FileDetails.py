from django.db import models

from .Resource import Resource
from ..file_paths import _resource_directory_path


class FileDetails(models.Model):
    resource = models.OneToOneField(
        Resource, on_delete=models.CASCADE, primary_key=True
    )
    format = models.CharField(max_length=15)
    file = models.FileField(upload_to=_resource_directory_path, blank=True)
    remote_url = models.URLField(blank=True)
