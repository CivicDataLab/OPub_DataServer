import json

from graphql import GraphQLError

from dataset_api.decorators import request_to_server
from dataset_api.models.DataAccessModel import DataAccessModel
from dataset_api.models.DatasetAccessModelRequest import DatasetAccessModelRequest
from dataset_api.models.DatasetAccessModel import DatasetAccessModel


def auth_query_dam_request(action):
    def accept_func(func):
        def inner(*args, **kwargs):
            act, arg = action.split("||")
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            org_id = args[1].context.META.get("HTTP_ORGANIZATION", "")

            if arg == "request_id":
                dam_request_id = kwargs["data_access_model_request_id"]

                acess_model_id = DatasetAccessModelRequest.objects.get(
                    pk=dam_request_id
                ).access_model_id

                dam_id = DatasetAccessModel.objects.get(
                    pk=acess_model_id
                ).data_access_model_id

                org_id = org_id = DataAccessModel.objects.get(pk=dam_id).organization_id
            if user_token == "":
                print("Whoops! Empty user")
                raise GraphQLError("Empty User")
            body = json.dumps(
                {
                    "access_token": user_token,
                    "access_req": act,
                    "access_org_id": org_id,
                    "access_data_id": "",
                }
            )
            response_json = request_to_server(body, "check_user_access")

            if not response_json["Success"]:
                raise GraphQLError(response_json["error_description"])
            if response_json["access_allowed"]:
                kwargs["role"] = response_json["role"]
                return func(*args, **kwargs)
            else:
                raise GraphQLError("Access Denied.")

        return inner

    return accept_func
