from collections.abc import Iterable

import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from .decorators import validate_token
from .enums import ReviewType
from .models import Dataset
from .models import DatasetReviewRequest

from .search import index_data


class ModerationRequestType(DjangoObjectType):
    class Meta:
        model = DatasetReviewRequest
        fields = "__all__"


class ReviewRequestType(DjangoObjectType):
    class Meta:
        model = DatasetReviewRequest
        fields = "__all__"


class StatusType(graphene.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Query(graphene.ObjectType):
    all_moderation_requests = graphene.List(ModerationRequestType)
    moderation_request = graphene.Field(ModerationRequestType, moderation_request_id=graphene.Int())
    moderation_request_user = graphene.List(ModerationRequestType)
    review_request_user = graphene.List(ModerationRequestType)
    all_review_requests = graphene.List(ReviewRequestType)
    review_request = graphene.Field(ReviewRequestType, review_request_id=graphene.Int())

    def resolve_all_moderation_requests(self, info, **kwargs):
        return DatasetReviewRequest.objects.filter(request_type=ReviewType.MODERATION.value).order_by("-modified_date")

    def resolve_moderation_request(self, info, moderation_request_id):
        return DatasetReviewRequest.objects.get(pk=moderation_request_id)

    @validate_token
    def resolve_review_request_user(self, info, username, **kwargs):
        return DatasetReviewRequest.objects.filter(user=username).order_by("-modeified_date")

    @validate_token
    def resolve_moderation_request_user(self, info, username, **kwargs):
        return DatasetReviewRequest.objects.filter(user=username).order_by("-modified_date")

    def resolve_all_review_requests(self, info, **kwargs):
        return DatasetReviewRequest.objects.filter(request_type=ReviewType.REVIEW.value).order_by("-modified_date")

    def resolve_review_request(self, info, request_id):
        return DatasetReviewRequest.objects.get(pk=request_id)


class ModerationRequestInput(graphene.InputObjectType):
    id = graphene.ID()
    status = StatusType()
    description = graphene.String(required=True)
    dataset = graphene.String(required=True)
    remark = graphene.String(required=False)
    reject_reason = graphene.String(required=False)


class ReviewRequestInput(graphene.InputObjectType):
    id = graphene.ID()
    status = StatusType()
    description = graphene.String(required=True)
    dataset = graphene.String(required=True)


class ModerationRequestsApproveRejectInput(graphene.InputObjectType):
    ids: Iterable = graphene.List(graphene.ID, required=True)
    status = StatusType()
    remark = graphene.String(required=False)


class ReviewRequestsApproveRejectInput(graphene.InputObjectType):
    ids: Iterable = graphene.List(graphene.ID, required=True)
    status = StatusType()
    remark = graphene.String(required=False)


class ModerationRequestMutation(graphene.Mutation, Output):
    class Arguments:
        moderation_request = ModerationRequestInput()

    moderation_request = graphene.Field(ModerationRequestType)

    @staticmethod
    @validate_token
    def mutate(root, info, moderation_request: ModerationRequestInput, username=""):
        moderation_request_instance = DatasetReviewRequest(
            status=moderation_request.status,
            description=moderation_request.description,
            remark=moderation_request.remark,
            user=username,
        )
        dataset = Dataset.objects.get(id=moderation_request.dataset)
        moderation_request_instance.dataset = dataset
        moderation_request_instance.save()
        # TODO: fix magic string
        dataset.status = "UNDERMODERATION"
        dataset.save()
        return ModerationRequestMutation(moderation_request=moderation_request_instance)


class ReviewRequestMutation(graphene.Mutation, Output):
    class Arguments:
        review_request = ReviewRequestInput()

    review_request = graphene.Field(ReviewRequestType)

    @staticmethod
    @validate_token
    def mutate(root, info, review_request: ReviewRequestInput, username=""):
        review_request_instance = DatasetReviewRequest(
            status=review_request.status,
            description=review_request.description,
            remark=review_request.remark,
            user=username,
        )
        dataset = Dataset.objects.get(id=review_request.dataset)
        review_request_instance.dataset = dataset
        review_request_instance.save()
        # TODO: fix magic string
        dataset.status = "UNDERREVIEW"
        dataset.save()
        return ReviewRequestMutation(review_request=review_request_instance)


class ApproveRejectModerationRequests(graphene.Mutation, Output):
    class Arguments:
        moderation_request = ModerationRequestsApproveRejectInput()

    moderation_requests = graphene.List(of_type=ModerationRequestType)

    @staticmethod
    def mutate(root, info, moderation_request: ModerationRequestsApproveRejectInput = None):
        errors = []
        moderation_requests = []
        for request_id in moderation_request.ids:
            try:
                moderation_request_instance = DatasetReviewRequest.objects.get(id=request_id)
            except DatasetReviewRequest.DoesNotExist as e:
                errors.append({"message": f"Moderation request with id {request_id} does not exist", "code": "404"})
                continue

            if moderation_request_instance:
                moderation_request_instance.status = moderation_request.status
                if moderation_request.remark:
                    moderation_request_instance.remark = moderation_request.remark
            #     TODO: FIX magic strings
            if moderation_request.status == "APPROVED":
                dataset = moderation_request_instance.dataset
                dataset.status = "PUBLISHED"
                dataset.save()
                # Index data in Elasticsearch
                index_data(dataset)
            if moderation_request.status == "REJECTED":
                dataset = moderation_request_instance.dataset
                dataset.status = "DRAFT"
                dataset.save()
            moderation_request_instance.save()
            moderation_requests.append(moderation_request_instance)
        if errors:
            return {"success": False,
                    "errors": {"ids": errors}}

        return ApproveRejectModerationRequests(moderation_requests=moderation_requests)


class ApproveRejectReviewRequests(graphene.Mutation, Output):
    class Arguments:
        review_request = ReviewRequestsApproveRejectInput()

    review_requests = graphene.List(of_type=ReviewRequestType)

    @staticmethod
    def mutate(root, info, review_request: ReviewRequestsApproveRejectInput = None):
        errors = []
        review_requests = []
        for request_id in review_request.ids:
            try:
                review_request_instance = DatasetReviewRequest.objects.get(id=request_id)
            except DatasetReviewRequest.DoesNotExist as e:
                errors.append({"message": f"Review request with id {request_id} does not exist", "code": "404"})
                continue

            if review_request_instance:
                review_request_instance.status = review_request.status
                if review_request.remark:
                    review_request_instance.remark = review_request.remark
            #     TODO: FIX magic strings
            if review_request.status == "APPROVED":
                dataset = review_request_instance.dataset
                dataset.status = "REVIEWED"
                dataset.save()
                # Index data in Elasticsearch
                index_data(dataset)
            if review_request.status == "REJECTED":
                dataset = review_request_instance.dataset
                dataset.status = "DRAFT"
                dataset.save()
            review_request_instance.save()
            review_requests.append(review_request_instance)
        if errors:
            return {"success": False,
                    "errors": {"ids": errors}}

        return ApproveRejectReviewRequests(review_requests=review_requests)


class Mutation(graphene.ObjectType):
    moderation_request = ModerationRequestMutation.Field()
    review_request = ReviewRequestMutation.Field()
    approve_reject_moderation_requests = ApproveRejectModerationRequests.Field()
