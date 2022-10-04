import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from graphene_file_upload.scalars import Upload

from .models import Resource, ModerationRequest, Dataset
from .decorators import validate_token


class ModerationRequestType(DjangoObjectType):
    class Meta:
        model = ModerationRequest
        fields = "__all__"


class StatusType(graphene.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Query(graphene.ObjectType):
    all_moderation_requests = graphene.List(ModerationRequestType)
    moderation_request = graphene.Field(ModerationRequestType, moderation_request_id=graphene.Int())
    moderation_request_user = graphene.Field(ModerationRequestType)

    def resolve_all_moderation_requests(self, info, **kwargs):
        return ModerationRequest.objects.all()

    def resolve_moderation_request(self, info, moderation_request_id):
        return ModerationRequest.objects.get(pk=moderation_request_id)

    @validate_token
    def resolve_moderation_request_user(self, info, username, **kwargs):
        return ModerationRequest.objects.get(user=username)


class ModerationRequestInput(graphene.InputObjectType):
    id = graphene.ID()
    status = StatusType()
    description = graphene.String(required=True)
    dataset = graphene.String(required=True)
    remark = graphene.String(required=False)
    reject_reason = graphene.String(required=False)


class ModerationRequestUpdateInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = StatusType()
    remark = graphene.String(required=False)


class ModerationRequestMutation(graphene.Mutation, Output):
    class Arguments:
        data_request = ModerationRequestInput()

    moderation_request = graphene.Field(ModerationRequestType)

    @staticmethod
    @validate_token
    def mutate(root, info, data_request: ModerationRequestInput = None, username=None):
        moderation_request_instance = ModerationRequest(
            status=data_request.status,
            description=data_request.description,
            remark=data_request.remark,
            user=username,
        )
        dataset = Dataset.objects.get(id=data_request.dataset)
        moderation_request_instance.dataset = dataset
        moderation_request_instance.save()
        return ModerationRequestMutation(data_request=moderation_request_instance)


class ApproveRejectModerationRequest(graphene.Mutation, Output):
    class Arguments:
        moderation_request = ModerationRequestUpdateInput()

    moderation_request = graphene.Field(ModerationRequestType)

    @staticmethod
    def mutate(root, info, moderation_request: ModerationRequestUpdateInput = None):
        moderation_request_instance = ModerationRequest.objects.get(id=moderation_request.id)
        # TODO: change to try except
        if moderation_request_instance:
            moderation_request_instance.status = moderation_request.status
            if moderation_request.remark:
                moderation_request_instance.remark = moderation_request.remark
        #     TODO: FIX magic strings
        if moderation_request.status == "APPROVED":
            dataset = moderation_request_instance.dataset
            dataset.status = "READYTOPUBLISH"
            dataset.save()
        moderation_request_instance.save()
        return ApproveRejectModerationRequest(moderation_request=moderation_request_instance)
