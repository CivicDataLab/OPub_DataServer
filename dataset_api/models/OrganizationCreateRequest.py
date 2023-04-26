from django.db import models

from dataset_api.enums import OrganizationRequestStatusType, OrganizationSubTypes
from dataset_api.file_paths import _organization_file_directory_path, _cdo_notification_directory_path
from dataset_api.models.Organization import Organization
from dataset_api.models.Geography import Geography


class OrganizationCreateRequest(Organization):
    data_description = models.CharField(max_length=500, null=True, blank=True)
    upload_sample_data_file = models.FileField(
        upload_to=_organization_file_directory_path, blank=True
    )
    sample_data_url = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=OrganizationRequestStatusType.choices, blank=False
    )
    cdo_notification = models.FileField(
        upload_to=_cdo_notification_directory_path, blank=True
    )
    username = models.CharField(default="", blank=False, null=False, max_length=200)
    dpa_email = models.EmailField(default="", blank=True, null=True, max_length=100)
    remark = models.CharField(max_length=500, blank=True, null=True)
    address = models.CharField(default="", blank=True, null=True, max_length=500)
    state = models.ForeignKey(Geography, on_delete=models.PROTECT, default='', null=True)
    organization_subtypes = models.CharField(max_length=20, choices=OrganizationSubTypes.choices, blank=True, null=True, default='')
    dpa_name = models.CharField(default="", blank=True, null=True, max_length=200)
    dpa_designation = models.CharField(default="", blank=True, null=True, max_length=200)
    dpa_phone = models.CharField(default="", blank=True, null=True, max_length=15)
    ogd_tid   = models.IntegerField(blank=True, null=True)
