from django.db import models

from .Dataset import Dataset
from ..enums import ReviewType


class DatasetReviewRequest(models.Model):
    status = models.CharField(max_length=20)
    description = models.CharField(max_length=500)
    remark = models.CharField(max_length=500, blank=True)
    dataset = models.ForeignKey(
        Dataset, blank=False, null=False, on_delete=models.CASCADE
    )
    creation_date = models.DateTimeField(auto_now_add=True, null=False)
    modified_date = models.DateTimeField(auto_now=True, null=False)
    reject_reason = models.CharField(max_length=500, blank=True)
    user = models.CharField(max_length=50, blank=False, null=False)
    request_type = models.CharField(max_length=50, choices=ReviewType.choices, default=ReviewType.REVIEW)
