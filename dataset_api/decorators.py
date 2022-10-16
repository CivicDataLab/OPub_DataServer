import requests
import json

auth_url = "https://auth.idp.civicdatalab.in/users/verify_user_token"
check_action_url = "https://auth.idp.civicdatalab.in/users/check_user_access"


def request_to_server(body, headers):
    response = requests.request("POST", check_action_url, data=body, headers=headers)
    response_json = json.loads(response.text)
    return response_json


def validate_token(func):
    def inner(*args, **kwargs):
        print(args)
        user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
        if user_token == "":
            print("Whoops! Empty user")
            return {
                "success": False,
                "errors": {"user": [{"message": "Empty User", "code": "no_user"}]},
            }

        headers = {}
        body = json.dumps({"access_token": user_token})
        response_json = request_to_server(body, headers)
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
            org_id = args[1].context.META.get("Organization")
            if user_token == "":
                print("Whoops! Empty user")
                return {
                    "success": False,
                    "errors": {"user": [{"message": "Empty User", "code": "no_user"}]},
                }

            headers = {"Content-type": "application/json"}
            print(action)
            body = json.dumps(
                {
                    "access_token": user_token,
                    "access_req": action,
                    "access_org_id": org_id,
                    "access_data_id": dataset_id,
                }
            )
            response_json = request_to_server(body, headers)

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
                    pass
                break
            
            user_token = args[1].context.META.get('HTTP_AUTHORIZATION')
            org_id = args[1].context.META.get('Organization') # Required from Frontend.
            if user_token == "":
                print("Whoops! Empty user")
                return {
                    "success": False,
                    "errors": {"user": [{"message": "Empty User", "code": "no_user"}]},
                }

            headers = {"Content-type": "application/json"}
            body = json.dumps(
                {
                    "access_token": user_token,
                    "access_req": action,
                    "access_org_id": org_id,
                    "access_data_id": dataset_id,
                }
            )
            response_json = request_to_server(body, headers)
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
