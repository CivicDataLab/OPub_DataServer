from django.contrib.postgres.fields import ArrayField
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
    highlights = ArrayField(models.CharField(max_length=100, blank=True, null=True), blank=True, null=True)
    remote_issued = models.DateField(blank=True, null=True)
    remote_modified = models.DateField(blank=True, null=True)
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
    download_count = models.IntegerField(default=0)
    language = models.CharField(blank=True, null=True, max_length=100)
    in_series = models.CharField(blank=True, null=True, max_length=100)
    theme = models.CharField(blank=True, null=True, max_length=100)
    qualified_attribution = models.CharField(blank=True, null=True, max_length=100)
    contact_point = models.CharField(blank=True, null=True, max_length=100)
    confirms_to = models.CharField(blank=True, null=True, max_length=100)
    spatial_coverage = models.CharField(blank=True, null=True, max_length=100)
    spatial_resolution = models.CharField(blank=True, null=True, max_length=100)
    temporal_resolution = models.CharField(blank=True, null=True, max_length=100)
    temporal_coverage = models.CharField(blank=True, null=True, max_length=100)
