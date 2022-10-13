import os
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# TODO: Add choices to choice fields
from dataset_api.enums import RatingStatus


def _organization_directory_path(org, filename):
    """
    Create a directory path to upload the organization logo

    """
    org_name = org.title
    _, extension = os.path.splitext(filename)
    return f"resources/{org_name}/{extension[1:]}/{filename}"


def _resource_directory_path(file_details, filename):
    """
    Create a directory path to upload the resources.

    """
    dataset_name = file_details.resource.dataset.title
    resource_name = file_details.resource.title
    _, extension = os.path.splitext(filename)
    return f"resources/{dataset_name}/{resource_name}/{extension[1:]}/{filename}"


def _info_directory_path(info, filename):
    """
    Create a directory path to upload additional info.

    """
    dataset_name = info.dataset.title
    resource_name = info.title
    _, extension = os.path.splitext(filename)
    return f"info/{dataset_name}/{resource_name}/{extension[1:]}/{filename}"


def _contract_directory_path(dam, filename):
    """
    Create a directory path to upload DAM contract files.

    """
    dataset_name = dam.dataset.title
    dam_name = dam.title
    _, extension = os.path.splitext(filename)
    return f"info/{dataset_name}/{dam_name}/{extension[1:]}/{filename}"


def _license_directory_path(license, filename):
    """
    Create a directory path to upload license files.

    """
    org_name = license.organization.title
    license_name = license.title
    _, extension = os.path.splitext(filename)
    return f"info/{org_name}/{license_name}/{extension[1:]}/{filename}"


def _data_request_directory_path(request, filename):
    """
    Create a directory path to receive the request data.

    """
    _, extension = os.path.splitext(filename)
    return f"request/{request.id}/{extension[1:]}/{filename}"


class Organization(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=500)
    logo = models.ImageField(upload_to=_organization_directory_path, blank=True)
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
    status = models.CharField(max_length=50, default="Draft")
    remark = models.CharField(
        max_length=200, default="Please follow creation instructions"
    )
    funnel = models.CharField(max_length=50, default="upload")
    action = models.CharField(max_length=50, default="create data")
    geography = models.ManyToManyField(Geography, blank=True)
    catalog = models.ForeignKey(Catalog, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)
    dataset_type = models.CharField(max_length=500, default="")


class Resource(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, default="Draft")
    masked_fields = ArrayField(
        models.CharField(max_length=10, blank=True), blank=True, null=True
    )
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)


class ResourceSchema(models.Model):
    key = models.CharField(max_length=100)
    format = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    parent = models.OneToOneField(
        "self",
        unique=False,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="parent_field",
    )
    array_field = models.OneToOneField(
        "self",
        unique=False,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="array_item",
    )


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


class APIDetails(models.Model):
    resource = models.OneToOneField(Resource, on_delete=models.CASCADE, primary_key=True)
    api_source = models.ForeignKey(APISource, on_delete=models.CASCADE)
    auth_required = models.BooleanField()
    url_path = models.URLField(null=False, blank=False, default="")
    response_type = models.CharField(max_length=20)


class FileDetails(models.Model):
    resource = models.OneToOneField(Resource, on_delete=models.CASCADE, primary_key=True)
    format = models.CharField(max_length=15)
    file = models.FileField(upload_to=_resource_directory_path, blank=True)
    remote_url = models.URLField(blank=True)


class APIResource(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, default="Draft")
    masked_fields = ArrayField(
        models.CharField(max_length=10, blank=True), blank=True, null=True
    )
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    url_path = models.URLField(null=False, blank=False)
    api_source = models.ForeignKey(APISource, on_delete=models.CASCADE)
    auth_required = models.BooleanField()
    # response_type = models.CharField(max_length=20)


class DatasetRatings(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    review = models.CharField(max_length=500)
    # overall = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    data_quality = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    status = models.CharField(max_length=50, choices=[(tag, tag.value) for tag in RatingStatus])
    # data_standards = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    # coverage = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])


class AdditionalInfo(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    remote_url = models.URLField(blank=True)
    format = models.CharField(max_length=15)
    type = models.CharField(max_length=50)
    file = models.FileField(upload_to=_info_directory_path, blank=True)


class ModerationRequest(models.Model):
    status = models.CharField(max_length=20)
    description = models.CharField(max_length=500)
    remark = models.CharField(max_length=500, blank=True)
    dataset = models.ForeignKey(Dataset, blank=False, null=False, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True, null=False)
    modified_date = models.DateTimeField(auto_now=True, null=False)
    reject_reason = models.CharField(max_length=500, blank=True)
    user = models.CharField(max_length=50, blank=False, null=False)


class License(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, blank=False, null=False)
    remote_url = models.URLField(blank=True)
    file = models.FileField(upload_to=_contract_directory_path, blank=True)


class DataAccessModel(models.Model):
    title = models.CharField(max_length=100)
    type = models.CharField(max_length=100, default="OPEN")
    description = models.CharField(max_length=500)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    contract_url = models.URLField(blank=True, null=True)
    contract = models.FileField(upload_to=_contract_directory_path, blank=True)
    # license = models.ForeignKey(License, on_delete=models.CASCADE, blank=False, null=False)
    license = models.CharField(max_length=100, default="not_specified")
    quota_limit = models.IntegerField(blank=False)
    quota_limit_unit = models.CharField(blank=False, max_length=100)
    rate_limit = models.IntegerField(blank=False)
    rate_limit_unit = models.CharField(blank=False, max_length=100)
    resources = models.ManyToManyField(Resource)


class DataAccessModelRequest(models.Model):
    data_access_model_id = models.ForeignKey(DataAccessModel, blank=False, null=False, on_delete=models.CASCADE)
    user = models.CharField(max_length=50, blank=False, null=False)
    status = models.CharField(max_length=20)
    description = models.CharField(max_length=500)
    remark = models.CharField(max_length=500, blank=True, null=True)
    purpose = models.CharField(max_length=500, default="")
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class DataRequest(models.Model):
    status = models.CharField(max_length=20)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=_data_request_directory_path, blank=True, null=True
    )
    creation_date = models.DateTimeField(auto_now_add=True, null=True)
    reject_reason = models.CharField(max_length=500, blank=True)
    data_access_model_request = models.ForeignKey(DataAccessModelRequest, on_delete=models.CASCADE)
    user = models.CharField(max_length=50)
