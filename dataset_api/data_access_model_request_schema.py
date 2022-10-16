import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from .decorators import validate_token
from .models import DataAccessModel, DataAccessModelRequest


class DataAccessModelRequestType(DjangoObjectType):
    class Meta:
        model = DataAccessModelRequest
        fields = "__all__"


class DataAccessModelRequestStatusType(graphene.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PurposeType(graphene.Enum):
    EDUCATION = "EDUCATION"
    RESEARCH = "RESEARCH"
    PERSONAL = "PERSONAL"
    OTHERS = "OTHERS"


class Query(graphene.ObjectType):
    all_data_access_model_requests = graphene.List(DataAccessModelRequestType)
    data_access_model_request = graphene.Field(DataAccessModelRequestType, data_access_model_request_id=graphene.Int())
    data_access_model_request_user = graphene.List(DataAccessModelRequestType)

    def resolve_all_data_access_model_requests(self, info, **kwargs):
        return DataAccessModelRequest.objects.all().order_by("-modified")

    def resolve_data_access_model_request(self, info, data_access_model_request_id):
        return DataAccessModelRequest.objects.get(pk=data_access_model_request_id)

    @validate_token
    def resolve_data_access_model_request_user(self, info, username, **kwargs):
        return DataAccessModelRequest.objects.filter(user=username).order_by("-modified")


class DataAccessModelRequestInput(graphene.InputObjectType):
    id = graphene.ID()
    description = graphene.String(required=True)
    data_access_model = graphene.String(required=True)
    purpose = PurposeType(required=True)


class DataAccessModelRequestUpdateInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = DataAccessModelRequestStatusType()
    remark = graphene.String(required=False)


class DataAccessModelRequestMutation(graphene.Mutation, Output):
    class Arguments:
        data_access_model_request = DataAccessModelRequestInput()

    data_access_model_request = graphene.Field(DataAccessModelRequestType)

    @staticmethod
    @validate_token
    def mutate(root, info, data_access_model_request: DataAccessModelRequestInput = None, username=""):
        data_access_model = DataAccessModel.objects.get(id=data_access_model_request.data_access_model)
        # TODO: fix magic strings
        data_access_model_request_instance = DataAccessModelRequest(
            status="REQUESTED",
            purpose=data_access_model_request.purpose,
            description=data_access_model_request.description,
            user=username,
            data_access_model_id=data_access_model
        )
        data_access_model_request_instance.save()
        data_access_model.save()
        return DataAccessModelRequestMutation(data_access_model_request=data_access_model_request_instance)


class ApproveRejectDataAccessModelRequest(graphene.Mutation, Output):
    class Arguments:
        data_access_model_request = DataAccessModelRequestUpdateInput()

    data_access_model_request = graphene.Field(DataAccessModelRequestType)

    @staticmethod
    def mutate(root, info, data_access_model_request: DataAccessModelRequestUpdateInput = None):
        try:
            data_access_model_request_instance = DataAccessModelRequest.objects.get(id=data_access_model_request.id)
        except DataAccessModelRequest.DoesNotExist as e:
            return {"success": False,
                    "errors": {"id": [{"message": "Data Access Model with given id not found", "code": "404"}]}}
        data_access_model_request_instance.status = data_access_model_request.status
        if data_access_model_request.remark:
            data_access_model_request_instance.remark = data_access_model_request.remark
        data_access_model_request_instance.save()
        return ApproveRejectDataAccessModelRequest(data_access_model_request=data_access_model_request_instance)


class Mutation(graphene.ObjectType):
    data_access_model_request = DataAccessModelRequestMutation.Field()
    approve_reject_data_access_model_request = ApproveRejectDataAccessModelRequest.Field()