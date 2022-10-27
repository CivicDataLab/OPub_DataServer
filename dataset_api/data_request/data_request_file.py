import json
import mimetypes
import os

import jwt
from django.conf import settings
from django.http import HttpResponse

from dataset_api.data_request.token_handler import create_access_jwt_token
from dataset_api.models.DataRequest import DataRequest


def download(request, data_request_id):
    return get_request_file(data_request_id)


def get_request_file(data_request_id):
    request = DataRequest.objects.get(pk=data_request_id)
    file_path = request.file.path
    if len(file_path):
        mime_type = mimetypes.guess_type(file_path)[0]
        response = HttpResponse(request.file, content_type=mime_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
        # TODO: delete file after download
        # request.file
        # request.save()
    else:
        response = HttpResponse("file doesnt exist", content_type='text/plain')
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
        return get_request_file(token_payload.get("data_request"))

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
        return HttpResponse({'access_token': access_token})
    return HttpResponse("Something went wrong request again!!", content_type='text/plain')
