import copy
import json
import mimetypes
import os

import jwt
import magic
import pandas as pd
import requests
import xmltodict
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import HttpResponse, FileResponse, HttpResponseForbidden, JsonResponse
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
from ..enums import ParameterTypes
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
    if dataset.status == "PUBLISHED":
        dataset.download_count = count + 1
        dataset.save()
        index_data(dataset)
    # update download count in user datasetreq table
    headers = {}
    # TODO: Move this to appropriate place
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


class InvalidDataException(Exception):
    pass


def filter_csv(request, csv_file, paginate_from, size):
    # paginate
    start = paginate_from
    end = len(csv_file) if (size == -1 or  start + size > len(csv_file)) else start + size
    csv_file = csv_file[start:end]
    csv_file = csv_file.applymap(str)

    # filter
    filters = dict(request.GET.items())
    print('******-----', filters)
    # col_list = [filters[key] for key in filters if key not in ["format", "size", "from"]]
    # csv_file = csv_file.loc[:, csv_file.columns.isin(col_list)] if len(col_list) > 0 else csv_file
    try:
        for key in filters:
            if key not in ["format", "size", "from", "token"]:
                csv_file = csv_file[csv_file[key] == filters[key]]
    except Exception as e:
        print('filter exception csv----', str(e))

    return csv_file


class FormatConverter:
    @classmethod
    def convert_csv_to_json(cls, csv_file, csv_file_path, src_mime_type, return_type="data", size=-1,
                            paginate_from=0,
                            request=None):
        csv_file = pd.DataFrame(
            pd.read_csv(csv_file, sep=",", header=0, index_col=False, )
        )

        csv_file = filter_csv(request, csv_file, paginate_from, size)

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
            response = JsonResponse(csv_file.to_dict(orient="records"), safe=False)
            return response

    @classmethod
    def convert_csv_to_xml(cls, csv_file, csv_file_path, src_mime_type, return_type="data", size=-1, paginate_from=0,
                           request=None):
        csv_file = pd.DataFrame(
            pd.read_csv(csv_file, sep=",", header=0, index_col=False)
        )

        csv_file = filter_csv(request, csv_file, paginate_from, size)
        if return_type == "file":
            csv_file.to_xml("file.xml", index=False)
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
    def convert_xml_to_json(cls, xml_file_path, src_mime_type, return_type="data", size=-1, paginate_from=0,
                            request=None):
        with open(xml_file_path) as xmlFile:
            xml_contents = xmlFile.read()
            data_dict = xmltodict.parse(xml_contents)
        if return_type == "file":
            with open("file.json", "w") as jsonFile:
                json.dump(data_dict, jsonFile)

            response = FileResponse(
                open("file.json", "rb"), content_type="application/x-download"
            )
            file_name = (
                    ".".join(os.path.basename(xml_file_path).split(".")[:-1]) + ".json"
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.json")
            return response
        elif return_type == "data":
            response = JsonResponse(data_dict, safe=False)
            return response

    @classmethod
    def convert_xml_to_csv(cls, xml_file, xml_file_path, src_mime_type, return_type="data", size=-1, paginate_from=0,
                           request=None):
        df = pd.read_xml(xml_file)
        # with open(xml_file_path) as xmlFile:
        #     xml_contents = xmlFile.read()
        #     data_dict = xmltodict.parse(xml_contents)
        #     df = pd.DataFrame.from_dict(data_dict)
        if return_type == "file":
            df.to_csv("file.csv", index=False)

            response = FileResponse(
                open("file.csv", "rb"), content_type="application/x-download"
            )
            file_name = (
                    ".".join(os.path.basename(xml_file_path).split(".")[:-1]) + ".csv"
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.csv")
            return response
        elif return_type == "data":
            response = HttpResponse(df.to_string(index=False), content_type="text/csv")
            return response

    @classmethod
    def convert_xml_to_xml(cls, xml_file, xml_file_path, src_mime_type, return_type="data", size=-1, paginate_from=0,
                           request=None):
        if return_type == "file":
            with open("file.xml", "w") as f:
                f.write(xml_file.read().decode("utf-8"))
            response = FileResponse(
                open("file.xml", "rb"), content_type="application/x-download"
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                os.path.basename(xml_file_path)
            )
            os.remove("file.xml")
        elif return_type == "data":
            # with open(xml_file_path) as f:
            f = xml_file
            contents = f.read()
            response = HttpResponse(contents, content_type="application/xml")
        return response

    @classmethod
    def convert_csv_to_csv(cls, csv_file, csv_file_path, src_mime_type, return_type="data", size=-1, paginate_from=0,
                           request=None):
        csv_file = pd.DataFrame(
            pd.read_csv(csv_file, sep=",", header=0, index_col=False)
        )

        try:
            csv_file = filter_csv(request, csv_file, paginate_from, size)
        except Exception as e:
            print('----filtercall', str(e))

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
            response = HttpResponse(csv_file.to_string(index=False), content_type="text/csv")
            return response

    @classmethod
    def convert_json_to_json(cls, json_file, json_file_path, src_mime_type, return_type="data", size=-1,
                             paginate_from=0,
                             request=None):
        if return_type == "file":
            with open("file.json", "w") as f:
                f.write(json_file.read().decode("utf-8"))
            response = FileResponse(
                open("file.json", "rb"), content_type=src_mime_type
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                os.path.basename(json_file_path)
            )
            os.remove("file.json")
        elif return_type == "data":
            # with open(json_file_path) as f:
            f = json_file
            json_data = json.load(f)
            response = JsonResponse(json_data, safe=False)
        return response

    @classmethod
    def convert_json_to_csv(cls, json_file, json_file_path, src_mime_type, return_type="data", size=-1,
                            paginate_from=0,
                            request=None):
        # final_json = pd.read_json(json_file_path, orient='index' )  #cls.process_json_data(json_file_path)
        final_json = cls.process_json_data(json_file)
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
            response = HttpResponse(final_json.to_csv(index=False), content_type="text/csv")
            return response

    @classmethod
    def process_json_data(cls, json_file_path):
        with open("dummy.json", "w") as fp:
            data = json.load(json_file_path)

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
            if final_result and len(final_result[-1]) > 0 and final_result[-1]:
                list_cols = final_result[-1][1]
                all_coll = [a[0] for a in final_result]
                all_coll = [a for i, a in enumerate(all_coll) if a not in all_coll[:i]]
                for a in list_cols:
                    all_coll = [each for each in all_coll if not each[:len(a)] == a]
                try:
                    df = pd.DataFrame.from_dict(data)
                except (KeyError, ValueError) as e:
                    raise InvalidDataException("Please ensure data is in standard formats.")
                # for col_path in list_cols:
                #     try:
                #         df = pd.json_normalize(
                #             df, record_path=col_path, meta=all_coll
                #         ).to_dict(orient="records")
                #     except KeyError as e:
                #         pass
                for col_path in list_cols:
                    df = df.explode(col_path)
                final_json = pd.DataFrame(df)
                os.remove("dummy.json")
                return final_json
            else:
                os.remove("dummy.json")
                return pd.DataFrame.from_dict(data)

    @classmethod
    def convert_json_to_xml(cls, json_file, json_file_path, src_mime_type, return_type="data", size=-1,
                            paginate_from=0,
                            request=None):
        final_json = cls.process_json_data(json_file)
        if return_type == "file":
            final_json.to_xml("file.xml", index=False)
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
            response = HttpResponse(final_json.to_xml(index=False), content_type="application/xml")
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
            df.to_xml("file.xml", index=False)
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
            response = HttpResponse(df.to_xml(index=False), content_type="application/xml")
            return response


def refresh_token(request):
    token = request.GET.get("token")
    try:
        token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return HttpResponse("Authentication failed! Kindly Refresh", content_type="text/plain")
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
        return HttpResponse("Authentication failed! Kindly Refresh", content_type="text/plain")
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
        size=-1,
        paginate_from=0,
        request=None,
):
    data_request = DataRequest.objects.get(pk=data_request_id)
    file_path = data_request.file.name
    file_obj = data_request.file  # default_storage.open(data_request.file.name, 'r')
    try:
        if len(file_path):
            deep_copy_file_1 = copy.deepcopy(data_request.file)
            mime_type = mimetypes.guess_type(deep_copy_file_1.name)[0]
            if data_request.resource.dataset.dataset_type == "FILE" and target_format and target_format in ["CSV",
                                                                                                            "XML",
                                                                                                            "JSON"]:
                src_format = data_request.resource.filedetails.format
                response = getattr(
                    FormatConverter,
                    f"convert_{src_format.lower()}_to_{target_format.lower()}",
                )(file_obj, file_path, mime_type, return_type, size, paginate_from, request)
            else:
                response = HttpResponse(data_request.file, content_type=mime_type)
                response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                    os.path.basename(file_path)
                )
            update_download_count(username, data_request)
            file_path = "/" + data_request.file.name
            if default_storage.exists(file_path):
                try:
                    data_request.file.delete()
                except Exception as e:
                    print (e)
            return response
    except InvalidDataException as e:
        raise e
        print("Error requesting data " + str(e))
        return HttpResponse("There is a problem with data!! Please contact Data Provider", content_type="text/plain",
                            status=502)
    except Exception as e:
        raise e
        print("Error requesting data " + str(e))
        return HttpResponse("There is a problem with data!! Please contact Data Provider", content_type="text/plain",
                            status=502)
    finally:
        file_obj.close()
    return HttpResponse("There is a problem with data!! Please contact Data Provider", content_type="text/plain",
                        status=502)


def get_resource_file(request, data_request, token, apidetails, username, return_type="file"):
    format = request.GET.get("format")
    size = request.GET.get("size", -1)
    paginate_from = request.GET.get("from", 0)
    if not size == -1 and (not str(size).isdigit() or not str(paginate_from).isdigit()):
        return HttpResponse(
            "invalid pagination params",
            content_type="text/plain",
            status=400
        )
    else:
        size = int(size)
        paginate_from = int(paginate_from)
    if data_request:

        data_request_id = data_request.id
        data_request.refresh_from_db()

        dam = data_request.dataset_access_model_request.access_model.data_access_model
        if data_request.status != "FETCHED":
            return HttpResponse(
                "Request in progress. Please try again in some time",
                content_type="text/plain",
                status=503
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
                        return_type,
                        size,
                        paginate_from,
                        request,
                    )
                    print("file after quota", get_file)
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
                    return_type,
                    size,
                    paginate_from,
                    request
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
    return_type = request.GET.get("type")
    if not return_type:
        return_type = "data"
    try:
        token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return HttpResponse("Authentication failed! Kindly refresh authentication token!", content_type="text/plain")
    except IndexError:
        return HttpResponse("Token prefix missing", content_type="text/plain")

    if token_payload:
        dam_resource_id = token_payload.get("dam_resource")
        dam_request_id = token_payload.get("dam_request")
        dam_resource_resource_id = token_payload.get("resource_id")
        username = token_payload.get("username")
        token_time = token_payload.get("token_time")

        dam_resource = DatasetAccessModelResource.objects.get(id=dam_resource_id)
        dam_request = DatasetAccessModelRequest.objects.get(pk=dam_request_id)
        if token_time != dam_request.token_time.strftime("%m/%d/%Y, %H:%M:%S"):
            return HttpResponse("Invalid token!! try again", content_type="text/plain", status=502)

        try:
            apidetails = dam_resource.resource.apidetails
        except:
            apidetails = None

        parameters = {}
        default_parameters = []
        if apidetails:
            default_parameters = apidetails.apiparameter_set.all().exclude(type="PREVIEW")
        for param in default_parameters:
            if param.key in request.GET:
                parameters[param.key] = request.GET.get(param.key)
            if return_type != "data" and param.type == ParameterTypes.DOWNLOAD:
                parameters[param.key] = param.default
            # else:
            #     parameters[param.key] = param.default

        data_request_id = initiate_dam_request(
            dam_request, dam_resource.resource, username, parameters, True,
            target_format=request.GET.get("format", "" if not apidetails else apidetails.response_type))
        data_request = DataRequest.objects.get(pk=data_request_id)

        # do we need this ?
        # access_token = create_access_jwt_token(data_request, username)
        # print("------a1", data_request.id)

        return get_resource_file(request, data_request, token, apidetails, username, return_type)

    return HttpResponse(
        "Something went wrong request again!!", content_type="text/plain", status=502
    )
