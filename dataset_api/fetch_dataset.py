import graphene
import requests
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from graphene_file_upload.scalars import Upload

from .models import Resource, DataRequest, APIResource
from .decorators import validate_token


class DataRequestType(DjangoObjectType):
    class Meta:
        model = DataRequest
        fields = "__all__"


class StatusType(graphene.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FULFILLED = "FULFILLED"
    FETCHED = "FETCHED"


class PurposeType(graphene.Enum):
    EDUCATION = "EDUCATION"
    RESEARCH = "RESEARCH"
    PERSONAL = "PERSONAL"
    OTHERS = "OTHERS"


class Query(graphene.ObjectType):
    all_data_requests = graphene.List(DataRequestType)
    data_request = graphene.Field(DataRequestType, data_request_id=graphene.Int())
    data_request_user = graphene.Field(DataRequestType)

    def resolve_all_data_requests(self, info, **kwargs):
        return DataRequest.objects.all()

    def resolve_data_request(self, info, data_request_id):
        return DataRequest.objects.get(pk=data_request_id)

    @validate_token
    def resolve_data_request_user(self, info, username, **kwargs):
        return DataRequest.objects.get(user=username)


class DataRequestInput(graphene.InputObjectType):
    id = graphene.ID()
    status = StatusType()
    purpose = PurposeType()
    description = graphene.String(required=True)
    remark = graphene.String(required=False)
    file = Upload(required=False)
    resource_list = graphene.List(of_type=graphene.String, required=True)
    reject_reason = graphene.String(required=False)


class DataRequestUpdateInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = StatusType()
    remark = graphene.String(required=False)
    file = Upload(required=False)


class DataRequestMutation(graphene.Mutation, Output):
    class Arguments:
        data_request = DataRequestInput()

    data_request = graphene.Field(DataRequestType)

    @staticmethod
    @validate_token
    def mutate(root, info, data_request: DataRequestInput = None, username=None):
        print(root, info)
        # To do: Check if resource id's provided exists!!
        data_request_instance = DataRequest(
            status=data_request.status,
            description=data_request.description,
            remark=data_request.remark,
            purpose=data_request.purpose,
            user=username,
            file=data_request.file
        )
        data_request_instance.save()
        for resource_id in data_request.resource_list:
            try:
                resource = Resource.objects.get(id=int(resource_id))
                data_request_instance.resource.add(resource)
            except Resource.DoesNotExist as e:
                pass
            try:
                resource = APIResource.objects.get(id=int(resource_id))
                data_request_instance.api_resource.add(resource)
            except APIResource.DoesNotExist as e:
                pass

        return DataRequestMutation(data_request=data_request_instance)


class DataRequestUpdateMutation(graphene.Mutation, Output):
    class Arguments:
        data_request = DataRequestUpdateInput()

    data_request = graphene.Field(DataRequestType)

    @staticmethod
    def mutate(root, info, data_request: DataRequestUpdateInput = None):
        data_request_instance = DataRequest.objects.get(id=data_request.id)
        if data_request_instance:
            data_request_instance.status = data_request.status
            if data_request.remark:
                data_request_instance.remark = data_request.remark
            data_request_instance.file = data_request.file
        data_request_instance.save()
        return DataRequestUpdateMutation(data_request=data_request_instance)


class DataRequestApproveRejectInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = StatusType()
    remark = graphene.String(required=True)


class ApproveRejectDataRequest(graphene.Mutation, Output):
    class Arguments:
        data_request = DataRequestApproveRejectInput()

    data_request = graphene.Field(DataRequestType)

    @staticmethod
    def mutate(root, info, data_request: DataRequestApproveRejectInput = None):
        data_request_instance = DataRequest.objects.get(id=data_request.id)
        if data_request_instance:
            data_request_instance.status = data_request.status
            data_request_instance.remark = data_request.remark
        data_request_instance.save()
        resource = data_request_instance.resource.all()[0]
        dataset = resource.dataset
        try:
            api_resource = data_request_instance.api_resource.all()[0]
        except IndexError:
            api_resource = None
        if resource and dataset.dataset_type is "API" and data_request.status is StatusType.APPROVED:
            url = f"https://pipeline.ndp.civicdatalab.in/transformer/api_source_query?api_source_id={resource.id}&request_id={data_request.id}"
            payload = {}
            headers = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            print(response.text)
        elif resource and dataset.dataset_type is "FILE" and data_request.status is StatusType.APPROVED:
            data_request_instance.file = resource.filedetails.file
            data_request_instance.status = StatusType.FETCHED
        data_request_instance.save()
        return DataRequestUpdateMutation(data_request=data_request_instance)
