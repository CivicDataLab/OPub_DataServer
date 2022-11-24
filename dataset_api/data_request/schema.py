import json
import mimetypes
import os
from typing import Iterator

import graphene
import pandas as pd
import requests
from django.core.files import File
from django.db.models import Q
from elasticsearch import Elasticsearch, helpers
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output

from DatasetServer import settings
from dataset_api.constants import DATAREQUEST_SWAGGER_SPEC, FORMAT_MAPPING
from dataset_api.data_request.token_handler import (
    create_access_jwt_token,
    generate_refresh_token, create_data_jwt_token, create_data_refresh_token,
)
from dataset_api.dataset_access_model_request.schema import (
    create_dataset_access_model_request,
)
from dataset_api.decorators import validate_token, validate_token_or_none
from dataset_api.enums import DataType
from dataset_api.es_utils import es_create_index_if_not_exists
from dataset_api.models import (
    Resource,
    DatasetAccessModel,
    DatasetAccessModelResource,
    FileDetails, DataRequestParameter, ResourceSchema,
)
from dataset_api.models.DataRequest import DataRequest
from dataset_api.models.DatasetAccessModelRequest import DatasetAccessModelRequest


class DataRequestType(DjangoObjectType):
    access_token = graphene.String()
    refresh_token = graphene.String()
    data_token = graphene.String()
    data_refresh_token = graphene.String()
    spec = graphene.JSONString()
    parameters = graphene.JSONString()
    remaining_quota = graphene.Int()

    class Meta:
        model = DataRequest
        fields = "__all__"

    @validate_token_or_none
    def resolve_access_token(self: DataRequest, info, username):
        return create_access_jwt_token(self, username)

    @validate_token_or_none
    def resolve_refresh_token(self: DataRequest, info, username):
        return generate_refresh_token(self, username)

    @validate_token_or_none
    def resolve_data_token(self: DataRequest, info, username):
        dam_resource = DatasetAccessModelResource.objects.get(Q(resource=self.resource),
                                                              Q(dataset_access_model=self.dataset_access_model_request.access_model))
        return create_data_jwt_token(dam_resource, username)

    @validate_token_or_none
    def resolve_data_refresh_token(self: DataRequest, info, username):
        dam_resource = DatasetAccessModelResource.objects.get(Q(resource=self.resource),
                                                              Q(dataset_access_model=self.dataset_access_model_request.access_model))
        return create_data_refresh_token(dam_resource, username)

    @validate_token_or_none
    def resolve_spec(self: DataRequest, info, username):
        spec = DATAREQUEST_SWAGGER_SPEC.copy()
        dam_resource = DatasetAccessModelResource.objects.get(Q(resource=self.resource),
                                                              Q(dataset_access_model=self.dataset_access_model_request.access_model))
        spec["paths"]["/refreshtoken"]["get"]["parameters"][0][
            "example"
        ] = generate_refresh_token(self, username)
        spec["paths"]["/refresh_data_token"]["get"]["parameters"][0][
            "example"
        ] = create_data_refresh_token(dam_resource, username)
        data_token = create_data_jwt_token(dam_resource, username)
        spec["paths"]["/getresource"]["get"]["parameters"][0][
            "example"
        ] = create_access_jwt_token(self, username)
        spec["paths"]["/update_data"]["get"]["parameters"][0][
            "example"
        ] = data_token
        parameters = []
        resource = self.resource
        if resource and resource.dataset.dataset_type == "API":
            parameters = resource.apidetails.apiparameter_set.all()
        for parameter in parameters:
            param_input = {
                "name": parameter.key,
                "in": "query",
                "required": "true",
                "description": parameter.description,
                "schema": {
                    "type": parameter.format
                },
                "example": parameter.default
            }
            spec["paths"]["/update_data"]["get"]["parameters"].append(param_input)
        # spec["info"]["title"] = self.resource.title
        # spec["info"]["description"] = self.resource.description
        return spec

    def resolve_parameters(self: DataRequest, info):
        parameters = {}
        for parameter in self.datarequestparameter_set.all():
            parameters[parameter.api_parameter.key] = parameter.value
        return parameters


class DatasetRequestStatusType(graphene.Enum):
    REQUESTED = "REQUESTED"
    FULFILLED = "FULFILLED"
    FETCHED = "FETCHED"


class Query(graphene.ObjectType):
    all_data_requests = graphene.List(DataRequestType)
    data_request = graphene.Field(DataRequestType, data_request_id=graphene.Int())
    data_request_user = graphene.Field(DataRequestType)

    def resolve_all_data_requests(self, info, **kwargs):
        return DataRequest.objects.all()

    def resolve_data_request(self, info, data_request_id):
        return DataRequest.objects.get(pk=data_request_id)

    @validate_token
    def resolve_data_request_user(self, info, username, **kwargs):
        return DataRequest.objects.get(user=username)


class DataRequestParameterInput(graphene.InputObjectType):
    key = graphene.ID(required=True)
    value = graphene.String(required=True)


class DataRequestInput(graphene.InputObjectType):
    dataset_access_model_request = graphene.ID(required=True)
    resource = graphene.ID(required=True)
    parameters: Iterator = graphene.List(of_type=DataRequestParameterInput, required=False)


class OpenDataRequestInput(graphene.InputObjectType):
    dataset_access_model = graphene.ID(required=True)
    resource = graphene.ID(required=True)


class DataRequestUpdateInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = DatasetRequestStatusType()
    file = Upload(required=False)


def initiate_dam_request(dam_request, resource, username, parameters=None, default=False):
    if parameters is None:
        parameters = {}
    data_request_instance = DataRequest(
        status="REQUESTED",
        user=username,
        resource=resource,
        dataset_access_model_request=dam_request,
        default=default
    )
    data_request_instance.save()
    dam_resource = DatasetAccessModelResource.objects.get(
        dataset_access_model=dam_request.access_model_id, resource=resource.id
    )
    fields = []
    for field in dam_resource.fields:
        schema_field = ResourceSchema.objects.get(id=field)
        fields.append(schema_field.key)

    # TODO: fix magic strings
    if resource and resource.dataset.dataset_type == "API":
        for parameter in resource.apidetails.apiparameter_set.all():
            value = parameters.get(parameter.key, parameter.default)
            dr_parameter_instance = DataRequestParameter(api_parameter=parameter, value=value,
                                                         data_request=data_request_instance)
            dr_parameter_instance.save()
        url = f"{settings.PIPELINE_URL}api_source_query"
        payload = json.dumps(
            {
                "api_source_id": resource.id,
                "request_id": data_request_instance.id,
                "request_columns": [x for x in fields],
                "request_rows": "",
            }
        )
        headers = {}
        response = requests.request("POST", url, headers=headers, data=payload)
        print(response.text)
    elif resource and resource.dataset.dataset_type == DataType.FILE.value:
        data_request_instance.file = File(
            resource.filedetails.file,
            os.path.basename(resource.filedetails.file.path),
        )
        file_instance = FileDetails.objects.get(resource=resource)
        data_request_instance.save()
        if file_instance.format.lower() == "csv":
            file_data = pd.read_csv(data_request_instance.file)
            file_columns = file_data.columns.values.tolist()
            remove_cols = [x for x in file_columns if x not in fields]
            if len(fields) == 0:
                remove_cols = []
            file_data.drop(remove_cols, axis=1, inplace=True)
            file_data.to_csv(data_request_instance.file.path, index=False)
            update_data_request_index(data_request_instance)
        elif file_instance.format.lower() == "json":
            read_file = open(data_request_instance.file.path, "r")
            file = json.load(read_file)
            remove_cols = [x for x in file.keys() if x not in fields]
            if len(fields) == 0:
                remove_cols = []
            for x in fields:
                del file[x]
            read_file.close()
            output_file = open(data_request_instance.file.path, "w")
            file = json.dump(file, output_file, indent=4)
            output_file.close()
        data_request_instance.status = "FETCHED"
    data_request_instance.save()
    return data_request_instance


class DataRequestMutation(graphene.Mutation, Output):
    class Arguments:
        data_request = DataRequestInput()

    data_request = graphene.Field(DataRequestType)

    @staticmethod
    @validate_token_or_none
    def mutate(root, info, data_request: DataRequestInput, username=""):
        try:
            resource = Resource.objects.get(id=data_request.resource)
            dam_request = DatasetAccessModelRequest.objects.get(
                id=data_request.dataset_access_model_request
            )
            input_parameters = data_request.parameters
            if not input_parameters:
                input_parameters = []
            parameters = {}
            for parameter in input_parameters:
                parameters[parameter.key] = parameter.value
        except (Resource.DoesNotExist, DatasetAccessModelRequest.DoesNotExist) as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {
                            "message": "Data Access Model or resource with given id not found",
                            "code": "404",
                        }
                    ]
                },
            }
        data_request_instance = initiate_dam_request(dam_request, resource, username, parameters, default=True)
        return DataRequestMutation(data_request=data_request_instance)


class OpenDataRequestMutation(graphene.Mutation, Output):
    class Arguments:
        data_request = OpenDataRequestInput()

    data_request = graphene.Field(DataRequestType)

    @staticmethod
    @validate_token_or_none
    def mutate(root, info, data_request: OpenDataRequestInput = None, username=""):
        resource = Resource.objects.get(id=data_request.resource)
        dataset_access_model = DatasetAccessModel.objects.get(
            id=data_request.dataset_access_model
        )
        dam_request = create_dataset_access_model_request(
            dataset_access_model,
            "",
            "OTHERS",
            username,
            user_email=username,
            status="APPROVED",
        )
        data_request_instance = initiate_dam_request(dam_request, resource, username, None)
        return OpenDataRequestMutation(data_request=data_request_instance)


def generator(dict_df, index):
    for _, line in enumerate(dict_df):
        yield {
            '_index': index,
            '_type': '_doc',
            '_source': line
        }


def update_data_request_index(data_request: DataRequest):
    es_client = Elasticsearch(settings.ELASTICSEARCH)
    file_path = data_request.file.path
    if len(file_path):
        mime_type = mimetypes.guess_type(file_path)[0]
        src_format = FORMAT_MAPPING[mime_type]
        index_name = str(data_request.id)
        es_create_index_if_not_exists(es_client, index_name)
        if src_format.lower() == "csv":
            csv_file = pd.DataFrame(
                pd.read_csv(file_path, sep=",")
            )
            csv_file.fillna("", inplace=True)
            json_df = csv_file.to_dict(orient="records")
            res = helpers.bulk(es_client, generator(json_df, index=index_name))
        elif src_format.lower() == "json":
            df = pd.DataFrame(pd.read_json(file_path, orient="index"))
            df.fillna("", inplace=True)
            json_df = df.to_dict(orient="records")
            json_df = pd.json_normalize(json_df).fillna("", inplace=True)
            json_df = json_df.to_dict(orient="records")
            res = helpers.bulk(es_client, generator(json_df, index=index_name))
        elif src_format.lower() == "xml":
            df = pd.DataFrame(pd.read_xml(file_path))
            df.fillna("", inplace=True)
            json_df = df.to_dict(orient="records")
            res = helpers.bulk(es_client, generator(json_df, index=index_name))


class DataRequestUpdateMutation(graphene.Mutation, Output):
    class Arguments:
        data_request = DataRequestUpdateInput()

    data_request = graphene.Field(DataRequestType)

    @staticmethod
    def mutate(root, info, data_request: DataRequestUpdateInput = None):
        data_request_instance = DataRequest.objects.get(id=data_request.id)
        if data_request_instance:
            data_request_instance.status = data_request.status
            data_request_instance.file = data_request.file
        data_request_instance.save()
        update_data_request_index(data_request_instance)
        return DataRequestUpdateMutation(data_request=data_request_instance)


class Mutation(graphene.ObjectType):
    data_request = DataRequestMutation.Field()
    open_data_request = OpenDataRequestMutation.Field()
    update_data_request = DataRequestUpdateMutation.Field()
