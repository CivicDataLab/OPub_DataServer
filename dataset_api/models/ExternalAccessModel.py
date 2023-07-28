from django.db import models

from dataset_api.models.License import License
from dataset_api.models.Dataset import Dataset
from dataset_api.models.Policy import Policy


class ExternalAccessModel(models.Model):
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
