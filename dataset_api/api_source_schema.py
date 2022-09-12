import graphene
from graphene_django import DjangoObjectType

from .models import APISource


class APISourceType(DjangoObjectType):
    class Meta:
        model = APISource
        fields = "__all__"


class Query(graphene.ObjectType):
    all_api_source = graphene.List(APISourceType)
    API_source = graphene.Field(APISourceType, api_source_id=graphene.Int())

    def resolve_all_api_source(self, info, **kwargs):
        return APISource.objects.all()

    def resolve_api_source(self, info, api_source_id):
        return APISource.objects.get(pk=api_source_id)


class APISourceInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String()
    # organization = graphene.String()


class CreateAPISource(graphene.Mutation):
    class Arguments:
        api_source_data = APISourceInput(required=True)

    API_source = graphene.Field(APISourceType)

    @staticmethod
    def mutate(root, info, api_source_data=None):
        api_source_instance = APISource(
            name=api_source_data.name,
        )
        api_source_instance.save()
        return CreateAPISource(API_source=api_source_instance)


class Mutation(graphene.ObjectType):
    create_api_source = CreateAPISource.Field()
