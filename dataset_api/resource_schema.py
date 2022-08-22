import graphene
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output

from .models import Resource, Dataset
from .resource_form import CreateResourceMutationForm


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
    id = graphene.ID()
    title = graphene.String()
    description = graphene.String()
    file = Upload()
    dataset = graphene.String(required=True)


class CreateResource(graphene.Mutation, Output):
    # form = CreateResourceMutationForm

    class Arguments:
        resource_data = ResourceInput()
        # title = graphene.String(required=True, description="Resource title")
        # description = graphene.String(required=True, description="Resource description")
        # file = Upload(required=True, description="Data file")
        # dataset = graphene.String(required=True)

    resource = graphene.Field(ResourceType)

    @staticmethod
    def mutate(root, info, resource_data=None):
        # resource_data = {}
        # if resource_data.file:
        #     file_data = {"file": file}
        print(resource_data)
        dataset = Dataset.objects.get(id=resource_data.dataset)
        # resource_form = CreateResource.form(resource_data, file_data)
        # if resource_form.is_valid():
        resource_instance = Resource(
            title=resource_data.title,
            description=resource_data.description,
            dataset=dataset,
            file=resource_data.file
        )
        resource_instance.save()
        # resource_form.save()
        return CreateResource(success=True)
        # else:
        #     return CreateResource(success=False, errors=resource_form.errors.get_json_data())
        # resource_instance = Resource(
        #     title=title,
        #     description=description,
        #     file=file
        # )
        # resource_instance.save()
        # return CreateResource(resource=resource_instance)
