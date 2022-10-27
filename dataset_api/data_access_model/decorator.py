import json

from graphql import GraphQLError

from ..decorators import request_to_server
from ..models.DataAccessModel import DataAccessModel

check_action_url = "https://auth.idp.civicdatalab.in/users/check_user_access"


def auth_user_action_dam(action):
    def accept_func(func):
        def inner(*args, **kwargs):
            org_id = args[1].context.META.get("HTTP_ORGANIZATION")
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            if user_token == "":
                raise GraphQLError("Empty User")

            body = json.dumps(
                {
                    "access_token": user_token,
                    "access_req": action,
                    "access_org_id": org_id,
                    "access_data_id": "",
                }
            )
            response_json = request_to_server(body, check_action_url)
            if not response_json["Success"]:
                raise GraphQLError(response_json["error_description"])
            if response_json["access_allowed"]:
                return func(*args, **kwargs)
            else:
                raise GraphQLError("Access Denied")

        return inner

    return accept_func
