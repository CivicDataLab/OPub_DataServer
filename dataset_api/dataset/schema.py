from typing import Iterable

import graphene
from django.db.models import Q, Prefetch
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from graphql_auth.bases import Output

from dataset_api.decorators import validate_token, auth_user_by_org
from dataset_api.enums import DataType
from dataset_api.models import (
    Dataset,
    Catalog,
    Tag,
    Geography,
    Sector,
    Organization,
    DataRequest,
    Agreement,
    DatasetAccessModelRequest,
    DatasetAccessModel,
)
from dataset_api.search import index_data
from dataset_api.utils import (
    get_client_ip,
    dataset_slug,
    log_activity,
    get_average_rating,
)
from .decorators import (
    auth_user_action_dataset,
    map_user_dataset,
    auth_query_dataset,
    get_user_datasets,
)
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
    DISABLED = "DISABLED"


def _add_update_attributes_to_dataset(
        dataset_instance, object_field, attribute_list, attribute_type
):
    if not attribute_list:
        return
    dataset_attribute = getattr(dataset_instance, object_field)
    dataset_attribute.clear()
    for attribute in attribute_list:
        if object_field == "sector":
            query = {"{0}".format("pk"): attribute}
        else:
            query = {"{0}".format("name"): attribute}
        try:
            attribute_object = attribute_type.objects.get(**query)
        except attribute_type.DoesNotExist as e:
            attribute_object = attribute_type(name=attribute)
            attribute_object.save()
        dataset_attribute.add(attribute_object)
    dataset_instance.save()


def add_pagination_filters(first, query, skip):
    if skip:
        query = query[skip:]
    if first:
        query = query[:first]
    return query


class Query(graphene.ObjectType):
    all_datasets = graphene.List(DatasetType, first=graphene.Int(), skip=graphene.Int())
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
    def resolve_all_datasets(self, info, username, first=None, skip=None, **kwargs):
        prefetch_agreements = Prefetch(
            "agreements",
            queryset=Agreement.objects.filter(username=username).distinct(),
        )

        prefetch_data_requests = Prefetch(
            "datarequest_set",
            queryset=DataRequest.objects.filter(default=True, user=username),
        )
        prefetch_dam_requests = Prefetch(
            "datasetaccessmodelrequest_set",
            queryset=DatasetAccessModelRequest.objects.filter(user=username)
            .order_by("-modified")
            .prefetch_related(prefetch_data_requests)
            .distinct(),
        )
        prefetch_dataset_am = Prefetch(
            "datasetaccessmodel_set",
            queryset=DatasetAccessModel.objects.filter(
                datasetaccessmodelrequest__user=username,
            )
            .prefetch_related(prefetch_agreements, prefetch_dam_requests)
            .distinct(),
        )
        dataset_query = Dataset.objects.filter(
            Q(datasetaccessmodel__datasetaccessmodelrequest__user=username), ).prefetch_related(
            prefetch_dataset_am).distinct()
        dataset_query = add_pagination_filters(first, dataset_query, skip)
        return dataset_query

    # Access : PMU / DPA
    @auth_user_by_org(action="query")
    @validate_token
    @get_user_datasets
    def resolve_org_datasets(
            self,
            info,
            role,
            dataset_list,
            first=None,
            skip=None,
            status: DatasetStatus = None,
            username="",
            **kwargs
    ):
        if role == "PMU" or role == "DPA" or role == "DP":
            org_id = info.context.META.get("HTTP_ORGANIZATION")
            organization = Organization.objects.get(id=org_id)
            if status:
                query = Dataset.objects.filter(
                    catalog__organization=organization,
                    status=status,
                    id__in=dataset_list,
                ).order_by("-modified")
            else:
                query = Dataset.objects.filter(
                    catalog__organization=organization,
                    id__in=dataset_list,
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
            return dataset_instance
        else:
            raise GraphQLError("Access Denied")

    # Access : PMU / DPA / DP
    @auth_query_dataset(action="query||id")
    def resolve_dataset(self, info, dataset_id, role=None):
        dataset_instance = Dataset.objects.get(pk=dataset_id)
        if dataset_instance.status == "PUBLISHED":
            return dataset_instance
        if role:
            if (role == "PMU" or role == "DPA" or role == "DP") and dataset_instance.status != "DISABLED":
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
    source = graphene.String(required=True)
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
    is_datedynamic = graphene.String(required=False, default_value=False)


class PatchDatasetInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    title = graphene.String(required=False)
    description = graphene.String(required=False)
    funnel = graphene.String(default=None)
    status = graphene.String(default=None)
    hvd_rating = graphene.Float(required=False)


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
            raise GraphQLError("Organization with given id not found")
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
            raise GraphQLError("Organization with given id not found")
        except Dataset.DoesNotExist as e:
            raise GraphQLError("Dataset with given id not found")
        catalog = Catalog.objects.filter(organization=organization)[0]
        dataset_instance.source = dataset_data.source
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
        dataset_instance.is_datedynamic = dataset_data.is_datedynamic
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
            raise GraphQLError("Dataset with given id not found")
        if dataset_data.status:
            dataset_instance.status = dataset_data.status
        if dataset_data.funnel:
            dataset_instance.funnel = dataset_data.funnel
        if dataset_data.title:
            dataset_instance.title = dataset_data.title
        if dataset_data.description:
            dataset_instance.description = dataset_data.description
        if dataset_data.hvd_rating:
            dataset_instance.hvd_rating = dataset_data.hvd_rating
        dataset_instance.save()
        log_activity(
            target_obj=dataset_instance,
            ip=get_client_ip(info),
            target_group=dataset_instance.catalog.organization,
            username=username,
            verb="Updated",
        )
        update_provider_agreement(dataset_instance, username)
        if dataset_instance.status == "PUBLISHED":
            index_data(dataset_instance)

        return PatchDataset(success=True, dataset=dataset_instance)


class Mutation(graphene.ObjectType):
    create_dataset = CreateDataset.Field()
    update_dataset = UpdateDataset.Field()
    patch_dataset = PatchDataset.Field()
