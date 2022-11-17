from typing import Iterable

import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from graphql import GraphQLError

from dataset_api.decorators import validate_token, auth_user_by_org
from dataset_api.enums import DataType
from dataset_api.models import Dataset, Catalog, Tag, Geography, Sector, Organization
from dataset_api.utils import (
    get_client_ip,
    dataset_slug,
    log_activity,
    get_average_rating,
)
from .decorators import auth_user_action_dataset, map_user_dataset, auth_query_dataset
from ..data_access_model.contract import update_provider_agreement


class DatasetType(DjangoObjectType):
    slug = graphene.String()
    average_rating = graphene.Float()

    class Meta:
        model = Dataset
        fields = "__all__"

    def resolve_slug(self: Dataset, info):
        return dataset_slug(self.id)

    def resolve_average_rating(self: Dataset, info):
        return get_average_rating(dataset=self)


class DatasetStatus(graphene.Enum):
    DRAFT = "DRAFT"
    UNDERREVIEW = "UNDERREVIEW"
    REVIEWED = "REVIEWED"
    PUBLISHED = "PUBLISHED"
    UNDERMODERATION = "UNDERMODERATION"
    READYTOPUBLISH = "READYTOPUBLISH"
    TRANSFORMATIONINPROGRESS = "TRANSFORMATIONINPROGRESS"


def _add_update_attributes_to_dataset(
        dataset_instance, object_field, attribute_list, attribute_type
):
    if not attribute_list:
        return
    dataset_attribute = getattr(dataset_instance, object_field)
    dataset_attribute.clear()
    for attribute in attribute_list:
        try:
            attribute_object = attribute_type.objects.get(name=attribute)
        except attribute_type.DoesNotExist as e:
            attribute_object = attribute_type(name=attribute)
            attribute_object.save()
        dataset_attribute.add(attribute_object)
    dataset_instance.save()


class Query(graphene.ObjectType):
    all_datasets = graphene.List(DatasetType)
    org_datasets = graphene.List(
        DatasetType,
        first=graphene.Int(),
        skip=graphene.Int(),
        status=DatasetStatus(required=False),
    )
    dataset = graphene.Field(DatasetType, dataset_id=graphene.Int())
    dataset_by_title = graphene.Field(DatasetType, dataset_title=graphene.String())
    dataset_by_slug = graphene.Field(DatasetType, dataset_slug=graphene.String())

    @validate_token
    def resolve_all_datasets(self, info, username, **kwargs):
        return Dataset.objects.filter(
            Q(datasetaccessmodel__datasetaccessmodelrequest__user=username),
            Q(datasetaccessmodel__datasetaccessmodelrequest__status="APPROVED"),
        )

    # Access : PMU / DPA
    @auth_user_by_org(action="query")
    def resolve_org_datasets(
            self, info, role, first=None, skip=None, status: DatasetStatus = None, **kwargs
    ):
        if role == "PMU" or role == "DPA":
            org_id = info.context.META.get("HTTP_ORGANIZATION")
            organization = Organization.objects.get(id=org_id)
            if status:
                query = Dataset.objects.filter(
                    catalog__organization=organization, status=status
                ).order_by("-modified")
            else:
                query = Dataset.objects.filter(
                    catalog__organization=organization
                ).order_by("-modified")
            if skip:
                query = query[skip:]
            if first:
                query = query[:first]
            return query
        else:
            raise GraphQLError("Access Denied")

    # Access : PMU / DPA / DP
    @auth_query_dataset(action="query||title")
    def resolve_dataset_by_title(self, info, dataset_title, role=None, **kwargs):
        dataset_instance = Dataset.objects.get(title__iexact=dataset_title)
        if dataset_instance.status == "PUBLISHED":
            return dataset_instance
        if role:
            if role == "PMU" or role == "DPA" or role == "DP":
                return dataset_instance
            else:
                raise GraphQLError("Access Denied")
        else:
            raise GraphQLError("Access Denied")

    # Access : PMU / DPA / DP
    @auth_query_dataset(action="query||slug")
    def resolve_dataset_by_slug(self, info, dataset_slug: str, role=None, **kwargs):
        dataset_id = dataset_slug.split("_")[-1]
        dataset_instance = Dataset.objects.get(id=dataset_id)
        if dataset_instance.status == "PUBLISHED":
            return dataset_instance
        if role:
            if role == "PMU" or role == "DPA":
                return dataset_instance
            else:
                raise GraphQLError("Access Denied")
        else:
            raise GraphQLError("Access Denied")

    # Access : PMU / DPA / DP
    @auth_query_dataset(action="query||id")
    def resolve_dataset(self, info, dataset_id, role=None):
        dataset_instance = Dataset.objects.get(pk=dataset_id)
        if dataset_instance.status == "PUBLISHED":
            return dataset_instance
        if role:
            if role == "PMU" or role == "DPA" or role == "DP":
                return dataset_instance
            else:
                raise GraphQLError("Access Denied")
        else:
            raise GraphQLError("Access Denied")


class CreateDatasetInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    dataset_type = graphene.Enum.from_enum(DataType)(required=True)
    funnel = graphene.String(required=True, default_value="upload")


class UpdateDatasetInput(graphene.InputObjectType):
    id = graphene.ID()
    remote_issued = graphene.Date(required=True)
    remote_modified = graphene.Date(required=False)
    period_from = graphene.Date(required=False)
    period_to = graphene.Date(required=False)
    update_frequency = graphene.String(required=True)
    highlights = graphene.List(of_type=graphene.String, required=False, default=[])
    funnel = graphene.String(required=False, default_value="upload")
    action = graphene.String(required=False, default_value="create data")
    tags_list: Iterable = graphene.List(
        of_type=graphene.String, default=[], required=False
    )
    geo_list: Iterable = graphene.List(
        of_type=graphene.String, default=[], required=True
    )
    sector_list: Iterable = graphene.List(
        of_type=graphene.String, default=[], required=True
    )
    language = graphene.String(required=False, default_value="")
    in_series = graphene.String(required=False, default_value="")
    theme = graphene.String(required=False, default_value="")
    qualified_attribution = graphene.String(required=False, default_value="")
    contact_point = graphene.String(required=False, default_value="")
    confirms_to = graphene.String(required=False, default_value="")
    spatial_coverage = graphene.String(required=False, default_value="")
    spatial_resolution = graphene.String(required=False, default_value="")
    temporal_resolution = graphene.String(required=False, default_value="")
    temporal_coverage = graphene.String(required=False, default_value="")


class PatchDatasetInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    funnel = graphene.String(default=None)
    status = graphene.String(default=None)


class CreateDataset(Output, graphene.Mutation):
    class Arguments:
        dataset_data = CreateDatasetInput()

    dataset = graphene.Field(DatasetType)

    @staticmethod
    @validate_token
    @auth_user_action_dataset(action="create_dataset")
    @map_user_dataset
    def mutate(
            root,
            info,
            username,
            dataset_data: CreateDatasetInput = None,
    ):
        try:
            org_id = info.context.META.get("HTTP_ORGANIZATION")
            organization = Organization.objects.get(id=org_id)
            catalog = Catalog.objects.filter(organization=organization)[0]
        except Organization.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {
                            "message": "Organization with given id not found",
                            "code": "404",
                        }
                    ]
                },
            }
        dataset_instance = Dataset(
            title=dataset_data.title,
            description=dataset_data.description,
            status="DRAFT",
            dataset_type=dataset_data.dataset_type,
            funnel=dataset_data.funnel,
            catalog=catalog,
        )
        dataset_instance.save()
        log_activity(
            target_obj=dataset_instance,
            ip=get_client_ip(info),
            target_group=organization,
            username=username,
            verb="Created",
        )
        update_provider_agreement(dataset_instance, username)
        return CreateDataset(dataset=dataset_instance)


class UpdateDataset(Output, graphene.Mutation):
    class Arguments:
        dataset_data = UpdateDatasetInput()

    dataset = graphene.Field(DatasetType)

    @staticmethod
    @validate_token
    @auth_user_action_dataset(action="update_dataset")
    def mutate(root, info, username, dataset_data: UpdateDatasetInput = None):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        try:
            dataset_instance = Dataset.objects.get(id=dataset_data.id)
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {
                            "message": "Organization with given id not found",
                            "code": "404",
                        }
                    ]
                },
            }
        except Dataset.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {"message": "Dataset with given id not found", "code": "404"}
                    ]
                },
            }
        catalog = Catalog.objects.filter(organization=organization)[0]
        dataset_instance.remote_issued = dataset_data.remote_issued
        dataset_instance.remote_modified = dataset_data.remote_modified
        dataset_instance.funnel = dataset_data.funnel
        dataset_instance.action = dataset_data.action
        dataset_instance.catalog = catalog
        dataset_instance.status = "DRAFT"
        dataset_instance.period_to = dataset_data.period_to
        dataset_instance.period_from = dataset_data.period_from
        dataset_instance.update_frequency = dataset_data.update_frequency
        dataset_instance.highlights = dataset_data.highlights
        dataset_instance.language = dataset_data.language
        dataset_instance.in_series = dataset_data.in_series
        dataset_instance.theme = dataset_data.theme
        dataset_instance.qualified_attribution = dataset_data.qualified_attribution
        dataset_instance.contact_point = dataset_data.contact_point
        dataset_instance.confirms_to = dataset_data.confirms_to
        dataset_instance.spatial_coverage = dataset_data.spatial_coverage
        dataset_instance.spatial_resolution = dataset_data.spatial_resolution
        dataset_instance.temporal_resolution = dataset_data.temporal_resolution
        dataset_instance.temporal_coverage = dataset_data.temporal_coverage
        dataset_instance.save()
        _add_update_attributes_to_dataset(
            dataset_instance, "tags", dataset_data.tags_list, Tag
        )
        _add_update_attributes_to_dataset(
            dataset_instance, "geography", dataset_data.geo_list, Geography
        )
        _add_update_attributes_to_dataset(
            dataset_instance, "sector", dataset_data.sector_list, Sector
        )
        log_activity(
            target_obj=dataset_instance,
            ip=get_client_ip(info),
            target_group=organization,
            username=username,
            verb="Updated",
        )
        update_provider_agreement(dataset_instance, username)

        return UpdateDataset(dataset=dataset_instance)


class PatchDataset(Output, graphene.Mutation):
    class Arguments:
        dataset_data = PatchDatasetInput()

    success = graphene.Boolean()
    dataset = graphene.Field(DatasetType)

    @validate_token
    @auth_user_action_dataset(action="patch_dataset")
    def mutate(root, info, username, dataset_data: PatchDatasetInput = None):
        try:
            dataset_instance = Dataset.objects.get(id=dataset_data.id)
        except Dataset.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {"message": "Dataset with given id not found", "code": "404"}
                    ]
                },
            }
        if dataset_data.status:
            dataset_instance.status = dataset_data.status
        if dataset_data.funnel:
            dataset_instance.funnel = dataset_data.funnel
        if dataset_data.title:
            dataset_instance.title = dataset_data.title
        if dataset_data.description:
            dataset_instance.description = dataset_data.description
        dataset_instance.save()
        log_activity(
            target_obj=dataset_instance,
            ip=get_client_ip(info),
            target_group=dataset_instance.catalog.organization,
            username=username,
            verb="Updated",
        )
        update_provider_agreement(dataset_instance, username)

        return PatchDataset(success=True, dataset=dataset_instance)


class Mutation(graphene.ObjectType):
    create_dataset = CreateDataset.Field()
    update_dataset = UpdateDataset.Field()
    patch_dataset = PatchDataset.Field()
