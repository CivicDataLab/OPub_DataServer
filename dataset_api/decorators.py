import requests
import json

auth_url = 'https://auth.idp.civicdatalab.in/users/verify_token'


def validate_token(func):
    def inner(*args, **kwargs):
        user_token = args[1].context.META.get('HTTP_AUTHORIZATION')
        # user_token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJCdXFLSkxZRUo0azdxc2M3RHItRjRZYlY0YWVsTzNMUnEtaDZWR3ZZR0ZNIn0.eyJleHAiOjE2NjQyNjA5ODYsImlhdCI6MTY2NDI2MDY4NiwianRpIjoiMGIxODM0ZjEtNTcwNi00MmYyLThmMjEtNTY0OTFmYzg2NGFjIiwiaXNzIjoiaHR0cHM6Ly9rYy5uZHAuY2l2aWNkYXRhbGFiLmluL2F1dGgvcmVhbG1zL2V4dGVybmFsIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6ImE3M2EyZThlLWQ3NjktNDA5OC1iNzAxLWFmMjAzN2M5OGY5ZCIsInR5cCI6IkJlYXJlciIsImF6cCI6Im9wdWItaWRwIiwic2Vzc2lvbl9zdGF0ZSI6ImZjODA5ZGFkLWUwNzAtNGJkYy04NzZjLWQxYzQ4NDg5YmU5MCIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiKiJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJkZWZhdWx0LXJvbGVzLWV4dGVybmFsIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6InByb2ZpbGUgZW1haWwiLCJzaWQiOiJmYzgwOWRhZC1lMDcwLTRiZGMtODc2Yy1kMWM0ODQ4OWJlOTAiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwibmFtZSI6IkFiaGluYXYiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJhYmhpbmF2IiwiZ2l2ZW5fbmFtZSI6IkFiaGluYXYiLCJlbWFpbCI6ImFiaGluYXZAY2l2aWNkYXRhbGFiLmluIn0.kZSTW-uSZtg4OPM3OTqUtGjCuNtdDItd0wpoNvnoBfOWs4EkgXFh-ro-Dyt6_xn9joMw4drIYRVZl1P9uqFdgXdOUPi6yEBoxTgr5RNxWWPW_rEXiq2owf9fN8siluUDun91CRlxL8dBzQgp5hOG5q0Y0A7_D_uhdBAhwq601H5lVzdQ6fVK01R1kNElsVctmaXMmpkKgZ9tKZXmUxjxPI3mZtdataKQaI4-kmAgmGrtFvRSjlV6QxhobnLyJK9trVetszIi0PqWwQYVVeRCS83nQQp5AJp5sP0nu8tyA2CX9ENDhdFwsc-zUqxOU1axFcgA-K3-7yuAPEqcqB6Crw"
        print("checking token ", user_token, " validity")
        if user_token == "":
            print("Whoops! Empty user")
            return {"Success": False, "error": "Empty user", "error_description": "Empty user"}

        headers = {}
        body = json.dumps({"access_token": user_token.replace("Bearer ", "")})
        response = requests.request("POST", auth_url, data=body, headers=headers)
        response_json = json.loads(response.text)
        print(response_json)
        if not response_json['success']:
            return {"Success": False, "error": response_json['error'],
                    "error_description": response_json['error_description']}

        kwargs['username'] = response_json['preferred_username']
        return func(*args, **kwargs)

    return inner
