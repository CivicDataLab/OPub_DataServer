from django.db import models

from .Dataset import Dataset
from ..file_paths import _info_directory_path


class AdditionalInfo(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    remote_url = models.URLField(blank=True)
    format = models.CharField(max_length=15)
    type = models.CharField(max_length=50)
    file = models.FileField(upload_to=_info_directory_path, blank=True)
