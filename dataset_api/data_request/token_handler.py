import datetime

import jwt
from django.conf import settings

from dataset_api.models import (
    DataRequest,
    DatasetAccessModelResource,
    DatasetAccessModelRequest,
)


def create_access_jwt_token(data_request: DataRequest, username):
    access_token_payload = {
        "username": username,
        "data_request": str(data_request.id),
        "dam": data_request.dataset_access_model_request.access_model.id,
        "resource_id": data_request.resource.id,
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(days=0, minutes=settings.ACCESS_TOKEN_EXPIRY_MINS),
        "iat": datetime.datetime.utcnow(),
    }
    access_token = jwt.encode(
        access_token_payload, settings.SECRET_KEY, algorithm="HS256"
    ).decode("utf-8")
    return access_token


def generate_refresh_token(data_request: DataRequest, username):
    refresh_token_payload = {
        "username": username,
        "dam": data_request.dataset_access_model_request.access_model.id,
        "data_request": str(data_request.id),
        "resource_id": data_request.resource.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7, minutes=0),
        "iat": datetime.datetime.utcnow(),
    }
    refresh_token = jwt.encode(
        refresh_token_payload, settings.REFRESH_TOKEN_SECRET, algorithm="HS256"
    ).decode("utf-8")

    return refresh_token


def create_data_jwt_token(
    dam_resource: DatasetAccessModelResource,
    dam_request: DatasetAccessModelRequest,
    username,
):
    access_token_payload = {
        "username": username,
        "dam_resource": dam_resource.id,
        "dam_request": dam_request.id,
        "dam": dam_resource.dataset_access_model.id,
        "resource_id": dam_resource.resource.id,
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(days=0, minutes=settings.ACCESS_TOKEN_EXPIRY_MINS),
        "iat": datetime.datetime.utcnow(),
    }
    access_token = jwt.encode(
        access_token_payload, settings.SECRET_KEY, algorithm="HS256"
    ).decode("utf-8")
    return access_token


def create_data_refresh_token(
    dam_resource: DatasetAccessModelResource,
    dam_request: DatasetAccessModelRequest,
    username,
):
    refresh_token_payload = {
        "username": username,
        "dam_resource": dam_resource.id,
        "dam_request": dam_request.id,
        "dam": dam_resource.dataset_access_model.id,
        "resource_id": dam_resource.resource.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7, minutes=0),
        "iat": datetime.datetime.utcnow(),
    }
    refresh_token = jwt.encode(
        refresh_token_payload, settings.SECRET_KEY, algorithm="HS256"
    ).decode("utf-8")
    return refresh_token
