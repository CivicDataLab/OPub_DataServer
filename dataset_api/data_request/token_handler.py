import datetime

import jwt
from django.conf import settings

from dataset_api.models import (
    DatasetAccessModelResource,
    DatasetAccessModelRequest,
)
from ..utils import get_data_access_model_request_validity


def create_access_jwt_token(dataset_access_model_request: DatasetAccessModelRequest,
                            dam_resource: DatasetAccessModelResource, username):
    access_token_payload = {
        "username": username,
        "dam_request": str(dataset_access_model_request.id),
        "dam_resource": dam_resource.id,
        "exp": datetime.datetime.utcnow()
               + datetime.timedelta(days=0, minutes=settings.ACCESS_TOKEN_EXPIRY_MINS),
        "token_time": dataset_access_model_request.token_time.strftime("%m/%d/%Y, %H:%M:%S"),
        "iat": datetime.datetime.utcnow(),
    }
    access_token = jwt.encode(
        access_token_payload, settings.SECRET_KEY, algorithm="HS256"
    ).decode("utf-8")
    return access_token


def generate_refresh_token(dataset_access_model_request: DatasetAccessModelRequest,
                           dam_resource: DatasetAccessModelResource, username):
    refresh_token_payload = {
        "username": username,
        "dam": dataset_access_model_request.access_model.id,
        "dam_request": str(dataset_access_model_request.id),
        "dam_resource": dam_resource.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7, minutes=0),
        "token_time": dataset_access_model_request.token_time.strftime("%m/%d/%Y, %H:%M:%S"),
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
        "token_time": dam_request.token_time.strftime("%m/%d/%Y, %H:%M:%S"),
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
    validity = get_data_access_model_request_validity(dam_request)
    validity = (
        validity
        if validity and validity != ""
        else datetime.datetime.utcnow()
             + datetime.timedelta(days=0, minutes=settings.ACCESS_TOKEN_EXPIRY_MINS)
    )
    refresh_token_payload = {
        "username": username,
        "dam_resource": dam_resource.id,
        "dam_request": dam_request.id,
        "dam": dam_resource.dataset_access_model.id,
        "resource_id": dam_resource.resource.id,
        "exp": validity,
        "token_time": dam_request.token_time.strftime("%m/%d/%Y, %H:%M:%S"),
        "iat": datetime.datetime.utcnow(),
    }
    refresh_token = jwt.encode(
        refresh_token_payload, settings.SECRET_KEY, algorithm="HS256"
    ).decode("utf-8")
    return refresh_token
