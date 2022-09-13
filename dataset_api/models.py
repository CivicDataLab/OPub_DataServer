import os

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


def _resource_directory_path(resource, filename):
    """
    Create a directory path to upload the resources.

    """
    dataset_name = resource.dataset.title
    resource_name = resource.title
    _, extension = os.path.splitext(filename)
    return f"resources/{dataset_name}/{resource_name}/{extension[1:]}/{filename}"


class Organization(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    homepage = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, blank=False)


class Catalog(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)


class Geography(models.Model):
    name = models.CharField(max_length=75)


class Sector(models.Model):
    name = models.CharField(max_length=75)


class Dataset(models.Model):
    title = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=500, blank=True)
    issued = models.DateTimeField(auto_now_add=True)
    remote_issued = models.DateTimeField(blank=True, null=True)
    remote_modified = models.DateTimeField(blank=True, null=True)
    period_from = models.DateField(blank=True, null=True)
    period_to = models.DateField(blank=True, null=True)
    update_frequency = models.CharField(max_length=50, blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)
    sector = models.ManyToManyField(Sector, blank=True)
    status = models.CharField(max_length=50, default='Draft')
    remark = models.CharField(max_length=200, default='Please follow creation instructions')
    funnel = models.CharField(max_length=50, default='upload')
    action = models.CharField(max_length=50, default='create data')
    access_type = models.CharField(max_length=50, default='open')
    geography = models.ManyToManyField(Geography, blank=True)
    License = models.CharField(max_length=100, default='not_specified')
    catalog = models.ForeignKey(Catalog, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)


class Resource(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, default='Draft')
    masked_fields = ArrayField(models.CharField(max_length=10, blank=True), blank=True, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    remote_url = models.URLField(blank=True)
    format = models.CharField(max_length=15)
    file = models.FileField(upload_to=_resource_directory_path, blank=True)


class ResourceSchema(models.Model):
    key = models.CharField(max_length=100)
    format = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)


class APISource(models.Model):
    title = models.CharField(max_length=100)
    base_url = models.URLField(null=False, blank=False)
    description = models.CharField(max_length=500)
    api_version = models.CharField(max_length=50)
    headers = ArrayField(models.JSONField(blank=True, null=True), blank=True, null=True)
    auth_loc = models.CharField(max_length=50)
    auth_type = models.CharField(max_length=50)
    auth_credentials = models.JSONField(blank=True, null=True)
    auth_token = models.CharField(blank=True, null=True, max_length=200)


class APIResource(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, default='Draft')
    masked_fields = ArrayField(models.CharField(max_length=10, blank=True), blank=True, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    url_path = models.URLField(null=False, blank=False)
    api_source = models.ForeignKey(APISource, on_delete=models.CASCADE)
    auth_required = models.BooleanField()
    response_type = models.CharField(max_length=20)


class DatasetRatings(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    review = models.CharField(max_length=500)
    overall = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    data_quality = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    data_standards = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    coverage = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
