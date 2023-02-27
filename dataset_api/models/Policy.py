from django.db import models

from dataset_api.file_paths import _policy_directory_path
from dataset_api.policy.enums import PolicyStatus
from dataset_api.models import Organization


class Policy(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=100000)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, blank=True, null=True)
    remote_url = models.URLField(blank=True)
    file = models.FileField(upload_to=_policy_directory_path, blank=True)
    status = models.CharField(max_length=50, choices=PolicyStatus.choices)
    reject_reason = models.CharField(max_length=500, blank=True)
