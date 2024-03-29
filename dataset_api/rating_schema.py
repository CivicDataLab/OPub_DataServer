import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from graphql import GraphQLError

from .decorators import validate_token, validate_token_or_none
from .enums import RatingStatus
from .models import DatasetRatings, Dataset
from .utils import get_client_ip, log_activity
import datetime

# from .search import update_rating


class DatasetRatingType(DjangoObjectType):
    class Meta:
        model = DatasetRatings
        fields = "__all__"


class Query(graphene.ObjectType):
    all_dataset_ratings = graphene.List(DatasetRatingType)
    dataset_rating = graphene.List(DatasetRatingType, dataset_id=graphene.Int())
    rating = graphene.Field(DatasetRatingType, dataset_rating_id=graphene.Int())
    rating_by_org = graphene.List(DatasetRatingType)

    def resolve_all_dataset_ratings(self, info, **kwargs):
        return DatasetRatings.objects.all()

    def resolve_dataset_rating(self, info, dataset_id):
        return DatasetRatings.objects.filter(dataset=dataset_id)

    def resolve_rating(self, info, rating_id):
        return DatasetRatings.objects.get(pk=rating_id)
    
    def resolve_rating_by_org(self, info):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        dataset_ids = list(Dataset.objects.filter(catalog__organization=org_id).values_list('id', flat=True))
        # print(dataset_ids)
        return DatasetRatings.objects.filter(dataset__in=dataset_ids)


class DatasetRatingInput(graphene.InputObjectType):
    id = graphene.ID()
    dataset = graphene.ID(required=True)
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
    @validate_token
    def mutate(root, info, rating_data: DatasetRatingInput, username=None, **kwargs):
        dataset = Dataset.objects.get(id=rating_data.dataset)
        previous_rating_instance = DatasetRatings.objects.filter(
            user=username, dataset=dataset
        ).order_by("-modified")
        if previous_rating_instance.exists():
            time_check = previous_rating_instance[0].modified + datetime.timedelta(
                days=1
            )
            if datetime.datetime.now(datetime.timezone.utc) > time_check:
                rating_instance = DatasetRatings(
                    review=rating_data.review,
                    # overall=rating_data.overall,
                    data_quality=rating_data.data_quality,
                    # data_standards=rating_data.data_standards,
                    # coverage=rating_data.coverage,
                    status=RatingStatus.CREATED.value,
                    dataset=dataset,
                    user=username,
                )
                rating_instance.save()
            else:
                raise GraphQLError(
                    "You have already rated this dataset. Try again after 1 day."
                )
        else:
            rating_instance = DatasetRatings(
                review=rating_data.review,
                # overall=rating_data.overall,
                data_quality=rating_data.data_quality,
                # data_standards=rating_data.data_standards,
                # coverage=rating_data.coverage,
                status=RatingStatus.CREATED.value,
                dataset=dataset,
                user=username,
            )
            rating_instance.save()

            log_activity(
                target_obj=rating_instance,
                ip=get_client_ip(info),
                username=username,
                target_group=dataset.catalog.organization,
                verb="Commented",
            )
        # Update rating in elasticsearch
        # update_rating(rating_instance)
        return CreateDatasetRating(dataset_rating=rating_instance)


class ApproveRejectRating(graphene.Mutation, Output):
    class Arguments:
        rating_data = DatasetRatingApproveRejectInput(required=True)

    dataset_rating = graphene.Field(DatasetRatingType)

    @staticmethod
    @validate_token_or_none
    def mutate(root, info, username, rating_data: DatasetRatingApproveRejectInput):
        try:
            rating_instance = DatasetRatings.objects.get(id=rating_data.id)
        except DatasetRatings.DoesNotExist as e:
            raise GraphQLError("Dataset with given id not found")
        rating_instance.status = rating_data.status
        rating_instance.save()
        # Update rating in elasticsearch
        # update_rating_index(rating_instance)
        log_activity(
            target_obj=rating_instance,
            ip=get_client_ip(info),
            username=username,
            target_group=rating_instance.dataset.catalog.organization,
            verb=rating_data.status,
        )
        return ApproveRejectRating(dataset_rating=rating_instance)


class Mutation(graphene.ObjectType):
    create_dataset_rating = CreateDatasetRating.Field()
    approve_reject_dataset_rating = ApproveRejectRating.Field()
