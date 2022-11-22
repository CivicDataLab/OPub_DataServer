from django.db import models

from dataset_api.models import APIDetails


class APIParameter(models.Model):
    key = models.CharField(max_length=100, null=False, blank=False)
    format = models.CharField(max_length=100, null=False, blank=False)
    default = models.CharField(max_length=500, default="")
    description = models.CharField(max_length=500, default="")
    api_details = models.ForeignKey(APIDetails, on_delete=models.PROTECT)
