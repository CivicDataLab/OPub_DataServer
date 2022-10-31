from django.db import models

from dataset_api.models.Resource import Resource


class ResourceSchema(models.Model):
    class Meta:
        unique_together = ('resource', 'key')

    key = models.CharField(max_length=100)
    format = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT)
    parent = models.ForeignKey(
        "self",
        unique=False,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="parent_field",
    )
    array_field = models.OneToOneField(
        "self",
        unique=False,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="array_item",
    )
