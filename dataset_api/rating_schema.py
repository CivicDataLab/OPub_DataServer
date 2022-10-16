import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from .enums import RatingStatus
from .models import DatasetRatings, Dataset


# from .search import update_rating


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
    dataset = graphene.String(required=True)
    review = graphene.String(required=True)
    # overall = graphene.Float()
    data_quality = graphene.Float(required=True)
    # data_standards = graphene.Float()
    # coverage = graphene.Float()


class DatasetRatingApproveRejectInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = graphene.Enum.from_enum(RatingStatus)(required=True)


class CreateDatasetRating(Output, graphene.Mutation):
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
            status=RatingStatus.CREATED.value,
            dataset=dataset
        )
        rating_instance.save()
        # Update rating in elasticsearch
        # update_rating(rating_instance)
        return CreateDatasetRating(dataset_rating=rating_instance)


class ApproveRejectRating(graphene.Mutation, Output):
    class Arguments:
        rating_data = DatasetRatingApproveRejectInput(required=True)

    dataset_rating = graphene.Field(DatasetRatingType)

    @staticmethod
    def mutate(root, info, rating_data: DatasetRatingApproveRejectInput):
        try:
            rating_instance = DatasetRatings.objects.get(id=rating_data.id)
        except DatasetRatings.DoesNotExist as e:
            return {"success": False, "errors": {"id": [{"message": "Dataset with given id not found", "code": "404"}]}}
        rating_instance.status = rating_data.status
        rating_instance.save()
        # Update rating in elasticsearch
        # update_rating_index(rating_instance)
        return ApproveRejectRating(dataset_rating=rating_instance)


class Mutation(graphene.ObjectType):
    create_dataset_rating = CreateDatasetRating.Field()
    approve_reject_dataset_rating = ApproveRejectRating.Field()
