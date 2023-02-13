from django.db import models

from dataset_api.enums import OrganizationRequestStatusType
from dataset_api.models import Organization


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
    user = models.CharField(max_length=50, blank=True, null=True)
    user_email = models.CharField(default="", max_length=50, blank=False, null=False)
    remark = models.CharField(max_length=500, blank=True, null=True)
