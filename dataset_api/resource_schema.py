import graphene
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output

from .models import Resource, Dataset


class ResourceType(DjangoObjectType):
    class Meta:
        model = Resource
        fields = "__all__"


class Query(graphene.ObjectType):
    all_resources = graphene.List(ResourceType)
    resource = graphene.Field(ResourceType, resource_id=graphene.Int())

    def resolve_all_resources(self, info, **kwargs):
        return Resource.objects.all()

    def resolve_resource(self, info, resource_id):
        return Resource.objects.get(pk=resource_id)


class ResourceInput(graphene.InputObjectType):
    id: str = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=False)
    file = Upload(required=False)
    dataset = graphene.String(required=True)
    status = graphene.String(required=True)
    format = graphene.String(required=False)
    remote_url = graphene.String(required=False)


class CreateResource(graphene.Mutation, Output):
    class Arguments:
        resource_data = ResourceInput()

    resource = graphene.Field(ResourceType)

    @staticmethod
    def mutate(root, info, resource_data: ResourceInput = None):
        dataset = Dataset.objects.get(id=resource_data.dataset)
        resource_instance = Resource(
            title=resource_data.title,
            description=resource_data.description,
            dataset=dataset,
            format=resource_data.format,
            status=resource_data.status,
            remote_url=resource_data.remote_url,
            file=resource_data.file
        )
        resource_instance.save()
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
            return UpdateResource(success=True, resource=resource_instance)
        return UpdateResource(success=False, resource=None)
