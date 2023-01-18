from django.conf import settings
import json
import requests
from graphql import GraphQLError

from .models import Resource, OrganizationCreateRequest, DatasetReviewRequest

auth_url = settings.AUTH_URL


def request_to_server(body, server_url):
    bd = json.loads(body)
    headers = {"Content-type": "application/json", "access-token": bd.get("access_token")}
    bd.pop("access_token", None)
    body = bd
    response = requests.request(
        "POST", auth_url + server_url, data=body, headers=headers
    )
    response_json = json.loads(response.text)
    return response_json


def validate_token(func):
    def inner(*args, **kwargs):
        user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
        if user_token == "":
            print("Whoops! Empty user")
            raise GraphQLError("Empty User")
        body = json.dumps({"access_token": user_token})
        response_json = request_to_server(body, "verify_user_token")
        if not response_json["success"]:
            raise GraphQLError(response_json["error_description"])

        kwargs["username"] = response_json["preferred_username"]
        return func(*args, **kwargs)

    return inner


def validate_token_or_none(func):
    def inner(*args, **kwargs):
        username = None
        user_token = ""
        if hasattr(args[0], "META"):
            user_token = args[0].META.get("HTTP_AUTHORIZATION", "")
        else:
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION", "")
        if user_token == "":
            print("Whoops! Empty user")
        else:
            body = json.dumps({"access_token": user_token})
            response_json = request_to_server(body, "verify_user_token")
            username = response_json["preferred_username"]
            if not response_json["success"]:
                raise GraphQLError(response_json["error_description"])

        kwargs["username"] = username
        return func(*args, **kwargs)

    return inner


def auth_user_action_resource(action):
    def accept_func(func):
        def inner(*args, **kwargs):
            for keys in kwargs:
                try:
                    dataset_id = kwargs[keys]["dataset"]
                except:
                    resource_id = kwargs[keys]["id"]
                    dataset_id = Resource.objects.get(id=resource_id).dataset.id
                break

            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            org_id = args[1].context.META.get("HTTP_ORGANIZATION")
            if user_token == "":
                print("Whoops! Empty user")
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
                raise GraphQLError("Access Denied.")

        return inner

    return accept_func


def auth_query_resource(action):
    def accept_func(func):
        def inner(*args, **kwargs):
            act, arg = action.split("||")
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            org_id = args[1].context.META.get("HTTP_ORGANIZATION", "")
            if arg == "resource":
                dataset_id = Resource.objects.get(pk=kwargs["resource_id"]).dataset_id
                # if not org_id:
                #     catalog_id = Dataset.objects.get(pk=dataset_id).catalog_id
                #     org_id = Catalog.objects.get(pk=catalog_id).organization_id
            # IF not org_id -- Find one from dataset.
            else:
                dataset_id = kwargs["dataset_id"]
            if user_token == "":
                print("Whoops! Empty user")
                raise GraphQLError("Empty User")
            body = json.dumps(
                {
                    "access_token": user_token,
                    "access_req": act,
                    "access_org_id": org_id,
                    "access_data_id": dataset_id,
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


def auth_user_by_org(action):
    def accept_func(func):
        def inner(*args, **kwargs):
            org_id = args[1].context.META.get("HTTP_ORGANIZATION", "")
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            dataset_id = ""
            try:
                review_id = kwargs['moderation_request']['ids'][0] # Only for address moderation request mutation.
                dataset_id = DatasetReviewRequest.objects.get(pk=review_id).dataset_id
            except Exception as e:
                pass
            body = json.dumps(
                {
                    "access_token": user_token,
                    "access_org_id": org_id,
                    "access_data_id": dataset_id,
                    "access_req": action,
                }
            )
            response_json = request_to_server(body, "check_user_access")
            if not response_json["Success"]:
                raise GraphQLError(response_json["error_description"])
            if response_json["access_allowed"]:
                if action == "query" or action == "list_review_request":
                    kwargs["role"] = response_json["role"]
                return func(*args, **kwargs)
            else:
                raise GraphQLError("Access Denied")

        return inner

    return accept_func


def create_user_org(func):
    def inner(*args, **kwargs):
        value = func(*args, **kwargs)
        org_id = value.organization.id
        org_title = value.organization.title
        user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
        body = json.dumps(
            {
                "access_token": user_token,
                "org_id": org_id,
                "org_title": org_title,
            }
        )
        response_json = request_to_server(body, "create_user_role")
        if response_json["Success"]:
            return value

    return inner


def modify_org_status(func):
    def inner(*args, **kwargs):
        value = func(*args, **kwargs)
        org_list = [value.organization.id]
        org_status = value.organization.status.lower()

        user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
        body = json.dumps(
            {
                "access_token": user_token,
                "org_list": org_list,
                "org_status": org_status,
            }
        )
        response_json_approve = request_to_server(body, "modify_org_status")

        if value.rejected:
            rejected_list = value.rejected
            body = json.dumps(
                {
                    "access_token": user_token,
                    "org_list": rejected_list,
                    "org_status": "rejected",
                }
            )
            response_json_rejected = request_to_server(body, "modify_org_status")
        if response_json_approve["Success"]:
            return value
        else:
            raise GraphQLError(response_json_approve["error_description"])

    return inner


def auth_request_org(func):
    def inner(*args, **kwargs):
        org_id = args[0].id
        user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
        body = json.dumps(
            {
                "access_token": user_token,
                "org_id": org_id,
            }
        )
        response_json = request_to_server(body, "get_org_requestor")
        if response_json["Success"]:
            kwargs["username"] = response_json["username"]
            return func(*args, **kwargs)
        else:
            raise GraphQLError(response_json["error_description"])

    return inner


def update_user_org(func):
    def inner(*args, **kwargs):
        value = func(*args, **kwargs)
        if value.organization_request.status == "APPROVED":
            org_title = value.organization_request.organization.title
            tgt_user = value.organization_request.user
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            org_id = args[1].context.META.get("HTTP_ORGANIZATION")
            body = json.dumps(
                {
                    "access_token": user_token,
                    "org_id": org_id,
                    "org_title": org_title,
                    "tgt_user_name": tgt_user,
                    "role_name": "DP",
                    "action": "update",
                }
            )
            response_json = request_to_server(body, "update_user_role")
            if response_json["Success"]:
                return value
        else:
            return value

    return inner


def get_user_org(func):
    def inner(*args, **kwargs):
        user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
        body = json.dumps(
            {
                "access_token": user_token,
            }
        )
        response_json = request_to_server(body, "get_user_orgs")
        if response_json["Success"]:
            kwargs["org_ids"] = response_json["orgs"]
            return func(*args, **kwargs)

    return inner
