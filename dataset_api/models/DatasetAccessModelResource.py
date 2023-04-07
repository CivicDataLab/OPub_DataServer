from django.contrib.postgres.fields import ArrayField
from django.db import models

from dataset_api.models.DatasetAccessModel import DatasetAccessModel
from dataset_api.models.Resource import Resource
from dataset_api.models.ResourceSchema import ResourceSchema


class DatasetAccessModelResource(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    fields = models.ManyToManyField(ResourceSchema)
    dataset_access_model = models.ForeignKey(DatasetAccessModel, on_delete=models.CASCADE, default="")
    sample_enabled = models.BooleanField(blank=False, null=False, default=False)
    sample_rows = models.IntegerField(blank=False, null=False, default=5)
    parameters = ArrayField(models.JSONField(blank=True, null=True), blank=True, null=True)
