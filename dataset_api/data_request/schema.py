import os

import graphene
import requests
from django.core.files import File
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from graphene_file_upload.scalars import Upload

from dataset_api.models import Resource
from dataset_api.models.DataRequest import DataRequest
from dataset_api.models.DatasetAccessModelRequest import DatasetAccessModelRequest
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
    dataset_access_model_request = graphene.ID(required=True)
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
        try:
            resource = Resource.objects.get(id=data_request.resource)
            dam_request = DatasetAccessModelRequest(id=data_request.dataset_access_model_request)
        except (Resource.DoesNotExist, DatasetAccessModelRequest.DoesNotExist) as e:
            return {"success": False,
                    "errors": {
                        "id": [{"message": "Data Access Model or resource with given id not found", "code": "404"}]}}
        data_request_instance = DataRequest(
            status="REQUESTED",
            user=username,
            resource=resource,
            dataset_access_model_request=dam_request
        )
        data_request_instance.save()
        # TODO: fix magic strings
        # TODO: Move pipeline url to config
        if resource and resource.dataset.dataset_type == "API":
            url = f"https://pipeline.ndp.civicdatalab.in/transformer/api_source_query?api_source_id={resource.id}&request_id={data_request_instance.id}"
            payload = {}
            headers = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            print(response.text)
        elif resource and resource.dataset.dataset_type == "FILE":

            data_request_instance.file = File(resource.filedetails.file,
                                              os.path.basename(resource.filedetails.file.path))
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
