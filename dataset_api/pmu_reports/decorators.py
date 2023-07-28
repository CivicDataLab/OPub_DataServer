from django.conf import settings
import json
import requests
from graphql import GraphQLError

from dataset_api.models import Resource, DatasetReviewRequest, Organization
from dataset_api.utils import get_child_orgs

auth_url = settings.AUTH_URL


def request_to_server(body, server_url):
    bd = json.loads(body)
    headers = {"Content-type": "application/json", "access-token": bd.get("access_token")}
    bd.pop("access_token", None)
    body = json.dumps(bd)
    response = requests.request(
        "POST", auth_url + server_url, data=body, headers=headers
    )
    response_json = json.loads(response.text)
    return response_json


def auth_get_all_users(role):
    def accept_func(func):
        def inner(*args, **kwargs):
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            body = json.dumps(
                {
                    "access_token": user_token,
                    "org_id":"",
                    "user_type":role
                }
            )
            print ('------------getuserbody', body)
            response_json = request_to_server(body, "get_users")
            if not response_json["Success"]:
                raise GraphQLError(response_json["error_description"])
            if response_json["Success"]:
                kwargs["users"] = response_json["users"]
                return func(*args, **kwargs)
            else:
                raise GraphQLError("Access Denied")

        return inner

    return accept_func