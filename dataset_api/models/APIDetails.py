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
    response_type = models.CharField(max_length=20)
    request_type = models.CharField(max_length=20, unique=False)
    supported_formats = ArrayField(models.CharField(max_length=25, blank=False), blank=True, null=True)
    default_format = models.CharField(max_length=500, default="")
    format_loc = models.CharField(choices=FormatLocation.choices, max_length=50, default="")
