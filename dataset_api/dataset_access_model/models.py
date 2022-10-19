from django.db import models

from dataset_api.data_access_model.models import DataAccessModel
from dataset_api.models import Dataset


class DatasetAccessModel(models.Model):
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    data_access_model = models.ForeignKey(DataAccessModel, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)