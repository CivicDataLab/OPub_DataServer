from django.db import models

from dataset_api.models.License import License


class LicenseAddition(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    generic_item = models.BooleanField()
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    license = models.ForeignKey(License, on_delete=models.CASCADE, null=False, blank=False)
