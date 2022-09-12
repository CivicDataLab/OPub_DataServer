import mimetypes
import os

import graphene
from django.core.files.base import ContentFile
from graphene import List
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output
import pandas as pd

from .models import Dataset, ResourceSchema, APIResource, APISource


class ResourceSchemaInputType(graphene.InputObjectType):
    id = graphene.ID(required=False)
    key = graphene.String()
    format = graphene.String()
    description = graphene.String()


class ResourceSchemaType(DjangoObjectType):
    class Meta:
        model = ResourceSchema
        fields = "__all__"


class APIResourceType(DjangoObjectType):
    schema = graphene.List(ResourceSchemaType)

    class Meta:
        model = APIResource
        fields = "__all__"

    def resolve_schema(self, info):
        try:
            schema = ResourceSchema.objects.filter(resource=self)
            return schema
        except ResourceSchema.DoesNotExist as e:
            return []


class Query(graphene.ObjectType):
    all_api_resources = graphene.List(APIResourceType)
    api_resource = graphene.Field(APIResourceType, api_resource_id=graphene.Int())

    def resolve_all_api_resources(self, info, **kwargs):
        return APIResource.objects.all()

    def resolve_api_resource(self, info, api_resource_id):
        return APIResource.objects.get(pk=api_resource_id)


class ResponseType(graphene.Enum):
    JSON = "JSON"
    XML = "XML"
    CSV = "CSV"


class APIResourceInput(graphene.InputObjectType):
    id: str = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=False)
    dataset = graphene.String(required=True)
    status = graphene.String(required=True)
    schema: List = graphene.List(of_type=ResourceSchemaInputType, required=True)
    masked_fields = graphene.List(of_type=graphene.String, default=[], required=False)
    url_path = graphene.String(required=True)
    api_source = graphene.String(required=True)
    auth_required = graphene.Boolean(required=True)
    response_type = ResponseType()


class CreateAPIResource(graphene.Mutation, Output):
    class Arguments:
        resource_data = APIResourceInput()

    resource = graphene.Field(APIResourceType)

    @staticmethod
    def mutate(root, info, api_resource_data: APIResourceInput = None):
        api_source = APISource.objects.get(id=api_resource_data.api_source)
        dataset = Dataset.objects.get(id=api_resource_data.dataset)

        masked_fields = api_resource_data.masked_fields
        resource_instance = APIResource(
            title=api_resource_data.title,
            description=api_resource_data.description,
            dataset=dataset,
            status=api_resource_data.status,
            masked_fields=masked_fields,
            api_source=api_source,
            auth_required=api_resource_data.auth_required,
            response_type=api_resource_data.response_type,
            url_path=api_resource_data.url_path
        )
        for schema in api_resource_data.schema:
            schema_instance = ResourceSchema(key=schema.key, format=schema.format, description=schema.description,
                                             resource=resource_instance)
            schema_instance.save()
        return CreateAPIResource(success=True, resource=resource_instance)


class UpdateAPIResource(graphene.Mutation, Output):
    class Arguments:
        resource_data = APIResourceInput(required=True)

    api_resource = graphene.Field(APIResourceType)

    @staticmethod
    def mutate(root, info, api_resource_data: APIResourceInput = None):
        api_resource_instance = APIResource.objects.get(id=int(api_resource_data.id))
        dataset = Dataset.objects.get(id=api_resource_data.dataset)
        api_source = APISource.objects.get(id=api_resource_data.api_source)
        if api_resource_instance:
            api_resource_instance.title = api_resource_data.title
            api_resource_instance.description = api_resource_data.description
            api_resource_instance.dataset = dataset
            api_resource_instance.status = api_resource_data.status
            api_resource_instance.masked_fields = api_resource_data.masked_fields
            api_resource_instance.api_source = api_source
            api_resource_instance.url_path = api_resource_data.url_path
            api_resource_instance.auth_required = api_resource_data.auth_required
            api_resource_instance.response_type = api_resource_data.response_type
            api_resource_instance.save()
            for schema in api_resource_data.schema:
                try:
                    if schema.id:
                        schema_instance = ResourceSchema.objects.get(id=int(schema.id))
                        schema_instance.key = schema.key
                        schema_instance.format = schema.format
                        schema_instance.description = schema.description
                        schema_instance.save()
                    else:
                        UpdateAPIResource.create_resource_schema_instance(api_resource_instance, schema)

                except ResourceSchema.DoesNotExist as e:
                    UpdateAPIResource.create_resource_schema_instance(api_resource_instance, schema)
            return UpdateAPIResource(success=True, resource=api_resource_instance)
        return UpdateAPIResource(success=False, resource=None)

    @staticmethod
    def create_resource_schema_instance(resource_instance, schema):
        schema_instance = ResourceSchema(key=schema.key, format=schema.format, description=schema.description,
                                         resource=resource_instance)
        schema_instance.save()


class DeleteAPIResource(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    resource = graphene.Field(APIResourceType)

    @staticmethod
    def mutate(root, info, id):
        resource_instance = APIResource.objects.get(id=id)
        resource_instance.delete()
        return DeleteAPIResource(success=True, resource=resource_instance)
