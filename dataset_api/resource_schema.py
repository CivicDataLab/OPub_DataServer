import mimetypes
import os
from typing import Iterable

import graphene
import pandas as pd
from django.core.files.base import ContentFile
from graphene import List
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output
from graphql import GraphQLError
import pandas as pd
import json

from .enums import DataType
from .models import (
    APISource,
    Resource,
    Dataset,
    ResourceSchema,
    APIDetails,
    FileDetails, APIParameter,
)
from .decorators import (
    auth_user_action_resource,
    validate_token,
    auth_user_by_org,
    auth_query_resource,
)
from .constants import FORMAT_MAPPING
from .utils import log_activity, get_client_ip, get_keys

from .api_resource import api_fetch
import genson




class ResourceSchemaInputType(graphene.InputObjectType):
    id = graphene.ID(required=False)
    key = graphene.String()
    display_name = graphene.String()
    format = graphene.String()
    description = graphene.String(required=False)
    parent = graphene.String(required=False)
    array_field = graphene.String(required=False)


class ResourceSchemaType(DjangoObjectType):
    class Meta:
        model = ResourceSchema
        fields = "__all__"


class APIParametersType(DjangoObjectType):
    class Meta:
        model = APIParameter
        fields = "__all__"


class FileDetailsType(DjangoObjectType):
    class Meta:
        model = FileDetails
        fields = "__all__"


class ApiDetailsType(DjangoObjectType):
    parameters = graphene.List(APIParametersType)

    class Meta:
        model = APIDetails
        fields = "__all__"

    def resolve_parameters(self: APIDetails, info):
        try:
            parameters = APIParameter.objects.filter(api_details=self)
            return parameters
        except APIParameter.DoesNotExist as e:
            return []


class ResourceType(DjangoObjectType):
    schema = graphene.List(ResourceSchemaType)
    file_details = graphene.Field(FileDetailsType)
    api_details = graphene.Field(ApiDetailsType)
    schema_exists = graphene.Boolean()

    class Meta:
        model = Resource
        fields = "__all__"

    def resolve_schema(self, info):
        try:
            schema = ResourceSchema.objects.filter(resource=self)
            return schema
        except ResourceSchema.DoesNotExist as e:
            return []

    def resolve_file_details(self, info):
        try:
            file_details = FileDetails.objects.get(resource=self)
            return file_details
        except FileDetails.DoesNotExist as e:
            return None

    def resolve_api_details(self, info):
        try:
            api_details = APIDetails.objects.get(resource=self)
            return api_details
        except APIDetails.DoesNotExist as e:
            return None

    def resolve_schema_exists(self, info):
        try:
            ResourceSchema.objects.filter(resource=self)
            return True
        except ResourceSchema.DoesNotExist as e:
            return False


class Query(graphene.ObjectType):
    all_resources = graphene.List(ResourceType)
    resource = graphene.Field(ResourceType, resource_id=graphene.Int())
    resource_columns = graphene.List(graphene.String, resource_id=graphene.Int())
    resource_dataset = graphene.List(ResourceType, dataset_id=graphene.Int())

    # Access : PMU
    @auth_user_by_org(action="query")
    def resolve_all_resources(self, info, role, **kwargs):
        if role == "PMU":
            return Resource.objects.all().order_by("-modified")
        else:
            raise GraphQLError("Access Denied")

    # Access : PMU - DPA/DP of that org to which this resource belongs.
    @auth_query_resource(action="query||resource")
    def resolve_resource(self, info, role, resource_id):
        if role == "PMU" or role == "DPA" or role == "DP":
            return Resource.objects.get(pk=resource_id)
        else:
            raise GraphQLError("Access Denied")

    # Access : PMU - DPA/DP of that org to which this resource belongs.
    @auth_query_resource(action="query||resource")
    def resolve_resource_columns(self, info, resource_id, role):
        if role == "PMU" or role == "DPA" or role == "DP":
            resource = Resource.objects.get(pk=resource_id)
            if resource.dataset.dataset_type == DataType.FILE.value:
                if resource.filedetails.file and len(resource.filedetails.file.path):
                    if "csv" in resource.filedetails.format.lower():
                        file = pd.read_csv(resource.filedetails.file.path)
                        return file.columns.tolist()
                    if resource.filedetails.format.lower() == "json":
                        with open(resource.filedetails.file.path) as jsonFile:
                            # return list(set(get_keys(jsonFile.read(), [])))
                            builder = genson.SchemaBuilder()
                            jsondata = json.loads(jsonFile.read())  #json.loads(resource.filedetails.file)
                            builder.add_object(jsondata)
                            schema_dict = builder.to_schema()
                            schema_dict = schema_dict.get("properties", {})
                            schema = []
                            api_fetch.parse_schema(schema_dict, "", schema)
                            return schema
            return []
        else:
            raise GraphQLError("Access Denied")

    # Access : DPA/DP of that org to which this resource belongs.
    @auth_query_resource(action="query||dataset")
    def resolve_resource_dataset(self, info, dataset_id, role):
        if role == "PMU" or role == "DPA" or role == "DP":
            return Resource.objects.filter(dataset=dataset_id).order_by("-modified")
        else:
            raise GraphQLError("Access Denied")

    # Access : DPA/DP of that org to which this resource belongs.
    @auth_query_resource(action="query||dataset")
    def resolve_resource_dataset(self, info, dataset_id, role):
        if role == "PMU" or role == "DPA" or role == "DP":
            return Resource.objects.filter(dataset=dataset_id).order_by("-modified")
        else:
            raise GraphQLError("Access Denied")


class ResponseType(graphene.Enum):
    JSON = "JSON"
    XML = "XML"
    CSV = "CSV"


class APIParameterInputType(graphene.InputObjectType):
    id = graphene.ID(required=False)
    key = graphene.String(required=True)
    format = graphene.String(required=False)
    default = graphene.String(required=True)
    description = graphene.String(required=True)


class ApiInputType(graphene.InputObjectType):
    api_source = graphene.ID(required=True)
    auth_required = graphene.Boolean(required=True)
    url_path = graphene.String(required=True)
    response_type = ResponseType()
    parameters: Iterable = graphene.List(of_type=APIParameterInputType, required=False)


class FileInputType(graphene.InputObjectType):
    # TODO: Add file format enum
    format = graphene.String(required=False)
    file = Upload(required=False)
    remote_url = graphene.String(required=False)


class ResourceInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=False)
    dataset = graphene.ID(required=True)
    status = graphene.String(required=True)
    schema: Iterable = graphene.List(of_type=ResourceSchemaInputType, required=False)
    masked_fields = graphene.List(of_type=graphene.String, default=[], required=False)
    api_details: ApiInputType = graphene.Field(ApiInputType, required=False)
    file_details: FileInputType = graphene.Field(FileInputType, required=False)
    byte_size = graphene.Float(required=False, default_value=0)
    release_date = graphene.Date(required=False)
    media_type = graphene.String(required=False, default_value="")
    compression_format = graphene.String(required=False, default_value="")
    packaging_format = graphene.String(required=False, default_value="")
    checksum = graphene.String(required=False, default_value="")


class DeleteResourceInput(graphene.InputObjectType):
    id = graphene.ID(required=True)


def _remove_masked_fields(resource_instance: Resource):
    if (
            resource_instance.masked_fields
            and len(resource_instance.filedetails.file.path)
            and "csv" in resource_instance.filedetails.format.lower()
    ):
        df = pd.read_csv(resource_instance.filedetails.file.path)
        df = df.drop(columns=resource_instance.masked_fields)
        data = df.to_csv(index=False)
        temp_file = ContentFile(data.encode("utf-8"))
        resource_instance.filedetails.file.save(
            os.path.basename(resource_instance.filedetails.file.path), temp_file
        )
    resource_instance.save()


def _create_update_schema(resource_data: ResourceInput, resource_instance):
    schema_ids = []  # List of schemas that already exists.
    resource_schema_instances = ResourceSchema.objects.filter(resource=resource_data.id)
    for schema in resource_schema_instances:
        schema_ids.append(schema.id)
    for schema in resource_data.schema:
        if schema.id:
            schema_ids.remove(int(schema.id))
    # Delete schema which were not updated or created.
    if schema_ids:
        ResourceSchema.objects.filter(id__in=schema_ids).delete()
    for schema in resource_data.schema:
        try:
            # Update existing schema
            if schema.id:
                schema_instance = ResourceSchema.objects.get(id=int(schema.id))
                schema_instance.key = schema.key
                schema_instance.display_name = get_display_name(schema),
                schema_instance.format = schema.format
                schema_instance.description = schema.description
                schema_instance.resource = resource_instance
                schema_instance.save()
            else:
                # Add new schema
                schema_instance = _create_resource_schema_instance(
                    resource_instance, schema
                )
        except ResourceSchema.DoesNotExist as e:
            schema_instance = _create_resource_schema_instance(
                resource_instance, schema
            )

    for schema in resource_data.schema:
        schema_instance = ResourceSchema.objects.get(
            resource_id=resource_instance.id, key=schema.key
        )
        if schema.parent and schema.parent != "":
            parent_instance = ResourceSchema.objects.get(
                resource_id=resource_instance.id, key=schema.parent
            )
            schema_instance.parent = parent_instance
        if schema.array_field and schema.array_field != "":
            array_field_instance = ResourceSchema.objects.get(
                resource=resource_instance.id, key=schema.array_field
            )
            schema_instance.array_field = array_field_instance
        schema_instance.save()


def _create_resource_schema_instance(resource_instance, schema):
    schema_instance = ResourceSchema(
        key=schema.key,
        display_name=get_display_name(schema),
        format=schema.format,
        description=schema.description,
        resource=resource_instance,
    )
    schema_instance.save()
    return schema_instance


def get_display_name(schema: ResourceSchemaInputType):
    if schema.display_name:
        return schema.display_name
    else:
        return schema.key


def _create_update_api_parameter(api_detail_instance, parameters):
    parameter_ids = []  # List of schemas that already exists.
    parameter_instances = APIParameter.objects.filter(api_details=api_detail_instance)
    for parameter in parameter_instances:
        parameter_ids.append(parameter.id)
    for parameter in parameters:
        if parameter.id:
            parameter_ids.remove(int(parameter.id))
    # Delete parameter which were not updated or created.
    if parameter_ids:
        APIParameter.objects.filter(id__in=parameter_ids).delete()
    for parameter in parameters:
        try:
            # Update existing schema
            if parameter.id:
                parameter_instance = APIParameter.objects.get(id=int(parameter.id))
                parameter_instance.key = parameter.key
                parameter_instance.format = parameter.format
                parameter_instance.default = parameter.default
                parameter_instance.api_details = api_detail_instance
                parameter_instance.description = parameter.description
                parameter_instance.save()
            else:
                # Add new schema
                parameter_instance = APIParameter(default=parameter.default, key=parameter.key, format=parameter.format,
                                                  api_details=api_detail_instance)
                parameter_instance.save()
        except ResourceSchema.DoesNotExist as e:
            parameter_instance = APIParameter(default=parameter.default, key=parameter.key, format=parameter.format,
                                              api_details=api_detail_instance)
            parameter_instance.save()

        parameter_instance.save()


def _create_update_api_details(resource_instance, attribute):
    api_source_instance = APISource.objects.get(id=attribute.api_source)
    try:
        api_detail_object = APIDetails.objects.get(resource=resource_instance)
    except APIDetails.DoesNotExist as e:
        api_detail_object = APIDetails()
    # Create/Update api_details.
    api_detail_object.resource = resource_instance
    api_detail_object.api_source = api_source_instance
    api_detail_object.auth_required = attribute.auth_required
    api_detail_object.url_path = attribute.url_path
    api_detail_object.response_type = attribute.response_type
    api_detail_object.save()
    _create_update_api_parameter(api_detail_object, attribute.parameters)


def _create_update_file_details(resource_instance, attribute):
    if not attribute:
        return

    try:
        file_detail_object = FileDetails.objects.get(resource=resource_instance)
    except FileDetails.DoesNotExist as e:
        file_detail_object = FileDetails(resource=resource_instance)
    if attribute.file:
        file_detail_object.file = attribute.file
        mime_type = mimetypes.guess_type(file_detail_object.file.path)[0]
        if isinstance(mime_type, dict) and "value" in mime_type.keys():
            mime_type = mime_type["value"]
        file_format = FORMAT_MAPPING[mime_type.lower()]
        try:
            if file_format.lower() == "csv":
                data = pd.read_csv(attribute.file)
            if file_format.lower() == "xlsx":
                data = pd.read_excel(attribute.file)
            if file_format.lower() == "json":
                data = json.load(attribute.file)
            if file_format.lower() == "xml":
                data = pd.read_xml(attribute.file)
        except Exception as e:
            resource_instance.delete()
            raise GraphQLError(str(e))

        if file_format:
            file_detail_object.format = file_format
        else:
            resource_instance.delete()
            raise GraphQLError("Unsupported format")
    if attribute.remote_url:
        file_detail_object.remote_url = attribute.remote_url
    file_detail_object.save()


class CreateResource(graphene.Mutation, Output):
    class Arguments:
        resource_data = ResourceInput()

    resource = graphene.Field(ResourceType)

    @staticmethod
    @validate_token
    @auth_user_action_resource(action="create_resource")
    def mutate(
            root,
            info,
            username,
            resource_data: ResourceInput = None,
    ):
        """

        :type resource_data: List of dictionary
        """
        try:
            dataset = Dataset.objects.get(id=resource_data.dataset)
        except Dataset.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {"message": "Dataset with given id not found", "code": "404"}
                    ]
                },
            }
        masked_fields = resource_data.masked_fields
        resource_instance = Resource(
            title=resource_data.title,
            description=resource_data.description,
            dataset=dataset,
            status=resource_data.status,
            masked_fields=masked_fields,
            byte_size=resource_data.byte_size,
            release_date=resource_data.release_date,
            media_type=resource_data.media_type,
            compression_format=resource_data.compression_format,
            packaging_format=resource_data.packaging_format,
            checksum=resource_data.checksum,
        )
        resource_instance.save()

        # Create either api or file object.
        if dataset.dataset_type == DataType.API.value:
            try:
                api_source_instance = APISource.objects.get(
                    id=resource_data.api_details.api_source
                )
                _create_update_api_details(
                    resource_instance=resource_instance,
                    attribute=resource_data.api_details,
                )
            except APISource.DoesNotExist as e:
                resource_instance.delete()
                return {
                    "success": False,
                    "errors": {
                        "id": [
                            {
                                "message": "API Source with given id not found",
                                "code": "404",
                            }
                        ]
                    },
                }
        elif dataset.dataset_type == DataType.FILE.value:
            _create_update_file_details(
                resource_instance=resource_instance,
                attribute=resource_data.file_details,
            )

        _remove_masked_fields(resource_instance)
        _create_update_schema(resource_data, resource_instance)
        log_activity(
            target_obj=resource_instance,
            ip=get_client_ip(info),
            target_group=dataset.catalog.organization,
            username=username,
            verb="Created",
        )

        return CreateResource(success=True, resource=resource_instance)


class UpdateResource(graphene.Mutation, Output):
    class Arguments:
        resource_data = ResourceInput(required=True)

    resource = graphene.Field(ResourceType)

    @staticmethod
    @validate_token
    @auth_user_action_resource(action="update_resource")
    def mutate(root, info, username, resource_data: ResourceInput = None):
        try:
            resource_instance = Resource.objects.get(id=resource_data.id)
            dataset = Dataset.objects.get(id=resource_data.dataset)
        except Resource.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {"message": "Resource with given id not found", "code": "404"}
                    ]
                },
            }
        except Dataset.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {"message": "Dataset with given id not found", "code": "404"}
                    ]
                },
            }
        resource_instance.title = resource_data.title
        resource_instance.description = resource_data.description
        resource_instance.dataset = dataset
        resource_instance.status = resource_data.status
        resource_instance.masked_fields = resource_data.masked_fields
        resource_instance.byte_size = resource_data.byte_size
        resource_instance.release_date = resource_data.release_date
        resource_instance.media_type = resource_data.media_type
        resource_instance.compression_format = resource_data.compression_format
        resource_instance.packaging_format = resource_data.packaging_format
        resource_instance.checksum = resource_data.checksum

        # resource_instance.save()
        # _remove_masked_fields(resource_instance)
        # _create_update_schema(resource_data, resource_instance)
        if dataset.dataset_type == "API":
            try:
                api_source_instance = APISource.objects.get(
                    id=resource_data.api_details.api_source
                )
                _create_update_api_details(
                    resource_instance=resource_instance,
                    attribute=resource_data.api_details,
                )
            except APISource.DoesNotExist as e:
                return {
                    "success": False,
                    "errors": {
                        "id": [
                            {
                                "message": "API Source with given id not found",
                                "code": "404",
                            }
                        ]
                    },
                }
        else:
            _create_update_file_details(
                resource_instance=resource_instance,
                attribute=resource_data.file_details,
            )
        resource_instance.save()
        _remove_masked_fields(resource_instance)
        _create_update_schema(resource_data, resource_instance)
        log_activity(
            target_obj=resource_instance,
            ip=get_client_ip(info),
            target_group=dataset.catalog.organization,
            username=username,
            verb="Updated",
        )
        return UpdateResource(success=True, resource=resource_instance)


class DeleteResource(graphene.Mutation, Output):
    class Arguments:
        resource_data = DeleteResourceInput()

    success = graphene.String()

    # resource = graphene.Field(ResourceType)

    @staticmethod
    @validate_token
    @auth_user_action_resource(action="delete_resource")
    def mutate(root, info, username, resource_data: DeleteResourceInput = None):
        try:
            resource_instance = Resource.objects.get(id=resource_data.id)
        except Resource.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {"message": "Resource with given id not found", "code": "404"}
                    ]
                },
            }
        log_activity(
            target_obj=resource_instance,
            ip=get_client_ip(info),
            target_group=resource_instance.dataset.catalog.organization,
            username=username,
            verb="Deleted",
        )
        resource_schema = ResourceSchema.objects.filter(resource=resource_instance)
        if resource_schema.exists():
            resource_schema.delete()
        resource_instance.delete()
        return DeleteResource(success=True)


class Mutation(graphene.ObjectType):
    create_resource = CreateResource.Field()
    update_resource = UpdateResource.Field()
    delete_resource = DeleteResource.Field()
