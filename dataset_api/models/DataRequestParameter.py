from django.db import models

from dataset_api.models import APIParameter, DataRequest


class DataRequestParameter(models.Model):
    api_parameter = models.ForeignKey(APIParameter, on_delete=models.PROTECT)
    data_request = models.ForeignKey(DataRequest, on_delete=models.PROTECT, to_field='id',
                                     related_name="datarequestparameters")
    value = models.CharField(max_length=100)
