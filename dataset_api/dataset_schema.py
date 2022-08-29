import graphene
from graphene_django import DjangoObjectType

from .models import Dataset, Catalog


class DatasetType(DjangoObjectType):
    class Meta:
        model = Dataset
        fields = "__all__"


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
    geography = graphene.String(required=True)
    remote_issued = graphene.DateTime(required=False)
    remote_modified = graphene.DateTime(required=False)
    funnel = graphene.String(required=False)
    action = graphene.String(required=False)
    status = graphene.String(required=True)
    access_type = graphene.String(required=True)


class CreateDataset(graphene.Mutation):
    class Arguments:
        dataset_data = DatasetInput()

    dataset = graphene.Field(DatasetType)

    @staticmethod
    def mutate(root, info, dataset_data=None):
        catalog = Catalog.objects.get(id=dataset_data.catalog)
        dataset_instance = Dataset(
            title=dataset_data.title,
            description=dataset_data.description,
            License=dataset_data.license,
            sector=dataset_data.sector,
            geography=dataset_data.geography,
            remote_issued=dataset_data.remote_issued,
            remote_modified=dataset_data.remote_modified,
            funnel=dataset_data.funnel,
            action=dataset_data.action,
            status=dataset_data.status,
            access_type=dataset_data.access_type,
            catalog=catalog
        )
        dataset_instance.save()
        return CreateDataset(dataset=dataset_instance)
