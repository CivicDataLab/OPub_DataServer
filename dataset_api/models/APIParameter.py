from django.contrib.postgres.fields import ArrayField
from django.db import models

from dataset_api.enums import ParameterTypes
from dataset_api.models import APIDetails


class APIParameter(models.Model):
    key = models.CharField(max_length=100, null=False, blank=False)
    format = models.CharField(max_length=100, null=False, blank=False)
    default = models.CharField(max_length=500, default="")
    description = models.CharField(max_length=500, default="")
    api_details = models.ForeignKey(APIDetails, on_delete=models.PROTECT)
    type = models.CharField(choices=ParameterTypes.choices, max_length=50)
    options = ArrayField(models.CharField(max_length=100, default=""), null=True, blank=True)
    download_options = ArrayField(models.CharField(max_length=100, default=""), null=True, blank=True)
    download_api_options_same = models.BooleanField(blank=False, null=False, default=False)
