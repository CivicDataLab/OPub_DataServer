from django.db import models

from dataset_api.models.DataAccessModel import DataAccessModel
from dataset_api.models.Dataset import Dataset


class DatasetAccessModel(models.Model):
    title = models.CharField(max_length=100)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    data_access_model = models.ForeignKey(DataAccessModel, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    sample_enabled = models.BooleanField(blank=False, null=False, default=False)
    sample_rows = models.IntegerField(blank=False, null=False, default=5)
