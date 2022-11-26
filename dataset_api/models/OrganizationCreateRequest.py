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
    username = models.CharField(default="", blank=False, null=False, max_length=200)
    remark = models.CharField(max_length=500, blank=True, null=True)
