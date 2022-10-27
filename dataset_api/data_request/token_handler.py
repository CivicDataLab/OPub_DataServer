import datetime

import jwt
from django.conf import settings

from dataset_api.models import DataRequest


def create_access_jwt_token(data_request: DataRequest, username):
    access_token_payload = {
        'username': username,
        'data_request': data_request.id,
        'dam': data_request.dataset_access_model_request.access_model.id,
        'resource_id': data_request.resource.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, minutes=5),
        'iat': datetime.datetime.utcnow(),
    }
    access_token = jwt.encode(access_token_payload,
                              settings.SECRET_KEY, algorithm='HS256').decode('utf-8')
    return access_token


def generate_refresh_token(data_request: DataRequest, username):
    refresh_token_payload = {
        'username': username,
        'dam': data_request.dataset_access_model_request.access_model.id,
        'data_request': data_request.id,
        'resource_id': data_request.resource.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7, minutes=0),
        'iat': datetime.datetime.utcnow(),
    }
    refresh_token = jwt.encode(
        refresh_token_payload, settings.REFRESH_TOKEN_SECRET, algorithm='HS256').decode('utf-8')

    return refresh_token
