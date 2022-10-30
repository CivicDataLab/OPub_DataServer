from django.db import models

from dataset_api.enums import DataType
from dataset_api.models.Geography import Geography
from dataset_api.models.Tag import Tag
from dataset_api.models.Sector import Sector
from dataset_api.models.Catalog import Catalog


class Dataset(models.Model):
    title = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=500, blank=True)
    issued = models.DateTimeField(auto_now_add=True)
    remote_issued = models.DateField(blank=True, null=True)
    remote_modified = models.DateTimeField(blank=True, null=True)
    period_from = models.DateField(blank=True, null=True)
    period_to = models.DateField(blank=True, null=True)
    update_frequency = models.CharField(max_length=50, blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)
    sector = models.ManyToManyField(Sector, blank=True)
    status = models.CharField(max_length=50, default="Draft")
    funnel = models.CharField(max_length=50, default="upload")
    action = models.CharField(max_length=50, default="create data")
    geography = models.ManyToManyField(Geography, blank=True)
    catalog = models.ForeignKey(Catalog, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)
    dataset_type = models.CharField(max_length=50, default=DataType.FILE.value, choices=DataType.choices)
