import json
import mimetypes
import os

import jwt
import pandas as pd
import requests
from django.conf import settings
from django.http import HttpResponse, FileResponse, HttpResponseForbidden
from elasticsearch import Elasticsearch
from pandas import DataFrame
from ratelimit import core

from dataset_api.data_request.token_handler import (
    create_access_jwt_token,
    create_data_jwt_token,
)
from dataset_api.decorators import validate_token_or_none
from dataset_api.models.DataRequest import DataRequest
from dataset_api.search import index_data
from dataset_api.utils import idp_make_cache_key
from .decorators import dam_request_validity

# Overwriting ratelimit's cache key function.
from .schema import initiate_dam_request
from ..constants import FORMAT_MAPPING
from ..models import DatasetAccessModelResource, DatasetAccessModelRequest

# from graphql import GraphQLError

core._make_cache_key = idp_make_cache_key

es_client = Elasticsearch(settings.ELASTICSEARCH)


@dam_request_validity
@validate_token_or_none
def download(request, data_request_id, username=None):
    target_format = request.GET.get("format", None)

    data_request_instance = DataRequest.objects.get(pk=str(data_request_id))
    dam = (
        data_request_instance.dataset_access_model_request.access_model.data_access_model
    )
    if dam.type == "OPEN":
        return get_request_file(username, data_request_id, target_format)
    else:
        # Get the quota count.
        get_quota_count = core.get_usage(
            request,
            group="quota",
            key="dataset_api.ratelimits.user_key",
            rate="dataset_api.ratelimits.quota_per_user",
            increment=False,
        )
        # If count < limit -- don't increment the counter.
        if get_quota_count["count"] < get_quota_count["limit"]:
            # Check for rate.
            get_rate_count = core.get_usage(
                request,
                group="rate",
                key="dataset_api.ratelimits.user_key",
                rate="dataset_api.ratelimits.rate_per_user",
                increment=False,
            )
            # Increment rate and quota count.
            if get_rate_count["count"] < get_rate_count["limit"]:
                get_file = get_request_file(username, data_request_id, target_format)
                get_rate_count = core.get_usage(
                    request,
                    group="rate",
                    key="dataset_api.ratelimits.user_key",
                    rate="dataset_api.ratelimits.rate_per_user",
                    increment=True,
                )
                get_quota_count = core.get_usage(
                    request,
                    group="quota",
                    key="dataset_api.ratelimits.user_key",
                    rate="dataset_api.ratelimits.quota_per_user",
                    increment=True,
                )
                return get_file
            else:
                return HttpResponseForbidden(content="Rate Limit Exceeded.")
        else:
            return HttpResponseForbidden(content="Quota Limit Exceeded.")


def update_download_count(username, data_request: DataRequest):
    # update download count in dataset
    dataset = data_request.dataset_access_model_request.access_model.dataset
    count = dataset.download_count
    dataset.download_count = count + 1
    dataset.save()
    index_data(dataset)
    # update download count in user datasetreq table
    headers = {}
    auth_url = settings.AUTH_URL + "update_datasetreq"
    response = requests.post(
        auth_url,
        data=json.dumps(
            {
                "username": username,
                "data_request_id": str(data_request.id),
                "dataset_access_model_request_id": data_request.dataset_access_model_request.id,
                "dataset_access_model_id": data_request.dataset_access_model_request.access_model.id,
                "dataset_id": dataset.id,
            }
        ),
        headers=headers,
    )
    response_json = json.loads(response.text)
    if not response_json["Success"]:
        return {
            "Success": False,
            "error": response_json["error"],
            "error_description": response_json["error_description"],
        }

    return {"Success": True, "message": "Dataset download count updated successfully"}


class FormatConverter:
    @classmethod
    def convert_csv_to_json(cls, csv_file_path, src_mime_type, return_type="data"):
        csv_file = pd.DataFrame(
            pd.read_csv(csv_file_path, sep=",", header=0, index_col=False, )
        )
        if return_type == "file":
            csv_file.to_json(
                "file.json",
                orient="records",
                date_format="epoch",
                double_precision=10,
                force_ascii=True,
                date_unit="ms",
                default_handler=None,
            )
            response = FileResponse(
                open("file.json", "rb"), content_type="application/x-download"
            )
            file_name = (
                    ".".join(os.path.basename(csv_file_path).split(".")[:-1]) + ".json"
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.json")
            return response
        elif return_type == "data":
            response = HttpResponse(csv_file.to_dict(), content_type="application/json")
            return response

    @classmethod
    def convert_csv_to_xml(cls, csv_file_path, src_mime_type, return_type="data"):
        csv_file = pd.DataFrame(
            pd.read_csv(csv_file_path, sep=",", header=0, index_col=False)
        )
        if return_type == "file":
            csv_file.to_xml("file.xml")
            response = FileResponse(
                open("file.xml", "rb"), content_type="application/x-download"
            )
            file_name = (
                    ".".join(os.path.basename(csv_file_path).split(".")[:-1]) + ".xml"
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.xml")
            return response
        elif return_type == "data":
            response = HttpResponse(csv_file.to_xml(), content_type="application/xml")
            return response

    @classmethod
    def convert_csv_to_csv(cls, csv_file_path, src_mime_type, return_type="data"):
        csv_file = pd.DataFrame(
            pd.read_csv(csv_file_path, sep=",", header=0, index_col=False)
        )
        if return_type == "file":
            csv_file.to_csv("file.csv", index=False)
            response = FileResponse(
                open("file.csv", "rb"), content_type="application/x-download"
            )
            file_name = (
                    ".".join(os.path.basename(csv_file_path).split(".")[:-1]) + ".csv"
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.csv")
            return response
        elif return_type == "data":
            csv_file = pd.DataFrame(
                pd.read_csv(csv_file_path, sep=",", header=0, index_col=False)
            )
            response = HttpResponse(csv_file.to_string(), content_type="text/csv")
            return response

    @classmethod
    def convert_json_to_json(cls, json_file_path, src_mime_type, return_type="data"):
        if return_type == "file":
            response = FileResponse(
                open(json_file_path, "rb"), content_type=src_mime_type
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                os.path.basename(json_file_path)
            )
        elif return_type == "data":
            json_file = pd.DataFrame(pd.read_json(json_file_path, orient="index"))
            response = HttpResponse(json_file.to_string(), content_type="text/csv")
        return response

    @classmethod
    def convert_json_to_csv(cls, json_file_path, src_mime_type, return_type="data"):
        final_json = cls.process_json_data(json_file_path)

        if return_type == "file":
            final_json.to_csv("file.csv", index=False)
            response = FileResponse(
                open("file.csv", "rb"), content_type="application/x-download"
            )
            file_name = (
                    ".".join(os.path.basename(json_file_path).split(".")[:-1]) + ".csv"
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.csv")
            return response
        elif return_type == "data":
            response = HttpResponse(final_json.to_csv(), content_type="text/csv")
            return response

    @classmethod
    def process_json_data(cls, json_file_path):
        with open(json_file_path, "r") as fp:
            data = json.load(fp)

            def get_paths(d, current=[], list_items=[]):
                if isinstance(d, str):
                    return
                for a, b in d.items():
                    yield current + [a], list_items
                    if isinstance(b, dict):
                        yield from get_paths(b, current + [a], list_items)
                    elif isinstance(b, list):
                        list_items = list_items + [current + [a]]
                        for i in b:
                            yield from get_paths(i, current + [a], list_items)

            temp = data
            if isinstance(data, list):
                temp = data[0]
            final_result = list(get_paths(temp))
            list_cols = final_result[-1][1]
            all_coll = [a[0] for a in final_result]
            all_coll = [a for i, a in enumerate(all_coll) if a not in all_coll[:i]]
            for a in list_cols:
                all_coll = [
                    each
                    for each in all_coll
                    if not ".".join(each).startswith(".".join(a))
                ]
            df = data
            for col_path in list_cols:
                try:
                    df = pd.json_normalize(
                        df, record_path=col_path, meta=all_coll
                    ).to_dict(orient="records")
                except KeyError as e:
                    pass
            final_json = pd.DataFrame(df)
        return final_json

    @classmethod
    def convert_json_to_xml(cls, json_file_path, src_mime_type, return_type="data"):
        final_json = cls.process_json_data(json_file_path)
        if return_type == "file":
            final_json.to_xml("file.xml")
            response = FileResponse(
                open("file.xml", "rb"), content_type="application/x-download"
            )
            file_name = (
                    ".".join(os.path.basename(json_file_path).split(".")[:-1]) + ".xml"
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.xml")
            return response
        elif return_type == "data":
            response = HttpResponse(final_json.to_xml(), content_type="application/xml")
            return response


class FormatExporter:
    @classmethod
    def convert_df_to_csv(cls, df, return_type="data"):
        if return_type == "file":
            df.to_csv("file.csv", index=False)
            response = FileResponse(
                open("file.csv", "rb"), content_type="application/x-download"
            )
            file_name = "output.csv"
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.csv")
            return response
        elif return_type == "data":
            response = HttpResponse(df.to_csv(index=False), content_type="text/csv")
            return response

    @classmethod
    def convert_df_to_json(cls, df: DataFrame, return_type="data"):
        if return_type == "file":
            df.to_json(
                "file.json",
                orient="records",
                date_format="epoch",
                double_precision=10,
                force_ascii=True,
                date_unit="ms",
                default_handler=None,
            )
            response = FileResponse(
                open("file.json", "rb"), content_type="application/x-download"
            )
            file_name = "output.json"
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.json")
            return response
        elif return_type == "data":
            json_result = df.to_json(
                orient="records",
                date_format="epoch",
                double_precision=10,
                force_ascii=True,
                date_unit="ms",
                default_handler=None,
            )
            response = HttpResponse(json_result, content_type="application/json")
            return response

    @classmethod
    def convert_df_to_xml(cls, df, return_type="data"):
        if return_type == "file":
            df.to_xml("file.xml")
            response = FileResponse(
                open("file.xml", "rb"), content_type="application/x-download"
            )
            file_name = "output.xml"
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.xml")
            return response
        elif return_type == "data":
            response = HttpResponse(df.to_xml(), content_type="application/xml")
            return response


def refresh_token(request):
    token = request.GET.get("token")
    try:
        token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return HttpResponse("Authentication failed", content_type="text/plain")
    except IndexError:
        return HttpResponse("Token prefix missing", content_type="text/plain")
    if token_payload:
        data_request_id = token_payload.get("data_request")
        username = token_payload.get("username")
        data_request_instance = DataRequest.objects.get(pk=data_request_id)
        access_token = create_access_jwt_token(data_request_instance, username)
        return HttpResponse(access_token, content_type="text/plain")
    return HttpResponse(
        "Something went wrong request again!!", content_type="text/plain"
    )


def refresh_data_token(request):
    token = request.GET.get("token")
    try:
        token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return HttpResponse("Authentication failed", content_type="text/plain")
    except IndexError:
        return HttpResponse("Token prefix missing", content_type="text/plain")
    if token_payload:
        data_resource_id = token_payload.get("dam_resource")
        data_request_id = token_payload.get("dam_request")
        username = token_payload.get("username")
        data_resource_instance = DatasetAccessModelResource.objects.get(
            pk=data_resource_id
        )
        dam_request_instance = DatasetAccessModelRequest.objects.get(pk=data_request_id)
        access_token = create_data_jwt_token(
            data_resource_instance, dam_request_instance, username
        )
        return HttpResponse(access_token, content_type="text/plain")
    return HttpResponse(
        "Something went wrong request again!!", content_type="text/plain"
    )


# def get_resource(request):
#     token = request.GET.get("token")
#     format = request.GET.get("format")
#     size = request.GET.get("size")
#     if not size:
#         size = 5
#     paginate_from = request.GET.get("from", 0)
#     try:
#         token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#     except jwt.ExpiredSignatureError:
#         return HttpResponse("Authentication failed", content_type="text/plain")
#     except IndexError:
#         return HttpResponse("Token prefix missing", content_type="text/plain")
#     username = token_payload.get("username")
#     if token_payload:
#         data_request_id = token_payload.get("data_request")
#         data_request = DataRequest.objects.get(pk=data_request_id)
#         dam = data_request.dataset_access_model_request.access_model.data_access_model
#         if data_request.status != "FETCHED":
#             return HttpResponse(
#                 "Request in progress. Please try again in some time",
#                 content_type="text/plain",
#             )
#         if dam.type != "OPEN":
#             # Get the quota count.
#             print("Checking Limits!!")
#             get_quota_count = core.get_usage(
#                 request,
#                 group="quota",
#                 key="dataset_api.ratelimits.user_key",
#                 rate="dataset_api.ratelimits.quota_per_user",
#                 increment=False,
#             )
#             # If count < limit -- don't increment the counter.
#             if get_quota_count["count"] < get_quota_count["limit"]:
#                 # Check for rate.
#                 get_rate_count = core.get_usage(
#                     request,
#                     group="rate",
#                     key="dataset_api.ratelimits.user_key",
#                     rate="dataset_api.ratelimits.rate_per_user",
#                     increment=False,
#                 )
#                 # Increment rate and quota count.
#                 if get_rate_count["count"] < get_rate_count["limit"]:
#                     get_file = get_request_file(
#                         token_payload.get("username"),
#                         data_request_id,
#                         format,
#                         "data",
#                         size,
#                         paginate_from,
#                     )
#                     get_rate_count = core.get_usage(
#                         request,
#                         group="rate",
#                         key="dataset_api.ratelimits.user_key",
#                         rate="dataset_api.ratelimits.rate_per_user",
#                         increment=True,
#                     )
#                     get_quota_count = core.get_usage(
#                         request,
#                         group="quota",
#                         key="dataset_api.ratelimits.user_key",
#                         rate="dataset_api.ratelimits.quota_per_user",
#                         increment=True,
#                     )
#                     return get_file
#                 else:
#                     return HttpResponseForbidden(content="Rate Limit Exceeded.")
#             else:
#                 return HttpResponseForbidden(content="Quota Limit Exceeded.")
#         else:
#             return get_request_file(
#                 token_payload.get("username"),
#                 data_request_id,
#                 format,
#                 "data",
#                 size,
#                 paginate_from,
#             )

#     return HttpResponse(json.dumps(token_payload), content_type="application/json")


# # def get_resource_file(request):
# def get_resource_file(request, data_request, token, apidetails):
#     # token = request.GET.get("token")
#     # format = apidetails.response_type #request.GET.get("format")
#     # size = request.GET.get("size")
#     # if not size:
#     #     size = 5
#     # paginate_from = request.GET.get("from", 0)
#     format = apidetails.response_type
#     print("---------a0", format)
#     size = 10000
#     paginate_from = 0
#     try:
#         token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#     except jwt.ExpiredSignatureError:
#         return HttpResponse("Authentication failed", content_type="text/plain")
#     except IndexError:
#         return HttpResponse("Token prefix missing", content_type="text/plain")
#     username = token_payload.get("username")
#     if token_payload:
#         # data_request_id = token_payload.get("data_request")
#         data_request_id = data_request.id
#         # data_request = DataRequest.objects.get(pk=data_request_id)
#         data_request.refresh_from_db()
#         dam = data_request.dataset_access_model_request.access_model.data_access_model
#         if data_request.status != "FETCHED":
#             return HttpResponse(
#                 "Request in progress. Please try again in some time",
#                 content_type="text/plain",
#             )
#         if dam.type != "OPEN":
#             # Get the quota count.
#             print("Checking Limits!!")
#             get_quota_count = core.get_usage(
#                 request,
#                 group="quota||" + str(data_request_id),
#                 key="dataset_api.ratelimits.user_key",
#                 rate="dataset_api.ratelimits.quota_per_user",
#                 increment=False,
#             )
#             # If count < limit -- don't increment the counter.
#             if get_quota_count["count"] < get_quota_count["limit"]:
#                 # Check for rate.
#                 get_rate_count = core.get_usage(
#                     request,
#                     group="rate||" + str(data_request_id),
#                     key="dataset_api.ratelimits.user_key",
#                     rate="dataset_api.ratelimits.rate_per_user",
#                     increment=False,
#                 )
#                 # Increment rate and quota count.
#                 if get_rate_count["count"] < get_rate_count["limit"]:
#                     get_file = get_request_file(
#                         token_payload.get("username"),
#                         data_request_id,
#                         format,
#                         "data",
#                         size,
#                         paginate_from,
#                     )
#                     get_rate_count = core.get_usage(
#                         request,
#                         group="rate||" + str(data_request_id),
#                         key="dataset_api.ratelimits.user_key",
#                         rate="dataset_api.ratelimits.rate_per_user",
#                         increment=True,
#                     )
#                     get_quota_count = core.get_usage(
#                         request,
#                         group="quota||" + str(data_request_id),
#                         key="dataset_api.ratelimits.user_key",
#                         rate="dataset_api.ratelimits.quota_per_user",
#                         increment=True,
#                     )
#                     return get_file
#                 else:
#                     return HttpResponseForbidden(content="Rate Limit Exceeded.")
#             else:
#                 return HttpResponseForbidden(content="Quota Limit Exceeded.")
#         else:
#             return get_request_file(
#                 token_payload.get("username"),
#                 data_request_id,
#                 format,
#                 "data",
#                 size,
#                 paginate_from,
#             )

#     return HttpResponse(json.dumps(token_payload), content_type="application/json")


# def update_data(request):
#     token = request.GET.get("token")
#     try:
#         token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#     except jwt.ExpiredSignatureError:
#         return HttpResponse("Authentication failed", content_type="text/plain")
#     except IndexError:
#         return HttpResponse("Token prefix missing", content_type="text/plain")
#     if token_payload:
#         dam_resource_id = token_payload.get("dam_resource")
#         data_request_id = token_payload.get("dam_request")
#         data_resource = DatasetAccessModelResource.objects.get(id=dam_resource_id)
#         dam_request_instance = DatasetAccessModelRequest.objects.get(pk=data_request_id)
#         username = token_payload.get("username")
#         apidetails = data_resource.resource.apidetails
#         parameters = {}
#         default_parameters = []
#         if apidetails:
#             default_parameters = apidetails.apiparameter_set.all()
#         for param in default_parameters:
#             if param.key in request.GET:
#                 parameters[param.key] = request.GET.get(param.key)
#             else:
#                 parameters[param.key] = param.default

#         data_request_id_1 = initiate_dam_request(
#             dam_request_instance, data_resource.resource, username, parameters
#         )
#         data_request = DataRequest.objects.get(pk=data_request_id_1)
#         access_token = create_access_jwt_token(data_request, username)
#         print("------a1", data_request.id)
#         return get_resource_file(request, data_request, access_token, apidetails)
#         # return HttpResponse(
#         #     json.dumps(
#         #         {
#         #             "access_token": access_token,
#         #             "message": "Get resource with provided token",
#         #         }
#         #     ),
#         #     content_type="application/json",
#         # )
#     return HttpResponse(
#         "Something went wrong request again!!", content_type="text/plain"
#     )


def get_request_file(
        username,
        data_request_id,
        target_format,
        return_type="file",
        size=10000,
        paginate_from=0,
):
    data_request = DataRequest.objects.get(pk=data_request_id)
    file_path = data_request.file.path
    if len(file_path):
        mime_type = mimetypes.guess_type(file_path)[0]
        if data_request.resource.dataset.dataset_type == "FILE" and target_format and target_format in ["CSV", "XML",
                                                                                                        "JSON"]:
            src_format = FORMAT_MAPPING[mime_type]
            response = getattr(
                FormatConverter,
                f"convert_{src_format.lower()}_to_{target_format.lower()}",
            )(file_path, mime_type, return_type)
        else:
            response = HttpResponse(data_request.file, content_type=mime_type)
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                os.path.basename(file_path)
            )
        update_download_count(username, data_request)
        data_request.file.delete()
        return response
    return HttpResponse("Something went wrong request again!!", content_type="text/plain")


def get_resource_file(request, data_request, token, apidetails, username):
    format = request.GET.get("format")
    size = request.GET.get("size")
    if not size:
        size = 10000
    paginate_from = request.GET.get("from", 0)

    if data_request:

        data_request_id = data_request.id
        data_request.refresh_from_db()

        dam = data_request.dataset_access_model_request.access_model.data_access_model
        if data_request.status != "FETCHED":
            return HttpResponse(
                "Request in progress. Please try again in some time",
                content_type="text/plain",
            )
        if dam.type != "OPEN":
            # Get the quota count.
            print("Checking Limits!!")
            get_quota_count = core.get_usage(
                request,
                group="quota||" + str(data_request_id),
                key="dataset_api.ratelimits.user_key",
                rate="dataset_api.ratelimits.quota_per_user",
                increment=False,
            )
            # If count < limit -- don't increment the counter.
            if get_quota_count["count"] < get_quota_count["limit"]:
                # Check for rate.
                get_rate_count = core.get_usage(
                    request,
                    group="rate||" + str(data_request_id),
                    key="dataset_api.ratelimits.user_key",
                    rate="dataset_api.ratelimits.rate_per_user",
                    increment=False,
                )
                # Increment rate and quota count.
                if get_rate_count["count"] < get_rate_count["limit"]:
                    get_file = get_request_file(
                        username,
                        data_request_id,
                        format,
                        "file",
                        size,
                        paginate_from,
                    )
                    get_rate_count = core.get_usage(
                        request,
                        group="rate||" + str(data_request_id),
                        key="dataset_api.ratelimits.user_key",
                        rate="dataset_api.ratelimits.rate_per_user",
                        increment=True,
                    )
                    get_quota_count = core.get_usage(
                        request,
                        group="quota||" + str(data_request_id),
                        key="dataset_api.ratelimits.user_key",
                        rate="dataset_api.ratelimits.quota_per_user",
                        increment=True,
                    )
                    return get_file
                else:
                    return HttpResponseForbidden(content="Rate Limit Exceeded.")
            else:
                return HttpResponseForbidden(content="Quota Limit Exceeded.")
        else:
            # Rate check for OPEN DAM.
            get_rate_count = core.get_usage(
                    request,
                    group="rate||" + str(data_request_id),
                    key="dataset_api.ratelimits.user_key",
                    rate="dataset_api.ratelimits.rate_per_user",
                    increment=False,
                )
            # Increment rate.
            if get_rate_count["count"] < get_rate_count["limit"]:
                get_file = get_request_file(
                        username,
                        data_request_id,
                        format,
                        "file",
                        size,
                        paginate_from,
                    )
                get_rate_count = core.get_usage(
                    request,
                    group="rate||" + str(data_request_id),
                    key="dataset_api.ratelimits.user_key",
                    rate="dataset_api.ratelimits.rate_per_user",
                    increment=True,
                )
                return get_file
            else:
                return HttpResponseForbidden(content="Rate Limit Exceeded.")

    return HttpResponse(json.dumps(token), content_type="application/json")


def get_dist_data(request):
    token = request.GET.get("token")

    try:
        token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return HttpResponse("Authentication failed", content_type="text/plain")
    except IndexError:
        return HttpResponse("Token prefix missing", content_type="text/plain")

    if token_payload:
        dam_resource_id = token_payload.get("dam_resource")
        dam_request_id = token_payload.get("dam_request")
        dam_resource_resource_id = token_payload.get("resource_id")
        username = token_payload.get("username")

        dam_resource = DatasetAccessModelResource.objects.get(id=dam_resource_id)
        dam_request = DatasetAccessModelRequest.objects.get(pk=dam_request_id)

        try:
            apidetails = dam_resource.resource.apidetails
        except:
            apidetails = None

        parameters = {}
        default_parameters = []
        if apidetails:
            default_parameters = apidetails.apiparameter_set.all()
        for param in default_parameters:
            if param.key in request.GET:
                parameters[param.key] = request.GET.get(param.key)
            else:
                parameters[param.key] = param.default

        data_request_id = initiate_dam_request(
            dam_request, dam_resource.resource, username, parameters, True)
        data_request = DataRequest.objects.get(pk=data_request_id)

        # do we need this ?
        # access_token = create_access_jwt_token(data_request, username)
        # print("------a1", data_request.id)

        return get_resource_file(request, data_request, token, apidetails, username)

    return HttpResponse(
        "Something went wrong request again!!", content_type="text/plain"
    )
