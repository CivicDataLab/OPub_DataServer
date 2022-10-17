import json
from ..decorators import request_to_server
from .models import DataAccessModel

check_action_url = "https://auth.idp.civicdatalab.in/users/check_user_access"


def auth_user_action_dam(action):
    def accept_func(func):
        def inner(*args, **kwargs):
            for keys in kwargs:
                try:
                    org_id = kwargs[keys]["organization"]
                except:
                    dam_id = kwargs[keys]["id"]
                    org_id = DataAccessModel.objects.get(id=dam_id).organization.id
                break
            
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
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
                return func(*args, **kwargs)
            else:
                return {
                    "success": False,
                    "errors": {"user": [{"message": "Access Denied.", "code": "401"}]},
                }

        return inner

    return accept_func