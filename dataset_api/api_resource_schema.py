import graphene
from graphene import List
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from .models import Dataset, ResourceSchema, APIResource, APISource
from .resource_schema import ResourceSchemaType, ResourceSchemaInputType
# from .search import index_api_resource, update_api_resource, delete_api_resource


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
    api_resource_dataset = graphene.List(APIResourceType, dataset_id=graphene.Int())

    def resolve_all_api_resources(self, info, **kwargs):
        return APIResource.objects.all()

    def resolve_api_resource(self, info, api_resource_id):
        return APIResource.objects.get(pk=api_resource_id)

    def resolve_api_resource_dataset(self, info, dataset_id):
        return APIResource.objects.get(dataset=dataset_id)


# class ResponseType(graphene.Enum):
#     JSON = "JSON"
#     XML = "XML"
#     CSV = "CSV"


class APIResourceInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=False)
    dataset = graphene.String(required=True)
    status = graphene.String(required=True)
    schema: List = graphene.List(of_type=ResourceSchemaInputType, required=True)
    masked_fields = graphene.List(of_type=graphene.String, default=[], required=False)
    url_path = graphene.String(required=True)
    api_source = graphene.String(required=True)
    auth_required = graphene.Boolean(required=True)
    # response_type = ResponseType()


class CreateAPIResource(graphene.Mutation, Output):
    class Arguments:
        api_resource_data = APIResourceInput()

    API_resource = graphene.Field(APIResourceType)

    @staticmethod
    def mutate(root, info, api_resource_data: APIResourceInput = None):
        api_source = APISource.objects.get(id=api_resource_data.api_source)
        dataset = Dataset.objects.get(id=api_resource_data.dataset)

        masked_fields = api_resource_data.masked_fields
        api_resource_instance = APIResource(
            title=api_resource_data.title,
            description=api_resource_data.description,
            dataset=dataset,
            status=api_resource_data.status,
            masked_fields=masked_fields,
            api_source=api_source,
            auth_required=api_resource_data.auth_required,
            # response_type=api_resource_data.response_type,
            url_path=api_resource_data.url_path,
        )
        api_resource_instance.save()

        for schema in api_resource_data.schema:
            schema_instance = ResourceSchema(
                key=schema.key,
                format=schema.format,
                description=schema.description,
                resource=api_resource_instance,
            )
            schema_instance.save()

        # Index data to Elasticsearch
        # index_api_resource(api_resource_instance)
        return CreateAPIResource(success=True, API_resource=api_resource_instance)


class UpdateAPIResource(graphene.Mutation, Output):
    class Arguments:
        api_resource_data = APIResourceInput(required=True)

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
                        UpdateAPIResource.create_resource_schema_instance(
                            api_resource_instance, schema
                        )

                except ResourceSchema.DoesNotExist as e:
                    UpdateAPIResource.create_resource_schema_instance(
                        api_resource_instance, schema
                    )

            # Update data in Elasticsearch
            # update_api_resource(api_resource_instance)
            return UpdateAPIResource(success=True, api_resource=api_resource_instance)
        return UpdateAPIResource(success=False, api_resource=None)

    @staticmethod
    def create_resource_schema_instance(resource_instance, schema):
        schema_instance = ResourceSchema(
            key=schema.key,
            format=schema.format,
            description=schema.description,
            resource=resource_instance,
        )
        schema_instance.save()


class DeleteAPIResource(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    # resource = graphene.Field(APIResourceType)
    success = graphene.String()

    @staticmethod
    def mutate(root, info, id):
        resource_instance = APIResource.objects.get(id=id)
        # Delete data in Elasticsearch
        # delete_api_resource(resource_instance)
        resource_instance.delete()
        return DeleteAPIResource(success=True)
