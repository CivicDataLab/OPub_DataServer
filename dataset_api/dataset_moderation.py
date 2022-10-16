from collections.abc import Iterable

import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from .decorators import validate_token
from .models import ModerationRequest, Dataset
from .search import index_data


class ModerationRequestType(DjangoObjectType):
    class Meta:
        model = ModerationRequest
        fields = "__all__"


class ModerationStatusType(graphene.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Query(graphene.ObjectType):
    all_moderation_requests = graphene.List(ModerationRequestType)
    moderation_request = graphene.Field(ModerationRequestType, moderation_request_id=graphene.Int())
    moderation_request_user = graphene.List(ModerationRequestType)

    def resolve_all_moderation_requests(self, info, **kwargs):
        return ModerationRequest.objects.all().order_by("-modified_date")

    def resolve_moderation_request(self, info, moderation_request_id):
        return ModerationRequest.objects.get(pk=moderation_request_id)

    @validate_token
    def resolve_moderation_request_user(self, info, username, **kwargs):
        return ModerationRequest.objects.filter(user=username).order_by("-modified_date")


class ModerationRequestInput(graphene.InputObjectType):
    id = graphene.ID()
    status = ModerationStatusType()
    description = graphene.String(required=True)
    dataset = graphene.String(required=True)
    remark = graphene.String(required=False)
    reject_reason = graphene.String(required=False)


class ModerationRequestsApproveRejectInput(graphene.InputObjectType):
    ids: Iterable = graphene.List(graphene.ID, required=True)
    status = ModerationStatusType()
    remark = graphene.String(required=False)


class ModerationRequestMutation(graphene.Mutation, Output):
    class Arguments:
        moderation_request = ModerationRequestInput()

    moderation_request = graphene.Field(ModerationRequestType)

    @staticmethod
    @validate_token
    def mutate(root, info, moderation_request: ModerationRequestInput = None, username=""):
        moderation_request_instance = ModerationRequest(
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
                moderation_request_instance = ModerationRequest.objects.get(id=request_id)
            except ModerationRequest.DoesNotExist as e:
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


class Mutation(graphene.ObjectType):
    moderation_request = ModerationRequestMutation.Field()
    approve_reject_moderation_requests = ApproveRejectModerationRequests.Field()
