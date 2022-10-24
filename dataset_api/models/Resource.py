from django.contrib.postgres.fields import ArrayField
from django.db import models

from dataset_api.models.Dataset import Dataset


class Resource(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, default="Draft")
    masked_fields = ArrayField(
        models.CharField(max_length=10, blank=True), blank=True, null=True
    )
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
