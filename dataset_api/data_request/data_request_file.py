import json
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
from ..models import DatasetAccessModelResource, DatasetAccessModelRequest

# from graphql import GraphQLError

core._make_cache_key = idp_make_cache_key

es_client = Elasticsearch(settings.ELASTICSEARCH)


@dam_request_validity
@validate_token_or_none
def download(request, data_request_id, username=None):
    target_format = request.GET.get("format", None)

    data_request_instance = DataRequest.objects.get(pk=data_request_id)
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
                "data_request_id": data_request.id,
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
            pd.read_csv(csv_file_path, sep=",", header=0, index_col=False)
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
        with open(csv_file_path, encoding="utf-8") as csvf:
            if return_type == "file":
                response = HttpResponse(csvf, content_type=src_mime_type)
                response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                    os.path.basename(csv_file_path)
                )
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
        json_file = pd.DataFrame(pd.read_json(json_file_path, orient="index"))
        if return_type == "file":
            json_file.to_csv("file.csv")
            response = FileResponse(
                open("file.csv", "rb"), content_type="application/x-download"
            )
            file_name = (
                ".".join(os.path.basename(json_file_path).split(".")[:-1]) + ".json"
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.csv")
            return response
        elif return_type == "data":
            response = HttpResponse(json_file.to_csv(), content_type="application/csv")
            return response

    @classmethod
    def convert_json_to_xml(cls, json_file_path, src_mime_type, return_type="data"):
        json_file = pd.DataFrame(pd.read_json(json_file_path, orient="index"))
        if return_type == "file":
            json_file.to_xml("file.xml")
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
            response = HttpResponse(json_file.to_xml(), content_type="application/xml")
            return response


class FormatExporter:
    @classmethod
    def convert_df_to_csv(cls, df, return_type="data"):
        if return_type == "file":
            df.to_csv("file.csv")
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
            response = HttpResponse(df.to_csv(), content_type="text/csv")
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


def get_request_file(
    username,
    data_request_id,
    target_format,
    return_type="file",
    size=10000,
    paginate_from=0,
):
    data_request = DataRequest.objects.get(pk=data_request_id)
    if target_format and target_format not in ["CSV", "XML", "JSON"]:
        return HttpResponse("invalid format", content_type="text/plain")
    index = str(data_request.id)
    result = es_client.search(
        index=index,
        size=size,
        from_=paginate_from,
    )
    items = result["hits"]["hits"]
    docs = pd.DataFrame()
    for num, doc in enumerate(items):
        source_data = doc["_source"]
        _id = doc["_id"]
        doc_data = pd.Series(source_data, name=_id)
        docs = docs.append(doc_data)
    
    docs.drop(columns=docs.columns[0], 
        axis=1, 
        inplace=True)
    old_cols = list(docs.columns)
    new_cols = [col.replace(": ", "_") if ":" in col else "sample" if col == "" else col for col in old_cols]
    docs.columns = new_cols
    docs[new_cols] = docs[new_cols].astype(str)
    response = getattr(
        FormatExporter,
        f"convert_df_to_{target_format.lower()}",
    )(docs, return_type)
    update_download_count(username, data_request)
    return response


def get_resource(request):
    token = request.GET.get("token")
    format = request.GET.get("format")
    size = request.GET.get("size")
    if not size:
        size = 5
    paginate_from = request.GET.get("from", 0)
    try:
        token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return HttpResponse("Authentication failed", content_type="text/plain")
    except IndexError:
        return HttpResponse("Token prefix missing", content_type="text/plain")
    if token_payload:
        data_request_id = token_payload.get("data_request")
        data_request = DataRequest.objects.get(pk=data_request_id)
        dam = data_request.dataset_access_model_request.access_model.data_access_model
        if dam.type == "OPEN":
            if data_request.status != "FETCHED":
                return HttpResponse(
                    "Request in progress. Please try again in some time",
                    content_type="text/plain",
                )
            return get_request_file(
                token_payload.get("username"),
                data_request_id,
                format,
                "data",
                size,
                paginate_from,
            )
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
                    get_file = get_request_file(
                        token_payload.get("username"),
                        data_request_id,
                        format,
                        "data",
                        size,
                        paginate_from,
                    )
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

    return HttpResponse(json.dumps(token_payload), content_type="application/json")


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


def update_data(request):
    token = request.GET.get("token")
    try:
        token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return HttpResponse("Authentication failed", content_type="text/plain")
    except IndexError:
        return HttpResponse("Token prefix missing", content_type="text/plain")
    if token_payload:
        dam_resource_id = token_payload.get("dam_resource")
        data_request_id = token_payload.get("dam_request")
        data_resource = DatasetAccessModelResource.objects.get(id=dam_resource_id)
        dam_request_instance = DatasetAccessModelRequest.objects.get(pk=data_request_id)
        username = token_payload.get("username")
        apidetails = data_resource.resource.apidetails
        parameters = {}
        default_parameters = []
        if apidetails:
            default_parameters = apidetails.apiparameter_set.all()
        for param in default_parameters:
            if param.key in request.GET:
                parameters[param.key] = request.GET.get(param.key)
            else:
                parameters[param.key] = param.default

        data_request = initiate_dam_request(
            dam_request_instance, data_resource.resource, username, parameters
        )
        access_token = create_access_jwt_token(data_request, username)
        return HttpResponse(
            json.dumps(
                {
                    "access_token": access_token,
                    "message": "Get resource with provided token",
                }
            ),
            content_type="application/json",
        )
    return HttpResponse(
        "Something went wrong request again!!", content_type="text/plain"
    )
