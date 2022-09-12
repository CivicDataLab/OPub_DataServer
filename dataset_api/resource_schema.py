import graphene
from graphene import List
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output
import pandas as pd

from .models import Resource, Dataset, ResourceSchema


class ResourceSchemaInputType(graphene.InputObjectType):
    id = graphene.ID(required=False)
    key = graphene.String()
    format = graphene.String()
    description = graphene.String()


class ResourceSchemaType(DjangoObjectType):
    class Meta:
        model = ResourceSchema
        fields = "__all__"


class ResourceType(DjangoObjectType):
    schema = graphene.List(ResourceSchemaType)

    class Meta:
        model = Resource
        fields = "__all__"

    def resolve_schema(self, info):
        try:
            schema = ResourceSchema.objects.filter(resource=self)
            return schema
        except ResourceSchema.DoesNotExist as e:
            return []


class Query(graphene.ObjectType):
    all_resources = graphene.List(ResourceType)
    resource = graphene.Field(ResourceType, resource_id=graphene.Int())
    resource_columns = graphene.List(graphene.String, resource_id=graphene.Int())

    def resolve_all_resources(self, info, **kwargs):
        return Resource.objects.all()

    def resolve_resource(self, info, resource_id):
        return Resource.objects.get(pk=resource_id)

    def resolve_resource_columns(self, info, resource_id):
        resource = Resource.objects.get(pk=resource_id)
        if resource.file and len(resource.file.path) and 'csv' in resource.format.lower():
            file = pd.read_csv(resource.file.path)
            return file.columns.tolist()


class ResourceInput(graphene.InputObjectType):
    id: str = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=False)
    file = Upload(required=False)
    dataset = graphene.String(required=True)
    status = graphene.String(required=True)
    format = graphene.String(required=False)
    remote_url = graphene.String(required=False)
    schema: List = graphene.List(of_type=ResourceSchemaInputType)


class CreateResource(graphene.Mutation, Output):
    class Arguments:
        resource_data = ResourceInput()

    resource = graphene.Field(ResourceType)

    @staticmethod
    def mutate(root, info, resource_data: ResourceInput = None):
        """

        :type resource_data: List of dictionary
        """
        dataset = Dataset.objects.get(id=resource_data.dataset)
        resource_instance = Resource(
            title=resource_data.title,
            description=resource_data.description,
            dataset=dataset,
            format=resource_data.format,
            status=resource_data.status,
            remote_url=resource_data.remote_url,
            file=resource_data.file,
        )
        resource_instance.save()
        for schema in resource_data.schema:
            schema_instance = ResourceSchema(key=schema.key, format=schema.format, description=schema.description,
                                             resource=resource_instance)
            schema_instance.save()
        return CreateResource(success=True, resource=resource_instance)


class UpdateResource(graphene.Mutation, Output):
    class Arguments:
        resource_data = ResourceInput(required=True)

    resource = graphene.Field(ResourceType)

    @staticmethod
    def mutate(root, info, resource_data: ResourceInput = None):
        resource_instance = Resource.objects.get(id=int(resource_data.id))
        dataset = Dataset.objects.get(id=resource_data.dataset)
        if resource_instance:
            resource_instance.title = resource_data.title
            resource_instance.description = resource_data.description
            resource_instance.dataset = dataset
            resource_instance.format = resource_data.format
            resource_instance.remote_url = resource_data.remote_url
            resource_instance.file = resource_data.file
            resource_instance.status = resource_data.status
            resource_instance.save()

            for schema in resource_data.schema:
                try:
                    if schema.id:
                        schema_instance = ResourceSchema.objects.get(id=int(schema.id))
                        schema_instance.key = schema.key
                        schema_instance.format = schema.format
                        schema_instance.description = schema.description
                        schema_instance.save()
                    else:
                        UpdateResource.create_resource_schema_instance(resource_instance, schema)

                except ResourceSchema.DoesNotExist as e:
                    UpdateResource.create_resource_schema_instance(resource_instance, schema)
            return UpdateResource(success=True, resource=resource_instance)
        return UpdateResource(success=False, resource=None)

    @staticmethod
    def create_resource_schema_instance(resource_instance, schema):
        schema_instance = ResourceSchema(key=schema.key, format=schema.format, description=schema.description,
                                         resource=resource_instance)
        schema_instance.save()


class DeleteResource(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    resource = graphene.Field(ResourceType)

    @staticmethod
    def mutate(root, info, id):
        resource_instance = Resource.objects.get(id=id)
        resource_instance.delete()
        return DeleteResource(success=True, resource=resource_instance)
