from django.db import models

from dataset_api.models import DatasetAccessModel, DatasetAccessModelRequest


class Transaction(models.Model):
    user = models.CharField(max_length=50, blank=False, null=False)
    status = models.CharField(max_length=50, blank=False, null=False)
    access_request = models.ForeignKey(DatasetAccessModelRequest, on_delete=models.CASCADE, related_name="transactions")
    payment_id = models.CharField(max_length=50, blank=True, null=True)
    payment_request_id = models.CharField(max_length=50, blank=False, null=False)
    payment_purpose = models.CharField(max_length=250, blank=False, null=False)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
