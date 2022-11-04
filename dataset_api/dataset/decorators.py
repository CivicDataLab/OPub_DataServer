import json
from graphql import GraphQLError
from dataset_api.decorators import request_to_server
from dataset_api.models import Dataset


def auth_user_action_dataset(action):
    def accept_func(func):
        def inner(*args, **kwargs):
            dataset_id = None
            for keys in kwargs:
                try:
                    dataset_id = kwargs[keys]["id"]
                    # org_id = kwargs[keys]["organization"]
                except:
                    pass
                break
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            org_id = args[1].context.META.get("HTTP_ORGANIZATION")
            if user_token == "":
                print("Whoops! Empty user")
                raise GraphQLError("Empty User")
            request_body = {
                "access_token": user_token,
                "access_req": action,
                "access_org_id": org_id,
                "access_data_id": "",
            }
            if dataset_id:
                request_body["access_data_id"] = dataset_id
            body = json.dumps(request_body)
            response_json = request_to_server(body, "check_user_access")

            if not response_json["Success"]:
                raise GraphQLError(response_json["error_description"])
            if response_json["access_allowed"]:
                return func(*args, **kwargs)
            else:
                raise GraphQLError("Access Denied")

        return inner

    return accept_func


def map_user_dataset(func):
    def inner(*args, **kwargs):
        value = func(*args, **kwargs)
        # TODO: IF org doesn't exist, mutation returns an error. Not handled here.
        # if not value["success"]:
        #         raise GraphQLError(value["errors"]["id"][0]["message"])
        dataset_id = value.dataset.id
        user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
        body = json.dumps(
            {
                "access_token": user_token,
                "dataset_id": dataset_id,
                "action": "create",
            }
        )
        response_json = request_to_server(body, "update_dataset_owner")
        print(response_json)
        if not response_json["Success"]:
            raise GraphQLError(response_json["comment"])
        else:
            return value

    return inner


def auth_query_dataset(action):
    def accept_func(func):
        def inner(*args, **kwargs):
            act, arg = action.split("||")
            user_token = args[1].context.META.get("HTTP_AUTHORIZATION")
            org_id = args[1].context.META.get("HTTP_ORGANIZATION", "")
            if arg == "title":
                dataset_id = Dataset.objects.get(
                    title__iexact=kwargs["dataset_title"]
                ).id
            elif arg == "slug":
                dataset_id = kwargs["dataset_slug"].split("_")[-1]
            else:
                dataset_id = kwargs["dataset_id"]
                # if not org_id:
                #     catalog_id = Dataset.objects.get(pk=dataset_id).catalog_id
                #     org_id = Catalog.objects.get(pk=catalog_id).organization_id
                #     print("org_id - ", org_id)
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
