import graphene
from graphene_django import DjangoObjectType

from .models import Dataset, Catalog, Tag, Geography, Sector, Organization
from .search import update_dataset
from .decorators import validate_token

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

    def resolve_all_datasets(self, info, **kwargs):
        return Dataset.objects.all().order_by("-modified")

    def resolve_dataset(self, info, dataset_id):
        return Dataset.objects.get(pk=dataset_id)


class DatasetInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    organization = graphene.ID(required=True)
    remote_issued = graphene.DateTime(required=False)
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


class CreateDataset(graphene.Mutation):
    class Arguments:
        dataset_data = DatasetInput()

    dataset = graphene.Field(DatasetType)

    @staticmethod
    def mutate(root, info, dataset_data: DatasetInput = None):
        organization = Organization.objects.get(id=dataset_data.organization)
        catalog = Catalog.objects.filter(organization=organization)[0]
        # catalog = organization.objects.select_related('catalog').all(0)
        # print(dataset_data)
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



class UpdateDataset(graphene.Mutation):
    class Arguments:
        dataset_data = DatasetInput()

    dataset = graphene.Field(DatasetType)
    @staticmethod
    def mutate(root, info, dataset_data: DatasetInput = None):
        dataset_instance = Dataset.objects.get(id=dataset_data.id)
        organization = Organization.objects.get(id=dataset_data.organization)
        catalog = Catalog.objects.filter(organization=organization)[0]
        if dataset_instance:
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

            dataset_instance.save()
            _add_update_attributes_to_dataset(dataset_instance, "tags", dataset_data.tags_list, Tag)
            _add_update_attributes_to_dataset(dataset_instance, "geography", dataset_data.geo_list, Geography)
            _add_update_attributes_to_dataset(dataset_instance, "sector", dataset_data.sector_list, Sector)

            # For updating indexed data in elasticsearch.
            update_dataset(dataset_instance)

            return UpdateDataset(dataset=dataset_instance)
        return UpdateDataset(dataset=None)

class PatchDataset(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        funnel = graphene.String()
        status = graphene.String()
    
    success = graphene.Boolean()
    dataset = graphene.Field(DatasetType)
    
    @validate_token
    def mutate(root, info, username, id, funnel=None, status=None):
        try:
            dataset_instance = Dataset.objects.get(id=id)
        except Dataset.DoesNotExist as e:
            return {"success": False, "errors": {"id": [{"message": "Dataset with given id not found", "code": "404"}]}}
        if status:
            dataset_instance.status = status
        if funnel:
            dataset_instance.funnel = funnel
        dataset_instance.save()
        return PatchDataset(success=True, dataset=dataset_instance)