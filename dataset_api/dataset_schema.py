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
    title = graphene.String()
    description = graphene.String()
    catalog = graphene.String()
    sector = graphene.String()
    license = graphene.String()
    geography = graphene.String()


class CreateDataset(graphene.Mutation):
    class Arguments:
        dataset_data = DatasetInput(required=True)

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
            catalog=catalog
        )
        dataset_instance.save()
        return CreateDataset(dataset=dataset_instance)
