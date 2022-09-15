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


class AuthLocation(graphene.Enum):
    HEADER = "HEADER"
    PARAM = "PARAM"


class AuthType(graphene.Enum):
    CREDENTIALS = "CREDENTIALS"
    TOKEN = "TOKEN"


class KeyValueType(graphene.InputObjectType):
    key = graphene.String()
    value = graphene.String()
    description = graphene.String()


class APISourceInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String()
    base_url = graphene.String()
    description = graphene.String()
    api_version = graphene.String()
    headers = graphene.List(of_type=KeyValueType)
    auth_loc = AuthLocation()
    auth_type = AuthType()
    auth_credentials = graphene.List(of_type=KeyValueType)
    auth_token = graphene.String()


class CreateAPISource(graphene.Mutation):
    class Arguments:
        api_source_data = APISourceInput(required=True)

    API_source = graphene.Field(APISourceType)

    @staticmethod
    def mutate(root, info, api_source_data=None):
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
        )
        api_source_instance.save()
        return CreateAPISource(API_source=api_source_instance)
