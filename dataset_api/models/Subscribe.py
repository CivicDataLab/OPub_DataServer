from django.db import models

from dataset_api.models import Dataset


class Subscribe(models.Model):
    user = models.CharField(max_length=100, blank=False, null=False)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
