import requests
import json
from .models import Resource

verify_token_url = "https://auth.idp.civicdatalab.in/users/verify_user_token"
check_action_url = "https://auth.idp.civicdatalab.in/users/check_user_access"
create_user_url = "https://auth.idp.civicdatalab.in/users/create_user_role"
dataset_owner_url = "https://auth.idp.civicdatalab.in/users/update_dataset_owner"

def request_to_server(body, server_url):
    headers = {"Content-type": "application/json"}
    response = requests.request("POST", server_url, data=body, headers=headers)
    response_json = json.loads(response.text)
    return response_json


def validate_token(func):
    def inner(*args, **kwargs):
        user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
        if user_token == "":
            print("Whoops! Empty user")
            return {
                "success": False,
                "errors": {"user": [{"message": "Empty User", "code": "no_user"}]},
            }
        body = json.dumps({"access_token": user_token})
        response_json = request_to_server(body, verify_token_url)
        if not response_json["success"]:
            return {
                "success": False,
                "errors": {
                    "user": [
                        {
                            "message": response_json["error_description"],
                            "code": response_json["error"],
                        }
                    ]
                },
            }

        kwargs["username"] = response_json["preferred_username"]
        return func(*args, **kwargs)

    return inner


def auth_user_action_dataset(action):
    def accept_func(func):
        def inner(*args, **kwargs):
            for keys in kwargs:
                try:
                    dataset_id = kwargs[keys]["id"]
                    org_id = kwargs[keys]["organization"]
                except:
                    pass
                break
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            org_id = args[1].context.META.get("HTTP_ORGANIZATION")
            if user_token == "":
                print("Whoops! Empty user")
                return {
                    "success": False,
                    "errors": {"user": [{"message": "Empty User", "code": "no_user"}]},
                }
            body = json.dumps(
                {
                    "access_token": user_token,
                    "access_req": action,
                    "access_org_id": org_id,
                    "access_data_id": dataset_id,
                }
            )
            response_json = request_to_server(body, check_action_url)

            if not response_json["Success"]:
                return {
                    "success": False,
                    "errors": {
                        "user": [
                            {
                                "message": response_json["error_description"],
                                "code": response_json["error"],
                            }
                        ]
                    },
                }
            if response_json["access_allowed"]:
                return func(*args, **kwargs)
            else:
                return {
                    "success": False,
                    "errors": {"user": [{"message": "Access Denied.", "code": "401"}]},
                }

        return inner

    return accept_func


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
            
            user_token = args[1].context.META.get('HTTP_AUTHORIZATION')
            org_id = args[1].context.META.get('HTTP_ORGANIZATION')  # Required from Frontend.
            if user_token == "":
                print("Whoops! Empty user")
                return {
                    "success": False,
                    "errors": {"user": [{"message": "Empty User", "code": "no_user"}]},
                }
            body = json.dumps(
                {
                    "access_token": user_token,
                    "access_req": action,
                    "access_org_id": org_id,
                    "access_data_id": dataset_id,
                }
            )
            response_json = request_to_server(body, check_action_url)
            if not response_json["Success"]:
                return {
                    "success": False,
                    "errors": {
                        "user": [
                            {
                                "message": response_json["error_description"],
                                "code": response_json["error"],
                            }
                        ]
                    },
                }
            if response_json["access_allowed"]:
                return func(*args, **kwargs)
            else:
                return {
                    "success": False,
                    "errors": {"user": [{"message": "Access Denied.", "code": "401"}]},
                }

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
        response_json = request_to_server(body, create_user_url)
        print(response_json)
        return value
    return inner

def map_user_dataset(func):
    def inner(*args, **kwargs):
        value = func(*args, **kwargs)
        dataset_id = value.dataset.id
        user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
        body = json.dumps(
                    {
                        "access_token": user_token,
                        "dataset_id": dataset_id,
                        "action": "create",
                    }
                )
        response_json = request_to_server(body, dataset_owner_url)
        return value
    return inner

def check_license_role(func):
    def inner(*args, **kwargs):
        user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
        # user_token = args[1].context.headers.get("Authorization").replace("Bearer ", "")
        for keys in kwargs:
            try:
                org_id = kwargs[keys]["organization"]
            except:
                pass
            break
        body = json.dumps(
                {
                    "access_token": user_token,
                    "access_req": "create_license",
                    "access_org_id": org_id,
                    "access_data_id": "",
                }
            )
        response_json = request_to_server(body, check_action_url)
        if not response_json["Success"]:
            return {
                "success": False,
                "errors": {
                    "user": [
                        {
                            "message": response_json["error_description"],
                            "code": response_json["error"],
                        }
                    ]
                },
            }
        if response_json["access_allowed"]:
            kwargs["role"] = response_json["role"]
            return func(*args, **kwargs)
    return inner