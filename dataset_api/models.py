import os

from django.db import models
from slugify import slugify


def _resource_directory_path(resource, filename):
    """
    Create a directory path to upload the resources.

    """
    dataset_name = slugify(resource.dataset.title)
    resource_name = slugify(resource.title)
    _, extension = os.path.splitext(filename)
    return f"resources/{dataset_name}/{resource_name}/{extension}"


class Organization(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    homepage = models.URLField(blank=True)
    contact_email = models.EmailField()


class Catalog(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)


class Dataset(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    sector = models.CharField(max_length=50, default='Other')
    geography = models.CharField(max_length=50, default='Other')
    License = models.CharField(max_length=100, default='not_specified')
    catalog = models.ForeignKey(Catalog, on_delete=models.CASCADE)


class Resource(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField()
    remote_url = models.URLField(blank=True)
    file = models.FileField(upload_to=_resource_directory_path, blank=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
