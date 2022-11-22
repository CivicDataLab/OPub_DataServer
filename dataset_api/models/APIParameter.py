from django.db import models

from dataset_api.models import APIDetails


class APIParameter(models.Model):
    key = models.CharField(max_length=100)
    format = models.CharField(max_length=100)
    default = models.CharField(max_length=100)
    api_details = models.ForeignKey(APIDetails, on_delete=models.PROTECT)
