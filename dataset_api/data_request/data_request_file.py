import json
import mimetypes
import os

import jwt
import pandas as pd
import requests
from django.conf import settings
from django.http import HttpResponse, FileResponse

from dataset_api.constants import FORMAT_MAPPING
from dataset_api.data_request.token_handler import create_access_jwt_token
from dataset_api.decorators import validate_token_or_none
from dataset_api.models.DataRequest import DataRequest
from dataset_api.search import index_data


@validate_token_or_none
def download(request, data_request_id, username=None):
    target_format = request.GET.get("format", None)
    return get_request_file(username, data_request_id, target_format)


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
        csv_file = pd.DataFrame(pd.read_csv(csv_file_path, sep=",", header=0, index_col=False))
        if return_type == "file":
            csv_file.to_json("file.json", orient="records", date_format="epoch", double_precision=10,
                             force_ascii=True, date_unit="ms", default_handler=None)
            response = FileResponse(open("file.json", "rb"), content_type="application/x-download")
            file_name = ".".join(os.path.basename(csv_file_path).split(".")[:-1]) + ".json"
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
        csv_file = pd.DataFrame(pd.read_csv(csv_file_path, sep=",", header=0, index_col=False))
        if return_type == "file":
            csv_file.to_xml("file.xml")
            response = FileResponse(open("file.xml", "rb"), content_type="application/x-download")
            file_name = ".".join(os.path.basename(csv_file_path).split(".")[:-1]) + ".xml"
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
        with open(csv_file_path, encoding='utf-8') as csvf:
            if return_type == "file":
                response = HttpResponse(csvf, content_type=src_mime_type)
                response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                    os.path.basename(csv_file_path)
                )
            elif return_type == "data":
                csv_file = pd.DataFrame(pd.read_csv(csv_file_path, sep=",", header=0, index_col=False))
                response = HttpResponse(csv_file.to_string(), content_type="text/csv")
            return response

    @classmethod
    def convert_json_to_json(cls, json_file_path, src_mime_type, return_type="data"):
        if return_type == "file":
            response = FileResponse(open(json_file_path, "rb"), content_type=src_mime_type)
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                os.path.basename(json_file_path)
            )
        elif return_type == "data":
            json_file = pd.DataFrame(pd.read_json(json_file_path))
            response = HttpResponse(json_file.to_string(), content_type="text/csv")
        return response

    @classmethod
    def convert_json_to_csv(cls, json_file_path, src_mime_type, return_type="data"):
        json_file = pd.DataFrame(pd.read_json(json_file_path))
        if return_type == "file":
            json_file.to_csv("file.csv")
            response = FileResponse(open("file.csv", "rb"), content_type="application/x-download")
            file_name = ".".join(os.path.basename(json_file_path).split(".")[:-1]) + ".json"
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.csv")
            return response
        elif return_type == "data":
            response = HttpResponse(json_file.to_csv(), content_type="application/json")
            return response

    @classmethod
    def convert_json_to_xml(cls, json_file_path, src_mime_type, return_type="data"):
        json_file = pd.DataFrame(pd.read_json(json_file_path))
        if return_type == "file":
            json_file.to_xml("file.xml")
            response = FileResponse(open("file.xml", "rb"), content_type="application/x-download")
            file_name = ".".join(os.path.basename(json_file_path).split(".")[:-1]) + ".xml"
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                file_name
            )
            os.remove("file.xml")
            return response
        elif return_type == "data":
            response = HttpResponse(json_file.to_dict(), content_type="application/xml")
            return response


def get_request_file(username, data_request_id, target_format, return_type="file"):
    data_request = DataRequest.objects.get(pk=data_request_id)
    if target_format and target_format not in ["CSV", "XML", "JSON"]:
        return HttpResponse("invalid format", content_type="text/plain")
    file_path = data_request.file.path
    if len(file_path):
        mime_type = mimetypes.guess_type(file_path)[0]
        if target_format:
            src_format = FORMAT_MAPPING[mime_type]
            response = getattr(FormatConverter, f"convert_{src_format.lower()}_to_{target_format.lower()}")(file_path,
                                                                                                            mime_type,
                                                                                                            return_type)
        else:
            response = HttpResponse(data_request.file, content_type=mime_type)
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                os.path.basename(file_path)
            )
        update_download_count(username, data_request)
        return response

        # TODO: delete file after download

    else:
        response = HttpResponse("file doesnt exist", content_type="text/plain")
    return response


def get_resource(request):
    token = request.GET.get("token")
    format = request.GET.get("format")
    try:
        token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return HttpResponse("Authentication failed", content_type='text/plain')
    except IndexError:
        return HttpResponse("Token prefix missing", content_type='text/plain')
    if token_payload:
        return get_request_file(token_payload.get("username"), token_payload.get("data_request"), format, "data")

    return HttpResponse(json.dumps(token_payload), content_type='application/json')


def refresh_token(request):
    token = request.GET.get("token")
    try:
        token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return HttpResponse("Authentication failed", content_type='text/plain')
    except IndexError:
        return HttpResponse("Token prefix missing", content_type='text/plain')
    if token_payload:
        data_request_id = token_payload.get("data_request")
        username = token_payload.get("username")
        data_request_instance = DataRequest.objects.get(pk=data_request_id)
        access_token = create_access_jwt_token(data_request_instance, username)
        return HttpResponse(access_token, content_type='text/plain')
    return HttpResponse("Something went wrong request again!!", content_type='text/plain')
