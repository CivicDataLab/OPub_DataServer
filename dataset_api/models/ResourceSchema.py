from django.db import models

from dataset_api.models.Resource import Resource


class ResourceSchema(models.Model):
    key = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    format = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT)
    parent = models.ForeignKey(
        "self",
        unique=False,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="parent_field",
    )
    array_field = models.OneToOneField(
        "self",
        unique=False,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="array_item",
    )
