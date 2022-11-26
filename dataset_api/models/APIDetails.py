from django.db import models

from .APISource import APISource
from .Resource import Resource

class APIDetails(models.Model):

    resource = models.OneToOneField(
        Resource, on_delete=models.CASCADE, primary_key=True
    )
    api_source = models.ForeignKey(APISource, on_delete=models.CASCADE)
    auth_required = models.BooleanField()
    url_path = models.URLField(null=False, blank=False, default="")
    response_type = models.CharField(max_length=20)
    request_type  = models.CharField(max_length=20, unique=False)
