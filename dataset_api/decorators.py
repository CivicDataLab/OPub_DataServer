import requests
import json

auth_url = 'https://auth.idp.civicdatalab.in/users/verify_token'


def validate_token(func):
    def inner(*args, **kwargs):
        user_token = args[1].context.META.get('HTTP_AUTHORIZATION')
        if user_token == "":
            print("Whoops! Empty user")
            return {"success": False, "errors": {"user": [{"message": "Empty User", "code": "no_user"}]}}

        headers = {}
        body = json.dumps({"access_token": user_token.replace("Bearer ", "")})
        response = requests.request("POST", auth_url, data=body, headers=headers)
        response_json = json.loads(response.text)
        if not response_json['success']:
            return {"success": False, "errors": {
                "user": [{"message": response_json['error_description'], "code": response_json['error']}]}}

        kwargs['username'] = response_json['preferred_username']
        return func(*args, **kwargs)

    return inner
