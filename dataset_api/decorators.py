import requests
import json

auth_url = 'https://auth.idp.civicdatalab.in/users/verify_token'


def validate_token(func):
    def inner(*args, **kwargs):
        user_token = args[1].context.META.get('HTTP_AUTHORIZATION')
        if user_token == "":
            print("Whoops! Empty user")
            return {"Success": False, "error": "Empty user", "error_description": "Empty user"}

        headers = {}
        body = json.dumps({"access_token": user_token.replace("Bearer ", "")})
        response = requests.request("POST", auth_url, data=body, headers=headers)
        response_json = json.loads(response.text)
        if not response_json['success']:
            return {"Success": False, "error": response_json['error'],
                    "error_description": response_json['error_description']}

        kwargs['username'] = response_json['preferred_username']
        return func(*args, **kwargs)

    return inner
