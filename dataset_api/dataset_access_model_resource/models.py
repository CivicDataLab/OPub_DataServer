from django.contrib.postgres.fields import ArrayField
from django.db import models

from dataset_api.dataset_access_model.models import DatasetAccessModel
from dataset_api.models import Resource


class DatasetAccessModelResource(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    fields = ArrayField(models.CharField(max_length=25, blank=False), blank=False, null=False)
    dataset_access_model = models.ForeignKey(DatasetAccessModel, on_delete=models.CASCADE, default="")