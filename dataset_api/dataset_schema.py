import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from .models import Dataset, Catalog, Tag, Geography, Sector, Organization
from .decorators import auth_user_action_dataset, map_user_dataset


class DatasetType(DjangoObjectType):
    class Meta:
        model = Dataset
        fields = "__all__"


class DataType(graphene.Enum):
    API = "API"
    FILE = "FILE"
    DATASET = "DATASET"


class DatasetStatus(graphene.Enum):
    DRAFT = "DRAFT"
    UNDERREVIEW = "UNDERREVIEW"
    PUBLISHED = "PUBLISHED"
    UNDERMODERATION = "UNDERMODERATION"
    READYTOPUBLISH = "READYTOPUBLISH"
    TRANSFORMATIONINPROGRESS = "TRANSFORMATIONINPROGRESS"


def _add_update_attributes_to_dataset(dataset_instance, object_field, attribute_list, attribute_type):
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
    dataset = graphene.Field(DatasetType, dataset_id=graphene.Int())
    dataset_by_title = graphene.Field(DatasetType, dataset_title=graphene.String())

    def resolve_all_datasets(self, info, **kwargs):
        return Dataset.objects.all().order_by("-modified")

    def resolve_dataset_by_title(self, info, dataset_title, **kwargs):
        return Dataset.objects.get(title__iexact=dataset_title)

    def resolve_dataset(self, info, dataset_id):
        return Dataset.objects.get(pk=dataset_id)


class DatasetInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    organization = graphene.ID(required=True)
    remote_issued = graphene.Date(required=False)
    remote_modified = graphene.DateTime(required=False)
    period_from = graphene.Date()
    period_to = graphene.Date()
    update_frequency = graphene.String()
    dataset_type = DataType(required=True)
    funnel = graphene.String(required=False, default_value='upload')
    action = graphene.String(required=False, default_value='create data')
    status = graphene.String(required=True)
    tags_list = graphene.List(of_type=graphene.String, default=[], required=False)
    geo_list = graphene.List(of_type=graphene.String, default=[], required=False)
    sector_list = graphene.List(of_type=graphene.String, default=[], required=False)


class PatchDatasetInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    funnel = graphene.String(default=None)
    status = graphene.String(default=None)


class CreateDataset(Output, graphene.Mutation):
    class Arguments:
        dataset_data = DatasetInput()

    dataset = graphene.Field(DatasetType)

    @staticmethod
    @auth_user_action_dataset(action="create_dataset")
    @map_user_dataset
    def mutate(root, info, dataset_data: DatasetInput = None):
        try:
            organization = Organization.objects.get(id=dataset_data.organization)
            catalog = Catalog.objects.filter(organization=organization)[0]
            # catalog = organization.objects.select_related('catalog').all(0)
        except Organization.DoesNotExist as e:
            return {"success": False,
                    "errors": {"id": [{"message": "Organization with given id not found", "code": "404"}]}}
        dataset_instance = Dataset(
            title=dataset_data.title,
            description=dataset_data.description,
            remote_issued=dataset_data.remote_issued,
            remote_modified=dataset_data.remote_modified,
            funnel=dataset_data.funnel,
            action=dataset_data.action,
            status=dataset_data.status,
            catalog=catalog,
            period_to=dataset_data.period_to,
            period_from=dataset_data.period_from,
            update_frequency=dataset_data.update_frequency,
            dataset_type=dataset_data.dataset_type
        )
        dataset_instance.save()
        _add_update_attributes_to_dataset(dataset_instance, "tags", dataset_data.tags_list, Tag)
        _add_update_attributes_to_dataset(dataset_instance, "geography", dataset_data.geo_list, Geography)
        _add_update_attributes_to_dataset(dataset_instance, "sector", dataset_data.sector_list, Sector)
        return CreateDataset(dataset=dataset_instance)


class UpdateDataset(Output, graphene.Mutation):
    class Arguments:
        dataset_data = DatasetInput()

    dataset = graphene.Field(DatasetType)

    @staticmethod
    @auth_user_action_dataset(action="update_dataset")
    def mutate(root, info, dataset_data: DatasetInput = None):
        try:
            dataset_instance = Dataset.objects.get(id=dataset_data.id)
            organization = Organization.objects.get(id=dataset_data.organization)
        except Organization.DoesNotExist as e:
            return {"success": False,
                    "errors": {"id": [{"message": "Organization with given id not found", "code": "404"}]}}
        except Dataset.DoesNotExist as e:
            return {"success": False, "errors": {"id": [{"message": "Dataset with given id not found", "code": "404"}]}}
        catalog = Catalog.objects.filter(organization=organization)[0]
        dataset_instance.title = dataset_data.title
        dataset_instance.description = dataset_data.description
        dataset_instance.remote_issued = dataset_data.remote_issued
        dataset_instance.remote_modified = dataset_data.remote_modified
        dataset_instance.funnel = dataset_data.funnel
        dataset_instance.action = dataset_data.action
        dataset_instance.status = dataset_data.status
        dataset_instance.catalog = catalog
        dataset_instance.period_to = dataset_data.period_to
        dataset_instance.period_from = dataset_data.period_from
        dataset_instance.dataset_type = dataset_data.dataset_type
        dataset_instance.update_frequency = dataset_data.update_frequency

        dataset_instance.save()
        _add_update_attributes_to_dataset(dataset_instance, "tags", dataset_data.tags_list, Tag)
        _add_update_attributes_to_dataset(dataset_instance, "geography", dataset_data.geo_list, Geography)
        _add_update_attributes_to_dataset(dataset_instance, "sector", dataset_data.sector_list, Sector)

        return UpdateDataset(dataset=dataset_instance)


class PatchDataset(Output, graphene.Mutation):
    class Arguments:
        dataset_data = PatchDatasetInput()

    success = graphene.Boolean()
    dataset = graphene.Field(DatasetType)

    @auth_user_action_dataset(action="patch_dataset")
    def mutate(root, info, dataset_data: PatchDatasetInput = None):
        try:
            dataset_instance = Dataset.objects.get(id=dataset_data.id)
        except Dataset.DoesNotExist as e:
            return {"success": False, "errors": {"id": [{"message": "Dataset with given id not found", "code": "404"}]}}
        if dataset_data.status:
            dataset_instance.status = dataset_data.status
        if dataset_data.funnel:
            dataset_instance.funnel = dataset_data.funnel
        dataset_instance.save()
        return PatchDataset(success=True, dataset=dataset_instance)


class Mutation(graphene.ObjectType):
    create_dataset = CreateDataset.Field()
    update_dataset = UpdateDataset.Field()
    patch_dataset = PatchDataset.Field()
