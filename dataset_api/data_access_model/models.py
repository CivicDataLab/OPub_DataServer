from django.contrib.postgres.fields import ArrayField
from django.db import models

from dataset_api.file_paths import _contract_directory_path, _data_request_directory_path
from dataset_api.models import Organization, License, LicenseAddition, Dataset, Resource


class DataAccessModel(models.Model):
    title = models.CharField(max_length=100)
    type = models.CharField(max_length=100, default="OPEN")
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, default="")
    contract = models.FileField(upload_to=_contract_directory_path, blank=True)
    license = models.ForeignKey(License, on_delete=models.CASCADE, blank=False, null=False)
    quota_limit = models.IntegerField(blank=False)
    quota_limit_unit = models.CharField(blank=False, max_length=100)
    rate_limit = models.IntegerField(blank=False)
    rate_limit_unit = models.CharField(blank=False, max_length=100)
    license_additions = models.ManyToManyField(LicenseAddition, blank=True)


class DatasetAccessModelMap(models.Model):
    data_access_model = models.ForeignKey(DataAccessModel, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)


class AccessModelResource(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    fields = ArrayField(models.CharField(max_length=25, blank=False), blank=False, null=False)
    dataset_access_map = models.ForeignKey(DatasetAccessModelMap, on_delete=models.CASCADE, default="")


class DataAccessModelRequest(models.Model):
    data_access_model_id = models.ForeignKey(DataAccessModel, blank=False, null=False, on_delete=models.CASCADE)
    user = models.CharField(max_length=50, blank=False, null=False)
    status = models.CharField(max_length=20)
    description = models.CharField(max_length=500)
    remark = models.CharField(max_length=500, blank=True, null=True)
    purpose = models.CharField(max_length=500, default="")
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class DataRequest(models.Model):
    status = models.CharField(max_length=20)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=_data_request_directory_path, blank=True, null=True
    )
    creation_date = models.DateTimeField(auto_now_add=True, null=True)
    reject_reason = models.CharField(max_length=500, blank=True)
    data_access_model_request = models.ForeignKey(DataAccessModelRequest, on_delete=models.CASCADE)
    user = models.CharField(max_length=50)