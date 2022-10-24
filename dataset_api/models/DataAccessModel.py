from django.db import models

from dataset_api.enums import SubscriptionUnits
from dataset_api.file_paths import _contract_directory_path
from dataset_api.models.LicenseAddition import LicenseAddition
from dataset_api.models.License import License
from dataset_api.models.Organization import Organization


class DataAccessModel(models.Model):
    title = models.CharField(max_length=100)
    type = models.CharField(max_length=100, default="OPEN")
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, default="")
    contract = models.FileField(upload_to=_contract_directory_path, blank=True)
    license = models.ForeignKey(License, on_delete=models.CASCADE, blank=False, null=False)
    subscription_quota = models.IntegerField(blank=False)
    subscription_quota_unit = models.CharField(blank=False, choices=SubscriptionUnits.choices, max_length=50)
    rate_limit = models.IntegerField(blank=True)
    rate_limit_unit = models.CharField(blank=True, max_length=100)
    license_additions = models.ManyToManyField(LicenseAddition, blank=True)
