import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from dataset_api.decorators import auth_user_action_dataset, map_user_dataset, validate_token
from dataset_api.enums import DataType
from dataset_api.models import Dataset, Catalog, Tag, Geography, Sector, Organization
from dataset_api.utils import get_client_ip, dataset_slug, log_activity, get_average_rating


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
    org_datasets = graphene.List(DatasetType, first=graphene.Int(), skip=graphene.Int(),
                                 status=DatasetStatus(required=False))
    dataset = graphene.Field(DatasetType, dataset_id=graphene.Int())
    dataset_by_title = graphene.Field(DatasetType, dataset_title=graphene.String())
    dataset_by_slug = graphene.Field(DatasetType, dataset_slug=graphene.String())

    def resolve_all_datasets(self, info, **kwargs):
        return Dataset.objects.all().order_by("-modified")

    def resolve_org_datasets(self, info, first=None, skip=None, status: DatasetStatus = None, **kwargs):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        organization = Organization.objects.get(id=org_id)
        if status:
            query = Dataset.objects.filter(catalog__organization=organization, status=status).order_by(
                "-modified")
        else:
            query = Dataset.objects.filter(catalog__organization=organization).order_by("-modified")
        if skip:
            query = query[skip:]
        if first:
            query = query[:first]
        return query

    def resolve_dataset_by_title(self, info, dataset_title, **kwargs):
        return Dataset.objects.get(title__iexact=dataset_title)

    def resolve_dataset_by_slug(self, info, dataset_slug: str, **kwargs):
        dataset_id = dataset_slug.split('_')[-1]
        return Dataset.objects.get(id=dataset_id)

    def resolve_dataset(self, info, dataset_id):
        return Dataset.objects.get(pk=dataset_id)


class DatasetInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    remote_issued = graphene.Date(required=False)
    remote_modified = graphene.DateTime(required=False)
    period_from = graphene.Date()
    period_to = graphene.Date()
    update_frequency = graphene.String()
    highlights = graphene.List(of_type=graphene.String, required=True)
    dataset_type = graphene.Enum.from_enum(DataType)(required=True)
    funnel = graphene.String(required=False, default_value="upload")
    action = graphene.String(required=False, default_value="create data")
    tags_list = graphene.List(of_type=graphene.String, default=[], required=False)
    geo_list = graphene.List(of_type=graphene.String, default=[], required=False)
    sector_list = graphene.List(of_type=graphene.String, default=[], required=False)


class PatchDatasetInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    funnel = graphene.String(default=None)
    status = graphene.String(default=None)


class CreateDataset(Output, graphene.Mutation):
    class Arguments:
        dataset_data = DatasetInput()

    dataset = graphene.Field(DatasetType)

    @staticmethod
    @validate_token
    @auth_user_action_dataset(action="create_dataset")
    @map_user_dataset
    def mutate(
            root,
            info,
            username,
            dataset_data: DatasetInput = None,
    ):
        try:
            org_id = info.context.META.get("HTTP_ORGANIZATION")
            organization = Organization.objects.get(id=org_id)
            catalog = Catalog.objects.filter(organization=organization)[0]
            # catalog = organization.objects.select_related('catalog').all(0)
        except Organization.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [{
                        "message": "Organization with given id not found",
                        "code": "404",
                    }]}}
        dataset_instance = Dataset(
            title=dataset_data.title,
            description=dataset_data.description,
            remote_issued=dataset_data.remote_issued,
            remote_modified=dataset_data.remote_modified,
            funnel=dataset_data.funnel,
            action=dataset_data.action,
            status="DRAFT",
            highlights=dataset_data.highlights,
            catalog=catalog,
            period_to=dataset_data.period_to,
            period_from=dataset_data.period_from,
            update_frequency=dataset_data.update_frequency,
            dataset_type=dataset_data.dataset_type,
        )
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
        log_activity(target_obj=dataset_instance, ip=get_client_ip(info), target_group=organization, username=username,
                     verb="Created")
        return CreateDataset(dataset=dataset_instance)


class UpdateDataset(Output, graphene.Mutation):
    class Arguments:
        dataset_data = DatasetInput()

    dataset = graphene.Field(DatasetType)

    @staticmethod
    @validate_token
    @auth_user_action_dataset(action="update_dataset")
    def mutate(root, info, username, dataset_data: DatasetInput = None):
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
        dataset_instance.title = dataset_data.title
        dataset_instance.description = dataset_data.description
        dataset_instance.remote_issued = dataset_data.remote_issued
        dataset_instance.remote_modified = dataset_data.remote_modified
        dataset_instance.funnel = dataset_data.funnel
        dataset_instance.action = dataset_data.action
        dataset_instance.catalog = catalog
        dataset_instance.status = "DRAFT"
        dataset_instance.period_to = dataset_data.period_to
        dataset_instance.period_from = dataset_data.period_from
        dataset_instance.dataset_type = dataset_data.dataset_type
        dataset_instance.update_frequency = dataset_data.update_frequency
        dataset_instance.highlights = dataset_data.highlights

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
        log_activity(target_obj=dataset_instance, ip=get_client_ip(info), target_group=organization, username=username,
                     verb="Updated")

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
        log_activity(target_obj=dataset_instance, ip=get_client_ip(info),
                     target_group=dataset_instance.catalog.organization, username=username,
                     verb="Updated")

        return PatchDataset(success=True, dataset=dataset_instance)


class Mutation(graphene.ObjectType):
    create_dataset = CreateDataset.Field()
    update_dataset = UpdateDataset.Field()
    patch_dataset = PatchDataset.Field()
