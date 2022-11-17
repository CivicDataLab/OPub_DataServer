from django.contrib.postgres.fields import ArrayField
from django.db import models

from dataset_api.models.Dataset import Dataset


class Resource(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, default="Draft")
    # TODO remove masked fields
    masked_fields = ArrayField(
        models.CharField(max_length=10, blank=True), blank=True, null=True
    )
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    byte_size = models.FloatField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    media_type = models.CharField(blank=True, null=True, max_length=100)
    compression_format = models.CharField(blank=True, null=True, max_length=100)
    packaging_format = models.CharField(blank=True, null=True, max_length=100)
    checksum = models.CharField(blank=True, null=True, max_length=100)
