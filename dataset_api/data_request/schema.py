import os

import graphene
import requests
import redis
import datetime

from django.core.files import File
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output

from DatasetServer import settings
from dataset_api.constants import DATAREQUEST_SWAGGER_SPEC
from dataset_api.data_request.token_handler import (
    create_access_jwt_token,
    generate_refresh_token,
)
from dataset_api.decorators import validate_token, validate_token_or_none
from dataset_api.enums import DataType, SubscriptionUnits, ValidationUnits
from dataset_api.models import Resource
from dataset_api.models.DataRequest import DataRequest
from dataset_api.models.DatasetAccessModelRequest import DatasetAccessModelRequest

r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


class DataRequestType(DjangoObjectType):
    access_token = graphene.String()
    refresh_token = graphene.String()
    spec = graphene.JSONString()
    remaining_quota = graphene.Int()

    class Meta:
        model = DataRequest
        fields = "__all__"

    @validate_token_or_none
    def resolve_access_token(self: DataRequest, info, username):
        return create_access_jwt_token(self, username)

    @validate_token_or_none
    def resolve_refresh_token(self: DataRequest, info, username):
        return generate_refresh_token(self, username)

    @validate_token_or_none
    def resolve_spec(self: DataRequest, info, username):
        spec = DATAREQUEST_SWAGGER_SPEC.copy()
        spec["paths"]["/refreshtoken"]["get"]["parameters"][0][
            "example"
        ] = generate_refresh_token(self, username)
        spec["paths"]["/getresource"]["get"]["parameters"][0][
            "example"
        ] = create_access_jwt_token(self, username)
        spec["info"]["title"] = self.resource.title
        spec["info"]["description"] = self.resource.description
        return spec

    @validate_token_or_none
    def resolve_remaining_quota(self: DataRequest, info, username=""):
        dam_id = self.dataset_access_model_request.access_model.data_access_model_id
        quota_limit = (
            self.dataset_access_model_request.access_model.data_access_model.subscription_quota
        )
        quota_limit_unit = (
            self.dataset_access_model_request.access_model.data_access_model.subscription_quota_unit
        )
        if not username:
            username = self.dataset_access_model_request.user

        if quota_limit_unit == SubscriptionUnits.DAILY:
            used_quota = r.get(
                ":1:rl||"
                + "||"
                + username
                + "||"
                + str(dam_id)
                + "||"
                + quota_limit_unit.lower()[0]
                + "||quota"
            )
            if used_quota:
                if quota_limit > int(used_quota.decode()):
                    return quota_limit - int(used_quota.decode())
                else:
                    return 0
            else:
                return quota_limit
        elif quota_limit_unit == SubscriptionUnits.WEEKLY:
            used_quota = r.get(
                ":1:rl||" + username + "||" + str(dam_id) + "||" + "7d||quota"
            )
            if used_quota:
                if quota_limit > int(used_quota.decode()):
                    return quota_limit - int(used_quota.decode())
                else:
                    return 0
            else:
                return quota_limit
        elif quota_limit_unit == SubscriptionUnits.MONTHLY:
            used_quota = r.get(
                ":1:rl||" + username + "||" + str(dam_id) + "||" + "30d||quota"
            )
            if used_quota:
                if quota_limit > int(used_quota.decode()):
                    return quota_limit - int(used_quota.decode())
                else:
                    return 0
            else:
                return quota_limit
        elif quota_limit_unit == SubscriptionUnits.QUARTERLY:
            used_quota = r.get(
                ":1:rl||" + username + "||" + str(dam_id) + "||" + "92d||quota"
            )
            if used_quota:
                if quota_limit > int(used_quota.decode()):
                    return quota_limit - int(used_quota.decode())
                else:
                    return 0
            else:
                return quota_limit
        else:
            used_quota = r.get(
                ":1:rl||" + username + "||" + str(dam_id) + "||" + "365d||quota"
            )
            if used_quota:
                if quota_limit > int(used_quota.decode()):
                    return quota_limit - int(used_quota.decode())
                else:
                    return 0
            else:
                return quota_limit


class DatasetRequestStatusType(graphene.Enum):
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
    status = DatasetRequestStatusType()
    file = Upload(required=False)


class DataRequestMutation(graphene.Mutation, Output):
    class Arguments:
        data_request = DataRequestInput()

    data_request = graphene.Field(DataRequestType)

    @staticmethod
    @validate_token_or_none
    def mutate(root, info, data_request: DataRequestInput = None, username=""):
        try:
            resource = Resource.objects.get(id=data_request.resource)
            dam_request = DatasetAccessModelRequest(
                id=data_request.dataset_access_model_request
            )
        except (Resource.DoesNotExist, DatasetAccessModelRequest.DoesNotExist) as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {
                            "message": "Data Access Model or resource with given id not found",
                            "code": "404",
                        }
                    ]
                },
            }
        data_request_instance = DataRequest(
            status="REQUESTED",
            user=username,
            resource=resource,
            dataset_access_model_request=dam_request,
        )
        data_request_instance.save()
        # TODO: fix magic strings
        if resource and resource.dataset.dataset_type == "API":
            url = f"{settings.PIPELINE_URL}transformer/api_source_query?api_source_id={resource.id}&request_id={data_request_instance.id}"
            payload = {}
            headers = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            print(response.text)
        elif resource and resource.dataset.dataset_type == DataType.FILE.value:

            data_request_instance.file = File(
                resource.filedetails.file,
                os.path.basename(resource.filedetails.file.path),
            )
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
