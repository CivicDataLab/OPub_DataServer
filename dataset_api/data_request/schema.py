import json
import mimetypes
import os
from typing import Iterator
import magic
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
    generate_refresh_token,
    create_data_jwt_token,
    create_data_refresh_token,
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
    FileDetails,
    DataRequestParameter,
    ResourceSchema,
)
from dataset_api.models.DataRequest import DataRequest
from dataset_api.models.DatasetAccessModelRequest import DatasetAccessModelRequest
from dataset_api.utils import json_keep_column


class DataRequestType(DjangoObjectType):
    access_token = graphene.String()
    refresh_token = graphene.String()
    data_token = graphene.String()
    data_refresh_token = graphene.String()
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
        dam_resource = DatasetAccessModelResource.objects.get(
            Q(resource=self.resource),
            Q(dataset_access_model=self.dataset_access_model_request.access_model),
        )
        return create_data_jwt_token(
            dam_resource, self.dataset_access_model_request, username
        )

    @validate_token_or_none
    def resolve_data_refresh_token(self: DataRequest, info, username):
        dam_resource = DatasetAccessModelResource.objects.get(
            Q(resource=self.resource),
            Q(dataset_access_model=self.dataset_access_model_request.access_model),
        )
        return create_data_refresh_token(
            dam_resource, self.dataset_access_model_request, username
        )

    def resolve_parameters(self: DataRequest, info):
        parameters = {}
        for parameter in self.datarequestparameters.all():
            parameters[parameter.api_parameter.key] = parameter.value
        return parameters


class DatasetRequestStatusType(graphene.Enum):
    REQUESTED = "REQUESTED"
    FULFILLED = "FULFILLED"
    FETCHED = "FETCHED"


class Query(graphene.ObjectType):
    all_data_requests = graphene.List(DataRequestType)
    data_request = graphene.Field(DataRequestType, data_request_id=graphene.UUID())
    data_request_user = graphene.Field(DataRequestType)

    def resolve_all_data_requests(self, info, **kwargs):
        return DataRequest.objects.all()

    def resolve_data_request(self, info, data_request_id):
        return DataRequest.objects.get(pk=data_request_id)

    @validate_token
    def resolve_data_request_user(self, info, username, **kwargs):
        return DataRequest.objects.filter(user=username)


class DataRequestParameterInput(graphene.InputObjectType):
    key = graphene.ID(required=True)
    value = graphene.String(required=True)


class DataRequestInput(graphene.InputObjectType):
    dataset_access_model_request = graphene.ID(required=True)
    resource = graphene.ID(required=True)
    parameters: Iterator = graphene.List(
        of_type=DataRequestParameterInput, required=False
    )


class OpenDataRequestInput(graphene.InputObjectType):
    dataset_access_model = graphene.ID(required=True)
    resource = graphene.ID(required=True)


class DataRequestUpdateInput(graphene.InputObjectType):
    id = graphene.UUID(required=True)
    status = DatasetRequestStatusType()
    file = Upload(required=False)


def initiate_dam_request(
        dam_request, resource, username, parameters=None, default=False, target_format=None
):
    if parameters is None:
        parameters = {}
    data_request_instance = DataRequest(
        status="REQUESTED",
        user=username,
        resource=resource,
        dataset_access_model_request=dam_request,
        default=default,
    )
    data_request_instance.save()
    dam_resource = DatasetAccessModelResource.objects.get(
        dataset_access_model=dam_request.access_model_id, resource=resource.id
    )
    dam_resource_field_ids = list(dam_resource.fields.all().values_list('id', flat=True))
    schema_rows = list(resource.resourceschema_set.filter(id__in=dam_resource_field_ids).values_list('path', flat=True))
    
    schema_rows
    print ('-------rows', schema_rows)
    fields = []
  
    try:
        for field in dam_resource.fields.all():
            fields.append(field.key)
    except:
        pass

    print('------------------field', resource.dataset.dataset_type, '---', fields)
    # TODO: fix magic strings
    if resource and resource.dataset.dataset_type == "API":
        for parameter in resource.apidetails.apiparameter_set.all():
            value = parameters.get(parameter.key, parameter.default)
            dr_parameter_instance = DataRequestParameter(
                api_parameter=parameter, value=value, data_request=data_request_instance
            )
            dr_parameter_instance.save()
        url = f"{settings.PIPELINE_URL}api_source_query"
        if not target_format:
            target_format = resource.apidetails.default_format
        payload = json.dumps(
            {
                "api_source_id": resource.id,
                "request_id": str(data_request_instance.id),
                "request_columns": [x for x in fields],
                "remove_nodes": [x for x in schema_rows], 
                "request_rows": "",
                "target_format": target_format 
            }
        )
        headers = {}
        response = requests.request("POST", url, headers=headers, data=payload)
        #print(response.text)
    elif resource and resource.dataset.dataset_type == DataType.FILE.value:
        print('-----------------bbbbbaaa')
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
        elif file_instance.format.lower() == "json":
            read_file = open(data_request_instance.file.path, "r")
            file = json.load(read_file)
            print("--------------------jsonparse", file, "----", fields)
            if len(fields) > 0:
                # skip_col(file, fields)
                file = json_keep_column(file, fields, schema_rows)
                # file = json_keep_column(file, fields)
            print("-----------------fltrddata", file)
            read_file.close()
            output_file = open(data_request_instance.file.path, "w")
            file = json.dump(file, output_file, indent=4)
            output_file.close()
        data_request_instance.status = "FETCHED"
        data_request_instance.save()
        #update_data_request_index(data_request_instance)
    return data_request_instance.id


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
        data_request_id = initiate_dam_request(
            dam_request, resource, username, parameters, default=True
        )
        data_request_instance = DataRequest.objects.get(pk=data_request_id)
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
        data_request_instance = initiate_dam_request(
            dam_request, resource, username, None
        )
        return OpenDataRequestMutation(data_request=data_request_instance)


def generator(dict_df, index):
    for _, line in enumerate(dict_df):
        yield {"_index": index, "_type": "_doc", "_source": line}


def update_data_request_index(data_request: DataRequest):
    es_client = Elasticsearch(settings.ELASTICSEARCH)
    file_path = data_request.file.path
    if len(file_path):
        mime_type = magic.from_file(file_path, mime=True)[0]
        src_format = FORMAT_MAPPING[mime_type]
        index_name = str(data_request.id)
        es_create_index_if_not_exists(es_client, index_name)
        if src_format.lower() == "csv":
            csv_file = pd.DataFrame(pd.read_csv(file_path, sep=","))
            csv_file.fillna("", inplace=True)
            json_df = csv_file.to_dict(orient="records")
            res = helpers.bulk(es_client, generator(json_df, index=index_name))
        elif src_format.lower() == "json":
            with open(file_path, "r") as fp:
                data = json.load(fp)
                temp = pd.json_normalize(data, max_level=2)
                list_cols = []
                all_cols = []
                for v in list(temp.columns):
                    if "." in v:
                        all_cols.append(v.split("."))
                    else:
                        all_cols.append(v)
                    keys = v.split(".")
                    rv = data
                    for key in keys:
                        rv = rv[key]
                    # print(rv)
                    if type(rv) == list:
                        list_cols.append(v)
                df = data
                for col_path in list_cols:
                    meta = all_cols.copy()
                    if "." in col_path:
                        path_list = col_path.split(".")
                        meta.remove(path_list)
                    else:
                        meta.remove(col_path)

                    df = pd.json_normalize(
                        df, record_path=col_path.split("."), meta=meta
                    ).to_dict(orient="records")
                df = pd.DataFrame(df)
                df.fillna("", inplace=True)
                json_df = df.to_dict(orient="records")
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
        print("------b1", data_request.id)
        data_request_instance = DataRequest.objects.get(id=data_request.id)
        if data_request_instance:
            data_request_instance.status = data_request.status
            data_request_instance.file = data_request.file
        data_request_instance.save()
        #update_data_request_index(data_request_instance)
        return DataRequestUpdateMutation(data_request=data_request_instance)


class Mutation(graphene.ObjectType):
    data_request = DataRequestMutation.Field()
    open_data_request = OpenDataRequestMutation.Field()
    update_data_request = DataRequestUpdateMutation.Field()
