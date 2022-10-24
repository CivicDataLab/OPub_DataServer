from django.db import models

from dataset_api.enums import OrganizationRequestStatusType
from dataset_api.file_paths import _organization_file_directory_path
from dataset_api.models.Organization import Organization


class OrganizationCreateRequest(Organization):
    data_description = models.CharField(max_length=500)
    upload_sample_data_file = models.FileField(
        upload_to=_organization_file_directory_path, blank=True
    )
    sample_data_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=20, choices=OrganizationRequestStatusType.choices, blank=False
    )
    remark = models.CharField(max_length=500, blank=True, null=True)


class OrganizationRequest(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, blank=False
    )
    description = models.CharField(max_length=500, blank=False)
    issued = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=OrganizationRequestStatusType.choices, blank=False
    )
    modified = models.DateTimeField(auto_now=True)
    user = models.CharField(max_length=50, blank=False, null=False)
    remark = models.CharField(max_length=500, blank=True, null=True)
