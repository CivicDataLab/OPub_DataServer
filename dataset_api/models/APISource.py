from django.contrib.postgres.fields import ArrayField
from django.db import models
from encrypted_json_fields.fields import EncryptedJSONField, EncryptedCharField

from dataset_api.models.Organization import Organization


class APISource(models.Model):
    title = models.CharField(max_length=100)
    base_url = models.URLField(null=False, blank=False)
    description = models.CharField(max_length=500)
    api_version = models.CharField(max_length=50, null=True)
    headers = ArrayField(models.JSONField(blank=True, null=True), blank=True, null=True)
    auth_loc = models.CharField(max_length=50, null=True)
    auth_type = models.CharField(max_length=50)
    auth_credentials = EncryptedJSONField(blank=True, null=True)
    auth_token = EncryptedCharField(blank=True, null=True, max_length=2000)
    auth_token_key = models.CharField(blank=True, null=True, max_length=200)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
