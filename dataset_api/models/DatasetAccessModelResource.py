from django.contrib.postgres.fields import ArrayField
from django.db import models

from dataset_api.models.DatasetAccessModel import DatasetAccessModel
from dataset_api.models.Resource import Resource
from dataset_api.models.ResourceSchema import ResourceSchema

class DatasetAccessModelResource(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    # Make this one to many field
    fields = models.ManyToManyField(ResourceSchema)
    dataset_access_model = models.ForeignKey(DatasetAccessModel, on_delete=models.CASCADE, default="")
