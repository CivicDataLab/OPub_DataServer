import graphene
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output

from .models import Resource
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


class CreateResource(graphene.Mutation, Output):
    form = CreateResourceMutationForm

    class Arguments:
        title = graphene.String(required=True, description="Resource title")
        description = graphene.String(required=True, description="Resource description")
        file = Upload(required=True, description="Data file")

    resource = graphene.Field(ResourceType)

    @staticmethod
    def mutate(root, info, file=None, **data):
        resource_data = {}
        if file:
            file_data = {"file": file}

        resource_form = CreateResource.form(data, file_data)
        if resource_form.is_valid():
            resource_form.save()
            return CreateResource(success=True)
        else:
            return CreateResource(success=False, errors=resource_form.errors.get_json_data())
        # resource_instance = Resource(
        #     title=title,
        #     description=description,
        #     file=file
        # )
        # resource_instance.save()
        # return CreateResource(resource=resource_instance)
