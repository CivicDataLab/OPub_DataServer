import json

from graphql import GraphQLError

from dataset_api.decorators import request_to_server


def auth_action_dam_resource(action):
    def accept_func(func):
        def inner(*args, **kwargs):
            for keys in kwargs:
                try:
                    dataset_id = kwargs[keys]["dataset_id"]
                except:
                    pass
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            org_id = args[1].context.META.get("HTTP_ORGANIZATION")
            if user_token == "":
                raise GraphQLError("Empty User")

            body = json.dumps(
                {
                    "access_token": user_token,
                    "access_req": action,
                    "access_org_id": org_id,
                    "access_data_id": dataset_id,
                }
            )
            response_json = request_to_server(body, "check_user_access")
            if not response_json["Success"]:
                raise GraphQLError(response_json["error_description"])
            if response_json["access_allowed"]:
                return func(*args, **kwargs)
            else:
                raise GraphQLError("Access Denied")

        return inner

    return accept_func
