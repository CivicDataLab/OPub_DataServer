from django.db import models

from dataset_api.enums import OrganizationTypes
from dataset_api.file_paths import _organization_directory_path


class Organization(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=500)
    logo = models.ImageField(upload_to=_organization_directory_path, blank=True)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    homepage = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    organization_types = models.CharField(
        max_length=15, choices=OrganizationTypes.choices
    )
