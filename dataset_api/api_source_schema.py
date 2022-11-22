import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from .models import APISource, Organization
from .enums import AuthLocation, AuthType
from .decorators import auth_user_by_org


class APISourceType(DjangoObjectType):
    class Meta:
        model = APISource
        fields = "__all__"


class Query(graphene.ObjectType):
    all_api_source = graphene.List(APISourceType)
    API_source = graphene.Field(APISourceType, api_source_id=graphene.Int())

    def resolve_all_api_source(self, info, **kwargs):
        return APISource.objects.all()

    def resolve_all_api_source_by_org(self, info, **kwargs):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        organization = Organization.objects.get(id=org_id)
        return APISource.objects.filter(organization=organization)

    def resolve_api_source(self, info, api_source_id):
        return APISource.objects.get(pk=api_source_id)


class KeyValueType(graphene.InputObjectType):
    key = graphene.String()
    value = graphene.String()
    description = graphene.String()


class APISourceInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    base_url = graphene.String(required=True)
    description = graphene.String(required=True)
    api_version = graphene.String()
    headers = graphene.List(of_type=KeyValueType)
    auth_loc = graphene.Enum.from_enum(AuthLocation)(default="")
    auth_type = graphene.Enum.from_enum(AuthType)(required=True)
    auth_credentials = graphene.List(of_type=KeyValueType)
    auth_token = graphene.String()


class CreateAPISource(Output, graphene.Mutation):
    class Arguments:
        api_source_data = APISourceInput(required=True)

    API_source = graphene.Field(APISourceType)

    @staticmethod
    @auth_user_by_org(action="create_api_source")
    def mutate(root, info, api_source_data=None):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        organization = Organization.objects.get(id=org_id)
        api_source_instance = APISource(
            title=api_source_data.title,
            base_url=api_source_data.base_url,
            description=api_source_data.description,
            api_version=api_source_data.api_version,
            headers=api_source_data.headers,
            auth_loc=api_source_data.auth_loc,
            auth_type=api_source_data.auth_type,
            auth_credentials=api_source_data.auth_credentials,
            auth_token=api_source_data.auth_token,
            organization=organization
        )
        api_source_instance.save()
        return CreateAPISource(API_source=api_source_instance)


class Mutation(graphene.ObjectType):
    create_api_source = CreateAPISource.Field()
