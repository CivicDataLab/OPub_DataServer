import graphene
from graphene_django import DjangoObjectType

from .models import Dataset


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


class CreateDataset(graphene.Mutation):
    class Arguments:
        dataset_data = DatasetInput(required=True)

    dataset = graphene.Field(DatasetType)

    @staticmethod
    def mutate(root, info, dataset_data=None):
        dataset_instance = Dataset(
            title=dataset_data.title,
            description=dataset_data.description,
        )
        dataset_instance.save()
        return CreateDataset(dataset=dataset_instance)
