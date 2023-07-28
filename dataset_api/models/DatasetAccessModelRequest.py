import datetime

from django.db import models

from dataset_api.models.DatasetAccessModel import DatasetAccessModel


class DatasetAccessModelRequest(models.Model):
    access_model = models.ForeignKey(DatasetAccessModel, blank=False, null=False, on_delete=models.CASCADE)
    user = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20)
    description = models.CharField(max_length=500)
    remark = models.CharField(max_length=500, blank=True, null=True)
    purpose = models.CharField(max_length=500, default="")
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    user_email = models.EmailField(blank=True, null=True)
    token_time = models.DateTimeField(blank=False, null=False, default=datetime.datetime.now())
