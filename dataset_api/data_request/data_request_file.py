import json
import mimetypes
import os

import jwt
import requests
from django.conf import settings
from django.http import HttpResponse

from dataset_api.data_request.token_handler import create_access_jwt_token
from dataset_api.models.DataRequest import DataRequest


def download(request, data_request_id):
    return get_request_file(request.META.get("HTTP_AUTHORIZATION"), data_request_id)


def update_download_count(access_token, data_request: DataRequest):
    # update download count in dataset
    dataset = data_request.dataset_access_model_request.access_model.dataset
    count = dataset.download_count
    dataset.download_count = count + 1

    # update download count in user datasetreq table
    headers = {}
    auth_url = settings.AUTH_URL + "update_datasetreq"
    response = requests.post(
        auth_url,
        data=json.dumps(
            {
                "access_token": access_token,
                "data_request_id": data_request.id,
                "dataset_access_model_request_id": data_request.dataset_access_model_request.id,
                "dataset_access_model_id": data_request.dataset_access_model_request.access_model.id,
                "dataset_id": dataset.id,
            }
        ),
        headers=headers,
    )
    response_json = json.loads(response.text)
    if not response_json["success"]:
        return {
            "Success": False,
            "error": response_json["error"],
            "error_description": response_json["error_description"],
        }

    return {"Success": True, "message": "Dataset download count updated successfully"}


def get_request_file(access_token, data_request_id):
    data_request = DataRequest.objects.get(pk=data_request_id)
    file_path = data_request.file.path
    if len(file_path):
        mime_type = mimetypes.guess_type(file_path)[0]
        response = HttpResponse(data_request.file, content_type=mime_type)
        response["Content-Disposition"] = 'attachment; filename="{}"'.format(
            os.path.basename(file_path)
        )

        update_download_count(access_token, data_request)

        # TODO: delete file after download
        # data_request.file
        # data_request.save()

    else:
        response = HttpResponse("file doesnt exist", content_type="text/plain")
    return response


def get_resource(request):
    token = request.GET.get("token")
    try:
        token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return HttpResponse("Authentication failed", content_type='text/plain')
    except IndexError:
        return HttpResponse("Token prefix missing", content_type='text/plain')
    if token_payload:
        return get_request_file(token, token_payload.get("data_request"))

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
