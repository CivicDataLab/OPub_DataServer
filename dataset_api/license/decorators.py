import json

from graphql import GraphQLError

from dataset_api.decorators import request_to_server
from dataset_api.models.License import License

def check_license_role(action):
    def accept_func(func):
        def inner(*args, **kwargs):
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            org_id = args[1].context.META.get("HTTP_ORGANIZATION")
            body = json.dumps(
                {
                    "access_token": user_token,
                    "access_req": action,
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

        return inner
    return accept_func


def auth_query_license(action):
    def accept_func(func):
        def inner(*args, **kwargs):
            act, arg = action.split("||")
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            org_id = args[1].context.META.get("HTTP_ORGANIZATION", "")

            if arg == "license_id":
                org_id = License.objects.get(pk=kwargs[arg]).created_organization_id
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
