import graphene
from graphene_django import DjangoObjectType

from .models import DatasetRatings, Dataset
from .search import update_rating


class DatasetRatingType(DjangoObjectType):
    class Meta:
        model = DatasetRatings
        fields = "__all__"


class Query(graphene.ObjectType):
    all_dataset_ratings = graphene.List(DatasetRatingType)
    dataset_rating = graphene.List(DatasetRatingType, dataset_id=graphene.Int())
    rating = graphene.Field(DatasetRatingType, dataset_rating_id=graphene.Int())

    def resolve_all_dataset_ratings(self, info, **kwargs):
        return DatasetRatings.objects.all()

    def resolve_dataset_rating(self, info, dataset_id):
        return DatasetRatings.objects.filter(dataset=dataset_id)

    def resolve_rating(self, info, rating_id):
        return DatasetRatings.objects.get(pk=rating_id)


class DatasetRatingInput(graphene.InputObjectType):
    id = graphene.ID()
    dataset = graphene.String()
    review = graphene.String()
    # overall = graphene.Float()
    data_quality = graphene.Float()
    # data_standards = graphene.Float()
    # coverage = graphene.Float()


class CreateDatasetRating(graphene.Mutation):
    class Arguments:
        rating_data = DatasetRatingInput(required=True)

    dataset_rating = graphene.Field(DatasetRatingType)

    @staticmethod
    def mutate(root, info, rating_data: DatasetRatingInput):
        dataset = Dataset.objects.get(id=rating_data.dataset)
        rating_instance = DatasetRatings(
            review=rating_data.review,
            # overall=rating_data.overall,
            data_quality=rating_data.data_quality,
            # data_standards=rating_data.data_standards,
            # coverage=rating_data.coverage,
            dataset=dataset
        )
        rating_instance.save()
        # Update rating in elasticsearch
        update_rating(rating_instance)
        return CreateDatasetRating(dataset_rating=rating_instance)
