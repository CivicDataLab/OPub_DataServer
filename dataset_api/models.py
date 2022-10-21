from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from dataset_api.enums import (
    OrganizationTypes,
    RatingStatus,
    OrganizationRequestStatusType,
)
from dataset_api.file_paths import (
    _organization_directory_path,
    _resource_directory_path,
    _info_directory_path,
    _organization_file_directory_path
)


# TODO: Add choices to choice fields


class Organization(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=500)
    logo = models.ImageField(upload_to=_organization_directory_path, blank=True)
    issued = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    homepage = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    organization_types = models.CharField(
        max_length=15, choices=OrganizationTypes.choices
    )


class OrganizationCreateRequest(Organization):
    data_description = models.CharField(max_length=500)
    upload_sample_data_file = models.FileField(
        upload_to=_organization_file_directory_path, blank=True
    )
    sample_data_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=20, choices=OrganizationRequestStatusType.choices, blank=False
    )
    remark = models.CharField(max_length=500, blank=True, null=True)


class OrganizationRequest(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, blank=False
    )
    description = models.CharField(max_length=500, blank=False)
    issued = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=OrganizationRequestStatusType.choices, blank=False
    )
    modified = models.DateTimeField(auto_now=True)
    user = models.CharField(max_length=50, blank=False, null=False)
    remark = models.CharField(max_length=500, blank=True, null=True)


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
    remote_issued = models.DateField(blank=True, null=True)
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
    resource = models.OneToOneField(
        Resource, on_delete=models.CASCADE, primary_key=True
    )
    api_source = models.ForeignKey(APISource, on_delete=models.CASCADE)
    auth_required = models.BooleanField()
    url_path = models.URLField(null=False, blank=False, default="")
    response_type = models.CharField(max_length=20)


class FileDetails(models.Model):
    resource = models.OneToOneField(
        Resource, on_delete=models.CASCADE, primary_key=True
    )
    format = models.CharField(max_length=15)
    file = models.FileField(upload_to=_resource_directory_path, blank=True)
    remote_url = models.URLField(blank=True)


class DatasetRatings(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    review = models.CharField(max_length=500)
    # overall = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    data_quality = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    status = models.CharField(max_length=50, choices=RatingStatus.choices)
    user = models.CharField(max_length=50, blank=False, null=False)
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
    dataset = models.ForeignKey(
        Dataset, blank=False, null=False, on_delete=models.CASCADE
    )
    creation_date = models.DateTimeField(auto_now_add=True, null=False)
    modified_date = models.DateTimeField(auto_now=True, null=False)
    reject_reason = models.CharField(max_length=500, blank=True)
    user = models.CharField(max_length=50, blank=False, null=False)
