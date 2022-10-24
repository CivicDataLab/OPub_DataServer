from django.contrib.postgres.fields import ArrayField
from django.db import models

from dataset_api.models.DatasetAccessModel import DatasetAccessModel
from dataset_api.models.Resource import Resource


class DatasetAccessModelResource(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    fields = ArrayField(models.CharField(max_length=25, blank=False), blank=False, null=False)
    dataset_access_model = models.ForeignKey(DatasetAccessModel, on_delete=models.CASCADE, default="")
