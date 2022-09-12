import graphene
from graphene_django import DjangoObjectType

from .models import Dataset, Catalog, Tag, Geography


class DatasetType(DjangoObjectType):
    class Meta:
        model = Dataset
        fields = "__all__"


def _add_update_attributes_to_dataset(dataset_instance, object_field, attribute_list, attribute_type):
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
        return Dataset.objects.all()

    def resolve_dataset(self, info, dataset_id):
        return Dataset.objects.get(pk=dataset_id)


class DatasetInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    catalog = graphene.String(required=True)
    sector = graphene.String(required=True)
    license = graphene.String(required=True)
    remote_issued = graphene.DateTime(required=False)
    remote_modified = graphene.DateTime(required=False)
    period_from = graphene.Date()
    period_to = graphene.Date()
    update_frequency = graphene.String()
    funnel = graphene.String(required=False)
    action = graphene.String(required=False)
    status = graphene.String(required=True)
    access_type = graphene.String(required=True)
    tags_list = graphene.List(of_type=graphene.String, default=[], required=False)
    geo_list = graphene.List(of_type=graphene.String, default=[], required=False)


class CreateDataset(graphene.Mutation):
    class Arguments:
        dataset_data = DatasetInput()

    dataset = graphene.Field(DatasetType)

    @staticmethod
    def mutate(root, info, dataset_data: DatasetInput = None):
        catalog = Catalog.objects.get(id=dataset_data.catalog)
        # print(dataset_data)
        dataset_instance = Dataset(
            title=dataset_data.title,
            description=dataset_data.description,
            License=dataset_data.license,
            sector=dataset_data.sector,
            remote_issued=dataset_data.remote_issued,
            remote_modified=dataset_data.remote_modified,
            funnel=dataset_data.funnel,
            action=dataset_data.action,
            status=dataset_data.status,
            access_type=dataset_data.access_type,
            catalog=catalog,
            period_to=dataset_data.period_to,
            period_from=dataset_data.period_from,
            update_frequency=dataset_data.update_frequency
        )
        dataset_instance.save()
        _add_update_attributes_to_dataset(dataset_instance, "tags", dataset_data.tags_list, Tag)
        _add_update_attributes_to_dataset(dataset_instance, "geography", dataset_data.geo_list, Geography)
        return CreateDataset(dataset=dataset_instance)


class UpdateDataset(graphene.Mutation):
    class Arguments:
        dataset_data = DatasetInput()

    dataset = graphene.Field(DatasetType)

    @staticmethod
    def mutate(root, info, dataset_data: DatasetInput = None):
        dataset_instance = Dataset.objects.get(id=dataset_data.id)
        catalog = Catalog.objects.get(id=dataset_data.catalog)
        if dataset_instance:
            dataset_instance.title = dataset_data.title
            dataset_instance.description = dataset_data.description
            dataset_instance.License = dataset_data.license
            dataset_instance.sector = dataset_data.sector
            dataset_instance.remote_issued = dataset_data.remote_issued
            dataset_instance.remote_modified = dataset_data.remote_modified
            dataset_instance.funnel = dataset_data.funnel
            dataset_instance.action = dataset_data.action
            dataset_instance.status = dataset_data.status
            dataset_instance.access_type = dataset_data.access_type
            dataset_instance.catalog = catalog
            dataset_instance.period_to = dataset_data.period_to
            dataset_instance.period_from = dataset_data.period_from
            dataset_instance.save()
            _add_update_attributes_to_dataset(dataset_instance, "tags", dataset_data.tags_list, Tag)
            _add_update_attributes_to_dataset(dataset_instance, "geography", dataset_data.geo_list, Geography)

            return UpdateDataset(dataset=dataset_instance)
        return UpdateDataset(dataset=None)
