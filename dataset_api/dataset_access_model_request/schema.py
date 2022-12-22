import copy
import datetime
import redis

import graphene
from django.utils import timezone
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from django.db.models import Q
from graphql import GraphQLError
from django.conf import settings
from activity_log.signal import activity

from dataset_api.models.DatasetAccessModelRequest import DatasetAccessModelRequest
from dataset_api.models.DatasetAccessModel import DatasetAccessModel
from dataset_api.decorators import (
    validate_token,
    validate_token_or_none,
    auth_user_by_org,
)
from .decorators import auth_query_dam_request
from dataset_api.enums import SubscriptionUnits, ValidationUnits
from ..constants import DATAREQUEST_SWAGGER_SPEC
from ..data_request.token_handler import create_data_refresh_token, create_data_jwt_token
from ..models import DatasetAccessModelResource, Resource 
from ..utils import get_client_ip, get_data_access_model_request_validity, log_activity

r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


class DataAccessModelRequestType(DjangoObjectType):
    validity = graphene.String()
    remaining_quota = graphene.Int()
    is_valid = graphene.Boolean()

    class Meta:
        model = DatasetAccessModelRequest
        fields = "__all__"

    @validate_token_or_none
    def resolve_validity(self: DatasetAccessModelRequest, info, username=""):
        validity = get_data_access_model_request_validity(self)
        if validity:
            return validity.strftime("%d-%m-%Y")
        return None

    @validate_token
    def resolve_is_valid(self: DatasetAccessModelRequest, info, username=""):
        validity = get_data_access_model_request_validity(self)
        dam_quota_unit = self.access_model.data_access_model.subscription_quota_unit
        quota_limit = self.access_model.data_access_model.subscription_quota

        if validity:
            if timezone.now() >= validity:
                return False
            else:
                if dam_quota_unit == SubscriptionUnits.LIMITEDDOWNLOAD:
                    used_quota = r.get(":1:rl||" + username + "||" + str(self.id) + "||" + "365d||quota")
                    if used_quota:
                        if quota_limit > int(used_quota.decode()):
                            return True
                        else:
                            return False
                    else:
                        return None
                else:
                    return True
        return None

    @validate_token_or_none
    def resolve_remaining_quota(self: DatasetAccessModelRequest, info, username=""):
        dam_request_id = self.id
        quota_limit = self.access_model.data_access_model.subscription_quota
        quota_limit_unit = self.access_model.data_access_model.subscription_quota_unit
        if not username:
            if self.user:
                username = self.user
            else:
                username = ""

        if quota_limit_unit == SubscriptionUnits.DAILY:
            used_quota = r.get(
                ":1:rl||"
                + username
                + "||"
                + str(dam_request_id)
                + "||"
                + quota_limit_unit.lower()[0]
                + "||quota"
            )
        elif quota_limit_unit == SubscriptionUnits.WEEKLY:
            used_quota = r.get(
                ":1:rl||" + username + "||" + str(dam_request_id) + "||" + "7d||quota"
            )
        elif quota_limit_unit == SubscriptionUnits.MONTHLY:
            used_quota = r.get(
                ":1:rl||" + username + "||" + str(dam_request_id) + "||" + "30d||quota"
            )
        elif quota_limit_unit == SubscriptionUnits.QUARTERLY:
            used_quota = r.get(
                ":1:rl||" + username + "||" + str(dam_request_id) + "||" + "92d||quota"
            )
        else:
            used_quota = r.get(
                ":1:rl||" + username + "||" + str(dam_request_id) + "||" + "365d||quota"
            )
        if used_quota:
            if quota_limit > int(used_quota.decode()):
                return quota_limit - int(used_quota.decode())
            else:
                return 0
        else:
            return quota_limit


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
    data_access_model_request = graphene.Field(
        DataAccessModelRequestType, data_access_model_request_id=graphene.Int()
    )
    data_access_model_request_user = graphene.List(DataAccessModelRequestType)
    data_access_model_request_org = graphene.List(
        DataAccessModelRequestType, org_id=graphene.Int()
    )
    data_spec = graphene.JSONString(resource_id=graphene.Argument(graphene.ID, required=True),
                                    dataset_access_model_request_id=graphene.Argument(graphene.ID, required=False),
                                    dataset_access_model_resource_id=graphene.Argument(graphene.ID, required=True))

    # Access : PMU
    @auth_user_by_org(action="query")
    def resolve_all_data_access_model_requests(self, info, role, **kwargs):
        if role == "PMU":
            return DatasetAccessModelRequest.objects.all().order_by("-modified")
        else:
            raise GraphQLError("Access Denied")

    # Access : PMU/DPA of that org.
    @auth_query_dam_request(action="query||request_id")
    def resolve_data_access_model_request(
        self, info, data_access_model_request_id, role
    ):
        if role == "PMU" or role == "DPA":
            return DatasetAccessModelRequest.objects.get(
                pk=data_access_model_request_id
            )
        else:
            raise GraphQLError("Access Denied")

    @validate_token
    def resolve_data_access_model_request_user(self, info, username, **kwargs):
        return DatasetAccessModelRequest.objects.filter(user=username).order_by(
            "-modified"
        )

    # Access : PMU/DPA of that org.
    @auth_user_by_org(action="query")
    def resolve_data_access_model_request_org(self, info, role):
        if role == "PMU" or role == "DPA":
            org_id = info.context.META.get("HTTP_ORGANIZATION")
            return DatasetAccessModelRequest.objects.filter(
                Q(access_model_id__data_access_model__organization=org_id),
            ).order_by("-modified")
        else:
            raise GraphQLError("Access Denied")

    @validate_token_or_none
    def resolve_data_spec(self, info, username, resource_id, dataset_access_model_resource_id,
                         dataset_access_model_request_id=""):
        resource_instance = Resource.objects.get(pk=resource_id)
        dam_resource = DatasetAccessModelResource.objects.get(pk=dataset_access_model_resource_id)
        dataset_access_model = dam_resource.dataset_access_model
        is_open = dataset_access_model.data_access_model.type == "OPEN"
        spec = copy.deepcopy(DATAREQUEST_SWAGGER_SPEC)
        if not username:
            username = get_client_ip(info)
        if dataset_access_model_request_id != "":
            dam_request = DatasetAccessModelRequest.objects.get(pk=dataset_access_model_request_id)
        elif is_open:
            dam_request = create_dataset_access_model_request(
                dataset_access_model,
                "",
                "OTHERS",
                username,
                user_email=username,
                status="APPROVED",
            )
        else:
            raise GraphQLError("Invalid access id")
        data_token = create_data_refresh_token(dam_resource, dam_request, username)
        spec["paths"]["/refresh_data_token"]["get"]["parameters"][0]["example"] = data_token
        data_token = create_data_jwt_token(dam_resource, dam_request, username)
        spec["paths"]["/get_dist_data"]["get"]["parameters"][0]["example"] = data_token
        parameters = []
        if resource_instance and resource_instance.dataset.dataset_type == "API":
            parameters = resource_instance.apidetails.apiparameter_set.all().exclude(type="PREVIEW")
            for parameter in parameters:
                param_input = {
                    "name": parameter.key,
                    "in": "query",
                    "required": True,
                    "description": parameter.description,
                    "schema": {"type": parameter.format},
                    "example": parameter.default,
                }
                spec["paths"]["/get_dist_data"]["get"]["parameters"].append(param_input)
            if resource_instance.apidetails.format_key and resource_instance.apidetails.format_key != "":
                param_input = {
                    "name": "format",
                    "in": "query",
                    "required": True,
                    "description": "Return format of data",
                    "schema": {"type": "string", "enum": resource_instance.apidetails.supported_formats},
                    "example": resource_instance.apidetails.default_format,
                }
                spec["paths"]["/get_dist_data"]["get"]["parameters"].append(param_input)
        elif resource_instance and resource_instance.dataset.dataset_type == "FILE":
            if resource_instance.filedetails.format in ["CSV", "XML", "JSON"]:
                param_input = {
                    "name": "format",
                    "in": "query",
                    "required": True,
                    "description": "Return format of data",
                    "schema": {"type": "string", "enum": ["CSV", "XML", "JSON"]},
                    "example": resource_instance.filedetails.format,
                }
                spec["paths"]["/get_dist_data"]["get"]["parameters"].append(param_input)
                if resource_instance.filedetails.format in ["CSV"]:
                    pagination_size_param = {
                        "name": "size",
                        "in": "query",
                        "required": "true",
                        "description": "number of records to return",
                        "schema": {
                            "type": "integer",
                            "miniumum": 1
                        },
                        "example": 5
                    }
                    pagination_start_param = {
                        "name": "from",
                        "in": "query",
                        "required": "true",
                        "description": "start of records to return",
                        "schema": {
                            "type": "integer",
                            "miniumum": 0
                        },
                        "example": 0
                    }
                    filter_params = {
                        "name": "filters",
                        "in": "query",
                        "required": False,
                        "description": "Filter data",
                        "schema": {
                            "type": "object",
                        }
                    }
                    properties = {}
                    spec["paths"]["/get_dist_data"]["get"]["parameters"].append(pagination_size_param)
                    spec["paths"]["/get_dist_data"]["get"]["parameters"].append(pagination_start_param)
                    for field in dam_resource.fields.all():
                        filter_param = {
                            "name": field.key,
                            "in": "query",
                            "required": False,
                            "description": "Filter data by" + field.key,
                            "schema": {
                                "type": field.format,
                            }
                        }
                        # properties[field.key] = {
                        #     "type": field.format
                        # }
                        spec["paths"]["/get_dist_data"]["get"]["parameters"].append(filter_param)
                    # filter_params["schema"]["properties"] = properties

                    # spec["paths"]["/get_dist_data"]["get"]["parameters"].append(filter_params)
        spec["info"]["title"] = resource_instance.title
        spec["info"]["description"] = resource_instance.description
        return {"data_token": data_token, "spec": spec}


class DataAccessModelRequestInput(graphene.InputObjectType):
    id = graphene.ID()
    description = graphene.String(required=True)
    access_model = graphene.ID(required=True)
    purpose = PurposeType(required=True)
    username = graphene.String(required=False)
    user_email = graphene.String(required=False)


class DataAccessModelRequestUpdateInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = DataAccessModelRequestStatusType()
    remark = graphene.String(required=False)


def create_dataset_access_model_request(
    access_model,
    description,
    purpose,
    username,
    status="REQUESTED",
    user_email=None,
    id=None,
):
    try:
        data_access_model_request_instance = DatasetAccessModelRequest.objects.filter(
            access_model=access_model, status=status, user=username
        ).order_by('-modified')
        print('--dam--req--', data_access_model_request_instance)
        if data_access_model_request_instance.exists():
            print('--dam--req--0--', data_access_model_request_instance[0])
            validity = get_data_access_model_request_validity(data_access_model_request_instance[0])
            if validity:
                print('validity--', validity)
                if timezone.now() <= validity:
                    print('Request is valid')
                    return data_access_model_request_instance[0]
                else:
                    pass
    except DatasetAccessModelRequest.DoesNotExist as e:
        pass
    if not id:
        data_access_model_request_instance = DatasetAccessModelRequest(
            access_model=access_model
        )
    else:
        data_access_model_request_instance = DatasetAccessModelRequest.objects.get(
            id=id
        )
    data_access_model_request_instance.status = status
    data_access_model_request_instance.purpose = purpose
    data_access_model_request_instance.description = description
    data_access_model_request_instance.user = username
    data_access_model_request_instance.user_email = user_email
    data_access_model_request_instance.save()
    access_model.save()
    return data_access_model_request_instance


class DataAccessModelRequestMutation(graphene.Mutation, Output):
    class Arguments:
        data_access_model_request = DataAccessModelRequestInput()

    data_access_model_request = graphene.Field(DataAccessModelRequestType)

    @staticmethod
    @validate_token_or_none
    def mutate(
        root,
        info,
        data_access_model_request: DataAccessModelRequestInput = None,
        username=None,
    ):
        id = None
        if data_access_model_request.id:
            id = data_access_model_request.id
        purpose = data_access_model_request.purpose
        description = data_access_model_request.description
        access_model = DatasetAccessModel.objects.get(
            id=data_access_model_request.access_model
        )
        if not username:
            username = data_access_model_request.username
        data_access_model_request_instance = create_dataset_access_model_request(
            access_model,
            description,
            purpose,
            username,
            user_email=data_access_model_request.user_email,
            id=id,
        )
        log_activity(
            target_obj=data_access_model_request_instance,
            ip=get_client_ip(info),
            username=username,
            target_group=data_access_model_request_instance.access_model.dataset.catalog.organization,
            verb="Created",
        )
        return DataAccessModelRequestMutation(
            data_access_model_request=data_access_model_request_instance
        )


class ApproveRejectDataAccessModelRequest(graphene.Mutation, Output):
    class Arguments:
        data_access_model_request = DataAccessModelRequestUpdateInput()

    data_access_model_request = graphene.Field(DataAccessModelRequestType)

    @staticmethod
    @validate_token_or_none
    def mutate(
        root,
        info,
        username,
        data_access_model_request: DataAccessModelRequestUpdateInput = None,
    ):
        try:
            data_access_model_request_instance = DatasetAccessModelRequest.objects.get(
                id=data_access_model_request.id
            )
        except DatasetAccessModelRequest.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {
                            "message": "Data Access Model with given id not found",
                            "code": "404",
                        }
                    ]
                },
            }
        data_access_model_request_instance.status = data_access_model_request.status
        if data_access_model_request.remark:
            data_access_model_request_instance.remark = data_access_model_request.remark
        data_access_model_request_instance.save()

        log_activity(
            target_obj=data_access_model_request_instance,
            ip=get_client_ip(info),
            username=username,
            target_group=data_access_model_request_instance.access_model.dataset.catalog.organization,
            verb=data_access_model_request_instance.status,
        )
        return ApproveRejectDataAccessModelRequest(
            data_access_model_request=data_access_model_request_instance
        )


class Mutation(graphene.ObjectType):
    data_access_model_request = DataAccessModelRequestMutation.Field()
    approve_reject_data_access_model_request = (
        ApproveRejectDataAccessModelRequest.Field()
    )