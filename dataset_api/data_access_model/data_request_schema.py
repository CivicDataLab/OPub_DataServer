import graphene
import requests
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from graphene_file_upload.scalars import Upload

from dataset_api.models import Resource
from dataset_api.data_access_model.models import DataAccessModelRequest, DataRequest
from dataset_api.decorators import validate_token


class DataRequestType(DjangoObjectType):
    class Meta:
        model = DataRequest
        fields = "__all__"


class StatusType(graphene.Enum):
    REQUESTED = "REQUESTED"
    FULFILLED = "FULFILLED"
    FETCHED = "FETCHED"


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
    data_access_model_request = graphene.ID(required=True)
    resource = graphene.ID(required=True)


class DataRequestUpdateInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = StatusType()
    file = Upload(required=False)


class DataRequestMutation(graphene.Mutation, Output):
    class Arguments:
        data_request = DataRequestInput()

    data_request = graphene.Field(DataRequestType)

    @staticmethod
    @validate_token
    def mutate(root, info, data_request: DataRequestInput = None, username=""):
        # TODO: Check if resource id's provided exists!!
        try:
            resource = Resource.objects.get(id=data_request.resource)
            dam_request = DataAccessModelRequest(id=data_request.data_access_model_request)
        except (Resource.DoesNotExist, DataAccessModelRequest.DoesNotExist) as e:
            return {"success": False,
                    "errors": {
                        "id": [{"message": "Data Access Model or resource with given id not found", "code": "404"}]}}
        data_request_instance = DataRequest(
            status="REQUESTED",
            user=username,
            resource=resource,
            data_access_model_request=dam_request
        )
        data_request_instance.save()
        # TODO: fix magic strings
        # TODO: Move pipeline url to config
        if resource and resource.dataset.dataset_type == "API":
            url = f"https://pipeline.ndp.civicdatalab.in/transformer/api_source_query?api_source_id={resource.id}&request_id={data_request.id}"
            payload = {}
            headers = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            print(response.text)
        elif resource and resource.dataset.dataset_type == "FILE":
            data_request_instance.file = resource.filedetails.file
            data_request_instance.status = "FETCHED"
        data_request_instance.save()
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
            data_request_instance.file = data_request.file
        data_request_instance.save()
        return DataRequestUpdateMutation(data_request=data_request_instance)


class Mutation(graphene.ObjectType):
    data_request = DataRequestMutation.Field()
    update_data_request = DataRequestUpdateMutation.Field()
