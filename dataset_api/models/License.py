from django.db import models

from dataset_api.enums import LicenseStatus
from dataset_api.file_paths import _license_directory_path
from dataset_api.models.Organization import Organization


class License(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=100000)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    created_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, blank=True, null=True)
    remote_url = models.URLField(blank=True)
    file = models.FileField(upload_to=_license_directory_path, blank=True)
    status = models.CharField(max_length=50, choices=LicenseStatus.choices)
    reject_reason = models.CharField(max_length=500, blank=True)
