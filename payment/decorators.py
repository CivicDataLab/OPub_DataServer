import json

from django.http import HttpResponseForbidden

from dataset_api.decorators import request_to_server


def rest_validate_token(func):
    def inner(*args, **kwargs):
        user_token = args[0].META.get("HTTP_AUTHORIZATION", "")
        if user_token == "":
            raise HttpResponseForbidden("Empty User")
        body = json.dumps({"access_token": user_token})
        response_json = request_to_server(body, "verify_user_token")
        if not response_json["success"]:
            raise HttpResponseForbidden(response_json["error_description"])

        kwargs["username"] = response_json["preferred_username"]
        return func(*args, **kwargs)

    return inner
