from django.contrib.postgres.fields import ArrayField
from django.db import models

from .APISource import APISource
from .Resource import Resource
from ..enums import FormatLocation


class APIDetails(models.Model):
    resource = models.OneToOneField(
        Resource, on_delete=models.CASCADE, primary_key=True
    )
    api_source = models.ForeignKey(APISource, on_delete=models.CASCADE)
    auth_required = models.BooleanField()
    url_path = models.URLField(null=False, blank=False, default="")
    response_type = models.CharField(max_length=20, blank=True, null=True)
    request_type = models.CharField(max_length=20, unique=False)
    supported_formats = ArrayField(models.CharField(max_length=25, blank=False), blank=True, null=True)
    download_formats = ArrayField(models.CharField(max_length=25, blank=False), blank=True, null=True)
    download_same_as_api = models.BooleanField(default=True, blank=False, null=False)
    is_large_dataset = models.BooleanField(default=True, blank=False, null=False)
    default_format = models.CharField(max_length=500, default="", blank=True, null=True)
    format_key = models.CharField(max_length=200, default="", blank=True, null=True)
    format_loc = models.CharField(choices=FormatLocation.choices, max_length=50, default=FormatLocation.PARAM.value,
                                  blank=True, null=True)
